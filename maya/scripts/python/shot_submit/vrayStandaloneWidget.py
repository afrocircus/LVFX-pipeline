import os
import PySide.QtGui as QtGui


class VRayStandaloneWidget(QtGui.QWidget):
    def __init__(self):
        super(VRayStandaloneWidget, self).__init__()
        self.setLayout(QtGui.QGridLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(QtGui.QLabel('Vray Filename:'), 0, 0)
        self.fileTextBox = QtGui.QLineEdit()
        self.fileTextBox.setReadOnly(True)
        self.fileTextBox.setText('')
        browseButton = QtGui.QToolButton()
        browseButton.setText('...')
        browseButton.clicked.connect(self.openFileBrowser)
        self.layout().addWidget(self.fileTextBox, 0, 1)
        self.layout().addWidget(browseButton, 0, 2)
        self.layout().addWidget(QtGui.QLabel('Frame List:'), 1, 0)
        self.frameRangeEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.frameRangeEdit, 1, 1)
        self.layout().addWidget(QtGui.QLabel('Frame Step:'), 1, 2)
        self.frameStepEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.frameStepEdit, 1, 3)
        self.layout().addWidget(QtGui.QLabel('Image Width:'), 2, 0)
        self.imgWidEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.imgWidEdit, 2, 1)
        self.layout().addWidget(QtGui.QLabel('Image Height:'), 2, 2)
        self.imgHghEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.imgHghEdit, 2, 3)
        self.layout().addWidget(QtGui.QLabel('Verbosity Level:'), 3, 0)
        self.verbosityBox = QtGui.QComboBox()
        self.layout().addWidget(self.verbosityBox, 3, 1)
        self.populateVerbosityBox()
        self.layout().addWidget(QtGui.QLabel('Output File'), 4, 0)
        self.outfileEdit = QtGui.QLineEdit()
        self.layout().addWidget(self.outfileEdit, 4, 1)
        self.layout().addWidget(QtGui.QLabel('Output Dir'), 5, 0)
        self.outdirEdit = QtGui.QLineEdit()
        self.outdirEdit.setReadOnly(True)
        self.layout().addWidget(self.outdirEdit, 5, 1)
        dirBrowseButton = QtGui.QToolButton()
        dirBrowseButton.setText('...')
        dirBrowseButton.clicked.connect(self.openDirBrowser)
        self.layout().addWidget(dirBrowseButton, 5, 2)

    def populateVerbosityBox(self):
        self.verbosityBox.addItem('0: No information')
        self.verbosityBox.addItem('1: Errors only')
        self.verbosityBox.addItem('2: Errors and warnings')
        self.verbosityBox.addItem('3: Errors, warnings and info')
        self.verbosityBox.addItem('4: All')

    def openFileBrowser(self):
        dialog = QtGui.QFileDialog()
        filename, fileType = dialog.getOpenFileName(self, "Select File",
                                                    os.path.dirname(self.fileTextBox.text()),
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        self.fileTextBox.setText(str(filename))

    def openDirBrowser(self):
        dialog = QtGui.QFileDialog()
        dir = dialog.getExistingDirectory(self, "Select Directory",
                                          os.path.dirname(self.fileTextBox.text()),
                                          options=QtGui.QFileDialog.DontUseNativeDialog)
        self.outdirEdit.setText(str(dir))

    def getRenderParams(self):
        rendererParams = ''
        filename = self.fileTextBox.text()
        fname, fext = os.path.splitext(filename)
        if filename is '' or not os.path.exists(filename) or fext not in ['.vrscene']:
            return '', rendererParams
        if str(self.frameRangeEdit.text()) is not '':
            rendererParams = '%s -frames %s' % (rendererParams, str(self.frameRangeEdit.text()))
        if str(self.frameStepEdit.text()) is not '':
            rendererParams = '%s -fstep %s' % (rendererParams, str(self.frameStepEdit.text()))
        if str(self.imgWidEdit.text()) is not '':
            rendererParams = '%s -width %s' % (rendererParams, str(self.imgWidEdit.text()))
        if str(self.imgHghEdit.text()) is not '':
            rendererParams = '%s -height %s' % (rendererParams, str(self.imgHghEdit.text()))
        rendererParams = '%s -verbose %s' % (rendererParams, str(self.verbosityBox.currentIndex()))
        if str(self.outfileEdit.text()) is not '':
            rendererParams = '%s -outfile "%s"' % (rendererParams, str(self.outfileEdit.text()))
        if str(self.outdirEdit.text()) is not '':
            rendererParams = '%s -outdir "%s"' % (rendererParams, str(self.outdirEdit.text()))
        return filename, rendererParams
