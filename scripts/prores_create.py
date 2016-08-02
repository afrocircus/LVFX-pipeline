import os
import sys
import getopt
import subprocess
import shlex


def createProres(quality, framerate):
    currentDir = os.getcwd()
    movFiles = [os.path.join(currentDir, f) for f in os.listdir(currentDir) if os.path.isfile(f) and
                os.path.splitext(f)[-1] == '.mov']
    q = 2
    prDir = 'pr422'
    if quality == 4444:
        prDir = 'pr4444'
    proresDir = os.path.join(currentDir, prDir)
    if not os.path.exists(proresDir):
        os.makedirs(proresDir)
    for inputFile in movFiles:
        fpath, fname = os.path.split(inputFile)
        outputFile = os.path.join(os.path.join(fpath, proresDir), fname)
        print outputFile
        ffmpegCmd = 'ffmpeg -y -an -i "{0}" -vcodec prores -profile:v {1} -r "{2}" ' \
                    '"{3}"'.format(inputFile, q, framerate, outputFile)
        args = shlex.split(ffmpegCmd)
        subprocess.call(args)


def main(argv):
    quality = 422
    framerate = 24.0
    try:
        opts, args = getopt.getopt(argv, 'hq:r:', ['quality=', 'framerate='])
    except getopt.GetoptError:
        print 'prores_create.py -q <quality> -r <framerate>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: prores_create.py -q <quality> -r <framerate>\n' \
                  'Finds all .mov files in current working directory and converts to prores \n' \
                  'quality = 422 or 4444 Default=422 \n' \
                  'framerate = number Default=24'
            sys.exit()
        elif opt in ('-q', '--quality'):
            if arg not in ('422', '4444'):
                print 'Invalid quality value. Valid options are 422 or 4444'
                sys.exit()
            quality = int(arg)
        elif opt in ('-r', '--framerate'):
            try:
                framerate = float(arg)
            except ValueError:
                print 'Invalid framerate value. Framerate rate must be a number'
                sys.exit()
    createProres(quality, framerate)

if __name__ == '__main__':
    main(sys.argv[1:])
