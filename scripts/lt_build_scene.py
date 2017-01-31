import sys
import os
import ftrack
import argparse
import glob
import re
import shutil
import maya.cmds as cmds
import maya.standalone

def getRenderCam(shot):
    camera = shot.get('shot_cam')
    return camera


def getTaskByName(shot, taskName):
    for t in shot.getTasks():
        if t.getType().getName().lower() == taskName:
            return t
    return None


def getCharPublishFile(shot):
    animMeta = {}
    animTask = getTaskByName(shot, 'animation')
    version = None
    if animTask:
        meta = animTask.getMeta()
        refs = [ (key, meta[key]) for key in meta.keys() if 'ref' in key ]
        for ref, filepath in refs:
            charname = ref.split('ref_')[-1]
            animMeta[charname] = {'ref': filepath}
            publishKey = 'publish_%s' % charname
            if publishKey in meta:
                animMeta[charname]['publish'] = meta[publishKey]
            mayaKey = 'mayanode_%s' % charname
            if mayaKey in meta:
                animMeta[charname]['mayaNode'] = meta[mayaKey]
        if 'version' in meta:
            version = meta['version']
    return animMeta, version


def getEnvPublishFile(shot):
    layoutTask = getTaskByName(shot, 'layout')
    version = None
    envFile = None
    if layoutTask:
        metadata = layoutTask.getMeta()
        if 'publish_env_file' in metadata:
            envFile = metadata['publish_env_file']
        if 'version' in metadata:
            version = metadata['version']
    return envFile, version


def isValidFile(filepath):
    if filepath and os.path.exists(filepath):
        return True
    else:
        return False


def getModelingRef(rigFile):
    modelRef = ''
    assetDir = rigFile.split('rigging')[0]
    modelPublishDir = os.path.join(assetDir, 'modeling', 'publish')
    if os.path.exists(modelPublishDir):
        refFiles = [f for f in glob.glob(os.path.join(modelPublishDir, '*_ref.mb')) if os.path.isfile(f)]
        if refFiles:
            modelRef = refFiles[0]

    return modelRef


def buildScene(cameraFile, envFile, charFile):
    '''
    Build the final lighting scene file.
    :param cameraFile: Camera alembic file to import
    :param envFile:  Published layout env file to reference
    :param charFile: Baked char file to reference
    :return:
    '''
    if isValidFile(envFile):
        try:
            # Check if env file is already referenced.
            cmds.referenceQuery(envFile, filename=True)
        except RuntimeError:
            cmds.file(envFile, r=True)

    if isValidFile(charFile):
        try:
            # Check if env file is already referenced.
            cmds.referenceQuery(charFile, filename=True)
        except RuntimeError:
            cmds.file(charFile, r=True)

    if isValidFile(cameraFile):
        # Check if camera exists in scene
        cameraNodes = cmds.ls('renderCam')
        if len(cameraNodes) == 1:
            # Camara exists, delete and re-import alembic
            cameraNode = cameraNodes[0]
            cmds.delete(cameraNode)
        cmds.AbcImport(cameraFile, mode='import')

    cmds.file(save=True, type='mayaBinary', force=True)


def version_get(string, prefix, suffix=None):
    """Extract version information from filenames.  Code from Foundry's nukescripts.version_get()"""

    if string is None:
        raise ValueError, "Empty version string - no match"

    regex = "[/_.]" + prefix + "\d+"
    matches = re.findall(regex, string, re.IGNORECASE)
    if not len(matches):
        msg = "No \"_" + prefix + "#\" found in \"" + string + "\""
        raise ValueError, msg
    return matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group()


def getLatestVersion(taskDir):
    '''
    Get the max lighting file version in the folder
    :param taskDir: Lighting task folder on disk
    :return: maxVersion
    '''
    publishFile = ''
    lightingFiles = [f for f in glob.glob(os.path.join(taskDir, '*_v[0-9]*.mb'))]
    maxVersion = 1
    if lightingFiles:
        for f in lightingFiles:
            try:
                version = int(version_get(f, 'v')[1])
            except ValueError:
                continue
            if version >= maxVersion:
                publishFile = f
                maxVersion = version
    return maxVersion


