import sys
import os
import argparse


def main(argv):
    parser = argparse.ArgumentParser(description='Creates symlinks of all files in the given folder'
                                                 'while maintaining file hierarchy.')
    parser.add_argument('-source', help='Name of the source version dir', required=True)
    parser.add_argument('-dest', help='Name of the destination dir', required=True)

    args = parser.parse_args()
    sd = args.source
    dd = args.dest
    currDir = os.getcwd()
    destDir = os.path.join(currDir, dd)
    srcDir = os.path.join(currDir, sd)
    if not os.path.exists(destDir):
        os.makedirs(destDir)
    version = os.path.basename(srcDir.strip('/'))
    if os.path.exists(srcDir):
        for rootDir, subdirs, files in os.walk(srcDir):
            if not rootDir == srcDir:
                dirs = rootDir.partition(srcDir)[-1].replace(version, 'latest')
                dirs = dirs.lstrip('/')
                newDest = os.path.join(destDir, dirs)
                if not os.path.exists(newDest):
                    os.makedirs(newDest)
                    print 'made folder: %s' % newDest
                for f in files:
                    srcFile = os.path.join(rootDir, f)
                    destFile = os.path.join(newDest, f).replace(version, 'latest')
                    if os.path.exists(destFile):
                        os.remove(destFile)
                    os.symlink(srcFile, destFile)
                    print 'created symlink for %s' % f
        print "Symlink creation successfull"
    else:
        print "Not a valid source directory"


if __name__ == '__main__':
    main(sys.argv[1:])
