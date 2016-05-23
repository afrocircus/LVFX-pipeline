__author__ = 'natasha'

import os
import PySide.QtGui as QtGui
import threading
import Utils.ftrack_utils as ftrackUtils

from Widgets.FtrackBrowser import BrowserDialog
from PySide.QtCore import Qt
from PySide.QtCore import Signal


class MyLabel(QtGui.QLabel):
    def paintEvent( self, event ):
        painter = QtGui.QPainter(self)

        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), Qt.ElideMiddle, self.width())

        painter.drawText(self.rect(), self.alignment(), elided)


class MovieUploadWidget(QtGui.QWidget):

    uploadComplete = Signal(str)

    def __init__(self, parent=None, taskid=None, session=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QGridLayout())
        self.frameIn = 0
        self.frameOut = 150
        self.session = session
        frameBox = QtGui.QWidget()
        frameLayout = QtGui.QGridLayout()
        frameBox.setLayout(frameLayout)
        frameLayout.addWidget(QtGui.QLabel('Link To:'))
        taskid = taskid
        taskPath = ''
        if taskid:
            taskPath = ftrackUtils.getTaskPath(self.session, taskid)
        self.taskEdit = QtGui.QLineEdit(taskPath)
        self.taskEdit.setReadOnly(True)
        frameLayout.addWidget(self.taskEdit, 0, 1)
        self.taskEdit.textChanged.connect(self.updateAssetDrop)
        self.browseButton = QtGui.QPushButton('Browse')
        self.browseButton.clicked.connect(self.openBrowserDialog)
        frameLayout.addWidget(self.browseButton, 0, 2)

        frameLayout.addWidget(QtGui.QLabel('Assets:'), 1, 0)
        hlayout = QtGui.QHBoxLayout()
        self.assetDrop = QtGui.QComboBox()
        self.assetDrop.addItem('Select')
        self.assetDrop.addItem('new')
        self.assetDrop.setMinimumWidth(100)
        self.assetDrop.activated[str].connect(self.assetSelected)
        hlayout.addWidget(self.assetDrop)
        hlayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        frameLayout.addLayout(hlayout, 1, 1)

        frameLayout.addWidget(QtGui.QLabel('Asset Name:'), 2, 0)
        self.assetEdit = QtGui.QLineEdit()
        self.assetEdit.setDisabled(True)
        frameLayout.addWidget(self.assetEdit)

        vLayout = QtGui.QVBoxLayout()
        vLayout.addWidget(QtGui.QLabel('Comment'))
        vLayout.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))
        frameLayout.addLayout(vLayout, 3, 0)
        self.commentBox = QtGui.QTextEdit()
        frameLayout.addWidget(self.commentBox, 3, 1)

        frameLayout.addWidget(QtGui.QLabel('Status:'), 4, 0)
        hlayout1 = QtGui.QHBoxLayout()
        self.statusDrop = QtGui.QComboBox()
        self.statusDrop.setMinimumWidth(100)
        hlayout1.addWidget(self.statusDrop)
        hlayout1.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        frameLayout.addLayout(hlayout1, 4, 1)

        frameLayout.addWidget(QtGui.QLabel('Output Movie'), 5, 0)
        self.movieLabel = MyLabel()
        self.movieLabel.setMinimumWidth(100)
        self.movieLabel.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        frameLayout.addWidget(self.movieLabel)
        self.framerate = '24'

        self.uploadButton = QtGui.QPushButton('Upload')
        self.uploadButton.setDisabled(True)
        self.uploadButton.clicked.connect(self.uploadMovie)
        frameLayout.addWidget(self.uploadButton, 6, 0)
        self.layout().addWidget(frameBox)
        self.layout().addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding), 1, 0)
        if not taskPath == '':
            self.updateAssetDrop()

    def setFrameCount(self, framein, frameout):
        self.frameIn = framein
        self.frameOut = frameout

    def setFrameRate(self, framerate):
        self.framerate = framerate

    def setMoviePath(self, moviePath):
        self.movieLabel.setText(str(moviePath))

    def setPath(self, newPath):
        self.taskEdit.setText(newPath)

    def assetSelected(self, assetName):
        if assetName == 'Select':
            self.assetEdit.setDisabled(True)
            self.uploadButton.setEnabled(False)
        elif assetName == 'new' :
            self.assetEdit.setDisabled(False)
            self.assetEdit.textChanged.connect(self.enableUploadButton)
        else:
            self.assetEdit.setDisabled(True)
            self.enableUploadButton()

    def updateAssetDrop(self):
        newPath = str(self.taskEdit.text())
        self.assetDrop.clear()
        self.assetDrop.addItem('Select')
        self.assetDrop.addItem('new')
        self.assetEdit.setDisabled(False)
        assetList = ftrackUtils.getAllAssets(self.session, newPath)
        self.assetDrop.addItems(assetList)
        self.updateStatusDrop(newPath)

    def updateStatusDrop(self, projectPath):
        statusList = ftrackUtils.getStatusList(self.session, projectPath)
        self.statusDrop.clear()
        self.statusDrop.addItems(statusList)
        currentStatus = ftrackUtils.getCurrentStatus(self.session, projectPath)
        self.statusDrop.setCurrentIndex(statusList.index(currentStatus))

    def openBrowserDialog(self):
        taskpath = str(self.taskEdit.text())
        self.gui = BrowserDialog(taskpath, parent=self, session=self.session)
        self.gui.show()
        self.gui.winClosed.connect(self.setPath)

    def enableUploadButton(self):
        self.uploadButton.setEnabled(True)

    def uploadMovie(self):
        self.uploadButton.setDisabled(True)
        self.uploadButton.setText('Uploading ...')
        inputFile = str(self.movieLabel.text())
        outfilemp4 =  os.path.splitext(inputFile)[0] + '.mp4'
        outfilewebm = os.path.splitext(inputFile)[0] + '.webm'
        thumnbail = os.path.join(os.path.split(inputFile)[0], 'thumbnail.png')
        threading.Thread( None, self.newThreadUpload, args=[inputFile, outfilemp4, outfilewebm, thumnbail]).start()

    def newThreadUpload(self, inputFile, outfilemp4, outfilewebm, thumnbail):
        result = self.convertFiles(inputFile, outfilemp4, outfilewebm)
        comment = str(self.commentBox.toPlainText())
        if result:
            thumbresult = ftrackUtils.createThumbnail(outfilemp4, thumnbail)
            taskPath = str(self.taskEdit.text())
            assetName = str(self.assetDrop.currentText())
            if assetName == 'new':
                assetName = str(self.assetEdit.text())
            asset = ftrackUtils.getAsset(self.session, taskPath, assetName)
            version = ftrackUtils.createAndPublishVersion(self.session, taskPath, comment, asset,
                                                outfilemp4, outfilewebm, thumnbail,
                                                self.frameIn, self.frameOut, self.framerate)
            ftrackUtils.setTaskStatus(self.session, taskPath, version, str(self.statusDrop.currentText()))
        self.deleteFiles(outfilemp4, outfilewebm, thumnbail)

    def deleteFiles(self, outfilemp4, outfilewebm, thumbnail):
        if os.path.exists(outfilemp4):
            os.remove(outfilemp4)
        if os.path.exists(outfilewebm):
            os.remove(outfilewebm)
        if os.path.exists(thumbnail):
            os.remove(thumbnail)
        self.uploadButton.setEnabled(True)
        self.uploadButton.setText('Upload')
        self.uploadComplete.emit('Upload Complete!')

    def convertFiles(self, inputFile, outfilemp4, outfilewebm):
        mp4Result = ftrackUtils.convertMp4Files(inputFile, outfilemp4)
        webmResult = ftrackUtils.convertWebmFiles(inputFile, outfilewebm)

        if mp4Result == 0 and webmResult == 0:
            return True
        else:
            return False