def getCharBakeVersion(envVer, animVer, metadata):
    '''
    Get the char bake version based on the animation and layout publish versions
    :param envVer: Latest Layout Publish Version
    :param animVer: Latest Animation Publish Version
    :param metadata: Lighting task metadata
    :return: charVersion: Baked char version
    '''
    taskAnimVer = taskEnvVer = charVersion = None

    if 'anim_version' in metadata:
        taskAnimVer = metadata['anim_version']
    if 'env_version' in metadata:
        taskEnvVer = metadata['env_version']
    if 'char_version' in metadata:
        charVersion = int(metadata['char_version'].split('v')[-1])

    if not charVersion:
        charVersion = 1
    elif taskEnvVer != envVer or taskAnimVer != animVer:
        # If there is a new layout or animation publish version, char bake version changes
        charVersion += 1
    return charVersion


def buildCharFile(taskDir, animMeta, version):
    '''
    Build a char file containing the baked animation.
    :param taskDir: Lighting folder on disk
    :param animMeta: Animation task metadta
    :param version: Version of the baked char file
    :return: charFile: Baked char file path
    '''
    bakedDir = os.path.join(taskDir, 'baked')
    charFile = os.path.join(bakedDir, 'char.mb')
    if os.path.exists(charFile):
        os.remove(charFile)
    versionDir = os.path.join(bakedDir, 'v%02d' % version)
    if not os.path.exists(versionDir):
        os.makedirs(versionDir)
    charRefFile = os.path.join(versionDir, 'char.mb')
    if os.path.exists(charRefFile):
        os.remove(charRefFile)
    cmds.file(new=True, f=True)
    cmds.file(rename='%s' % charRefFile)

    for char in animMeta:
        if 'ref' in animMeta[char]:
            rigFile = animMeta[char]['ref']
            if 'modeling' in rigFile:
                modelRef = rigFile
            else:
                modelRef = getModelingRef(rigFile)
            if modelRef != '':
                cmds.file(modelRef, i=True, namespace='char_%s' % char)
                if 'publish' in animMeta[char] and 'mayaNode' in animMeta[char]:
                    cmds.AbcImport(animMeta[char]['publish'], connect=animMeta[char]['mayaNode'],
                                   mode='import', fitTimeRange=True)
                    print 'asset import: ' + animMeta[char]['publish']

    cmds.file(save=True, type='mayaBinary', force=True)
    cmds.quit()
    os.symlink(charRefFile, charFile)
    return charFile


def main(argv):
    parser = argparse.ArgumentParser(description='Builds a lighting scene file.')
    parser.add_argument('-taskid', help='Ftrack Task ID', required=True)
    parser.add_argument('-taskDir', help='Task Directory', required=True)

    # initialize maya
    maya.standalone.initialize('Python')
    cmds.loadPlugin('AbcImport')

    args = parser.parse_args()
    taskid = args.taskid
    taskDir = args.taskDir

    task = ftrack.Task(taskid)
    shot = task.getParent()
    shotCam = getRenderCam(shot)
    envFile, envVersion = getEnvPublishFile(shot)
    animMeta, animVersion = getCharPublishFile(shot)

    metadata = task.getMeta()
    # Get the char bake version
    charVersion = getCharBakeVersion(envVersion, animVersion, metadata)
    # Bake out the char file from latest animation publish
    charFile = buildCharFile(taskDir, animMeta, charVersion)

    filename = '%s_v01.mb' % shot.getName()
    filepath = os.path.join(taskDir, filename)

    if os.path.exists(filepath):
        version = getLatestVersion(taskDir)
        oldFile = '%s_v%02d.mb' % (shot.getName(), version)
        newFile = '%s_v%02d.mb' % (shot.getName(), version+1)
        oldFilePath = os.path.join(taskDir, oldFile)
        newFilePath = os.path.join(taskDir, newFile)
        shutil.copyfile(oldFilePath, newFilePath)
        cmds.file(filepath, open=True)
        metadata['filename'] = newFilePath
    else:
        cmds.file(new=True)
        cmds.file(rename=filepath)
        metadata['filename'] = filepath

    # build the scene
    buildScene(shotCam, envFile, charFile)

    cmds.quit()
    # Set metadata
    metadata['charFile'] = charFile
    metadata['char_version'] = 'v%02d' % charVersion
    metadata['anim_version'] = animVersion
    metadata['env_version'] = envVersion
    task.setMeta(metadata)

    os._exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
