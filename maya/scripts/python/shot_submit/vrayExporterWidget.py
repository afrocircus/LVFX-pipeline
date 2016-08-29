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
        self.fileTextBox.setText(cmds.file(q=True, sn=True))
        self.fileTextBox.textChanged.connect(self.setProjectDirectory)
        browseButton = QtGui.QToolButton()
        browseButton.setText('...')
        browseButton.clicked.connect(self.openFileBrowser)
        fileLayout.addWidget(self.fileTextBox)
        fileLayout.addWidget(browseButton)
        self.layout().addLayout(fileLayout)
        widgetLayout = QtGui.QGridLayout()
        self.layout().addLayout(widgetLayout)
        widgetLayout.addWidget(QtGui.QLabel('Start Frame:'), 0, 0)
        self.frameStartEdit = QtGui.QLineEdit()
        self.frameStartEdit.setText(str(cmds.playbackOptions(q=True, minTime=True)))
        widgetLayout.addWidget(self.frameStartEdit, 0, 1)
        widgetLayout.addWidget(QtGui.QLabel('End Frame:'), 0, 2)
        self.frameEndEdit = QtGui.QLineEdit()
        self.frameEndEdit.setText(str(cmds.playbackOptions(q=True, maxTime=True)))
        widgetLayout.addWidget(self.frameEndEdit, 0, 3)
        widgetLayout.addWidget(QtGui.QLabel('Step:'), 0, 4)
        self.frameStepEdit = QtGui.QLineEdit()
        self.frameStepEdit.setText(str(1.0))
        widgetLayout.addWidget(self.frameStepEdit, 0, 5)
        widgetLayout.addWidget(QtGui.QLabel('Render Layer:'), 1, 0)
        self.renderLayerEdit = QtGui.QLineEdit()
        self.renderLayerEdit.mousePressEvent = self.openPopupRender
        widgetLayout.addWidget(self.renderLayerEdit, 1, 1)
        widgetLayout.addWidget(QtGui.QLabel('Camera:'), 1, 2)
        self.cameraEdit = QtGui.QComboBox()
        self.cameraEdit.addItems(cmds.listCameras())
        widgetLayout.addWidget(self.cameraEdit, 1, 3)
        widgetLayout.addWidget(QtGui.QLabel('VRscene Filename:'), 2, 0)
        self.vrsceneLineEdit = QtGui.QLineEdit()
        filename = self.fileTextBox.text()
        if filename:
            vrsceneFile = os.path.splitext(os.path.split(filename)[-1])[0]
            self.vrsceneLineEdit.setText(vrsceneFile)
        widgetLayout.addWidget(self.vrsceneLineEdit, 2, 1)
        self.separateCheckbox = QtGui.QCheckBox()
        self.separateCheckbox.setText('Separate Frames')
        widgetLayout.addWidget(self.separateCheckbox, 2, 2)
        self.compressedCheckbox = QtGui.QCheckBox()
        self.compressedCheckbox.setText('Compressed')
        widgetLayout.addWidget(self.compressedCheckbox, 2, 3)
        projLayout = QtGui.QHBoxLayout()
        projLayout.addWidget(QtGui.QLabel('Project Dir'))
        self.projdirEdit = QtGui.QLineEdit()
        self.projdirEdit.setReadOnly(True)
        self.setProjectDirectory()
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
        if filename != '':
            self.fileTextBox.setText(str(filename))

    def openDirBrowser(self, lineEdit):
        dialog = QtGui.QFileDialog()
        dir = dialog.getExistingDirectory(self, "Select Directory",
                                          os.path.dirname(self.fileTextBox.text()),
                                          options=QtGui.QFileDialog.DontUseNativeDialog)
        if dir != '':
            lineEdit.setText(str(dir))

    def setProjectDirectory(self):
        filename = self.fileTextBox.text()
        if filename != '':
            projDir = os.path.join(os.path.dirname(filename), 'vrscene')
            self.projdirEdit.setText(projDir)

    def getRenderParams(self):
        rendererParams = '-r vray'
        filename = self.fileTextBox.text()
        fname, fext = os.path.splitext(filename)
        if filename is '' or fext not in ['.mb', '.ma']:
            return '', rendererParams
        projDir = self.projdirEdit.text()
        if projDir == '':
            projDir = os.path.dirname(filename)
        if not os.path.exists(projDir):
            os.makedirs(projDir)
        rendererParams += ' -proj "%s"' % projDir
        camera = self.cameraEdit.currentText()
        rendererParams += ' -cam %s' % camera
        if self.renderLayerEdit.text() != '':
            rendererParams += ' -rl %s' % str(self.renderLayerEdit.text())
        rendererParams += ' -exportFileName "%s"' % str(self.vrsceneLineEdit.text())
        rendererParams += ' -noRender'
        if self.compressedCheckbox.isChecked():
            rendererParams += ' -exportCompressed'
        if self.separateCheckbox.isChecked():
            rendererParams += ' -exportFramesSeparate'
        rendererParams += ' -s %s' % str(self.frameStartEdit.text())
        rendererParams += ' -e %s' % str(self.frameEndEdit.text())
        rendererParams += ' -b %s' % str(self.frameStepEdit.text())
        rendererParams += ' "%s"' % filename
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