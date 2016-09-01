__author__ = 'Natasha'

import ftrack
import ftrack_api
import os
import shlex
import subprocess
import json
from datetime import datetime


def startANewSession():
    session = ftrack_api.Session(
            server_url='http://192.168.0.209',
            api_user='Natasha',
            api_key='68ec1c94-8e8f-4355-a121-d054f4af91f5'
        )
    return session

def startASession():
    session = ftrack_api.session.Session()
    return session


def getInputFilePath(shotid):
    baseDir = '/data/production/'
    shot = ftrack.Shot(id=shotid)
    shotName = '%s_%s' % (shot.getSequence().getName(), shot.getName())
    hierarchy = reversed(shot.getParents())
    imgDir = baseDir

    for p in hierarchy:
        if isinstance(p, ftrack.Project):
            pname = p.getName()
            if pname == 'willowstr':
                pname = 'ds_willowStreet'
            imgDir = os.path.join(imgDir, pname)
            imgDir = os.path.join(imgDir, 'shots')
        else:
            imgDir = os.path.join(imgDir, p.getName())

    baseDir = os.path.join(imgDir, shotName)
    inputFile = ''
    imgDir = os.path.join(baseDir, 'img/comp')
    if os.path.exists(imgDir):
        verDirs = [d for d in os.listdir(imgDir) if os.path.isdir(os.path.join(imgDir, d))]
        if verDirs:
            imgDir = os.path.join(imgDir, verDirs[-1])
            files = [f for f in os.listdir(imgDir) if os.path.isfile(os.path.join(imgDir, f))]
            if files:
                inputFile = files[0]
    return imgDir, inputFile


def getOutputFilePath(shotid, taskid, inBaseDir):
    baseDir = '/data/production/'
    shot = ftrack.Shot(id=shotid)
    pname = shot.getProject().getName()
    if pname == 'willowstr':
        pname = 'ds_willowStreet'
    baseDir = os.path.join(baseDir, pname)
    today = datetime.today()
    day = str(today.day)
    if len(day) == 1:
        day = '0%s' % day
    datefolder = '%s-%s-%s' % (today.year, today.month, day)
    baseDir = os.path.join(baseDir, 'production/approvals')
    baseDir = os.path.join(baseDir, datefolder)
    if not os.path.exists(baseDir):
        os.mkdir(baseDir)
    sq = shot.getSequence().getName()
    task = ftrack.Task(taskid).getName()
    ver = inBaseDir.split('/')[-1]
    filename = '%s_%s_%s_%s.mov' % (sq, shot.getName(), task, ver)
    outputFile = os.path.join(baseDir, filename)
    outputFile = outputFile.replace(' ', '_')
    return outputFile


def getTaskPath(session, taskid):
    item = session.query('Task where id is %s' % taskid).one()
    taskPath = ''
    while True:
        taskPath = item['name'] + taskPath
        item = item['parent']
        if not item:
            break
        taskPath = ' / ' + taskPath
    return taskPath


def getAllProjectNames(session):
    projects = session.query('Project').all()
    projList = [proj['name'] for proj in projects]
    projList.sort()
    return projList


def getProject(session, projName):
    project = session.query('Project where name is "%s"' % projName).one()
    return project


def getNode(session, nodePath):
    nodes = nodePath.split(' / ')
    parent = getProject(session, nodes[0])
    nodes = nodes[1:]
    if nodes:
        for node in nodes:
            for child in parent['children']:
                if child['name'] == node.strip():
                    parent = child
                    break
    return parent


def getTask(session, projPath):
    parent = getNode(session, projPath)
    taskName = projPath.split(' / ')[-1]
    projName = projPath.split(' / ')[0]
    task = session.query('Task where parent.id is %s and name is %s '
                         'and project.name is %s' % (parent['parent']['id'],
                                                     taskName, projName)).one()
    return task


def isTask(session, taskPath):
    task = getTask(session, taskPath)
    if task['object_type']['name'] == 'Task':
        return True
    else:
        return False


