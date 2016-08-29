import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
import maya.mel as mm
import xmlrpclib
import json
from Widgets.submit.hqueueWidget import HQueueWidget
from vrayStandaloneWidget import VRayStandaloneWidget
from vrayMayaWidget import VRayMayaWidget
from vrayExporterWidget import VRayExporterWidget


class ShotSubmitUI(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName('ShotSubmitUI')
        self.setLayout(QtGui.QVBoxLayout())
        renderBox = QtGui.QGroupBox('Render Set')
        renderBoxLayout = QtGui.QGridLayout()
        renderBox.setLayout(renderBoxLayout)
        self.layout().addWidget(renderBox)
        data = self.jsonRead('vrayStandaloneSettings.json')
        self.vrayStandalone = VRayStandaloneWidget(data)
        self.vrayMaya = VRayMayaWidget()
        renderBoxLayout.addWidget(self.vrayStandalone, 0, 0)
        self.vrayMaya.hide()
        self.vrayStandalone.hide()
        renderBoxLayout.addWidget(self.vrayMaya, 0, 0)
        self.vrayExporter = VRayExporterWidget()
        renderBoxLayout.addWidget(self.vrayExporter, 0, 0)
        self.jobWidget = HQueueWidget('Maya')
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
        filename = ''
        renderer = self.jobWidget.getRenderer('Maya')
        chunk = self.jobWidget.getSplitMode()
        pool = self.jobWidget.getClientPools()
        if pool == 'Linux Farm':
            pool = None
        dependency = self.jobWidget.getDependentJob()
        user = self.jobWidget.getSlackUser()
        priority = self.jobWidget.getPriority()
        hq_server = self.jobWidget.getHQProxy()
        if not isinstance(hq_server, xmlrpclib.ServerProxy):
            QtGui.QMessageBox.critical(self, 'HQueue Server Error', "Unable to connect to HQueue server")
            return
        if self.vrayExporter.isVisible():
            filename, rendererParams = self.vrayExporter.getRenderParams()
            if filename is '':
                QtGui.QMessageBox.critical(self, 'Error', 'Please select a valid file to render!')
                return
            fileDir, fname = os.path.split(filename)
            jobname = 'VRay - %s' % fname
            rendererParams = '%s %s' % (renderer, rendererParams)
            jobIds = self.jobWidget.submitVRExport(hq_server, jobname, rendererParams, priority,
                                                   pool, user, dependency)
            QtGui.QMessageBox.about(self, 'Job Submit Successful', "Job submitted successfully. "
                                                                   "Job Id = {0}".format(jobIds))
        elif self.vrayStandalone.isVisible():
            paramDict, rendererParams = self.vrayStandalone.getRenderParams()
            self.jsonWrite('vrayStandaloneSettings.json', paramDict)
            if paramDict['filename'] == '':
                QtGui.QMessageBox.critical(self, 'Error', 'Please select a valid file to render!')
                return
            fileDir, fname = os.path.split(paramDict['filename'])
            jobname = 'VRay - %s' % fname
            rendererParams = '%s %s' % (renderer, rendererParams)
            jobIds = self.jobWidget.submitVRStandalone(hq_server, jobname, paramDict['filename'],
                                                       paramDict['imgFile'], rendererParams,
                                                       paramDict['startFrame'], paramDict['endFrame'],
                                                       paramDict['step'], chunk, paramDict['multiple'],
                                                       pool, priority, paramDict['review'], user, dependency)
            QtGui.QMessageBox.about(self, 'Job Submit Successful', "Job submitted successfully. "
                                                                   "Job Id = {0}".format(jobIds))



    def jsonWrite(self, jsonFilename, jsonDict):
        mayaFile = cmds.file(q=True, sn=True)
        if not mayaFile:
            return
        jsonDir = os.path.join(os.path.dirname(mayaFile), 'tmp')
        if not os.path.exists(jsonDir):
            os.makedirs(jsonDir)
        jsonFile = os.path.join(jsonDir, jsonFilename)
        with open(jsonFile, 'w') as jf:
            json.dump(jsonDict, jf, indent=4)

    def jsonRead(self, filename):
        mayaFile = cmds.file(q=True, sn=True)
        if not mayaFile:
            return {}
        fileDir= os.path.split(mayaFile)[0]
        tmpDir = os.path.join(fileDir, 'tmp')
        jsonFile = os.path.join(tmpDir, filename)
        data = {}
        if os.path.exists(jsonFile):
            jsonFile = open(jsonFile).read()
            data = json.loads(jsonFile)
        return data



'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = ShotSubmitUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''
