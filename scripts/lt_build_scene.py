import sys
import os
import ftrack
import argparse
import glob
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
    return animMeta


def getEnvPublishFile(shot):
    layoutTask = getTaskByName(shot, 'layout')
    envFile = None
    if layoutTask:
        metadata = layoutTask.getMeta()
        if 'publish_env_file' in metadata:
            envFile = metadata['publish_env_file']
    return envFile


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


def buildScene(filepath, cameraFile, envFile, animMeta):
    cmds.file(new=True)
    cmds.file(rename=filepath)
    if isValidFile(envFile):
        cmds.file(envFile, r=True)
    if isValidFile(cameraFile):
        cmds.AbcImport(cameraFile, mode='import')

    for char in animMeta:
        if 'ref' in animMeta[char]:
            rigFile = animMeta[char]['ref']
            if 'modeling' in rigFile:
                modelRef = rigFile
            else:
                modelRef = getModelingRef(rigFile)
            if modelRef != '':
                cmds.file(modelRef, r=True, namespace='char_%s' % char)
                if 'publish' in animMeta[char] and 'mayaNode' in animMeta[char]:
                    print animMeta[char]
                    cmds.AbcImport(animMeta[char]['publish'], connect=animMeta[char]['mayaNode'],
                                   mode='import', fitTimeRange=True)
                    print 'asset import: ' + animMeta[char]['publish']

    cmds.file(save=True, type='mayaBinary', force=True)


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
    envFile = getEnvPublishFile(shot)
    animMeta = getCharPublishFile(shot)

    filename = '%s_v01.mb' % shot.getName()
    filepath = os.path.join(taskDir, filename)
    buildScene(filepath, shotCam, envFile, animMeta)

    cmds.quit()
    os._exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