def getAllChildren(session, projPath):
    parent = getNode(session, projPath)
    children = parent['children']
    childList = []
    for child in children:
        if child['name'] == 'Asset builds' or child['object_type']['name'] == 'Asset Build':
            childList.append(('assetbuild', child['name']))
        elif child['object_type']['name'] == 'Episode':
            childList.append(('episode', child['name']))
        elif child['object_type']['name'] == 'Sequence':
            childList.append(('sequence', child['name']))
        elif child['object_type']['name'] == 'Shot':
            childList.append(('shot', child['name']))
        elif child['object_type']['name'] == 'Folder':
            childList.append(('folder', child['name']))
        else:
            childList.append(('task', child['name']))
    return childList


def getAllAssets(session, projPath):
    parent = getNode(session, projPath)
    assets = session.query('Asset where parent.name is "%s"' % parent['parent']['name'])
    assetList = [asset['name'] for asset in assets]
    return assetList


def getAllStatuses(session, projPath):
    projectName = projPath.split(' / ')[0]
    project = getProject(session, projectName)
    task = getTask(session, projPath)
    projectSchema = project['project_schema']
    statuses = projectSchema.get_statuses('Task', task['type']['id'])
    return statuses


def getStatusList(session, projPath):
    statuses = getAllStatuses(session, projPath)
    statusList = [status['name'] for status in statuses]
    return statusList


def getCurrentStatus(session, projPath):
    task = getTask(session, projPath)
    status = task['status']['name']
    return status


def convertToJpg(inputFile, outfilejpg):
    jpgcmd = 'convert.exe %s %s' % (inputFile, outfilejpg)
    args = shlex.split(jpgcmd)
    result = subprocess.call(args)
    return result


def convertMp4Files(inputFile, outfilemp4):
    mp4cmd = 'ffmpeg -y -i "%s" -ac 2 -b:v 2000k -c:a aac -c:v libx264 ' \
             '-pix_fmt yuv420p -g 30 -vf scale="trunc((a*oh)/2)*2:720" ' \
             '-b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 "%s"' % (inputFile, outfilemp4)
    args = shlex.split(mp4cmd)
    result = subprocess.call(args)
    return result


def convertWebmFiles(inputFile, outfilewebm):
    webmcmd = 'ffmpeg -y -i "%s" -qscale:a 6 -g 30 -ac 2 -c:a libvorbis ' \
              '-c:v libvpx -pix_fmt yuv420p -b:v 2000k -vf scale="trunc((a*oh)/2)*2:720" ' \
              '-crf 5 -qmin 0 -qmax 50 -f webm "%s"' % (inputFile, outfilewebm)
    args = shlex.split(webmcmd)
    result = subprocess.call(args)
    return result


def createThumbnail(inputFile, outputFile):
    cmd = 'ffmpeg -y -i "%s" -vf  "thumbnail,scale=640:360" -frames:v 1 "%s"' % (inputFile, outputFile)
    args = shlex.split(cmd)
    result = subprocess.call(args)
    return result


def getList(session, listName, listCategory, project, user):
    try:
        listCategoryObj = session.query('ListCategory where name is %s' % listCategory).one()
    except Exception:
        print "No list category named %s" % listCategory
        return None
    try:
        list = session.query('AssetVersionList where name is %s and project_id is %s' % (listName, project['id'])).one()
    except Exception:
        list = session.create('AssetVersionList',{
            'owner': user,
            'project': project,
            'category': listCategoryObj,
            'name': listName
        })
    return list


def addToList(session, taskPath, date, version):
    task = getTask(session, taskPath)
    if len(task['appointments']) > 0:
        user = task['appointments'][0]['resource']
    else:
        user = session.query('User where username is %s' % os.environ['LOGNAME']).one()
    listname = 'Dailies_%s' % date
    listObj = getList(session, listname, 'Reviews', task['project'], user)
    listObj['items'].append(version)
    session.commit()


