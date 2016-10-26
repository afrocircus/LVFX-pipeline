import sys
import re
import logging
import os
import argparse
import glob
import shutil
from datetime import datetime


def version_get(string, prefix, suffix=None):
    """Extract version information from filenames.  Code from Foundry's nukescripts.version_get()"""

    if string is None:
        raise ValueError, "Empty version string - no match"

    regex = "[/_.]" + prefix + "\d+"
    matches = re.findall(regex, string, re.IGNORECASE)
    if not len(matches):
        msg = "No \"_" + prefix + "#\" found in \"" + string + "\""
        raise ValueError, msg
    return (matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group())


def getDeliveryFolder(project):
    # Create delivery folder /data/production/<project>/production/deliveries/<Date>
    projectPath = '/data/production/{0}'.format(project)
    today = datetime.today()
    date = '{}-{:02d}-{:02d}'.format(today.year, today.month, today.day)
    deliveryFolder = os.path.join(projectPath, 'production', 'deliveries', date)
    if not os.path.exists(deliveryFolder):
        os.makedirs(deliveryFolder)
    try:
        os.chmod(deliveryFolder, 0777)
    except OSError:
        logging.warning('Unable to change directory permissions to {}'.format(deliveryFolder))
    return deliveryFolder


def getVersionFolder(project, sq, shot, ver):
    # Get the output version folder /data/production/<project>/shots/<sq>/<shot>/img/comps/<version>
    projectPath = '/data/production/{0}'.format(project)
    compsFolder = os.path.join(projectPath, 'shots', sq, shot, 'img', 'comps')
    if ver:
        versionFolder = os.path.join(compsFolder, 'v{:02d}'.format(int(ver)))
    else:
        versions = [os.path.split(d)[1] for d in glob.glob(os.path.join(compsFolder, 'v[0-9]*'))
                    if os.path.isdir(d)]
        versions.sort()
        versionFolder = os.path.join(compsFolder, versions[-1])
    return versionFolder


def validateArgs(project, sq, shot, ver):
    # Validate arguments
    projectPath = '/data/production/{0}'.format(project)
    if not project or not os.path.exists(projectPath):
        logging.error('Please specify a valid project')
        return False

    if not sq or not shot:
        logging.error('Please specify a valid sq and shot name')
        return False

    shotFolder = os.path.join(projectPath, 'shots', sq, shot)
    if not os.path.exists(shotFolder):
        logging.error('Shot folder not found. Please specify a valid sq and shot name')
        return False

    if ver:
        try:
            ver = int(ver)
        except ValueError:
            logging.error('Invalid version. Version must be an integer.')
            return False
    return True


def copyQCtoDelivery(deliveryFolder, versionFolder, shot, sq):
    # Copy to QC Delivery folder
    version = os.path.split(versionFolder)[1]
    qcFolder = os.path.join(versionFolder, 'qc')
    if os.path.exists(qcFolder):
        print ('Processing {}:{}:{}. Copying QC movie...'.format(sq, shot, version))
        shotDelivery = os.path.join(deliveryFolder, 'qc')
        if not os.path.exists(shotDelivery):
            os.makedirs(shotDelivery)
        for f in os.listdir(qcFolder):
            qcFile = os.path.join(qcFolder, f)
            destFile = os.path.join(shotDelivery, f)
            if os.path.isfile(qcFile):
                shutil.copyfile(qcFile, destFile)
        print ('QC movie copy complete for {}:{}:{}'.format(sq, shot, version))


def copyDPXtoDelivery(deliveryFolder, versionFolder, shot, sq):
    # Copy DPX images to the delivery folder
    version = os.path.split(versionFolder)[1]
    imgFolder = os.path.join(versionFolder, 'img')
    if os.path.exists(imgFolder):
        print ('Processing {}:{}:{}. Copying DPX images...'.format(sq, shot, version))
        shotDelivery = os.path.join(deliveryFolder, 'dpx', sq, shot)
        if not os.path.exists(shotDelivery):
            os.makedirs(shotDelivery)
        else:
            shutil.rmtree(shotDelivery)
            os.makedirs(shotDelivery)
        for f in os.listdir(imgFolder):
            qcFile = os.path.join(imgFolder, f)
            destFile = os.path.join(shotDelivery, f)
            if os.path.isfile(qcFile):
                shutil.copyfile(qcFile, destFile)
        print ('DPX images copy complete for {}:{}:{}'.format(sq, shot, version))


def processCopy(project, sq, shot, ver):
    deliveryFolder = getDeliveryFolder(project)
    versionFolder = getVersionFolder(project, sq, shot, ver)
    copyQCtoDelivery(deliveryFolder, versionFolder, shot, sq)
    copyDPXtoDelivery(deliveryFolder, versionFolder, shot, sq)


def main(argv):
    parser = argparse.ArgumentParser(description='Copies dpx and qc movie to the delivery folder.')
    parser.add_argument('-file', help='Text file containing shot information. \n'
                                      'Each line in the text file must be of format project:ep:sq:shot:ver '
                                      'eg. ex_proj:ep01:sq01:sq01_sh010:4 or \n'
                                      'if there is no episode whalecaller::112:112_0010:5\n'
                                      'or if there no episode or version whalecaller::112:112_0050: ')
    parser.add_argument('-project', help='Name of project')
    parser.add_argument('-ep', help='Name of episode')
    parser.add_argument('-sq', help='Name of sequence')
    parser.add_argument('-shot', help='Name of shot')
    parser.add_argument('-ver', help='Version number. If no version is specified, latest version is copied')

    args = parser.parse_args()
    filename = args.file
    project = args.project
    ep = args.ep
    sq = args.sq
    shot = args.shot
    ver = args.ver

    if filename and os.path.exists(filename):
        # If a file is passed, ignore all other arguments and parse the file
        validLines = []
        invalidLines = []
        with open(filename) as fp:
            for line in fp:
                if len(line.split(':')) != 5:
                    logging.error('Invalid file formatting. Each line of the text file must be '
                                  'of the format project:ep:sq:shot:ver. \n'
                                  'If there is no episode, the format is project::sq:shot:ver \n'
                                  'If there is no version, the format is project::sq:shot:')
                    sys.exit(2)
                else:
                    validLines.append(line.strip())
        for line in validLines:
            infoSplit = line.split(':')
            project = infoSplit[0]
            sq = infoSplit[2]
            if infoSplit[1] != '':
                sq = os.path.join(infoSplit[1], sq)
            shot = infoSplit[3]
            ver = infoSplit[4]
            if validateArgs(project, sq, shot, ver):
                processCopy(project, sq, shot, ver)
            else:
                invalidLines.append(line)
        if invalidLines:
            logging.error('Unable to process the following lines in the file:')
            for line in invalidLines:
                print line
    else:
        # If there is an episode passed in the arguments, the new sq is now ep/sq
        if ep:
            sq = os.path.join(ep, sq)
        if validateArgs(project, sq, shot, ver):
            processCopy(project, sq, shot, ver)
        else:
            sys.exit(2)


if __name__ == '__main__':
    main(sys.argv[1:])
