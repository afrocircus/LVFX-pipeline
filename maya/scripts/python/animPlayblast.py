import os
import datetime
import shlex
import subprocess
import maya.cmds as cmds
import threading

from pymel.core import *
from Utils import ftrack_utils2


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class UI(object):

    def __init__(self, *args):
        self.win = 'window2'
        self.session = ftrack_utils2.startSession()
        self.shotName = self.version = ''
        self.task = None
        if window(self.win, q=True, ex=True):
            deleteUI(self.win)

    def buildUI(self):
        self.showHUD()
        template = uiTemplate('PlayblastTemplate', force=True)
        template.define(button, width=100, height=30, align='left')
        template.define(frameLayout, borderVisible=True, labelVisible=False)

        with window(s=True, title='Animation Playblast') as win:
            # start the template block
            with template:
                with columnLayout(adj=True):
                    text('')
                    with frameLayout():
                        with horizontalLayout(spacing=5):
                            button(label='Show HUD', bgc=(0.5, 0.2, 0.5), command=self.showHUD)
                            button(label='HIDE HUD', bgc=(0.1, 0.6, 0.9), command=self.hideHUD)
                    text(' ')
                    with frameLayout():
                        with columnLayout(rowSpacing=2, adj=True):
                            intSliderGrp('qualitySlider', label='Quality', field=True,
                                         minValue=0, maxValue=100, value=70)
                            floatSliderGrp('scaleSlider', label='Scale', field=True,
                                           minValue=0.1, maxValue=1.0, value=0.7)
                            button(label='Playblast', bgc=(0.2, 0.2, 0.2), command=self.playBlast)
                    with frameLayout():
                        with columnLayout(rowSpacing=2, adj=True):
                            with horizontalLayout():
                                button(label='Load Current Playblast Version', bgc=(0.2, 0.2, 0.1),
                                       command=self.loadPlayblast)
                                button(label='Load Selected Playblast', bgc=(0.2, 0.2, 0.1),
                                       command=self.loadSelectedPlayblast)
                            with horizontalLayout():
                                button(label='Upload Current Version to Dailies', bgc=(0.5, 0.5, 0.1),
                                       command=self.uploadToDailies)
                                button(label='Upload Selected to Dailies', bgc=(0.5, 0.5, 0.1),
                                       command=self.uploadSelectedToDailies)

    def getShotInfo(self, *args):
        taskid = None
        filename = cmds.file(q=True, sn=True)
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

    def playBlast(self, *args):
        filename = cmds.file(q=True, sn=True)
        dirname = os.path.dirname(filename)
        playblastDir = os.path.join(dirname, 'playblasts')
        if not os.path.exists(playblastDir):
            os.makedirs(playblastDir)
        outFile = os.path.join(playblastDir, '{0}_{1}_playblast.mov'.format(self.shotName, self.version))
        qlty = intSliderGrp('qualitySlider', q=True, value=True)
        perc = int(floatSliderGrp('scaleSlider', q=True, value=True)*100)
        playblast(fo=True, filename=outFile, format='qt', compression='jpeg', v=True,
                  quality=qlty, cc=True, widthHeight=(0,0), p=perc)

    def getLatestFile(self):
        filename = cmds.file(q=True, sn=True)
        dirname = os.path.dirname(filename)
        playblastDir = os.path.join(dirname, 'playblasts')
        outFile = os.path.join(playblastDir, '{0}_{1}_playblast.mov'.format(self.shotName, self.version))
        return outFile

    def getSelectedFile(self):
        filename = fileDialog()
        return filename

    def playMovie(self, outFile):
        mov_player = '/usr/bin/djv_view'
        if not os.path.exists(mov_player):
            mov_player = '/usr/bin/vlc'
            if not os.path.exists(mov_player):
                mov_player = ''
        if mov_player == '':
            print "No movie player found"
            return
        if os.path.exists(outFile):
            cmd = '{0} "{1}"'.format(mov_player, outFile)
            args = shlex.split(cmd)
            subprocess.call(args)

    def loadPlayblast(self, *args):
        outFile = self.getLatestFile()
        self.playMovie(outFile)

    def loadSelectedPlayblast(self, *args):
        outFile = self.getSelectedFile()
        if outFile:
            self.playMovie(outFile)

    def uploadToDailies(self, *args):
        filename = self.getLatestFile()
        mayaFile = cmds.file(q=True, sn=True)
        if self.task:
            self.uploadToFtrack(filename, mayaFile)
        else:
            print "No valid task found"

    def uploadSelectedToDailies(self, *args):
        filename = self.getSelectedFile()
        mayaFile = cmds.file(q=True, sn=True)
        if self.task and filename:
            self.uploadToFtrack(filename, mayaFile)
        else:
            print "No valid task found"

    @async
    def uploadToFtrack(self, filename, mayaFile):
        taskMeta = {'filename': mayaFile}
        ftrack_utils2.addMetadata(self.session, self.task, taskMeta)
        outfilemp4, outfilewebm, thumbnail, metadata = ftrack_utils2.prepMediaFiles(filename)
        print outfilemp4, outfilewebm, thumbnail
        ff, lf = ftrack_utils2.getFrameLength(filename)
        result = ftrack_utils2.convertFiles(filename, outfilemp4, outfilewebm, thumbnail)
        if result:
            print "file conversion complete"
            asset = ftrack_utils2.getAsset(self.session, self.task, 'ReviewAsset')
            status = ftrack_utils2.getStatus(self.session, 'Pending Internal Review')
            print asset, status
            try:
                print "starting upload..."
                ftrack_utils2.createAndPublishVersion(self.session, self.task, asset,
                                                      status,'Upload for Internal Review',
                                                      thumbnail, filename, outfilemp4,
                                                      outfilewebm, metadata, ff, lf, 24)
                print "upload complete..."
                ftrack_utils2.deleteFiles(outfilemp4, outfilewebm, thumbnail)
                print "file deleted"
            except Exception:
                print "Upload Failed"
        else:
            print "file conversion failed"

    def HUD(self):
        displayColor('headsUpDisplayLabels', 18, dormant=True)
        headsUpDisplay('leftTopHUD', section=0, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getShotInfo, atr=True)
        headsUpDisplay('rightTopHUD', section=4, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getDate, atr=True)
        headsUpDisplay('rightBottomHUD', section=9, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getFrame, atr=True)

    def showHUD(self, *args):
        headsUpDisplayList = headsUpDisplay(lh=True)
        if headsUpDisplayList:
            for headDisplay in headsUpDisplayList:
                headsUpDisplay(headDisplay, rem=True)
        self.HUD()

    def hideHUD(self, *args):
        headsUpDisplayList = headsUpDisplay(lh=True)
        for headDisplay in headsUpDisplayList:
            headsUpDisplay(headDisplay, rem=True)
