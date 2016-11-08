import PySide.QtCore as QtCore


class BrowserTableModel(QtCore.QAbstractTableModel):

    def __init__(self, videos=[[]], parent=None):

        QtCore.QAbstractTableModel.__init__(self, parent)
        self.__videos = videos

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__videos)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.__videos[0])

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if role == QtCore.Qt.ItemDataRole:
            row = index.row()
            column = index.column()
            try:
                value = self.__videos[row][column]
            except:
                value = ''
            return value

        elif role == QtCore.Qt.DisplayRole:
            return ''
