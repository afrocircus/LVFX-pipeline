"""
Media browser tool.
:author: Natasha Kelkar
:description: Lets the user build a library of reference media, playback media files
and allows copying media file paths to applications like Nuke.
"""

import sys
import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore

from bson import ObjectId
from table_model import BrowserTableModel
from table_model import CategoryListModel
from delegate import VideoDelegate
from view import TableView
from view import ListView
from db_manager import *
from style import pyqt_style_rc


MEDIA_EXT = ('mov', 'mp4', 'flv', 'jpg', 'jpeg', 'bmp', 'png', 'gif', 'tiff')


class MediaBrowser(QtGui.QMainWindow):
    """
    Main Browser window
    """

    def __init__(self, parent=None):
        """
        Intialize Widget. Connect to database.
        """
        QtGui.QMainWindow.__init__(self, parent)
        self.db = getDatabase()
        self.addToLibWidget = LibWidget(self, self.db)
        self.setGeometry(100, 100, 800, 800)
        self.setWindowTitle('Media Browser')
        self.setWindowStyle()
        self.setupUI()

    def setWindowStyle(self):
        f = QtCore.QFile('style/style.qss')
        f.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
        ts = QtCore.QTextStream(f)
        self.stylesheet = ts.readAll()
        self.setStyleSheet(self.stylesheet)

    def setupUI(self):
        """
        Setting up the UI
        """
        menubar = QtGui.QMenuBar(self)
        self.setMenuBar(menubar)
        exitMenu = menubar.addMenu('File')
        addToLibAction = QtGui.QAction('Add/Update Library', self)
        addToLibAction.triggered.connect(self.addToLibWidget.show)
        self.addToLibWidget.libUpdate.connect(self.updateListModel)
        exitMenu.addAction(addToLibAction)
        reloadLibAction = QtGui.QAction('Reload Library', self)
        reloadLibAction.triggered.connect(self.updateListModel)
        exitMenu.addAction(reloadLibAction)
        exitAction = QtGui.QAction('Exit', self)
        exitAction.triggered.connect(QtGui.qApp.quit)
        exitMenu.addAction(exitAction)

        centralWidget = QtGui.QWidget()
        centralLayout = QtGui.QHBoxLayout()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)

        sideTab = QtGui.QTabWidget()

        listView = ListView(self.stylesheet)
        folders = self.readFromDatabase()
        self.listModel = CategoryListModel(folders)
        self.listModel.dataSet.connect(self.updateDb)
        listView.setModel(self.listModel)
        listView.doubleClick.connect(self.addBrowserTabs)
        sideTab.addTab(listView, 'Category')
        sideTab.setFocusPolicy(QtCore.Qt.NoFocus)
        centralLayout.addWidget(sideTab)
        sideTab.setFixedWidth(200)

        self.browserTabs = QtGui.QTabWidget()
        self.browserTabs.setFixedWidth(610)
        self.browserTabs.setTabsClosable(True)
        self.browserTabs.tabCloseRequested.connect(self.removeBrowserTabs)
        centralLayout.addWidget(self.browserTabs)

    def readFromDatabase(self):
        """
        Read from database
        :return: List of tuples (folder_name, object_id)
        """
        self.media = read(self.db)
        folders = []
        for each in self.media:
            folders.append((each['name'], each['_id']))
        folders.sort()
        return folders

    def removeAllRows(self):
        """
        Clear the list widget
        """
        rows = self.listModel.rowCount(self)
        self.listModel.clearRows(0, rows)

    def updateListModel(self):
        """
        Update the list widget by first clearing and then re-inserting rows.
        """
        self.removeAllRows()
        folders = self.readFromDatabase()
        self.listModel.insertRows(0, len(folders), folders)

    def updateDb(self, value, id):
        """
        Update database
        :param value: Name of the folder
        :param id: Object ID
        """
        results = find(self.db, '_id', ObjectId(id))
        if results:
            update(self.db, value, results[0]['tags'], results[0]['refDir'])

    def addBrowserTabs(self, category, id):
        """
        Called when a list item is double clicked.
        Opens a tab and loads table widget with media.
        :param category: Name of the list item
        :param id: Database Object ID
        """
        tableView = TableView(self.stylesheet)
        results = find(self.db, '_id', ObjectId(id))
        if results:
            refFolder = results[0]['refDir']
            videos = self.createVideoList(refFolder)
            model = BrowserTableModel(videos)
            tableView.setModel(model)

            for row in range(0, model.rowCount()):
                tableView.setRowHeight(row, 200)
                for col in range(0, model.columnCount()):
                    tableView.setItemDelegate(VideoDelegate(self))
                    tableView.openPersistentEditor(model.index(row, col))
                    tableView.setColumnWidth(col, 200)

            self.browserTabs.addTab(tableView, category)

    def removeBrowserTabs(self, index):
        self.browserTabs.removeTab(index)

    def createVideoList(self, refFolder):
        """
        Create a list of all media files in the selected folder
        :param refFolder: Media Reference folder.
        :return: List of media paths.
        """
        refFiles = [os.path.join(refFolder, f) for f in os.listdir(refFolder)
                    if os.path.isfile(os.path.join(refFolder, f)) and f.endswith(MEDIA_EXT)]
        colSize = 3
        videoList = [refFiles[i:i+colSize] for i in xrange(0, len(refFiles), colSize)]
        return videoList


