import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
import pymel.core as pm
from Utils import ftrack_utils2

class ImportWidget(QtGui.QWidget):
    def __init__(self, shotAssetPath, shot):
        super(ImportWidget, self).__init__()
        self.setLayout(QtGui.QVBoxLayout())
        self.setContentsMargins(0, 0, 0, 0)
        objTypeLayout = QtGui.QHBoxLayout()
        objTypeLayout.addWidget(QtGui.QLabel('Object Type:'))
        self.objTypeCombobox = QtGui.QComboBox()
        self.objTypeCombobox.addItems(['camera', 'geometry'])
        self.objTypeCombobox.currentIndexChanged.connect(self.changeObjWidget)
        objTypeLayout.addWidget(self.objTypeCombobox)
        objTypeLayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding,
                                                QtGui.QSizePolicy.Minimum))
        self.layout().addLayout(objTypeLayout)
        self.camImport = CameraImportWidget(shotAssetPath, shot)
        self.layout().addWidget(self.camImport)
        self.layout().addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Minimum,
                                                QtGui.QSizePolicy.Expanding))

    def changeObjWidget(self):
        index = self.objTypeCombobox.currentIndex()
        if index == 0:
            self.camImport.setVisible(True)
        elif index == 1:
            self.camImport.setVisible(False)


class CameraImportWidget(QtGui.QWidget):
    def __init__(self, shotAssetPath, shot):
        super(CameraImportWidget, self).__init__()
        self.setLayout(QtGui.QHBoxLayout())
        camFilePath = ''
        if shotAssetPath and shot:
            camFilePath = self.getCamFilePath(shot, shotAssetPath)
        self.latestButton = QtGui.QPushButton('Import Latest Camera')
        self.latestButton.clicked.connect(lambda: self.importLatest(camFilePath))
        self.layout().addWidget(self.latestButton)
        self.selectButton = QtGui.QPushButton('Import Selected Camera')
        self.layout().addWidget(self.selectButton)
        self.selectButton.clicked.connect(lambda: self.importSelected(camFilePath))

    def getCamFilePath(self, shot, shotAssetPath):
        camFilePath = shot['custom_attributes']['shot_cam']
        print camFilePath
        if camFilePath == '':
            shotName = shot['name']
            camAssetDir = os.path.join(shotAssetPath, 'camera')
            version = self.getLatestVersion(camAssetDir)
            camFileName = '%s_camera_v%02d.abc' % (shotName, version)
            camFilePath = os.path.join(camAssetDir, camFileName)
        return camFilePath

    def getLatestVersion(self, folder):
        version = 1
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            maxVersion = 1
            if files:
                for f in files:
                    try:
                        version = int(ftrack_utils2.version_get(f, 'v')[1])
                    except ValueError:
                        version = 1
                    if version >= maxVersion:
                        maxVersion = version
        return version

    def importSelected(self, camFilePath):
        dialog = QtGui.QFileDialog()
        filename, fileType = dialog.getOpenFileName(self, "Select File",
                                                    os.path.dirname(camFilePath),
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        if filename:
            cmds.AbcImport(filename)
            pm.confirmDialog(t= 'Camera Import',
                             m='%s imported successfully' % os.path.split(filename)[1],
                             b='OK')

    def importLatest(self, camFilePath):
        cmds.AbcImport(camFilePath)
        pm.confirmDialog(t= 'Camera Import',
                         m='%s imported successfully' % os.path.split(camFilePath)[1],
                         b='OK')
