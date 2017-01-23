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
        self.multipleCheckBox = QtGui.QCheckBox()
        self.multipleCheckBox.setText('Multiple VRScene Files')
        if 'multiple' in dataDict.keys():
            self.multipleCheckBox.setChecked(dataDict['multiple'])
        else:
            self.multipleCheckBox.setChecked(False)
        self.layout().addWidget(self.multipleCheckBox)
        widgetLayout = QtGui.QHBoxLayout()
        self.layout().addLayout(widgetLayout)
        widgetLayout.addWidget(QtGui.QLabel('Start Frame:'))
        self.frameStartEdit = QtGui.QLineEdit()
        self.frameStartEdit.setText(str(int(cmds.playbackOptions(q=True, minTime=True))))
        widgetLayout.addWidget(self.frameStartEdit)
        widgetLayout.addWidget(QtGui.QLabel('End Frame:'))
        self.frameEndEdit = QtGui.QLineEdit()
        self.frameEndEdit.setText(str(int(cmds.playbackOptions(q=True, maxTime=True))))
        widgetLayout.addWidget(self.frameEndEdit)
        widgetLayout.addWidget(QtGui.QLabel('Frame Step:'))
        self.frameStepEdit = QtGui.QLineEdit()
        widgetLayout.addWidget(self.frameStepEdit)
        self.frameStepEdit.setText('1')
        outFileLayout = QtGui.QHBoxLayout()
        outFileLayout.addWidget(QtGui.QLabel('Output File'))
        self.outfileEdit = QtGui.QLineEdit()
        if 'outfile' in dataDict.keys():
            self.outfileEdit.setText(dataDict['outfile'])
        self.outfileEdit.textChanged.connect(self.constructLabel)
        outFileLayout.addWidget(self.outfileEdit)
        self.layout().addLayout(outFileLayout)
        outDirLayout = QtGui.QHBoxLayout()
        outDirLayout.addWidget(QtGui.QLabel('Output Dir'))
        self.outdirEdit = QtGui.QLineEdit()
        if 'outdir' in dataDict.keys():
            self.outdirEdit.setText(dataDict['outdir'])
        outDirLayout.addWidget(self.outdirEdit)
        self.outdirEdit.textChanged.connect(self.constructLabel)
        dirBrowseButton = QtGui.QToolButton()
        dirBrowseButton.setText('...')
        dirBrowseButton.clicked.connect(self.openDirBrowser)
        outDirLayout.addWidget(dirBrowseButton)
        self.layout().addLayout(outDirLayout)
        self.ftrackCheckbox = QtGui.QCheckBox()
        self.ftrackCheckbox.setText('Upload To Ftrack')
        if 'review' in dataDict.keys():
            self.ftrackCheckbox.setChecked(True)
        else:
            self.ftrackCheckbox.setChecked(False)
        self.layout().addWidget(self.ftrackCheckbox)
        self.outfileLabel = QtGui.QLabel()
        self.layout().addWidget(self.outfileLabel)
        self.constructLabel()

    def constructLabel(self):
        outDir = self.outdirEdit.text()
        outFile = self.outfileEdit.text()
        filename = os.path.join(outDir, outFile)
        self.outfileLabel.setText(filename)

    def openFileBrowser(self):
        dialog = QtGui.QFileDialog()
        filename = self.fileTextBox.text()
        if filename == '':
            filename = cmds.file(q=True, sn=True)
        fileDir = os.path.join(os.path.dirname(filename), 'vrscene')
        filename, fileType = dialog.getOpenFileName(self, "Select File",
                                                    fileDir,
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        self.fileTextBox.setText(str(filename))

    def openDirBrowser(self):
        dialog = QtGui.QFileDialog()
        filename = self.fileTextBox.text()
        if filename == '':
            filename = cmds.file(q=True, sn=True)
        shotDir = filename.split('scene')[0]
        imgDir = os.path.join(shotDir, 'img', 'renders')
        dir = dialog.getExistingDirectory(self, "Select Directory",
                                          imgDir,
                                          options=QtGui.QFileDialog.DontUseNativeDialog)
        self.outdirEdit.setText(str(dir))

    def getRenderParams(self):
        rendererParams = '-display=0 -interactive=0 -verboseLevel=3'
        paramDict = {}
        filename = self.fileTextBox.text()
        fname, fext = os.path.splitext(filename)
        if fext not in ['.vrscene']:
            filename = ''
        paramDict['filename'] = str(filename)
        paramDict['imgFile'] = os.path.join(self.outdirEdit.text(), self.outfileEdit.text())
        paramDict['outfile'] = self.outfileEdit.text()
        paramDict['outdir'] = self.outdirEdit.text()
        rendererParams += ' -imgFile="%s"' % paramDict['imgFile']
        paramDict['startFrame'] = int(self.frameStartEdit.text())
        paramDict['endFrame'] = int(self.frameEndEdit.text())
        paramDict['step'] = int(self.frameStepEdit.text())
        if self.multipleCheckBox.isChecked():
            paramDict['multiple'] = True
        else:
            paramDict['multiple'] = False
        '''if self.ftrackCheckbox.isChecked():
            paramDict['review'] = True
        else:
            paramDict['review'] = False'''
        paramDict['review'] = False
        return paramDict, rendererParams

    def getUploadCheck(self):
        uploadCheck = self.ftrackCheckbox.isChecked()
        return uploadCheck

    def setFilename(self, filename):
        self.fileTextBox.setText(filename)
