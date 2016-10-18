import ftrack
import os
import subprocess
import re
import sys
import shutil


def getShotFolder(task):
    shotFolder = ''
    parents = task.getParents()
    parents.reverse()
    for parent in parents:
        if 'objecttypename' in parent.keys():
            shotFolder = os.path.join(shotFolder, parent.getName())
    return shotFolder


def getProjectFolder(project):
    projFolder = project.get('root')
    if projFolder == '':
        disk = ftrack.Disk(project.get('diskid'))
        rootFolder = ''
        if sys.platform == 'win32':
            rootFolder = disk.get('windows')
        elif sys.platform == 'linux2':
            rootFolder = disk.get('unix')
        projFolder = os.path.join(rootFolder, project.getName())
    return projFolder


def copyTemplateFiles(templateFolder, task, taskFolder, shotName):
    taskName = task.getType().getName().lower()
    for file in os.listdir(templateFolder):
        filepath = os.path.join(templateFolder, file)
        if os.path.isfile(filepath):
            if taskName in file:
                fname, fext = os.path.splitext(file)
                newFilepath = os.path.join(taskFolder, '%s_v01%s' % (shotName, fext))
                if not os.path.exists(newFilepath):
                    shutil.copy(filepath, newFilepath)
                os.chmod(newFilepath, 0666)
                parentDir = os.path.dirname(newFilepath)
                try:
                    os.chmod(parentDir, 0777)
                except:
                    print "could not change directory permission for %s" % parentDir
                metadata = {
                    'filename':newFilepath
                }
                task.setMeta(metadata)


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


def copyFromLayoutPublish(taskFolder, taskName):
    layoutDir = os.path.join(taskFolder.split(taskName)[0], 'layout', 'publish')
    publishFile = ''
    # If the layout publish dir exists
    if os.path.exists(layoutDir):
        versions = []
        # get the latest published version
        for each in os.listdir(layoutDir):
            versionDir = os.path.join(layoutDir, each)
            if os.path.isdir(versionDir):
                try:
                    versions.append(version_get(versionDir, 'v')[1])
                except ValueError:
                    continue
        versions.sort()
        latestVersion = os.path.join(layoutDir, 'v' + versions[-1])
        publishFile = os.path.join(latestVersion, 'animation_publish.mb')
    return publishFile


def createTemplateFiles(templateFolder, task, taskFolder, shotName):
    # Create template files based on task type
    taskType = task.getType().getName().lower()
    if taskType == 'modeling':
        filepath = os.path.join(templateFolder, taskType + '.mb')
        if os.path.exists(filepath):
            taskFolder = os.path.join(taskFolder, 'maya')
            if not os.path.exists(taskFolder):
                os.makedirs(taskFolder)
            newFilePath = os.path.join(taskFolder, '%s_v01.mb' % shotName)
            if not os.path.exists(newFilePath):
                shutil.copy(filepath, newFilePath)
            os.chmod(newFilePath, 0666)
            metadata = {'filename': newFilePath}
            task.setMeta(metadata)
    elif taskType == 'previz':
        # Copying from latest layout publish
        publishFile = copyFromLayoutPublish(taskFolder, 'previz')
        newFilePath = os.path.join(taskFolder, '%s_v01.mb' % shotName)
        # if an animation_publish file exists in the latest layout publish, copy it over.
        if os.path.exists(publishFile) and not os.path.exists(newFilePath):
            shutil.copy(publishFile, newFilePath)
        os.chmod(newFilePath, 0666)
        metadata = {'filename': newFilePath}
        task.setMeta(metadata)
    elif taskType == 'animation':
        # First check if a previz version exists
        previzDir = os.path.join(taskFolder.split('animation')[0], 'previz')
        previzFiles = [f for f in os.listdir(previzDir) if os.path.isfile(os.path.join(previzDir, f))]
        # get latest previz file
        if previzFiles:
            maxVersion = 1
            for f in previzFiles:
                try:
                    version = int(version_get(f, 'v')[1])
                except ValueError:
                    continue
                if version >= maxVersion:
                    publishFile = f
                    maxVersion = version
            publishFile = os.path.join(previzDir, publishFile)
        # Else get latest layout publish file
        else:
            publishFile = copyFromLayoutPublish(taskFolder, 'animation')
        newFilePath = os.path.join(taskFolder, '%s_v01.mb' % shotName)

        # Copy over the latest publish file.
        if os.path.exists(publishFile) and not os.path.exists(newFilePath):
            shutil.copy(publishFile, newFilePath)
        os.chmod(newFilePath, 0666)
        metadata = {'filename': newFilePath}
        task.setMeta(metadata)
    else:
        copyTemplateFiles(templateFolder, task, taskFolder, shotName)


def createAssetFolders(task, projectFolder):
    taskName = task.getName().lower()
    asset = task.getParent()
    assetType = asset.getType().getName().lower()
    assetName = asset.getName()
    assetFolder = os.path.join(projectFolder, 'assets', assetType, assetName)
    taskFolder = os.path.join(assetFolder, taskName)
    if not os.path.exists(taskFolder):
        os.makedirs(taskFolder)
        try:
            os.chmod(taskFolder, 0777)
        except:
            print "could not change directory permission for %s" % taskFolder
    return taskFolder


def callback(event):
    """ This plugin creates a template folder structure on disk.
    """
    for entity in event['data'].get('entities', []):
        if entity.get('entityType') == 'task' and entity['action'] == 'add':
            task = ftrack.Task(id=entity['entityId'])
            taskName = task.getName().lower()
            if task.getObjectType() == 'Task':
                project = task.getProject()
                projFolder = getProjectFolder(project)
                shotName = task.getParent().getName()
                if task.getParent().get('objecttypename') == 'Asset Build':
                    taskFolder = createAssetFolders(task, projFolder)
                    shotName = '{0}_{1}'.format(shotName, taskName)
                else:
                    shotsFolder = os.path.join(projFolder, 'shots')
                    shotFolder = getShotFolder(task)
                    if shotFolder == '':
                        return
                    sceneFolder = os.path.join(shotsFolder, shotFolder, 'scene')
                    taskFolder = os.path.join(sceneFolder, taskName)
                    if not os.path.exists(taskFolder):
                        os.makedirs(taskFolder)
                        try:
                            os.chmod(taskFolder, 0777)
                        except:
                            print "could not change directory permission for %s" % taskFolder
                templateFolder = os.path.join(projFolder, 'template_files')
                createTemplateFiles(templateFolder, task, taskFolder, shotName)


# Subscribe to events with the update topic.
ftrack.setup()
ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
ftrack.EVENT_HUB.wait()
