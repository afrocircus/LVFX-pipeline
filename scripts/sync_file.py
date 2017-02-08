import sys
import os
import logging
import subprocess
import shlex
import argparse


def validateArgs(dest, srcObj, exclude):
    """
    Validate arguments
    :param dest: destination studio
    :param srcObj: src file or dir
    :param exclude: directories or files to exclude
    :return: dest, srcObj, excludeList
    """
    # Validate destination studio

    # if destination not specified, use env variable 'STUDIO'
    if not dest and 'STUDIO' in os.environ:
        if os.environ['STUDIO'] == 'JHB':
            dest = 'CPT'
        elif os.environ['STUDIO'] == 'CPT':
            dest = 'JHB'

    # Error if valid destination not specified
    if dest not in ['JHB', 'CPT']:
        dest = None

    # Validate srcObj
    if not os.path.exists(srcObj):
        srcObj = None
    else:
        srcObj = os.path.abspath(srcObj)

    # Validate exclude files
    excludeList = []
    if exclude:
        excludeList = exclude.split(',')

    return dest, srcObj, excludeList


def main(argv):
    parser = argparse.ArgumentParser(description='Sync file and directories ')
    parser.add_argument('-dest', help='Destination Location. Specify JHB|CPT')
    parser.add_argument('-file', help='File/Dir to transfer', required=True)
    parser.add_argument('-ex', help='comma separated list of directories or file types to exclude')

    args = parser.parse_args()
    dest = args.dest
    srcObj = args.file
    exclude = args.ex

    dest, srcObj, excludeList = validateArgs(dest, srcObj, exclude)
    if not dest:
        logging.error('No valid destination specified. Please specify -dest JHB|CPT')
        return

    if not srcObj:
        logging.error('Invalid src file/dir.')
        return

    rsyncCmd = 'rsync -auvrzh --progress'

    if excludeList:
        for ex in excludeList:
            rsyncCmd += ' --exclude=%s' % ex

    srcXfer = srcObj.rstrip('/')
    destLoc = ''
    destXfer = os.path.dirname(srcObj)
    if dest == 'CPT':
        destLoc = 'server@192.168.2.5'
    elif dest == 'JHB':
        destXfer = destXfer.replace('/data/production', '/mnt/production')
        destLoc = 'root@192.168.0.210'

    rsyncCmd += ' --rsync-path="mkdir -p \"{0}\" && rsync" "{1}" {2}:"{0}/"'.format(
                destXfer, srcXfer, destLoc)
    args = shlex.split(rsyncCmd)
    subprocess.call(args)


if __name__ == '__main__':
    main(sys.argv[1:])
