import ftrack
import os
import subprocess
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
                copyTemplateFiles(templateFolder, task, taskFolder, shotName)


# Subscribe to events with the update topic.
ftrack.setup()
ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
ftrack.EVENT_HUB.wait()
