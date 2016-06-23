import ftrack_api
import os
import threading
import nuke
import sys
import time
import writeNodeManager
import shutil
from Utils import ftrack_utils


_session = ftrack_api.Session(
    server_url=os.environ['FTRACK_SERVER'],
    api_user=os.environ['FTRACK_API_USER'],
    api_key=os.environ['FTRACK_API_KEY']
)


def isValidTask(projPath):
    task = None
    try:
        task = ftrack_utils.getTask(_session, projPath)
    except Exception:
        return False, None
    return True, task


def getProjectDetails(outputFile):
    pathItems = outputFile.split('/')
    projectName = pathItems[3]
    seqName = pathItems[5]
    shotName = pathItems[6]
    projPath = '%s / %s / %s / compositing' % (projectName, seqName, shotName)
    result, task = isValidTask(projPath)
    if not result:
        projPath = '%s / %s / %s / Compositing' % (projectName, seqName, shotName)
        result, task = isValidTask(projPath)
        if not result:
            print '%s is not a valid ftrack task' % projPath
            task = None
            projPath = ''
    return task, projPath


def prepMediaFiles(outputFile):
    outfilemp4 = os.path.splitext(outputFile)[0] + '.mp4'
    outfilewebm = os.path.splitext(outputFile)[0] + '.webm'
    thumbnail = os.path.join(os.path.split(outputFile)[0], 'thumbnail.png')
    metadata = {
        'source_file': outputFile
        }
    return outfilemp4, outfilewebm, thumbnail, metadata


def convertFiles(inputFile, outfilemp4, outfilewebm):
    mp4Result = ftrack_utils.convertMp4Files(inputFile, outfilemp4)
    webmResult = ftrack_utils.convertWebmFiles(inputFile, outfilewebm)
    if mp4Result == 0 and webmResult == 0:
        return True
    else:
        return False


def getUploadDetails(session, projPath):
    taskPath = projPath
    assetName = 'Quicktime Movie'
    asset = ftrack_utils.getAsset(session, taskPath, assetName)
    comment = 'Upload for internal review'
    return taskPath, asset, comment


def deleteFiles(outfilemp4, outfilewebm, thumbnail):
    if os.path.exists(outfilemp4):
        os.remove(outfilemp4)
    if os.path.exists(outfilewebm):
        os.remove(outfilewebm)
    if os.path.exists(thumbnail):
        os.remove(thumbnail)


def addToList(session, taskPath, outputFile, version):
    task = ftrack_utils.getTask(session, taskPath)
    projName = outputFile.split('/')[1]
    user = task['appointments'][0]['resource']
    date = getDate()
    listname = 'Dailies_%s' % date
    listObj = ftrack_utils.getList(session, listname, 'Reviews', projName, user)
    listObj['items'].append(version)
    session.commit()


def newThreadUpload(session, projPath, inputFile, outfilemp4, outfilewebm, thumnbail,
                    metadata, outputFile, nukeFile):

    firstFrame = int(nuke.tcl('frames first'))
    lastFrame = int(nuke.tcl('frames last'))
    frameCount = lastFrame-firstFrame
    if frameCount > 400:
        time.sleep(80)
    else:
        time.sleep(30)
    if os.path.exists(outputFile):
        ftrackUploadThread(session, projPath, inputFile, outfilemp4, outfilewebm,
                           thumnbail, metadata, outputFile, nukeFile)
    else:
        print "File %s does not exist on disk. Waiting another 30 sec."
        time.sleep(30)
        ftrackUploadThread(session, projPath, inputFile, outfilemp4, outfilewebm,
                           thumnbail, metadata, outputFile, nukeFile)


def createRVComponent(session, version, outputFile):
    server_location = session.query('Location where name is "ftrack.unmanaged"').one()
    component = version.create_component(
        path=outputFile,
        data={
            'name': 'movie'
        },
        location=server_location
    )
    component.session.commit()


def ftrackUploadThread(session, projPath, inputFile, outfilemp4, outfilewebm,
                       thumnbail, metadata, outputFile, nukeFile):
    try:
        approvedFile = copyToApprovals(outputFile)
    except:
        print "file permissions issue. Could not copy file to approvals folder."
    firstFrame = int(nuke.tcl('frames first'))
    lastFrame = int(nuke.tcl('frames last'))
    result = convertFiles(inputFile, outfilemp4, outfilewebm)
    if result:
        thumbresult = ftrack_utils.createThumbnail(outfilemp4, thumnbail)
        print "File conversion successful"
        taskPath, asset, comment = getUploadDetails(session, projPath)
        version = ftrack_utils.createAndPublishVersion(session, taskPath, comment, asset,
                                                       outfilemp4, outfilewebm, thumnbail,
                                                       firstFrame, lastFrame, 24)
        createRVComponent(session, version, outputFile)

        ftrack_utils.setTaskStatus(session, taskPath, version, 'Pending Internal Review')
        ftrack_utils.addMetadata(session, version, metadata)
        taskMeta = {'filename': nukeFile}
        ftrack_utils.addTaskMetadata(session, taskPath, taskMeta)
        print "file upload successful"
        ftrack_utils.addToList(session, projPath, getDate(), version)
    deleteFiles(outfilemp4, outfilewebm, thumnbail)


def getOutputFile():
    rootDir = writeNodeManager.getRootDir()
    filename = writeNodeManager.getFilename()
    outputFile = '%simg/comps/%s.mov' % (rootDir, filename)
    return outputFile


def copyToApprovals(outputFile):
    filename = os.path.split(outputFile)[-1]
    projFolder = outputFile.split('shots')[0]
    approvals = os.path.join(projFolder, 'production', 'approvals')
    date = getDate()
    appFolder = os.path.join(approvals, date)
    if not os.path.exists(appFolder):
        os.makedirs(appFolder)
    os.chmod(appFolder, 0777)
    dstFile = os.path.join(appFolder, filename)
    shutil.copyfile(outputFile, dstFile)
    return dstFile


def getDate():
    import datetime
    today = datetime.datetime.today()
    if today.hour > 10:
        dailiesDate = today + datetime.timedelta(1)
    else:
        dailiesDate = today
    date = '%d-%02d-%02d' % (dailiesDate.year, dailiesDate.month, dailiesDate.day)
    return date


def getTaskDetails(outputFile):
    task = None
    projPath = ''
    if 'FTRACK_TASKID' in os.environ:
        task = _session.query('Task where id is %s' % os.environ['FTRACK_TASKID']).one()
        shot = task['parent']
        sequence = shot['parent']
        project = task['project']['name']
        projPath = '%s / %s / %s / %s' % (project, sequence['name'], shot['name'], task['name'])
    else:
        task, projPath = getProjectDetails(outputFile)
    return task, projPath


def uploadToFtrack():
    node = None
    for node in nuke.allNodes('Write'):
        if node.name() == 'Write_mov':
            break
    if not nuke.GUI or (node and node.knob('uploadToFtrack').value()):
        print "Submitting to Dailies"
        outputFile = writeNodeManager.getOutputFile()
        nukeFile = nuke.scriptName()
        task, projPath = getTaskDetails(outputFile)
        node.knob('uploadToFtrack').setValue(False)
        if projPath is not '':
            outfilemp4, outfilewebm, thumbnail, metadata = prepMediaFiles(outputFile)
            print "Starting conversion..."
            threading.Thread(None, newThreadUpload, args=[_session, projPath, outputFile,
                                                          outfilemp4, outfilewebm, thumbnail,
                                                          metadata, outputFile, nukeFile]).start()
        else:
            print "Error in submitting to ftrack. The project details might be incorrect."