def getAsset(session, filePath, assetName):
    task = getTask(session, filePath)
    assetType = session.query('AssetType where name is Upload').one()
    try:
        asset = session.query('Asset where name is "%s" and parent.name is "%s"' %
                              (assetName, task['parent']['name'])).one()
    except:
        asset = session.create('Asset', {
            'name': assetName,
            'parent': task['parent'],
            'type': assetType
        })
        session.commit()
    return asset


def createAttachment(session, version, name, outfile, framein, frameout, framerate):
    server_location = session.query('Location where name is "ftrack.server"').one()
    component = version.create_component(
        path=outfile,
        data={
            'name': name
        },
        location=server_location
    )
    component['metadata']['ftr_meta'] = json.dumps({
        'frameIn': framein,
        'frameOut': frameout,
        'frameRate': framerate
    })
    component.session.commit()

def createVersion(session, filePath, asset, comment, istask=True):
    task = getTask(session, filePath)
    if istask:
        entity = task
        status = task['status']
        version = session.create('AssetVersion', {
            'asset': asset,
            'status': status,
            'comment': comment,
            'task': task
        })
    else:
        shot = task['parent']
        entity = shot
        version = session.create('AssetVersion', {
            'asset': asset,
            'comment': comment
        })
    return entity, version

def addTaskMetadata(session, taskPath, metadata):
    task = getTask(session, taskPath)
    task['metadata'] = metadata
    session.commit()


def addMetadata(session, version, metadict):
    for key in metadict.keys():
        version['metadata'][key] = metadict[key]
    session.commit()


def createAndPublishVersion(session, filePath, comment, asset, outfilemp4, outfilewebm, thumbnail, framein, frameout, framerate, istask=True):
    task, version = createVersion(session, filePath, asset, comment, istask)
    createAttachment(session, version, 'ftrackreview-mp4', outfilemp4, framein, frameout, framerate)
    createAttachment(session, version, 'ftrackreview-webm', outfilewebm, framein, frameout, framerate)
    session.commit()
    if os.path.exists(thumbnail):
        attachThumbnail(thumbnail, task, asset, version)
    return version


def publishImage(session, filePath, comment, asset, outfilejpg):
    task, version = createVersion(session, filePath, asset, comment)
    server_location = session.query('Location where name is "ftrack.server"').one()
    component = version.create_component(
        path=outfilejpg,
        data={
            'name': 'ftrackreview-image'
        },
        location=server_location
    )
    component['metadata']['ftr_meta'] = json.dumps({
        'format': 'image'
    })
    component.session.commit()
    attachThumbnail(outfilejpg, task, asset, version)
    return version


def attachThumbnail(thumbnail, task, asset, version):
    # Currently, it is not possible to set thumbnails using new API
    # This is a workaround using the old API.
    task_old_api = ftrack.Task(id=task['id'])
    asset_old_api = ftrack.Asset(id=asset['id'])
    for vers in asset_old_api.getVersions():
        if vers.getId() == version['id']:
            version_old_api = vers
            try:
                attachment = version_old_api.createThumbnail(thumbnail)
                task_old_api.setThumbnail(attachment)
            except Exception:
                print "Thumbnail upload error"
            break


def getStatus(session, statusName):
    status = session.query('Status where name is "%s"'  % statusName).one()
    return status


def setTaskStatus(session, filePath, version, statusName):
    task = getTask(session, filePath)
    status = getStatus(session, statusName)
    task['status'] = status
    version['status'] = status
    session.commit()


def getProjectFromShot(session, id):
    project = session.query('Project where descendants.id is %s' % id).one()
    return project['name']


def getProjectName(session, taskPath):
    task = getTask(session, taskPath)
    projectName = getProjectFromShot(session, task['id'])
    return projectName


def checkLogname(session, username):
    try:
        os.environ['LOGNAME']= username
        user = session.query('User where username is "%s' % username)
        return True
    except:
        return False
