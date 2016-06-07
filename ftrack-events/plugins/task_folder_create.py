import ftrack
import os
import sys
import shutil

def getSequence(task):
    sq = ''
    for parent in task.getParents():
        if 'objecttypename' in parent.keys():
            if parent.get('objecttypename') == 'Sequence':
                sq = parent.getName()
    return sq


def copyTemplateFiles(templateFolder, task, taskFolder, shotName):
    taskName = task.getName()
    for file in os.listdir(templateFolder):
        filepath = os.path.join(templateFolder, file)
        if os.path.isfile(filepath):
            if taskName in file:
                fname, fext = os.path.splitext(file)
                newFilepath = os.path.join(taskFolder, '%s_v01%s' % (shotName, fext))
                if not os.path.exists(newFilepath):
                    shutil.copy(filepath, newFilepath)
                metadata = {
                    'filename':newFilepath
                }
                task.setMeta(metadata)


def callback(event):
    """ This plugin creates a template folder structure on disk.
    """
    for entity in event['data'].get('entities', []):
        if entity.get('entityType') == 'task' and entity['action'] == 'add':
            task = ftrack.Task(id=entity['entityId'])
            taskName = task.getName().lower()
            if task.getObjectType() == 'Task':
                project = task.getProject()
                sq = getSequence(task)
                shotName = task.getParent().getName()
                if sq == '':
                    return
                projFolder = project.get('root')
                if projFolder == '':
                    disk = ftrack.Disk(project.get('diskid'))
                    rootFolder = ''
                    if sys.platform == 'win32':
                        rootFolder = disk.get('windows')
                    elif sys.platform == 'linux2':
                        rootFolder = disk.get('unix')
                    projFolder = os.path.join(rootFolder, project.getName())
                shotsFolder = os.path.join(projFolder, 'shots')
                templateFolder = os.path.join(projFolder, 'template_files')
                sqFolder = os.path.join(shotsFolder, sq)
                shotFolder = os.path.join(sqFolder, shotName)
                sceneFolder = os.path.join(shotFolder, 'scene')
                taskFolder = os.path.join(sceneFolder, taskName)
                if not os.path.exists(taskFolder):
                    os.makedirs(taskFolder)
                copyTemplateFiles(templateFolder, task, taskFolder, shotName)


# Subscribe to events with the update topic.
ftrack.setup()
ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
ftrack.EVENT_HUB.wait()
