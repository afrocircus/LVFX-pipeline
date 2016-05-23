import ftrack_api
import os
import threading
import nuke
import time
import writeNodeManager
import shutil
from Utils import ftrack_utils


_session = ftrack_api.Session(
        server_url=os.environ['FTRACK_SERVER'],
        api_user=os.environ['FTRACK_API_USER'],
        api_key=os.environ['FTRACK_API_KEY']
    )


def getProjectDetails(outputFile):
    pathItems = outputFile.split('/')
    projectName = pathItems[3]
    seqName = pathItems[5]
    shotName = pathItems[6]
    projPath = '%s / %s / %s / compositing' % (projectName, seqName, shotName)
    try:
        task = ftrack_utils.getTask(_session, projPath)
    except Exception:
        projPath = ''
        task = None
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
        time.sleep(40)
    if os.path.exists(outputFile):
        # copyToApprovals(outputFile)
        ftrackUploadThread(session, projPath, inputFile, outfilemp4, outfilewebm,
                           thumnbail, metadata, outputFile, nukeFile)
    else:
        print "File %s does not exist on disk. Waiting another 30 sec."
        time.sleep(30)
        # copyToApprovals(outputFile)
        ftrackUploadThread(session, projPath, inputFile, outfilemp4, outfilewebm,
                           thumnbail, metadata, outputFile, nukeFile)


def ftrackUploadThread(session, projPath, inputFile, outfilemp4, outfilewebm,
                       thumnbail, metadata, outputFile, nukeFile):
    firstFrame = int(nuke.tcl('frames first'))
    lastFrame = int(nuke.tcl('frames last'))
    result = convertFiles(inputFile, outfilemp4, outfilewebm)
    if result:
        thumbresult = ftrack_utils.createThumbnail(outfilemp4, thumnbail)
        taskPath, asset, comment = getUploadDetails(session, projPath)
        version = ftrack_utils.createAndPublishVersion(session, taskPath, comment, asset,
                                                       outfilemp4, outfilewebm, thumnbail,
                                                       firstFrame, lastFrame, 24)
        ftrack_utils.setTaskStatus(session, taskPath, version, 'Pending Internal Review')
        ftrack_utils.addMetadata(session, version, metadata)
        taskMeta = {'filename': nukeFile}
        ftrack_utils.addTaskMetadata(session, taskPath, taskMeta)
        # addToList(session, projPath, outputFile, version)
    deleteFiles(outfilemp4, outfilewebm, thumnbail)


def getOutputFile():
    rootDir = writeNodeManager.getRootDir()
    filename = writeNodeManager.getFilename()
    outputFile = '%simg/comps/%s.mov' % (rootDir, filename)
    return outputFile


def copyToApprovals(outputFile):
    projName = outputFile.split('/')[1]
    drive = os.path.splitdrive(outputFile)[0]
    filename = os.path.split(outputFile)[-1]
    date = getDate()
    appFolder = os.path.join(drive, '\\%s\\production\\approvals\\%s' % (projName, date))
    if not os.path.exists(appFolder):
        os.makedirs(appFolder)
    dstFile = os.path.join(appFolder, filename)
    srcFile = outputFile.replace('/', '\\')
    shutil.copyfile(srcFile, dstFile)
    qtFolder = writeNodeManager.getQuickTimeFolder()
    qtFolder = qtFolder.replace('/', '\\')
    shutil.copy(srcFile, qtFolder)


def getDate():
    import datetime
    today = datetime.datetime.today()
    date = '%d-%02d-%d' % (today.year, today.month, today.day)
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
    outputFile = writeNodeManager.getOutputFile()
    nukeFile = nuke.scriptName()
    task, projPath = getTaskDetails(outputFile)
    if projPath is not '':
        outfilemp4, outfilewebm, thumbnail, metadata = prepMediaFiles(outputFile)
        threading.Thread(None, newThreadUpload, args=[_session, projPath, outputFile,
                                                      outfilemp4, outfilewebm, thumbnail,
                                                      metadata, outputFile, nukeFile]).start()
    else:
        print "Error in submitting to ftrack. The project details might be incorrect."
