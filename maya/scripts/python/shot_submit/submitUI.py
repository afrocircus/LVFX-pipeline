import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
import maya.mel as mm
from Widgets.submit.jobWidget import JobWidget
from Utils.submit.submit import *
from vrayStandaloneWidget import VRayStandaloneWidget
from vrayMayaWidget import VRayMayaWidget


os.environ['SHOT_SUBMIT_CONFIG'] = '/data/production/pipeline/linux/common/config/shot_submit_config.json'


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
        self.vrayStandalone.hide()
        renderBoxLayout.addWidget(self.vrayMaya, 0, 0)
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

    def changeRendererOptions(self):
        if self.vrayStandalone.isHidden():
            self.vrayMaya.hide()
            self.vrayStandalone.show()
        else:
            self.vrayMaya.show()
            self.vrayStandalone.hide()
        self.repaint()

    def submitRender(self):
        if self.vrayStandalone.isHidden():
            filename, rendererParams = self.vrayMaya.getRenderParams()
        else:
            filename, rendererParams = self.vrayStandalone.getRenderParams()
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


'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = ShotSubmitUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''
