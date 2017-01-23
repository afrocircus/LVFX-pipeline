import os
from PySide.QtCore import QObject, Signal
import threading
import datetime
import json
import maya.cmds as cmds
import shlex
import subprocess

from pymel.core import *
from Utils import ftrack_utils2
from Utils import capture


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class AnimPlayblast(QObject):

    moviePlayFail = Signal()
    movieUploadFail = Signal(str)
    movieUploadUpdate = Signal(int, str)

    def __init__(self):
        QObject.__init__(self)
        self.session = ftrack_utils2.startSession()
        self.shotName = self.version = ''
        self.task = None

    def getShotInfo(self, *args):
        taskid = None
        filename = self.getCurrentMayaFile()
        if 'FTRACK_TASKID' in os.environ:
            taskid = os.environ['FTRACK_TASKID']

        self.task = ftrack_utils2.getTask(self.session, taskid, filename)
        if self.task:
            projectName = self.task['project']['name']
            self.shotName = self.task['parent']['name']
            taskName = self.task['name']
            username = ftrack_utils2.getUsername(self.task)
            try:
                self.version = 'v' + ftrack_utils2.version_get(filename, 'v')[1]
            except ValueError:
                self.version = 'v00'
            shotInfo = '{0} | {1} | {2} | {3} | {4}'.format(projectName, self.shotName,
                                                            taskName, self.version, username)
        else:
            shotInfo = 'No valid task found'
        return shotInfo

    def getDate(self, *args):
        today = datetime.datetime.today()
        dateStr = '%02d-%02d-%d' % (today.day, today.month, today.year)
        return dateStr

    def getFrame(self, *args):
        frameCount = cmds.currentTime(q=True)
        return frameCount

    def HUD(self):
        displayColor('headsUpDisplayLabels', 18, dormant=True)
        headsUpDisplay('leftTopHUD', section=0, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getShotInfo, atr=True)
        headsUpDisplay('rightTopHUD', section=4, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getDate, atr=True)
        headsUpDisplay('rightBottomHUD', section=9, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getFrame, atr=True)

    def showHUD(self):
        headsUpDisplayList = headsUpDisplay(lh=True)
        if headsUpDisplayList:
            for headDisplay in headsUpDisplayList:
                headsUpDisplay(headDisplay, rem=True)
        self.HUD()

    def hideHUD(self):
        headsUpDisplayList = headsUpDisplay(lh=True)
        for headDisplay in headsUpDisplayList:
            headsUpDisplay(headDisplay, rem=True)

    def load_preset(self, path):
        """Load options json from path"""
        with open(path, "r") as f:
            return json.load(f)

    def playBlast(self, qlty, camera):
        filename = self.getCurrentMayaFile()
        dirname = os.path.dirname(filename)
        playblastDir = os.path.join(dirname, 'playblasts')
        if not os.path.exists(playblastDir):
            os.makedirs(playblastDir)
        outFile = os.path.join(playblastDir, '{0}_{1}_playblast.mov'.format(self.shotName, self.version))
        presetName = 'default'

        presetPath = os.path.join(os.path.dirname(capture.__file__),
                                  'capture_presets',
                                  (presetName + '.json'))
        preset = self.load_preset(presetPath)
        preset['camera'] = camera

        audioNodes = cmds.ls(type='audio')
        if len(audioNodes) > 0:
            capture.capture(filename=outFile,
                            overwrite=True,
                            quality=70, compression='jpeg',
                            sound=audioNodes[0],
                            **preset)
        else:
            capture.capture(filename=outFile,
                            overwrite=True,
                            quality=70, compression='jpeg',
                            **preset)

    def getCurrentVersion(self):
        filename = self.getCurrentMayaFile()
        dirname = os.path.dirname(filename)
        playblastDir = os.path.join(dirname, 'playblasts')
        outFile = os.path.join(playblastDir, '{0}_{1}_playblast.mov'.format(self.shotName, self.version))
        return outFile

    def getCurrentMayaFile(self):
        filename = cmds.file(q=True, sn=True)
        return filename

    def getCameras(self):
        cameras = cmds.listCameras(p=True)
        return cameras

    def lookThruCamera(self, camera):
        cmds.lookThru(camera)

    @async
    def playMovie(self, outFile):
        mov_player = '/usr/bin/djv_view'
        try:
            cmd = '{0} "{1}"'.format(mov_player, outFile)
            args = shlex.split(cmd)
            subprocess.call(args)
        except Exception:
            mov_player = '/usr/bin/vlc'
            try:
                cmd = '{0} "{1}"'.format(mov_player, outFile)
                args = shlex.split(cmd)
                subprocess.call(args)
            except Exception:
                self.moviePlayFail.emit()

    @async
    def uploadToFtrack(self, filename, mayaFile, comment):
        if self.task:
            taskMeta = {'filename': mayaFile}
            self.movieUploadUpdate.emit(10, 'Updating metadata...')
            ftrack_utils2.addMetadata(self.session, self.task, taskMeta)
            self.movieUploadUpdate.emit(15, 'Prepping media files...')
            ftrack_utils2.copyToApprovals(filename, self.task['project'])
            outfilemp4, outfilewebm, thumbnail, metadata = ftrack_utils2.prepMediaFiles(filename)
            self.movieUploadUpdate.emit(20, 'Starting file conversion...')
            ff, lf = ftrack_utils2.getFrameLength(filename)
            result = ftrack_utils2.convertFiles(filename, outfilemp4, outfilewebm, thumbnail)
            if result:
                self.movieUploadUpdate.emit(45, 'File conversion complete.')
                self.movieUploadUpdate.emit(50, 'Starting file upload...')
                asset = ftrack_utils2.getAsset(self.session, self.task, 'ReviewAsset')
                status = ftrack_utils2.getStatus(self.session, 'Pending Internal Review')
                try:
                    ftrack_utils2.createAndPublishVersion(self.session, self.task, asset,
                                                          status, comment,
                                                          thumbnail, filename, outfilemp4,
                                                          outfilewebm, metadata, ff, lf, 24, True)
                    self.movieUploadUpdate.emit(95, 'cleaning up temporary files...')
                    ftrack_utils2.deleteFiles(outfilemp4, outfilewebm, thumbnail)
                    self.movieUploadUpdate.emit(100, 'Upload Complete!')
                except Exception:
                    self.movieUploadFail.emit('Upload Failed: Error uploading to ftrack.')
                ftrack_utils2.syncToJHB(filename)
            else:
                self.movieUploadFail.emit('Upload Failed: Error during file conversion.')
        else:
            self.movieUploadFail.emit('Upload Failed: No Valid Task Found')
