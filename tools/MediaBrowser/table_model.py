import PySide.QtCore as QtCore


class BrowserTableModel(QtCore.QAbstractTableModel):
    """ Data Model for table view. """

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


class CategoryListModel(QtCore.QAbstractListModel):
    """ Data Model for list view. """

    dataSet = QtCore.Signal(str, str)

    def __init__(self, listData=[], parent=None):

        QtCore.QAbstractListModel.__init__(self, parent)
        self.__listdata = listData

    def rowCount(self, parent):
        return len(self.__listdata)

    def data(self, index, role):
        # Each list item stores the name of the folder and database ID
        if role == QtCore.Qt.ItemDataRole:
            row = index.row()
            value, id = self.__listdata[row]
            return value, id

        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            value, id = self.__listdata[row]
            return value

        if role == QtCore.Qt.EditRole:
            row = index.row()
            return self.__listdata[row][0]

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            oldValue, id = self.data(index, QtCore.Qt.ItemDataRole)
            self.__listdata[row] = (value, id)
            self.dataSet.emit(value, str(id))
            return True
        return False

    def insertRows(self, position, rows, valueList, parent = QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + rows - 1)

        for i in range(rows):
            self.__listdata.append(valueList[i])

        self.endInsertRows()

        return True

    def clearRows(self, position, rows, parent = QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        self.__listdata = []
        self.endRemoveRows()
        return True
