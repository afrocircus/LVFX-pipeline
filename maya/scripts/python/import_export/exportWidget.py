import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
from Utils import ftrack_utils2

class ExportWidget(QtGui.QWidget):
    def __init__(self, session, shotAssetPath, shot):
        super(ExportWidget, self).__init__()
        self.setLayout(QtGui.QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)
        objTypeLayout = QtGui.QHBoxLayout()
        objTypeLayout.addWidget(QtGui.QLabel('Object Type:'))
        self.objTypeCombobox = QtGui.QComboBox()
        self.objTypeCombobox.addItems(['camera', 'geometry'])
        self.objTypeCombobox.currentIndexChanged.connect(self.changeObjWidget)
        objTypeLayout.addWidget(self.objTypeCombobox)
        objTypeLayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        self.layout().addLayout(objTypeLayout)
        self.camExport = CameraExportWidget(shotAssetPath, shot)
        self.layout().addWidget(self.camExport)
        self.exportButton = QtGui.QPushButton()
        self.exportButton.setText('Export')
        self.exportButton.clicked.connect(lambda: self.exportObjects(session, shot))
        self.layout().addWidget(self.exportButton)
        self.layout().addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Minimum,
                                                QtGui.QSizePolicy.Expanding))

    def exportObjects(self, session, shot):
        if self.camExport.isVisible():
            params = self.camExport.getCommandParams()
            cmds.AbcExport(j=params)
            shot['custom_attributes']['shot_cam'] = str(self.camExport.outFileEdit.text())
            session.commit()

    def changeObjWidget(self):
        index = self.objTypeCombobox.currentIndex()
        if index == 0:
            self.camExport.setVisible(True)
        elif index == 1:
            self.camExport.setVisible(False)


class CameraExportWidget(QtGui.QWidget):
    def __init__(self, shotAssetPath, shot):
        super(CameraExportWidget, self).__init__()
        self.setLayout(QtGui.QVBoxLayout())
        widgetLayout = QtGui.QGridLayout()
        self.layout().addLayout(widgetLayout)
        widgetLayout.addWidget(QtGui.QLabel('Select Camera:'), 0, 0)
        self.cameraBox = QtGui.QComboBox()
        self.populateCameraBox()
        widgetLayout.addWidget(self.cameraBox, 0, 1)
        widgetLayout.addWidget(QtGui.QLabel('Frame Start'), 1, 0)
        self.frameStartEdit = QtGui.QLineEdit()
        self.frameStartEdit.setText(str(cmds.playbackOptions(q=True, minTime=True)))
        widgetLayout.addWidget(self.frameStartEdit, 1, 1)
        widgetLayout.addWidget(QtGui.QLabel('Frame End'), 1, 2)
        self.frameEndEdit = QtGui.QLineEdit()
        self.frameEndEdit.setText(str(cmds.playbackOptions(q=True, maxTime=True)))
        widgetLayout.addWidget(self.frameEndEdit, 1, 3)
        widgetLayout.addWidget(QtGui.QLabel('Frame Step'), 2, 0)
        self.frameStepEdit = QtGui.QLineEdit()
        self.frameStepEdit.setText('1')
        widgetLayout.addWidget(self.frameStepEdit, 2, 1)
        fileLayout = QtGui.QHBoxLayout()
        fileLayout.addWidget(QtGui.QLabel('Output File:'))
        self.outFileEdit = QtGui.QLineEdit()
        camFilePath = ''
        if shotAssetPath and shot:
            camFilePath = self.getOutputFilename(shot, shotAssetPath)
        self.outFileEdit.setText(camFilePath)
        fileLayout.addWidget(self.outFileEdit)
        toolButton = QtGui.QToolButton()
        toolButton.setText('...')
        toolButton.clicked.connect(lambda: self.saveOutputFilename(camFilePath))
        fileLayout.addWidget(toolButton)
        self.layout().addLayout(fileLayout)

    def getOutputFilename(self, shot, shotAssetPath):
        shotName = shot['name']
        camAssetDir = os.path.join(shotAssetPath, 'camera')
        version = self.getLatestVersion(camAssetDir)
        camFileName = '%s_camera_v%02d.abc' % (shotName, version)
        camFilePath = os.path.join(camAssetDir, camFileName)
        return camFilePath

    def getLatestVersion(self, folder):
        version = 0
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            maxVersion = 1
            if files:
                for f in files:
                    try:
                        version = int(ftrack_utils2.version_get(f, 'v')[1])
                    except ValueError:
                        version = 0
                    if version >= maxVersion:
                        maxVersion = version
        version = version + 1
        return version

    def populateCameraBox(self):
        cameras = cmds.listCameras()
        self.cameraBox.addItems(cameras)

    def saveOutputFilename(self, shotAssetPath):
        dialog = QtGui.QFileDialog()
        filename, fileType = dialog.getSaveFileName(self, "Select File",
                                                    shotAssetPath,
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        if filename:
            self.outFileEdit.setText(filename)

    def getCommandParams(self):
        frameRange = '-fr {0} {1}'.format(float(self.frameStartEdit.text()),
                                                  float(self.frameEndEdit.text()))
        step = '-step {0}'.format(float(self.frameStepEdit.text()))
        cameraNode = '-root {0}'.format(str(self.cameraBox.currentText()))
        filename = '-file {0}'.format(str(self.outFileEdit.text()))
        return '{0} {1} {2} -ws -ef {3}'.format(frameRange, step, cameraNode, filename)