class LibWidget(QtGui.QDialog):
    """
    Add/Update media widget
    """

    libUpdate = QtCore.Signal()

    def __init__(self, parent=None, db=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.db = db
        self.initUI()

    def initUI(self):
        """
        Build the UI
        """
        layout = QtGui.QGridLayout()
        self.setLayout(layout)
        self.setWindowTitle("Add to Library")

        folderBtn = QtGui.QPushButton()
        folderBtn.setText('Choose Folder:')
        folderBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        folderBtn.clicked.connect(self.getFolder)
        layout.addWidget(folderBtn, 0, 0)
        self.folderLineEdit = QtGui.QLineEdit()
        layout.addWidget(self.folderLineEdit, 0, 1)
        self.folderLineEdit.setReadOnly(True)
        nameLabel = QtGui.QLabel('Name:')
        nameLabel.setAlignment(QtCore.Qt.AlignRight)
        layout.addWidget(nameLabel, 1, 0)
        self.nameLineEdit = QtGui.QLineEdit()
        layout.addWidget(self.nameLineEdit, 1, 1)
        tagLabel = QtGui.QLabel('Tags:')
        tagLabel.setAlignment(QtCore.Qt.AlignRight)
        layout.addWidget(tagLabel, 2, 0)
        self.tagLineEdit = QtGui.QLineEdit()
        layout.addWidget(self.tagLineEdit, 2, 1)
        self.tagLineEdit.setToolTip('Enter comma separated tags.')
        addBtn = QtGui.QPushButton()
        addBtn.setText('Add')
        addBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        layout.addWidget(addBtn, 3, 0)
        addBtn.clicked.connect(self.addToLibrary)

        hlayout = QtGui.QHBoxLayout()
        layout.addLayout(hlayout, 3, 1)
        cancelBtn = QtGui.QPushButton()
        cancelBtn.setText('Cancel')
        cancelBtn.setFixedWidth(100)
        hlayout.addWidget(cancelBtn)
        cancelBtn.setFocusPolicy(QtCore.Qt.NoFocus)
        hlayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        cancelBtn.clicked.connect(self.close)

    def getFolder(self):
        fileDialog = QtGui.QFileDialog()
        fileDialog.setFileMode(QtGui.QFileDialog.Directory)
        fileDialog.setOption(QtGui.QFileDialog.ShowDirsOnly)
        folder = fileDialog.getExistingDirectory(self, "Select Folder",
                                                 options= QtGui.QFileDialog.DontUseNativeDialog)
        name = os.path.split(folder)[-1]
        self.folderLineEdit.setText(str(folder))
        self.nameLineEdit.setText(name)

    def addToLibrary(self):
        """
        Add the chosen folder to the library
        """
        name = str(self.nameLineEdit.text())
        tags = str(self.tagLineEdit.text())
        folder = str(self.folderLineEdit.text())
        self.recurseAndValidateFolders(folder, name, tags)
        self.libUpdate.emit()
        self.close()

    def recurseAndValidateFolders(self, root, rootName, rootTags):
        """
        Recursively add/update folders to the database if the folder contains
         any media files.
        :param root: Folder Path
        :param rootName: Name of the folder
        :param rootTags: Tags associated with the media
        """
        for rootFolder, subFolder, files in os.walk(root):
            mediaFiles = [f for f in files if f.endswith(MEDIA_EXT)]
            rootFold = rootFolder + '/'
            depth = rootFold[len(root) + len(os.path.sep):].count(os.path.sep)
            if depth == 0:
                name = rootName
                tags = rootTags
            else:
                name = os.path.basename(rootFolder)
                tags = os.path.basename(rootFolder)
            if len(mediaFiles) > 0:
                self.checkIfEntryExits(rootFolder, name, tags)

    def checkIfEntryExits(self, folder, name, tags):
        # if entry exists, update the entry else insert a new entry
        if self.db.Media.find({'refDir': folder}).count() == 0:
            insert(self.db, folder, name, tags)
        else:
            update(self.db, name, tags, folder)


def main():
    app = QtGui.QApplication(sys.argv)
    main = MediaBrowser()
    main.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
