import os
import PySide.QtGui as QtGui
import maya.cmds as cmds


class VRayStandaloneWidget(QtGui.QWidget):
    def __init__(self, dataDict):
        super(VRayStandaloneWidget, self).__init__()
        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        fileLayout = QtGui.QHBoxLayout()
        fileLayout.addWidget(QtGui.QLabel('Vray Filename:'))
        self.fileTextBox = QtGui.QLineEdit()
        self.fileTextBox.setText('')
        if 'filename' in dataDict.keys():
            self.fileTextBox.setText(dataDict['filename'])
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
        if 'frames' in dataDict.keys():
            self.frameRangeEdit.setText(dataDict['frames'])
        widgetLayout.addWidget(self.frameRangeEdit, 0, 1)
        widgetLayout.addWidget(QtGui.QLabel('Frame Step:'), 0, 2)
        self.frameStepEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.frameStepEdit, 0, 3)
        widgetLayout.addWidget(QtGui.QLabel('Image Width:'), 1, 0)
        self.imgWidEdit = QtGui.QLineEdit()
        if 'width' in dataDict.keys():
            self.imgWidEdit.setText(dataDict['width'])
        widgetLayout.addWidget(self.imgWidEdit, 1, 1)
        widgetLayout.addWidget(QtGui.QLabel('Image Height:'), 1, 2)
        self.imgHghEdit = QtGui.QLineEdit()
        if 'height' in dataDict.keys():
            self.imgHghEdit.setText(dataDict['height'])
        widgetLayout.addWidget(self.imgHghEdit, 1, 3)
        widgetLayout.addWidget(QtGui.QLabel('Verbosity Level:'), 2, 0)
        self.verbosityBox = QtGui.QComboBox()
        if 'verbose' in dataDict.keys():
            self.verbosityBox.setCurrentIndex(dataDict['verbose'])
        widgetLayout.addWidget(self.verbosityBox, 2, 1)
        self.populateVerbosityBox()
        self.verbosityBox.setCurrentIndex(4)
        widgetLayout.addWidget(QtGui.QLabel('Output File'), 3, 0)
        self.outfileEdit = QtGui.QLineEdit()
        if 'outfile' in dataDict.keys():
            self.outfileEdit.setText(dataDict['outfile'])
        widgetLayout.addWidget(self.outfileEdit, 3, 1)
        widgetLayout.addWidget(QtGui.QLabel('Output Dir'), 4, 0)
        self.outdirEdit = QtGui.QLineEdit()
        if 'outdir' in dataDict.keys():
            self.outdirEdit.setText(dataDict['outdir'])
        widgetLayout.addWidget(self.outdirEdit, 4, 1)
        dirBrowseButton = QtGui.QToolButton()
        dirBrowseButton.setText('...')
        dirBrowseButton.clicked.connect(self.openDirBrowser)
        widgetLayout.addWidget(dirBrowseButton, 4, 2)
        self.ftrackCheckbox = QtGui.QCheckBox()
        self.ftrackCheckbox.setText('Ftrack Upload')
        if 'ftrack' in dataDict.keys():
            self.ftrackCheckbox.setChecked(True)
        widgetLayout.addWidget(self.ftrackCheckbox, 4, 3)

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
        dataDict = {}
        filename = self.fileTextBox.text()
        fname, fext = os.path.splitext(filename)
        if filename is '' or fext not in ['.vrscene']:
            return '', rendererParams
        dataDict['filename'] = str(filename)
        frameRange = self.getFrameRange()
        dataDict['frames'] = frameRange
        rendererParams = '%s -frames %s' % (rendererParams, frameRange)
        if str(self.frameStepEdit.text()) is not '':
            rendererParams = '%s -fstep %s' % (rendererParams, str(self.frameStepEdit.text()))
            dataDict['fstep'] = str(self.frameStepEdit.text())
        if str(self.imgWidEdit.text()) is not '':
            rendererParams = '%s -width %s' % (rendererParams, str(self.imgWidEdit.text()))
            dataDict['width'] = str(self.imgWidEdit.text())
        if str(self.imgHghEdit.text()) is not '':
            rendererParams = '%s -height %s' % (rendererParams, str(self.imgHghEdit.text()))
            dataDict['height'] = str(self.imgHghEdit.text())
        rendererParams = '%s -verbose %s' % (rendererParams, str(self.verbosityBox.currentIndex()))
        dataDict['verbose'] = int(self.verbosityBox.currentIndex())
        if str(self.outfileEdit.text()) is not '':
            rendererParams = '%s -outfile "%s"' % (rendererParams, str(self.outfileEdit.text()))
            dataDict['outfile'] = str(self.outfileEdit.text())
        if str(self.outdirEdit.text()) is not '':
            rendererParams = '%s -outdir "%s"' % (rendererParams, str(self.outdirEdit.text()))
            dataDict['outdir'] = str(self.outdirEdit.text())
        if self.ftrackCheckbox.isChecked():
            dataDict['ftrack'] = 'true'
        return filename, rendererParams, dataDict

    def getUploadCheck(self):
        uploadCheck = self.ftrackCheckbox.isChecked()
        return uploadCheck


    def getFrameRange(self):
        if str(self.frameRangeEdit.text()) is not '':
            frameRange = str(self.frameRangeEdit.text())
        else:
            minFrame = int(cmds.playbackOptions(q=True, minTime=True))
            maxFrame = int(cmds.playbackOptions(q=True, maxTime=True))
            frameRange = '%s-%s' % (minFrame, maxFrame)
        return frameRange
