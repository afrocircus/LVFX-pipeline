__author__ = 'Natasha'

import subprocess
import shlex
import os
import glob
from datetime import datetime


def getImageSize(filename):
    # Get size of the image
    ffprobecmd = 'ffprobe -v error -of flat=s=_ -select_streams v:0 ' \
                     '-show_entries stream=height,width "{0}"'.format(filename)
    process = subprocess.Popen(ffprobecmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    try:
        output = process.communicate()[0]
        parts = output.split('\n')
        width = parts[0].split('=')[-1]
        height = parts[1].split('=')[-1]
    except:
        width = 1920
        height = 1080
    size = '{0}x{1}'.format(width, height)
    return size


def makeSlate(size, filename, shotInfo, date):
    # generate slate
    slateFolder = os.path.split(filename)[0]
    slate = os.path.join(slateFolder, 'slate.png')
    slateCmd = 'convert -size {0} xc:transparent -font Palatino-Bold -pointsize 24 ' \
               '-fill white -gravity NorthWest -annotate +25+25 "{1}" ' \
               '-gravity NorthEast -annotate +25+25 "{2}" -gravity SouthEast ' \
               '"{3}"'.format(size, shotInfo, date, slate)
    process = subprocess.Popen(slateCmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    process.wait()
    return slate


def makeMovie(filename):
    slateFolder, outfileName = os.path.split(filename)
    fname,fext = os.path.splitext(outfileName)
    frameno = fname.split('.')[-1]
    filePart = os.path.join(slateFolder, fname.split('.')[0])
    outFile = os.path.join(slateFolder, '{0}.mov'.format(filePart))
    ffmpegCmd = 'ffmpeg -y -start_number %s -an -i %s.%%0%sd%s -vcodec libx264 -pix_fmt yuv420p ' \
                '-preset slow -crf 18 -vf "lutrgb=r=gammaval(0.45454545):g=gammaval(0.45454545):' \
                'b=gammaval(0.45454545),drawtext=fontfile=/usr/share/fonts/dejavu/DejaVuSans.ttf:' \
                'fontsize=24:text=%%{n}:x=(w-tw)-50: y=h-(2*lh):fontcolor=white: box=1:' \
                'boxcolor=0x00000099" %s' % (frameno, filePart,len(frameno),fext, outFile)
    process = subprocess.Popen(ffmpegCmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    process.wait()
    return outFile

def makeSlateMovie(filename, slate):
    # overlay slate on movie
    slateFolder, outfileName = os.path.split(filename)
    fname,fext = os.path.splitext(outfileName)
    slateMov = os.path.join(slateFolder, '{0}_slate{1}'.format(fname, fext))
    ffmpegSlate = 'ffmpeg -y -i "{0}" -i "{1}" -filter_complex "overlay=5:5" "{2}"'.format(filename,
                                                                                  slate, slateMov)
    process = subprocess.Popen(ffmpegSlate, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    process.wait()
    return slateMov


def getShotInfo(inputFolder, imageExt):
    '''
    Returns shot information
    :param inputFolder: Input Folder
    :param imageExt: Image extension
    :return: shotName, first frame, last frame and date
    '''
    date = datetime.now()
    dateStr = '%s/%s/%s' % (date.day, date.month, date.year)
    files = [file for file in os.listdir(inputFolder) if file.endswith(imageExt)]
    files.sort()
    if files:
        shotName = files[0].split('.')[0]
        firstFrame = files[0].split('.')[1]
        lastFrame = files[-1].split('.')[1]
        return shotName, int(firstFrame), int(lastFrame), dateStr, firstFrame
    else:
        return '',0,0,dateStr

def generateSlugImages(tmpDir, label, firstFrame, lastFrame, date, firstFrameStr, task):
    '''
    Slug Images are generated and stored in tmpDir
    :param tmpDir: Temporary Directory in the Users local temp
    :param shotName: Name of the shot  type:str
    :param firstFrame: First frame type:int
    :param lastFrame: Last frame type: int
    :param date: Date mm/dd/yyyy type:str
    :param task: Nuke Progress Bar object
    :return:
    '''

    slugCommand = 'convert -size 450x40 -background black -fill white -pointsize 20 ' \
                  'label:"quarks %s ball frames:10" %s/slug.jpg' % (date,tmpDir)
    args = shlex.split(slugCommand)
    result = []
    label = label.replace('Frame#', '')
    totalFrames = lastFrame - firstFrame
    incrValue = 100.0/totalFrames
    count = 0
    for i in range(firstFrame, lastFrame+1):
        if task.isCancelled():
            return 1
        frameStr = firstFrameStr[:-(len(str(i)))] + str(i)
        args[-1] = '%s/slug.%s.jpg' % (tmpDir, frameStr)
        args[-2] = 'label:%s %s' % (label, str(frameStr))
        result.append(subprocess.call(args))
        count = count + incrValue
        task.setProgress(int(count))
    for i in result:
        if i != 0:
            return 1
    return 0

def generateSlugMovie(tmpDir, firstFrame, firstFrameStr, frameRate):
    '''
    Generates a movie of the slug images. Stores it in the same temp folder
    :param tmpDir: Temp Folder in the users local temp.
    :param firstFrame: first frame
    :return:
    '''
    frameLen = len(str(firstFrameStr))
    slugMovCmd = 'ffmpeg -y -start_number %s -an -i "%s/slug.%%0%sd.jpg" ' \
                 '-vcodec prores -profile:v 2 -r %s "%s/slug.mov"' % (firstFrame, tmpDir, frameLen, frameRate, tmpDir)
    args = shlex.split(slugMovCmd)
    result = subprocess.call(args)
    return result

def generateFileMovie(inputFolder, tmpDir, outputFile, firstFrame, fileName, imageExt, lastFrame, firstFrameStr, frameRate):
    '''
    Composites the slug movie with the input images to generate the final movie.
    '''
    if imageExt == 'exr':
        # Convert exr to exr using imagemagik to get the exr format correct.
        convertExr(inputFolder, fileName, firstFrame, lastFrame, firstFrameStr)
        filePath = '%s/exrTmp/%s' % (os.environ['TEMP'], fileName)
    else:
        filePath = '%s/%s' % (inputFolder, fileName)
    inputFile = '%s.%s.%s' % (fileName, firstFrame, imageExt)

    frameLen = len(str(firstFrameStr))
    finalMovCmd = 'ffmpeg -y -start_number %s -an -i "%s.%%0%sd.%s" ' \
                  '-i "%s/slug.mov" -metadata comment="Source Image:%s" -filter_complex "overlay=1:1" ' \
                  '-vcodec prores -profile:v 2 -r %s "%s" ' % (firstFrame, filePath, frameLen, imageExt,
                                                             tmpDir, inputFile, frameRate, outputFile)
    return finalMovCmd

def generateFileMovieNoSlug(inputFolder, outputFile, firstFrame, fileName, imageExt, lastFrame, firstFrameStr, frameRate):
    '''
    Generate the movie without the slug, only from the input image sequence.
    '''
    if imageExt == 'exr':
        # Convert exr to correct format using imagemagik
        convertExr(inputFolder, fileName, firstFrame, lastFrame, firstFrameStr)
        filePath = '%s/exrTmp/%s' % (os.environ['TEMP'], fileName)
    else:
        filePath = '%s/%s' % (inputFolder, fileName)

    frameLen = len(str(firstFrameStr))
    finalMovCmd = 'ffmpeg -y -start_number %s -an -i "%s.%%0%sd.%s" ' \
                  '-metadata comment="Source Image:%s.%s.%s" -vcodec prores ' \
                  '-profile:v 2 -r %s "%s" ' % (firstFrame, filePath, frameLen, imageExt,
                                              fileName, firstFrame,imageExt, frameRate, outputFile)
    return finalMovCmd

def convertExr(inputFolder, fileName, firstFrame, lastFrame, firstFrameStr):
    '''
    Generate new exr from input exr images using ImageMagik.
    This was required as the compression type of the input exr images was not supported.
    '''
    if not os.path.exists('%s/exrTmp' % os.environ['TEMP']):
        os.mkdir('%s/exrTmp' % os.environ['TEMP'])
    slugCommand = 'convert %s/%s.exr "%s/exrTmp/%s.exr"' % (inputFolder,fileName,os.environ['TEMP'],fileName)
    args = shlex.split(slugCommand)
    for i in range(firstFrame, lastFrame+1):
        frameStr = firstFrameStr[:-(len(str(i)))] + str(i)
        args[1] = '%s/%s.%s.exr' % (inputFolder, fileName, frameStr)
        args[2] = '%s/exrTmp/%s.%s.exr' % (os.environ['TEMP'], fileName, frameStr)
        subprocess.call(args)

def getVideoPlayer():
    '''
    Checks if QuickTimePlayer exists. If not checks for VLC player.
    :return: videoPlayerDir: Path of the video player
    '''
    videoPlayerDir = ''
    videoPlayerDirList = glob.glob('C:\\Program*\\QuickTime*')
    if videoPlayerDirList:
        videoPlayerDir = '%s\\QuickTimePlayer.exe' % videoPlayerDirList[0]
    else:
        '''videoPlayerDirList = glob.glob('C:\Program*\\VideoLan*')
        if videoPlayerDirList:
            videoPlayerDir = '%s\\VLC\\vlc.exe' % videoPlayerDirList[0]'''
        videoPlayerDir = '/usr/bin/vlc'
    return videoPlayerDir
