import sys
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from style import pyqt_style_rc


class MediaBrowser(QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

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
        exitAction = QtGui.QAction('Exit', self)
        exitAction.triggered.connect(QtGui.qApp.quit)
        exitMenu.addAction(exitAction)

        centralWidget = QtGui.QWidget()
        centralLayout = QtGui.QHBoxLayout()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)

        sideTab = QtGui.QTabWidget()
        listWidget = QtGui.QListWidget()
        folders = ['fire', 'explosion', 'smoke']
        listWidget.addItems(folders)
        listWidget.itemDoubleClicked.connect(self.addBrowserTabs)
        sideTab.addTab(listWidget, 'Category')
        centralLayout.addWidget(sideTab)
        sideTab.setFixedWidth(200)

        self.browserTabs = QtGui.QTabWidget()
        self.browserTabs.setTabsClosable(True)
        self.browserTabs.tabCloseRequested.connect(self.removeBrowserTabs)
        centralLayout.addWidget(self.browserTabs)

    def addBrowserTabs(self, category):
        tableWidget = QtGui.QTableWidget()
        self.browserTabs.addTab(tableWidget, category.text())

    def removeBrowserTabs(self, index):
        self.browserTabs.removeTab(index)


def main():

    app = QtGui.QApplication(sys.argv)
    main = MediaBrowser()
    main.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()