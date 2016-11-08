import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from widget import VideoWidget


class VideoDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def paint(self,  painter,  option,  index):
        painter.save()
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        if option.state & QtGui.QStyle.State_Selected:
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 170, 0)))
        else:
            painter.setBrush(QtGui.QBrush(QtCore.Qt.transparent))
        painter.drawRect(option.rect)
        painter.restore()

    def createEditor(self, parent, option, index):
        filename = index.model().data(index, QtCore.Qt.ItemDataRole)
        if os.path.exists(filename):
            self.videoEditor = VideoWidget(parent)
        else:
            return ''
        return self.videoEditor

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        filename = index.model().data(index, QtCore.Qt.ItemDataRole)
        if os.path.exists(filename):
            self.videoEditor.setMediaSource(filename)
        editor.blockSignals(False)
