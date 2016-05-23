import os
import PySide.QtGui as QtGui


class VRayMayaWidget(QtGui.QWidget):
    def __init__(self):
        super(VRayMayaWidget, self).__init__()
        self.setLayout(QtGui.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(QtGui.QLabel('Maya Filename:'), 0, 0)
        self.fileTextBox = QtGui.QLineEdit()
        self.fileTextBox.setReadOnly(True)
        self.fileTextBox.setText('')
        self.fileTextBox.textChanged.connect(self.setProjectDirectory)
        browseButton = QtGui.QToolButton()
        browseButton.setText('...')
        browseButton.clicked.connect(self.openFileBrowser)
        self.layout().addWidget(self.fileTextBox, 0, 1)
        self.layout().addWidget(browseButton, 0, 2)
        self.layout().addWidget(QtGui.QLabel('Frame List:'), 1, 0)
        self.frameRangeEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.frameRangeEdit, 1, 1)
        self.layout().addWidget(QtGui.QLabel('Frame Step'), 1, 2)
        self.frameStepEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.frameStepEdit, 1, 3)
        self.layout().addWidget(QtGui.QLabel('Image Format'), 2, 0)
        self.imgFormatBox = QtGui.QComboBox()
        self.imgFormatBox.addItems(['png', 'jpeg', 'vrimage', 'hdr', 'exr', 'bmp', 'tga', 'sgi'])
        self.layout().addWidget(self.imgFormatBox)
        self.layout().addWidget(QtGui.QLabel('Image Width:'), 2, 2)
        self.imgWidEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.imgWidEdit, 2, 3)
        self.layout().addWidget(QtGui.QLabel('Image Height:'), 2, 4)
        self.imgHghEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.imgHghEdit, 2, 5)
        self.layout().addWidget(QtGui.QLabel('Render Layer:'), 3, 0)
        self.renderLayerEdit = QtGui.QLineEdit()
        self.renderLayerEdit.setToolTip('Enter comma seperated render layers')
        self.layout().addWidget(self.renderLayerEdit, 3, 1)
        self.layout().addWidget(QtGui.QLabel('Camera:'), 3, 2)
        self.cameraEdit = QtGui.QLineEdit()
        self.cameraEdit.setToolTip('Enter comma seperated cameras')
        self.layout().addWidget(self.cameraEdit, 3, 3)
        self.layout().addWidget(QtGui.QLabel('Output File'), 4, 0)
        self.outfileEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.outfileEdit, 4, 1)
        self.layout().addWidget(QtGui.QLabel('Output Dir'), 4, 2)
        self.outdirEdit = QtGui.QLineEdit()
        self.outdirEdit.setReadOnly(True)
        self.layout().addWidget(self.outdirEdit, 4, 3)
        dirBrowseButton = QtGui.QToolButton()
        dirBrowseButton.setText('...')
        dirBrowseButton.clicked.connect(lambda: self.openDirBrowser(self.outdirEdit))
        self.layout().addWidget(dirBrowseButton, 4, 4)
        self.layout().addWidget(QtGui.QLabel('Project Dir'), 5, 0)
        self.projdirEdit = QtGui.QLineEdit()
        self.projdirEdit.setReadOnly(True)
        self.layout().addWidget(self.projdirEdit, 5, 1)
        projBrowseButton = QtGui.QToolButton()
        projBrowseButton.setText('...')
        projBrowseButton.clicked.connect(lambda: self.openDirBrowser(self.projdirEdit))
        self.layout().addWidget(projBrowseButton, 5, 2)


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

    def setProjectDirectory(self):
        filename = self.fileTextBox.text()
        projDir = os.path.dirname(filename)
        self.projdirEdit.setText(projDir)

    def getRenderParams(self):
        rendererParams = ''
        filename = self.fileTextBox.text()
        fname, fext = os.path.splitext(filename)
        if filename is '' or not os.path.exists(filename) or fext not in ['.mb', '.ma']:
            return '', rendererParams
        if str(self.frameRangeEdit.text()) is not '':
            rendererParams = '%s -frames %s' % (rendererParams, str(self.frameRangeEdit.text()))
        if str(self.frameStepEdit.text()) is not '':
            rendererParams = '%s -fstep %s' % (rendererParams, str(self.frameStepEdit.text()))
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
        rendererParams = '%s -projdir "%s"' % (rendererParams, str(self.projdirEdit.text()))
        return filename, rendererParams
