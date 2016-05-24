import ftrack
import sys
import os
import json


FOLDER_STRUCT = os.path.join(os.environ['FTRACK_EVENT_SERVER_PLUGINS'], 'folder_structure.json')


def callback(event):
    """ This plugin creates a template folder structure on disk.
    """
    for entity in event['data'].get('entities', []):
        if entity.get('entityType') == 'show' and entity['action'] == 'add':
            project = ftrack.Project(id=entity['entityId'])
            schemeId = project.get('projectschemeid')
            scheme = ftrack.ProjectScheme(schemeId)
            if scheme.get('name') == 'VFX Scheme':
                projFolder = project.get('root')
                if projFolder == '':
                    disk = ftrack.Disk(project.get('diskid'))
                    rootFolder = ''
                    if sys.platform == 'win32':
                        rootFolder = disk.get('windows')
                    elif sys.platform == 'linux2':
                        rootFolder = disk.get('unix')
                    projFolder = os.path.join(rootFolder, project.getName())
                makeDirs(projFolder)


def makeDirs(projDir):
    try:
        jd = open(FOLDER_STRUCT).read()
        data = json.loads(jd)
        for key in data:
            folder = os.path.join(projDir, key)
            if not os.path.exists(folder):
                os.makedirs(folder)
            for each in data[key]:
                subFolder = os.path.join(folder, each)
                if not os.path.exists(subFolder):
                    os.makedirs(subFolder)
    except:
        print "Could not find " + FOLDER_STRUCT
        print "No directories created"

# Subscribe to events with the update topic.
ftrack.setup()
ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
ftrack.EVENT_HUB.wait()