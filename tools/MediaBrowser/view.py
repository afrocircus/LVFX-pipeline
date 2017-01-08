import PySide.QtGui as QtGui
import PySide.QtCore as QtCore


class TableView(QtGui.QTableView):
    """
    A table containing the media widgets
    """
    def __init__(self, styleSheet, parent=None):
        QtGui.QTableView.__init__(self, parent)

        self.__stylesheet = styleSheet
        self.adjustSize()
        self.setShowGrid(False)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def keyPressEvent(self, event):
        # Overriding the default key press event
        super(TableView, self).keyPressEvent(event)
        # Copy to clipboard when Ctrl+C pressed
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        else:
            event.ignore()

    def copy(self):
        # copy filepath of the source media to clipboard.
        # Allows multiple selection
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        fileList = []
        for index in indexes:
            fileList.append(index.model().data(index, QtCore.Qt.ItemDataRole))
        filename = '\n'.join(fileList)
        clipboard = QtGui.QApplication.clipboard()
        clipboard.setText(filename)

    def on_context_menu(self, point):
        # Right click context menu to copy file paths.
        menu = QtGui.QMenu()
        menu.setStyleSheet(self.__stylesheet)
        copyAction = menu.addAction('Copy Path')
        action = menu.exec_(self.mapToGlobal(point))
        if action == copyAction:
            self.copy()