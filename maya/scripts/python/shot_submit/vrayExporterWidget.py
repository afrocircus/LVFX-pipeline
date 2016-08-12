import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
from PySide.QtCore import Signal


class VRayExporterWidget(QtGui.QWidget):
    def __init__(self):
        super(VRayExporterWidget, self).__init__()
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        fileLayout = QtGui.QHBoxLayout()
        fileLayout.addWidget(QtGui.QLabel('Maya Filename:'))
        self.fileTextBox = QtGui.QLineEdit()
        self.fileTextBox.setText('')
        self.fileTextBox.textChanged.connect(self.setProjectDirectory)
        browseButton = QtGui.QToolButton()
        browseButton.setText('...')
        browseButton.clicked.connect(self.openFileBrowser)
        fileLayout.addWidget(self.fileTextBox)
        fileLayout.addWidget(browseButton)
        self.layout().addLayout(fileLayout)
        widgetLayout = QtGui.QGridLayout()
        self.layout().addLayout(widgetLayout)
        widgetLayout.addWidget(QtGui.QLabel('Frame List:'), 0, 0)
        self.frameRangeEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.frameRangeEdit, 0, 1)
        widgetLayout.addWidget(QtGui.QLabel('Image Format'), 1, 0)
        self.imgFormatBox = QtGui.QComboBox()
        self.imgFormatBox.addItems(['png', 'jpeg', 'vrimage', 'hdr', 'exr', 'bmp', 'tga', 'sgi'])
        widgetLayout.addWidget(self.imgFormatBox, 1, 1)
        widgetLayout.addWidget(QtGui.QLabel('Image Width:'), 1, 2)
        self.imgWidEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.imgWidEdit, 1, 3)
        widgetLayout.addWidget(QtGui.QLabel('Image Height:'), 1, 4)
        self.imgHghEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.imgHghEdit, 1, 5)
        widgetLayout.addWidget(QtGui.QLabel('Render Layer:'), 2, 0)
        self.renderLayerEdit = QtGui.QLineEdit()
        self.renderLayerEdit.mousePressEvent = self.openPopupRender
        self.renderLayerEdit.setToolTip('Enter comma seperated cameras')
        widgetLayout.addWidget(self.renderLayerEdit, 2, 1)
        widgetLayout.addWidget(QtGui.QLabel('Camera:'), 2, 2)
        self.cameraEdit = QtGui.QLineEdit()
        self.cameraEdit.setToolTip('Enter comma seperated cameras')
        self.cameraEdit.mousePressEvent = self.openPopupCamera
        widgetLayout.addWidget(self.cameraEdit, 2, 3)
        self.vRayCheckbox = QtGui.QCheckBox()
        self.vRayCheckbox.setText('VRay Restart')
        widgetLayout.addWidget(self.vRayCheckbox, 2, 4)
        self.vRayCheckbox.setChecked(True)
        widgetLayout.addWidget(QtGui.QLabel('VRscene Filename:'), 3, 0)
        self.vrsceneLineEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.vrsceneLineEdit, 3, 1)
        self.renderCheckbox = QtGui.QCheckBox()
        self.renderCheckbox.setText('No Render')
        self.renderCheckbox.setChecked(True)
        self.renderCheckbox.stateChanged.connect(self.renderStateChanged)
        widgetLayout.addWidget(self.renderCheckbox, 3, 2)
        self.separateCheckbox = QtGui.QCheckBox()
        self.separateCheckbox.setText('Separate')
        widgetLayout.addWidget(self.separateCheckbox, 3, 3)
        self.compressedCheckbox = QtGui.QCheckBox()
        self.compressedCheckbox.setText('Compressed')
        widgetLayout.addWidget(self.compressedCheckbox, 3, 4)
        widgetLayout.addWidget(QtGui.QLabel('Output File'), 4, 0)
        self.outfileEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.outfileEdit, 4, 1)
        widgetLayout.addWidget(QtGui.QLabel('Output Dir'), 4, 2)
        self.outdirEdit = QtGui.QLineEdit()
        self.outdirEdit.setReadOnly(True)
        self.outdirEdit.setDisabled(True)
        self.outfileEdit.setDisabled(True)
        widgetLayout.addWidget(self.outdirEdit, 4, 3)
        dirBrowseButton = QtGui.QToolButton()
        dirBrowseButton.setText('...')
        dirBrowseButton.clicked.connect(lambda: self.openDirBrowser(self.outdirEdit))
        widgetLayout.addWidget(dirBrowseButton, 4, 4)
        self.ftrackCheckbox = QtGui.QCheckBox()
        self.ftrackCheckbox.setText('Ftrack Upload')
        widgetLayout.addWidget(self.ftrackCheckbox, 4, 5)
        self.ftrackCheckbox.setDisabled(True)
        projLayout = QtGui.QHBoxLayout()
        projLayout.addWidget(QtGui.QLabel('Project Dir'))
        self.projdirEdit = QtGui.QLineEdit()
        self.projdirEdit.setReadOnly(True)
        projLayout.addWidget(self.projdirEdit)
        projBrowseButton = QtGui.QToolButton()
        projBrowseButton.setText('...')
        projBrowseButton.clicked.connect(lambda: self.openDirBrowser(self.projdirEdit))
        projLayout.addWidget(projBrowseButton)
        self.layout().addLayout(projLayout)

    def openFileBrowser(self):
        dialog = QtGui.QFileDialog()
        filename, fileType = dialog.getOpenFileName(self, "Select File",
                                                    os.path.dirname(self.fileTextBox.text()),
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        self.fileTextBox.setText(str(filename))

    def openDirBrowser(self, lineEdit):
        dialog = QtGui.QFileDialog()
        dir = dialog.getExistingDirectory(self, "Select Directory",
                                          os.path.dirname(self.fileTextBox.text()),
                                          options=QtGui.QFileDialog.DontUseNativeDialog)
        lineEdit.setText(str(dir))

    def renderStateChanged(self):
        if self.renderCheckbox.isChecked():
            self.outdirEdit.setDisabled(True)
            self.outfileEdit.setDisabled(True)
            self.ftrackCheckbox.setDisabled(True)
        else:
            self.outdirEdit.setDisabled(False)
            self.outfileEdit.setDisabled(False)
            self.ftrackCheckbox.setDisabled(False)

    def setProjectDirectory(self):
        filename = self.fileTextBox.text()
        projDir = os.path.dirname(filename)
        self.projdirEdit.setText(projDir)

    def getRenderParams(self):
        rendererParams = ''
        filename = self.fileTextBox.text()
        fname, fext = os.path.splitext(filename)
        if filename is '' or fext not in ['.mb', '.ma']:
            return '', rendererParams
        rendererParams = '%s -frames %s' % (rendererParams, self.getFrameRange())
        rendererParams = '%s -imgfmt %s' % (rendererParams, str(self.imgFormatBox.currentText()))
        if str(self.imgWidEdit.text()) is not '':
            rendererParams = '%s -width %s' % (rendererParams, str(self.imgWidEdit.text()))
        if str(self.imgHghEdit.text()) is not '':
            rendererParams = '%s -height %s' % (rendererParams, str(self.imgHghEdit.text()))
        if str(self.renderLayerEdit.text()) is not '':
            rendererParams = '%s -rl "%s"' % (rendererParams, str(self.renderLayerEdit.text()))
        if str(self.cameraEdit.text()) is not '':
            rendererParams = '%s -camera "%s"' % (rendererParams, str(self.cameraEdit.text()))
        if str(self.outfileEdit.text()) is not '':
            rendererParams = '%s -outfile "%s"' % (rendererParams, str(self.outfileEdit.text()))
        if str(self.outdirEdit.text()) is not '':
            rendererParams = '%s -outdir "%s"' % (rendererParams, str(self.outdirEdit.text()))
        if str(self.vrsceneLineEdit.text()) is not '':
            rendererParams = '%s -filename "%s"' % (rendererParams, str(self.vrsceneLineEdit.text()))
        if self.renderCheckbox.isChecked():
            rendererParams = '%s -norender' % (rendererParams)
        if self.separateCheckbox.isChecked():
            rendererParams = '%s -separate' % (rendererParams)
        if self.compressedCheckbox.isChecked():
            rendererParams = '%s -compressed' % (rendererParams)
        if self.vRayCheckbox.isChecked():
            prerender = 'source vrayPreRender.mel;vrayRestart()'
            rendererParams = "%s -prerender '%s'" % (rendererParams, prerender)
        rendererParams = '%s -projdir "%s"' % (rendererParams, str(self.projdirEdit.text()))
        return filename, rendererParams

    def getFrameRange(self):
        if str(self.frameRangeEdit.text()) is not '':
            frameRange = str(self.frameRangeEdit.text())
        else:
            minFrame = int(cmds.playbackOptions(q=True, minTime=True))
            maxFrame = int(cmds.playbackOptions(q=True, maxTime=True))
            frameRange = '%s-%s' % (minFrame, maxFrame)
        return frameRange

    def getUploadCheck(self):
        if self.ftrackCheckbox.isEnabled():
            uploadCheck = self.ftrackCheckbox.isChecked()
        else:
            uploadCheck = False
        return uploadCheck

    def openPopupRender(self, event):
        popup = PopupWidget('render')
        popup.itemsSelected.connect(self.populateRenderLineEdit)
        popup.exec_()

    def openPopupCamera(self, event):
        popup = PopupWidget('camera')
        popup.itemsSelected.connect(self.populateCameraLineEdit)
        popup.exec_()

    def populateRenderLineEdit(self, selection):
        self.renderLayerEdit.setText(selection)

    def populateCameraLineEdit(self, selection):
        self.cameraEdit.setText(selection)


class PopupWidget(QtGui.QDialog):
    itemsSelected = Signal(str)

    def __init__(self, itemType):
        super(PopupWidget, self).__init__()
        self.setLayout(QtGui.QVBoxLayout())
        self.listWidget = QtGui.QListWidget()
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setWindowTitle('Select')
        self.layout().addWidget(self.listWidget)
        self.populateWidget(itemType)
        button = QtGui.QPushButton('Select')
        self.layout().addWidget(button)
        button.clicked.connect(self.buttonClicked)

    def populateWidget(self, itemType):
        itemList = []
        if itemType == 'render':
            itemList = cmds.ls(type='renderLayer')
        elif itemType == 'camera':
            itemList = cmds.listCameras()
        self.listWidget.addItems(itemList)

    def buttonClicked(self):
        selectedItems = []
        for item in self.listWidget.selectedItems():
            selectedItems.append(str(item.text()))
        selection = ','.join(selectedItems)
        self.itemsSelected.emit(selection)
        self.close()