import os
import sys
import getopt
import shlex
import subprocess
import ftrack_api
from Utils import ftrack_utils


_session = ftrack_api.Session(
        server_url=os.environ['FTRACK_SERVER'],
        api_user=os.environ['FTRACK_API_USER'],
        api_key=os.environ['FTRACK_API_KEY']
    )


def makeMovie(sspec):
    specList = sspec.split(':')
    if not len(specList) == 3:
        print 'spec is incorrect'
        return 1, None, None, None
    filePath = '/data/production/%s/shots/%s/%s/img/plates' % (specList[0], specList[1], specList[2])
    if not os.path.exists(filePath):
        print '%s is not a valid path' % filePath
        return 1, None, None, None
    files = [f for f in os.listdir(filePath) if f.endswith('.dpx')]
    files.sort()
    if files:
        plateName = files[0].split('.')[0]
        firstFrame = files[0].split('.')[-2]
        lastFrame = files[-1].split('.')[-2]
        frameLen = len(firstFrame)
        filename = files[0].replace(firstFrame, '%%0%sd' % frameLen)
        fullFile = os.path.join(filePath, filename)
        outputFile = os.path.join(filePath, '%s.mov' % plateName)
        tmpFile = os.path.join(filePath, 'output.mov')
        cmd = 'ffmpeg -y -start_number %s -an -i %s -vcodec prores -profile:v 2 -r 24 %s' % (firstFrame,
                                                                                             fullFile, tmpFile)
        args = shlex.split(cmd)
        result = subprocess.call(args)
        if result == 0:
            cmd = 'ffmpeg -i %s -vcodec prores -profile:v 2 ' \
                  '-vf "drawtext=fontfile=/usr/share/fonts/dejavu/DejaVuSans.ttf:' \
                  'fontsize=32:text=%%{n}: x=(w-tw)-50: y=h-(2*lh): ' \
                  'fontcolor=white: box=1: boxcolor=0x00000099" -y %s' % (tmpFile, outputFile)
            args = shlex.split(cmd)
            result = subprocess.call(args)
            os.remove(tmpFile)
            return result, outputFile, firstFrame, lastFrame
    return 1, None, None, None


def uploadToFtrack(movieFile, sspec, firstFrame, lastFrame):
    specList = sspec.split(':')
    project = specList[0]
    sequence = specList[1]
    shot = specList[2]
    taskPath = '%s / %s / %s / compositing' % (project, sequence, shot)
    try:
        task = ftrack_utils.getTask(_session, taskPath)
    except Exception:
        print "ftrack_api.exception.NoResultFoundError: %s is not a valid task" % taskPath
        return
    outfilemp4, outfilewebm, thumbnail, metadata = prepMediaFiles(movieFile)
    upload(_session, firstFrame, lastFrame, taskPath, movieFile,
           outfilemp4, outfilewebm, thumbnail, metadata)


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


def deleteFiles(outfilemp4, outfilewebm, thumbnail):
    if os.path.exists(outfilemp4):
        os.remove(outfilemp4)
    if os.path.exists(outfilewebm):
        os.remove(outfilewebm)
    if os.path.exists(thumbnail):
        os.remove(thumbnail)


def getUploadDetails(session, projPath):
    taskPath = projPath
    assetName = 'reference'
    asset = ftrack_utils.getAsset(session, taskPath, assetName)
    comment = 'Reference clip'
    return taskPath, asset, comment


def upload(session, ff, lf, projPath, inputFile, outfilemp4, outfilewebm, thumnbail, metadata):

    result = convertFiles(inputFile, outfilemp4, outfilewebm)
    if result:
        thumbresult = ftrack_utils.createThumbnail(outfilemp4, thumnbail)
        taskPath, asset, comment = getUploadDetails(session, projPath)
        version = ftrack_utils.createAndPublishVersion(session, taskPath, comment, asset,
                                                       outfilemp4, outfilewebm, thumnbail,
                                                       ff, lf, 24, False)
        status = ftrack_utils.getCurrentStatus(session, taskPath)
        ftrack_utils.setTaskStatus(session, taskPath, version, status)
        ftrack_utils.addMetadata(session, version, metadata)
    deleteFiles(outfilemp4, outfilewebm, thumnbail)


def main(argv):
    sspec = ''
    try:
        opts, args = getopt.getopt(argv, 'hi:', ['sspec='])
    except getopt.GetoptError:
        print 'referenceClipHandler.py -sspec <project:sq:shot>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: referenceClipHandler.py -i <project:sq:shot> \n' \
                  'Assumes the project directory is located at /data/production/ \n' \
                  'project = Name of project directory \n' \
                  'sq = Name of sequence directory \n' \
                  'shot = Name of shot directory \n'
            sys.exit()
        elif opt in ('-i', '--sspec'):
            sspec = arg
    result, outputFile, ff, lf = makeMovie(sspec)
    if result == 0:
        print 'conversion successful'
        uploadToFtrack(outputFile, sspec, ff, lf)
    else:
        print 'conversion unsuccessful'

if __name__ == '__main__':
    main(sys.argv[1:])
