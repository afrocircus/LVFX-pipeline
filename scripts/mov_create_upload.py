#!/usr/local/bin/python2.7
import sys
import os
import logging
import glob
import getopt
import shutil
from renderFarm import config
from Utils import ftrack_utils2
from Utils import prores_utils


os.environ['FTRACK_SERVER'] = config.ftrack_server
os.environ['FTRACK_API_USER'] = config.ftrack_api_user
os.environ['FTRACK_API_KEY'] = config.ftrack_api_key


def createMov(outdir, filename, taskid):
    session = ftrack_utils2.startANewSession()
    # If taskid is not valid, then don't try and figure it out from filename as it can
    # be problematic. Only upload if there is a valid taskid.
    task = ftrack_utils2.getTask(session, taskid, '')
    extractDir = ''

    imgSeq = glob.glob(outdir)
    imgSeq.sort()
    size = prores_utils.getImageSize(imgSeq[0])
    # if exr, extract rgb channel
    if imgSeq[0].endswith('.exr'):
        print 'Extracting RGB channel from EXR image sequence...'
        extractDir = prores_utils.extractRGB(imgSeq)
        imgSeq = glob.glob(os.path.join(extractDir, '*'))
        imgSeq.sort()
    # make movie
    print 'Making movie...'
    movFile = prores_utils.makeMovie(imgSeq[0])
    movFilename = os.path.split(movFile)[-1]
    parentDir = os.path.dirname(outdir)

    print 'Created: %s' % movFile

    # copy movFile to out filename location
    print 'Copying to location: %s' % parentDir
    try:
        shutil.copy(movFile, parentDir)
    except shutil.Error:
        logging.warning('Files are the same. Skipping copy')

    movFile = os.path.join(parentDir, movFilename)

    if task:
        print 'Valid task found!'
        artist = ftrack_utils2.getUsername(task)
        date = ftrack_utils2.getDate()
        try:
            version = 'v' + ftrack_utils2.version_get(filename, 'v')[1]
        except:
            version = 'v01'
        shotInfo = '{0} | {1} | {2} | {3} | {4}'.format(task['project']['name'], task['parent']['name'],
                                                        task['name'], version, artist)

        if len(imgSeq) == 0:
            return

        slate = prores_utils.makeSlate(size, imgSeq[0], shotInfo, date)

        print 'Making slate movie'
        slateMov = prores_utils.makeSlateMovie(movFile, slate)

        logging.debug('Removing tmp files')
        if os.path.exists(slate):
            os.remove(slate)
        if os.path.exists(movFile):
            os.remove(movFile)
        movFile = slateMov

    logging.debug('Removing tmp exr files')
    if os.path.exists(extractDir):
        shutil.rmtree(extractDir)
    print 'Final movie file: %s' % movFile
    return movFile, task


def uploadToFtrack(task, movFile):
    session = ftrack_utils2.startANewSession()
    logging.info( "Encoding Media Files...")
    ftrack_utils2.copyToApprovals(movFile, task['project'])
    outfilemp4, outfilewebm, thumbnail, metadata = ftrack_utils2.prepMediaFiles(movFile)
    logging.info( 'Starting file conversion...')
    ff, lf = ftrack_utils2.getFrameLength(movFile)
    result = ftrack_utils2.convertFiles(movFile, outfilemp4, outfilewebm, thumbnail)
    if result:
        logging.info( 'File conversion complete.')
        logging.info( 'Starting file upload...')
        asset = ftrack_utils2.getAsset(session, task, 'ReviewAsset')
        status = ftrack_utils2.getStatus(session, 'In Progress')
        try:
            ftrack_utils2.createAndPublishVersion(session, task, asset,
                                                  status, 'Upload for Internal Review',
                                                  thumbnail, movFile, outfilemp4,
                                                  outfilewebm, metadata, ff, lf, 24)
            logging.debug( 'cleaning up temporary files...')
            ftrack_utils2.deleteFiles(outfilemp4, outfilewebm, thumbnail)
            logging.info( 'Upload Complete!')
        except Exception, e:
            logging.error( 'Upload Failed: Error uploading to ftrack.')
            logging.error(e)
    else:
        logging.error( 'Upload Failed: Error during file conversion.')


def main(argv):
    taskid = ''
    outdir = ''
    filename = ''
    upload = False
    try:
        opts, args = getopt.getopt(argv, 'hf:t:d:u', ['filename=', 'taskid=', 'outdir=', 'upload'])
    except getopt.GetoptError:
        print 'mov_create_upload.py -f <filename> -t <taskid> -d <outdir> -u'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: mov_create_upload.py -f <filename> -t <taskid> -d <outdir>\n' \
                  'Converts the images in outdir to mov with slate \n' \
                  'f = filename \n' \
                  't = taskid \n' \
                  'd = output file pattern eg. /data/production/ftrack_test/filename.#.exr\n' \
                  'u = If passed, then upload to ftrack'
            sys.exit()
        elif opt in ('-f', '--filename'):
            filename = arg
        elif opt in ('-t', '--taskid'):
            taskid = arg
        elif opt in ('-d', '--outfile'):
            outdir = arg.replace('#', '[0-9][0-9][0-9][0-9]')
        elif opt in ('-u', '--upload'):
            upload = True
    movFile, task = createMov(outdir, filename, taskid)

    if os.path.exists(movFile):
        if upload:
            if task:
                uploadToFtrack(task, movFile)
            else:
                logging.error( "No task found. Cannot upload to ftrack.")
        else:
            logging.info('Movie file creating complete.')
            logging.info('Mov File: %s' % movFile)
    else:
        logging.error('Unable to create a movie file.')


if __name__ == '__main__':
    main(sys.argv[1:])
