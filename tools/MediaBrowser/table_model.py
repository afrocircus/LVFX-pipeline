import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from PySide.phonon import Phonon


class BrowserTableModel(QtCore.QAbstractTableModel):

    def __init__(self, videos=[[]], parent=None):

        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__videos = videos

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__videos)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.__videos[0])

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if role == QtCore.Qt.ItemDataRole:
            row = index.row()
            column = index.column()
            value = self.__videos[row][column]
            return value

        elif role == QtCore.Qt.DisplayRole:
            return ''


class VideoEditor(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        self.setMouseTracking(True)
        self.setAutoFillBackground(True)
        self.setup(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def setup(self, parent):
        self.media = Phonon.MediaObject(parent)
        videoWidget = Phonon.VideoWidget(parent)
        Phonon.createPath(self.media, videoWidget)
        self.layout().addWidget(videoWidget)
        self.media.finished.connect(self.mediaFinished)

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

    def mousePressEvent(self, event):
        if self.media.state() == Phonon.State.PlayingState:
            self.media.pause()
        else:
            self.media.play()

    def on_context_menu(self, point):
        menu = QtGui.QMenu()
        copyAction = menu.addAction('Copy Path')
        action = menu.exec_(self.mapToGlobal(point))
        if action == copyAction:
            mediaFile = self.media.currentSource().fileName()
            clipboard = QtGui.QApplication.clipboard()
            clipboard.setText(mediaFile)


class VideoWidget(QtGui.QItemDelegate):

    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        self.videoEditor = VideoEditor(parent)
        return self.videoEditor

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        self.videoEditor.setMediaSource(index.model().data(index, QtCore.Qt.ItemDataRole))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentIndex())
