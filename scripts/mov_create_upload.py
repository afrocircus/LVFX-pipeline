#!/usr/local/bin/python2.7
import sys
import os
import glob
import getopt
from renderFarm import config
from Utils import ftrack_utils2
from Utils import prores_utils

os.environ['FTRACK_SERVER'] = config.ftrack_server
os.environ['FTRACK_API_USER'] = config.ftrack_api_user
os.environ['FTRACK_API_KEY'] = config.ftrack_api_key


def createMov(outdir, filename, taskid):
    session = ftrack_utils2.startANewSession()
    task = ftrack_utils2.getTask(session, taskid, filename)
    if not task:
        return '',  task
    artist = ftrack_utils2.getUsername(task)
    date = ftrack_utils2.getDate()
    try:
        version = 'v' + ftrack_utils2.version_get(filename, 'v')[1]
    except:
        version = 'v01'
    shotInfo = '{0} | {1} | {2} | {3} | {4}'.format(task['project']['name'], task['parent']['name'],
                                                    task['name'], version, artist)
    imgSeq = glob.glob(outdir)
    imgSeq.sort()
    if len(imgSeq) == 0:
        return
    size = prores_utils.getImageSize(imgSeq[0])
    slate = prores_utils.makeSlate(size, imgSeq[0], shotInfo, date)
    movFile = prores_utils.makeMovie(imgSeq[0])
    slateMov = prores_utils.makeSlateMovie(movFile, slate)
    if os.path.exists(slate):
        os.remove(slate)
    if os.path.exists(movFile):
        os.remove(movFile)
    return slateMov, task


def uploadToFtrack(task, movFile):
    session = ftrack_utils2.startANewSession()
    print "Encoding Media Files..."
    ftrack_utils2.copyToApprovals(movFile, task['project'])
    outfilemp4, outfilewebm, thumbnail, metadata = ftrack_utils2.prepMediaFiles(movFile)
    print 'Starting file conversion...'
    ff, lf = ftrack_utils2.getFrameLength(movFile)
    result = ftrack_utils2.convertFiles(movFile, outfilemp4, outfilewebm, thumbnail)
    if result:
        print  'File conversion complete.'
        print 'Starting file upload...'
        asset = ftrack_utils2.getAsset(session, task, 'ReviewAsset')
        status = ftrack_utils2.getStatus(session, 'In Progress')
        try:
            ftrack_utils2.createAndPublishVersion(session, task, asset,
                                                  status,'Upload for Internal Review',
                                                  thumbnail, movFile, outfilemp4,
                                                  outfilewebm, metadata, ff, lf, 24)
            print 'cleaning up temporary files...'
            ftrack_utils2.deleteFiles(outfilemp4, outfilewebm, thumbnail)
            print 'Upload Complete!'
        except Exception, e:
            print 'Upload Failed: Error uploading to ftrack.'
            print e
    else:
        print 'Upload Failed: Error during file conversion.'


def main(argv):
    taskid = ''
    outdir = ''
    filename = ''
    try:
        opts, args = getopt.getopt(argv, 'hf:t:d:', ['filename=', 'taskid=', 'outdir='])
    except getopt.GetoptError:
        print 'mov_create_upload.py -f <filename> -t <taskid> -d <outdir>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: mov_create_upload.py -f <filename> -t <taskid> -d <outdir>\n' \
                  'Converts the images in outdir to mov with slate \n' \
                  'f = filename \n' \
                  't = taskid \n' \
                  'd = output file pattern eg. /data/production/ftrack_test/filename.#.exr'
            sys.exit()
        elif opt in ('-f', '--filename'):
            filename = arg
        elif opt in ('-t', '--taskid'):
            taskid = arg
        elif opt in ('-d', '--outfile'):
            outdir = arg.replace('#', '[0-9][0-9][0-9][0-9]')
    movFile, task = createMov(outdir, filename, taskid)
    if task and os.path.exists(movFile):
        uploadToFtrack(task, movFile)
    else:
        print "No task found. Cannot upload to ftrack."


if __name__ == '__main__':
    main(sys.argv[1:])
