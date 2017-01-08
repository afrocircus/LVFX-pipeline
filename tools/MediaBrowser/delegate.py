import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from widget import VideoWidget


class VideoDelegate(QtGui.QStyledItemDelegate):
    """ Delegate for video widget items """
    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def paint(self,  painter,  option,  index):
        # Selected cell displays orange.
        painter.save()
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        if option.state & QtGui.QStyle.State_Selected:
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 170, 0)))
        else:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.transparent))
        painter.drawRect(option.rect)
        painter.restore()

    def createEditor(self, parent, option, index):
        # Initialize video widget if the filename is valid
        filename = index.model().data(index, QtCore.Qt.ItemDataRole)
        if os.path.exists(filename):
            self.videoEditor = VideoWidget(parent)
        else:
            return None
        return self.videoEditor

    def setEditorData(self, editor, index):
        # Set media source if filepath is valid.
        editor.blockSignals(True)
        filename = index.model().data(index, QtCore.Qt.ItemDataRole)
        if os.path.exists(filename):
            self.videoEditor.setMediaSource(filename)
        editor.blockSignals(False)
