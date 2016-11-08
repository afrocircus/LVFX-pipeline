import sys
import os
import ftrack
import logging
import argparse


def getShot(shotPath):
    shot = None
    try:
        shot = ftrack.getShot(shotPath)
    except Exception:
        pass
    return shot


def getProjectFolder(project):
    projFolder = project.get('root')
    if projFolder == '':
        disk = ftrack.Disk(project.get('diskid'))
        rootFolder = ''
        if sys.platform == 'win32':
            rootFolder = disk.get('windows')
        elif sys.platform == 'linux2':
            rootFolder = disk.get('unix')
        projFolder = os.path.join(rootFolder, project.getName())
    return projFolder


def getShotPlatesFolder(shot):
    project = ftrack.Project(id=shot.get('showid'))
    projectFolder = getProjectFolder(project)
    sequenceName = shot.getParent().getName()
    shotName = shot.getName()
    imgFolder = os.path.join(projectFolder, 'shots', sequenceName, shotName, 'img')
    platesFolder = os.path.join(imgFolder, 'plates')
    if not os.path.exists(platesFolder):
        platesFolder = os.path.join(platesFolder, 'proxy')
    return platesFolder


def getFrameRange(platesFolder):
    firstFrame = lastFrame = 0
    files = [f for f in os.listdir(platesFolder) if f.endswith('.dpx')]
    if len(files) == 0:
        # if no dpx images found then check for jpegs
        files = [f for f in os.listdir(platesFolder) if f.endswith('.jpeg')]
        if len(files) == 0:
            # if no jpegs found then return
            return firstFrame, lastFrame
    if files:
        files.sort()
        firstFrame = float(files[0].split('.')[-2])
        lastFrame = float(files[-1].split('.')[-2])
    return firstFrame, lastFrame


def main(argv):
    parser = argparse.ArgumentParser(description='Updates the frame range of the shot in ftrack')
    parser.add_argument('-project', help='Name of project' , )
    parser.add_argument('-ep', help='Name of episode')
    parser.add_argument('-sq', help='Name of sequence')
    parser.add_argument('-shot', help='Name of shot')

    args = parser.parse_args()
    project = args.project
    ep = args.ep
    sq = args.sq
    shot = args.shot

    if ep:
        shotPath = [project, ep, sq, shot]
    else:
        shotPath = [project, sq, shot]
    shot = getShot(shotPath)
    if not shot:
        logging.error('No matching shot found.')
        sys.exit(2)
    platesFolder = getShotPlatesFolder(shot)
    ff, lf = getFrameRange(platesFolder)
    try:
        shot.set('fstart', ff)
        shot.set('fend', lf)
    except Exception:
        logging.error('Unable to set frame range ff={0}, lf={1}'.format(ff, lf))
    print 'Frame range set for shot {}'.format(shot.getName())


if __name__ == '__main__':
    main(sys.argv[1:])
