import os
import PySide.QtGui as QtGui


class VRayMayaWidget(QtGui.QWidget):
    def __init__(self):
        super(VRayMayaWidget, self).__init__()
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
        widgetLayout.addWidget(QtGui.QLabel('Frame Step'), 0, 2)
        self.frameStepEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.frameStepEdit, 0, 3)
        widgetLayout.addWidget(QtGui.QLabel('Image Format'), 1, 0)
        self.imgFormatBox = QtGui.QComboBox()
        self.imgFormatBox.addItems(['png', 'jpeg', 'vrimage', 'hdr', 'exr', 'bmp', 'tga', 'sgi'])
        widgetLayout.addWidget(self.imgFormatBox)
        widgetLayout.addWidget(QtGui.QLabel('Image Width:'), 1, 2)
        self.imgWidEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.imgWidEdit, 1, 3)
        widgetLayout.addWidget(QtGui.QLabel('Image Height:'), 1, 4)
        self.imgHghEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.imgHghEdit, 1, 5)
        widgetLayout.addWidget(QtGui.QLabel('Render Layer:'), 2, 0)
        self.renderLayerEdit = QtGui.QLineEdit()
        self.renderLayerEdit.setToolTip('Enter comma seperated render layers')
        widgetLayout.addWidget(self.renderLayerEdit, 2, 1)
        widgetLayout.addWidget(QtGui.QLabel('Camera:'), 2, 2)
        self.cameraEdit = QtGui.QLineEdit()
        self.cameraEdit.setToolTip('Enter comma seperated cameras')
        widgetLayout.addWidget(self.cameraEdit, 2, 3)
        widgetLayout.addWidget(QtGui.QLabel('Output File'), 3, 0)
        self.outfileEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.outfileEdit, 3, 1)
        widgetLayout.addWidget(QtGui.QLabel('Output Dir'), 3, 2)
        self.outdirEdit = QtGui.QLineEdit()
        self.outdirEdit.setReadOnly(True)
        widgetLayout.addWidget(self.outdirEdit, 3, 3)
        dirBrowseButton = QtGui.QToolButton()
        dirBrowseButton.setText('...')
        dirBrowseButton.clicked.connect(lambda: self.openDirBrowser(self.outdirEdit))
        widgetLayout.addWidget(dirBrowseButton, 3, 4)
        widgetLayout.addWidget(QtGui.QLabel('Project Dir'), 4, 0)
        self.projdirEdit = QtGui.QLineEdit()
        self.projdirEdit.setReadOnly(True)
        widgetLayout.addWidget(self.projdirEdit, 4, 1)
        projBrowseButton = QtGui.QToolButton()
        projBrowseButton.setText('...')
        projBrowseButton.clicked.connect(lambda: self.openDirBrowser(self.projdirEdit))
        widgetLayout.addWidget(projBrowseButton, 4, 2)


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
        if filename is '' or fext not in ['.mb', '.ma']:
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
