import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
import maya.mel as mm
import json
import re
import shutil
from Widgets.submit.jobWidget import JobWidget
from Utils.submit.submit import *
from vrayStandaloneWidget import VRayStandaloneWidget
from vrayMayaWidget import VRayMayaWidget
from vrayExporterWidget import VRayExporterWidget
from Utils import ftrack_utils2


os.environ['SHOT_SUBMIT_CONFIG'] = '/data/production/pipeline/linux/common/config/shot_submit_config.json'
os.environ['SHOT_SUBMIT_TEMPLATE_DIR'] = '/data/production/pipeline/linux/common/template/'


class ShotSubmitUI(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName('ShotSubmitUI')
        self.setLayout(QtGui.QVBoxLayout())
        renderBox = QtGui.QGroupBox('Render Set')
        renderBoxLayout = QtGui.QGridLayout()
        renderBox.setLayout(renderBoxLayout)
        self.layout().addWidget(renderBox)
        self.vrayStandalone = VRayStandaloneWidget()
        self.vrayMaya = VRayMayaWidget()
        renderBoxLayout.addWidget(self.vrayStandalone, 0, 0)
        self.vrayMaya.hide()
        self.vrayStandalone.hide()
        renderBoxLayout.addWidget(self.vrayMaya, 0, 0)
        self.vrayExporter = VRayExporterWidget()
        renderBoxLayout.addWidget(self.vrayExporter, 0, 0)
        self.jobWidget = JobWidget('Maya')
        self.layout().addWidget(self.jobWidget)
        self.jobWidget.rendererChanged.connect(self.changeRendererOptions)
        hlayout = QtGui.QHBoxLayout()
        submitButton = QtGui.QPushButton('Submit')
        submitButton.clicked.connect(self.submitRender)
        hlayout.addWidget(submitButton)
        hlayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        self.layout().addLayout(hlayout)
        self.layout().addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

    def createDockLayout(self):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        columnLay = cmds.paneLayout(parent=gMainWindow, width=500)
        dockControl = cmds.dockControl(l='ShotSubmitUI', allowedArea='all',\
                                        area='right', content=columnLay, width=500)
        cmds.control(str(self.objectName()),e=True,p=columnLay)

    def changeRendererOptions(self, index):
        if index == 0:
            self.vrayExporter.show()
            self.vrayStandalone.hide()
            self.vrayMaya.hide()
        elif index == 1:
            self.vrayExporter.hide()
            self.vrayStandalone.show()
            self.vrayMaya.hide()
        elif index == 2:
            self.vrayExporter.hide()
            self.vrayStandalone.hide()
            self.vrayMaya.show()
        self.repaint()

    def submitRender(self):
        uploadCheck = False
        frameRange = rendererParams = filename = ''
        if self.vrayExporter.isVisible():
            filename, rendererParams = self.vrayExporter.getRenderParams()
            uploadCheck = self.vrayExporter.getUploadCheck()
            frameRange = self.vrayExporter.getFrameRange()
        elif self.vrayMaya.isVisible():
            filename, rendererParams = self.vrayMaya.getRenderParams()
        elif self.vrayStandalone.isVisible():
            filename, rendererParams = self.vrayStandalone.getRenderParams()
            uploadCheck = self.vrayStandalone.getUploadCheck()
            frameRange = self.vrayStandalone.getFrameRange()
        if filename is '':
            QtGui.QMessageBox.critical(self, 'Error', 'Please select a valid file to render!')
            return
        fileDir, fname = os.path.split(filename)
        jobName = 'Maya - %s' % fname
        renderer = self.jobWidget.getRenderer()
        splitMode = self.jobWidget.getSplitMode()
        pool = self.jobWidget.getClientPools()
        result = submitRender(jobName, renderer, pool, splitMode, rendererParams, filename)
        QtGui.QMessageBox.about(self, 'Submission Output', result)
        m = re.search(r'\[(\w+)\=(?P<id>\d+)\]', result)
        groupid = m.group('id')
        if uploadCheck:
            self.submitNukeJob(groupid, frameRange)

    def submitNukeJob(self, groupid, frameRange):
        filename = cmds.file(q=True, sn=True)
        fileDir, fname = os.path.split(filename)
        tmpDir = os.path.join(fileDir, 'tmp')
        if not os.path.exists(tmpDir):
            os.makedirs(tmpDir)
        print 'write json file to tmp dir'
        self.writeShotInfoToJson(filename, tmpDir)
        print 'copy nuke template to tmp dir'
        templateFile = os.path.join(os.environ['SHOT_SUBMIT_TEMPLATE_DIR'], 'render.nk')
        newFilePath = os.path.join(tmpDir, 'render.nk')
        shutil.copy(templateFile, newFilePath)
        print 'submit nuke job as dependant job'
        jobName = 'NukeDependant - %s' % fname
        renderer = 'Nuke/9.0v7'
        splitMode = '0,5'
        pool = self.jobWidget.getClientPools()
        nukeParams = ' -nj_dependency %s -frames %s -writenode Write1' % (groupid, frameRange)
        result = submitRender(jobName, renderer, pool, splitMode, nukeParams, newFilePath)
        print result

    def writeShotInfoToJson(self, filename, jsonDir):
        jsonFile = os.path.join(jsonDir, 'shot_info.json')
        jsonDict = {}
        jsonDict['filename'] = filename
        if self.vrayExporter.isVisible():
            jsonDict['outdir'] = str(self.vrayExporter.outdirEdit.text())
            jsonDict['outfile'] = str(self.vrayExporter.outfileEdit.text())
        elif self.vrayStandalone.isVisible():
            jsonDict['outdir'] = str(self.vrayStandalone.outdirEdit.text())
            jsonDict['outfile'] = str(self.vrayStandalone.outfileEdit.text())

        session = ftrack_utils2.startANewSession()
        taskid = ''
        if 'FTRACK_TASKID' in os.environ:
            taskid = os.environ['FTRACK_TASKID']
        task = ftrack_utils2.getTask(session, taskid, filename)
        if task:
            jsonDict['taskid'] = task['id']
            jsonDict['projectName'] = task['project']['name']
            jsonDict['shotName'] = task['parent']['name']
            jsonDict['taskName'] = task['name']
            jsonDict['username'] = ftrack_utils2.getUsername(task)
        else:
            jsonDict['taskid'] = ''
            jsonDict['projectName'] = ''
            jsonDict['shotName'] = ''
            jsonDict['taskName'] = ''
            jsonDict['username'] = ''
        try:
            jsonDict['version'] = ftrack_utils2.version_get(filename, 'v')[1]
        except ValueError:
            jsonDict['version'] = '0'
        with open(jsonFile, 'w') as jf:
            json.dump(jsonDict, jf, indent=4)


'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = ShotSubmitUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''
