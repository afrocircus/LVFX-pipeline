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


class LibWidget(QtGui.QDialog):

    closeSig = QtCore.Signal()

    def __init__(self, parent=None, db=None):
        QtGui.QDialog.__init__(self, parent)
        self.parent = parent
        self.db = db
        self.initUI()

    def initUI(self):
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
        name = str(self.nameLineEdit.text())
        tags = str(self.tagLineEdit.text())
        folder = str(self.folderLineEdit.text())
        self.recurseAndValidateFolders(folder, name, tags)
        self.close()

    def recurseAndValidateFolders(self, root, rootName, rootTags):
        mediaExt = ('mov', 'mp4', 'flv', 'jpg', 'jpeg', 'bmp', 'png', 'gif', 'tiff')
        for rootFolder, subFolder, files in os.walk(root):
            mediaFiles = [f for f in files if f.endswith(mediaExt)]
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
        if self.db.Media.find({'refDir':folder}).count() == 0:
            insert(self.db, folder, name, tags)
        else:
            update(self.db, name, tags, folder)

    def closeEvent(self, event):
        self.closeSig.emit()


class MediaBrowser(QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.db = getDatabase()
        self.media = read(self.db)
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

        menubar = QtGui.QMenuBar(self)
        self.setMenuBar(menubar)
        exitMenu = menubar.addMenu('File')
        addToLibAction = QtGui.QAction('Add/Update Library', self)
        addToLibAction.triggered.connect(LibWidget(self, self.db).show)
        exitMenu.addAction(addToLibAction)
        reloadLibAction = QtGui.QAction('Reload Library', self)
        reloadLibAction.triggered.connect(lambda: read(self.db))
        exitMenu.addAction(reloadLibAction)
        exitAction = QtGui.QAction('Exit', self)
        exitAction.triggered.connect(QtGui.qApp.quit)
        exitMenu.addAction(exitAction)

        centralWidget = QtGui.QWidget()
        centralLayout = QtGui.QHBoxLayout()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)

        sideTab = QtGui.QTabWidget()
        folders = []
        for each in self.media:
            folders.append((each['name'], each['_id']))
        listView = ListView(self.stylesheet)
        listModel = CategoryListModel(folders)
        listModel.dataSet.connect(self.updateDb)
        listView.setModel(listModel)
        listView.doubleClick.connect(self.addBrowserTabs)
        listView.contextMenu.connect(self.openUpdateWidget)
        sideTab.addTab(listView, 'Category')
        sideTab.setFocusPolicy(QtCore.Qt.NoFocus)
        centralLayout.addWidget(sideTab)
        sideTab.setFixedWidth(200)

        self.browserTabs = QtGui.QTabWidget()
        self.browserTabs.setFixedWidth(610)
        self.browserTabs.setTabsClosable(True)
        self.browserTabs.tabCloseRequested.connect(self.removeBrowserTabs)
        centralLayout.addWidget(self.browserTabs)

    '''def updateBrowser(self, index, category):
        print index, category
        model = index.model()
        model.setData(index, category, QtCore.Qt.EditRole)
        self.media = read(self.db)'''

    def updateDb(self, value, id):
        results = find(self.db, '_id', ObjectId(id))
        if results:
            update(self.db, value, results[0]['tags'], results[0]['refDir'])

    def openUpdateWidget(self, index):
        category, id = index.model().data(index, QtCore.Qt.ItemDataRole)
        results = find(self.db, '_id', ObjectId(id))
        if results:
            libWidget = LibWidget(self, self.db)
            libWidget.folderLineEdit.setText(results[0]['refDir'])
            libWidget.nameLineEdit.setText(category)
            libWidget.tagLineEdit.setText(results[0]['tags'])
            #libWidget.closeSig.connect(lambda: self.updateBrowser(index, category))
            libWidget.show()

    def addBrowserTabs(self, category, id):
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
        mediaExt = ('mov', 'mp4', 'flv', 'jpg', 'jpeg', 'bmp', 'png', 'gif', 'tiff')
        refFiles = [os.path.join(refFolder, f) for f in os.listdir(refFolder)
                    if os.path.isfile(os.path.join(refFolder, f)) and f.endswith(mediaExt)]
        colSize = 3
        videoList = [refFiles[i:i+colSize] for i in xrange(0, len(refFiles), colSize)]
        return videoList


def main():
    app = QtGui.QApplication(sys.argv)
    main = MediaBrowser()
    main.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
