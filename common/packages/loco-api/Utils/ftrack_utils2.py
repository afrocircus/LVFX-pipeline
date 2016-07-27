import ftrack_api
import logging
import os
import re
import uuid
import subprocess
import json


def startSession():
    session = ftrack_api.Session()
    return session


def startANewSession():
    session = ftrack_api.Session(
            server_url=os.environ['FTRACK_SERVER'],
            api_user=os.environ['FTRACK_API_USER'],
            api_key=os.environ['FTRACK_API_KEY']
        )
    return session


def getTask(session, taskid, filename):
    task = None
    if taskid:
        try:
            task = session.query('Task where id is {0}'.format(taskid)).one()
        except Exception, e:
            logging.info("No task found with id {0}".format(taskid))
            logging.error(e)
    else:
        # if no task id found we rely on the folder structure.
        # /data/production/project/shots/sq/shot/scene/task/file.ext
        try:
            filePathSplit = filename.split('shots')
            projectPart = filePathSplit[0].strip('/')
            sqShotPart = filePathSplit[1].strip('/')
            project = projectPart.split('/')[-1]
            seq = sqShotPart.split('/')[0]
            shot = sqShotPart.split('/')[1]
            taskName = sqShotPart.split('/')[3]
            task = session.query('Task where name is {0} and project.name is {1} '
                                 'and parent.name is {2}'.format(taskName, project, shot)).one()
        except Exception, e:
            logging.error(e)

    return task


def getUsername(task):
    try:
        username = task['appointments'][0]['resource']['username']
    except:
        username = 'No user assigned'
    return username


def version_get(string, prefix):
    """
    Extract version information from filenames.
    Code from Foundry's nukescripts.version_get()
    """
    if string is None:
        raise ValueError("Empty version string - no match")

    regex = "[/_.]"+prefix+"\d+"
    matches = re.findall(regex, string, re.IGNORECASE)
    if not len(matches):
        msg = "No \"_"+prefix+"#\" found in \""+string+"\""
        raise ValueError(msg)
    return (matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group())


def deleteFiles(outfilemp4, outfilewebm, thumbnail):
    if os.path.exists(outfilemp4):
        os.remove(outfilemp4)
    if os.path.exists(outfilewebm):
        os.remove(outfilewebm)
    if os.path.exists(thumbnail):
        os.remove(thumbnail)


def createThumbnail(inputFile, outputFile):
    cmd = 'ffmpeg -y -i "%s" -vf  "thumbnail,scale=640:360" -frames:v 1 "%s"' % (inputFile, outputFile)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    process.wait()


def convertMp4Files(inputFile, outfilemp4):
    mp4cmd = 'ffmpeg -y -i "%s" -ac 2 -b:v 2000k -c:a aac -c:v libx264 ' \
             '-pix_fmt yuv420p -g 30 -vf scale="trunc((a*oh)/2)*2:720" ' \
             '-b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 "%s"' % (inputFile, outfilemp4)
    process = subprocess.Popen(mp4cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    process.wait()


def convertWebmFiles(inputFile, outfilewebm):
    webmcmd = 'ffmpeg -y -i "%s" -qscale:a 6 -g 30 -ac 2 -c:a libvorbis ' \
              '-c:v libvpx -pix_fmt yuv420p -b:v 2000k -vf scale="trunc((a*oh)/2)*2:720" ' \
              '-crf 5 -qmin 0 -qmax 50 -f webm "%s"' % (inputFile, outfilewebm)
    process = subprocess.Popen(webmcmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    process.wait()


def getFrameLength(filename):
    cmd = 'ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames ' \
          '-of default=nokey=1:noprint_wrappers=1 {0}'.format(filename)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output = process.communicate()
    firstFrame = 1
    lastFrame = firstFrame + int(output[0])
    return firstFrame, lastFrame


def prepMediaFiles(outputFile):
    outfilemp4 = os.path.splitext(outputFile)[0] + '.mp4'
    outfilewebm = os.path.splitext(outputFile)[0] + '.webm'
    thumbnail = os.path.join(os.path.split(outputFile)[0], str(uuid.uuid4())+'.png')
    metadata = {
        'source_file': outputFile
        }
    return outfilemp4, outfilewebm, thumbnail, metadata


def convertFiles(inputFile, outfilemp4, outfilewebm, outfilethumb):
    convertMp4Files(inputFile, outfilemp4)
    convertWebmFiles(inputFile, outfilewebm)
    createThumbnail(inputFile, outfilethumb)
    if os.path.exists(outfilemp4) and os.path.exists(outfilewebm) and os.path.exists(outfilethumb):
        return True
    else:
        return False


def getAsset(session, task, assetName):
    assetType = session.query('AssetType where name is Upload').one()
    try:
        asset = session.query('Asset where name is {0} and '
                              'parent.id is {1}'.format(assetName, task['parent']['id'])).one()
    except:
        asset = session.create('Asset', {
            'name': assetName,
            'parent': task['parent'],
            'type': assetType
        })
        session.commit()
    return asset


def getStatus(session, statusName):
    status = session.query('Status where name is "%s"'  % statusName).one()
    return status


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


def addMetadata(session, entity, metadict):
    for key in metadict.keys():
        entity['metadata'][key] = metadict[key]
    session.commit()


def createAndPublishVersion(session, task, asset, status, comment, thumbnail, filename,
                            outfilemp4, outfilewebm, metadata, framein, frameout, framerate):
    version = session.create('AssetVersion', {
            'asset': asset,
            'status': status,
            'comment': comment,
            'task': task
        })
    createAttachment(session, version, 'ftrackreview-mp4', outfilemp4, framein, frameout, framerate)
    createAttachment(session, version, 'ftrackreview-webm', outfilewebm, framein, frameout, framerate)
    createRVComponent(session, version, filename)
    if os.path.exists(thumbnail):
        fileComponent = version.create_thumbnail(thumbnail)
        task['thumbnail'] = fileComponent
    addMetadata(session, version, metadata)
    session.commit()
