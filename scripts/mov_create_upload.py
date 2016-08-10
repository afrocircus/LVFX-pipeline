import sys
import os
import getopt
from Utils import ftrack_utils2
from Utils import prores_utils


def createMov(outdir, filename, taskid):
    session = ftrack_utils2.startANewSession()
    task = ftrack_utils2.getTask(session, taskid, filename)
    artist = ftrack_utils2.getUsername(task)
    date = ftrack_utils2.getDate()
    try:
        version = 'v' + ftrack_utils2.version_get(filename, 'v')[1]
    except:
        version = 'v01'
    shotInfo = '{0} | {1} | {2} | {3} | {4}'.format(task['project']['name'], task['parent']['name'],
                                                    task['name'], version, artist)
    imgSeq = [os.path.join(outdir, f) for f in os.listdir(outdir) if os.path.isfile(os.path.join(outdir, f))]
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
    return slateMov


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
                  'd = outdir path'
            sys.exit()
        elif opt in ('-f', '--filename'):
            filename = arg
        elif opt in ('-t', '--taskid'):
            taskid = arg
        elif opt in ('-d', '--outdir'):
            outdir = arg
    movFile = createMov(outdir, filename, taskid)
    print movFile

if __name__ == '__main__':
    main(sys.argv[1:])