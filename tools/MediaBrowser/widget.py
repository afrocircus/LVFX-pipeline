import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore

from PySide.phonon import Phonon
from style import pyqt_style_rc


class VideoWidget(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)
        #self.setContentsMargins(10, 10, 10, 10)
        self.setup(parent)

    def setup(self, parent):
        self.media = Phonon.MediaObject(parent)
        videoWidget = Phonon.VideoWidget(parent)
        Phonon.createPath(self.media, videoWidget)
        self.layout().addWidget(videoWidget)
        self.playBtn = QtGui.QPushButton()
        self.playBtn.setText('Play/Pause')
        self.playBtn.clicked.connect(self.playPauseEvent)
        self.layout().addWidget(self.playBtn)
        #self.media.finished.connect(self.mediaFinished)

    def setMediaSource(self, path):
        self.media.setCurrentSource(path)
        filename = os.path.split(path)[1]
        fname = os.path.splitext(filename)[0]
        label = QtGui.QLabel(fname)
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout().addWidget(label)
        self.media.play()
        self.media.pause()

    def mediaFinished(self):
        self.media.play()
        self.media.pause()

    def mediaStateChanged(self, newstate, oldstate):
        if oldstate == Phonon.State.PlayingState:
            self.media.play()
            self.media.pause()

    def playPauseEvent(self):
        if self.media.state() == Phonon.State.PlayingState:
            self.media.pause()
        else:
            self.media.play()

    '''def mousePressEvent(self, event):
        if self.media.state() == Phonon.State.PlayingState:
            self.media.pause()
        else:
            self.media.play()'''
