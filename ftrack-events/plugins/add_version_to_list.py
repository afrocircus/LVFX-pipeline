import ftrack
import datetime


def getDate():
    today = datetime.datetime.today()
    if today.hour >= 12:
        dailiesDate = today + datetime.timedelta(1)
    else:
        dailiesDate = today
    date = '%d-%02d-%02d' % (dailiesDate.year, dailiesDate.month, dailiesDate.day)
    return date


def addToList(taskid, version):
    task = ftrack.Task(id=taskid)
    project = task.getProject()
    listCategory = ftrack.ListCategory('Reviews')
    date = getDate()
    listName = 'Dailies_{0}'.format(date)
    try:
        listObj = project.getList(listName)
    except:
        listObj = project.createList(listName, listCategory, ftrack.AssetVersion)
    listObj.append(version)


def callback(event):
    """
    This plugin adds a newly uploaded asset version with status "Pending Internal Review"
    to the latest review list.
    """
    for entity in event['data'].get('entities', []):
        if entity.get('entityType') == 'assetversion' and entity['action'] == 'update':
            assetVersion = ftrack.AssetVersion(id=entity.get('entityId'))
            if assetVersion.getStatus().getName() == 'Pending Internal Review':
                if assetVersion.get('taskid'):
                    addToList(assetVersion.get('taskid'), assetVersion)

# Subscribe to events with the update topic.
ftrack.setup()
ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
ftrack.EVENT_HUB.wait()