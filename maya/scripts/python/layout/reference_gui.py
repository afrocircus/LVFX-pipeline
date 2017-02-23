import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from Utils import ftrack_utils2
import maya.cmds as cmds


class ReferenceGUI(QtGui.QWidget):

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Reference UI')
        self.setLayout(QtGui.QVBoxLayout())
        self.buildUI()

    def buildUI(self):
        envRefBtn = QtGui.QPushButton('Reference Env')
        envRefList = QtGui.QListWidget()
        self.layout().addWidget(envRefBtn)
        self.layout().addWidget(envRefList)

        envRefBtn.clicked.connect(lambda arg1=envRefList, arg2='env': self.showAssetGui(arg1, arg2))
        horizontalLine = QtGui.QFrame()
        horizontalLine.setFrameStyle(QtGui.QFrame.HLine)
        horizontalLine.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.layout().addWidget(horizontalLine)

        charRefBtn = QtGui.QPushButton('Reference Char')
        charRefList = QtGui.QListWidget()
        self.layout().addWidget(charRefBtn)
        self.layout().addWidget(charRefList)
        charRefBtn.clicked.connect(lambda arg1=charRefList, arg2='char': self.showAssetGui(arg1, arg2))
        horizontalLine = QtGui.QFrame()
        horizontalLine.setFrameStyle(QtGui.QFrame.HLine)
        horizontalLine.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.layout().addWidget(horizontalLine)

        self.refresh(envRefList, charRefList)
        refreshBtn = QtGui.QPushButton('Refresh GUI')
        self.layout().addWidget(refreshBtn)
        refreshBtn.clicked.connect(lambda arg1=envRefList, arg2=charRefList:
                                   self.refresh(arg1, arg2))

    def showAssetGui(self, listWidget, namespace):
        assetGui = AssetSelector(self, namespace)
        assetGui.assetAdd.connect(lambda arg1, arg2, arg3=listWidget: self.addToList(arg1, arg2, arg3))
        assetGui.show()

    def refresh(self, envListWidget, charListWidget):
        envListWidget.clear()
        charListWidget.clear()

        references = cmds.ls(references=True)
        for ref in references:
            filename = cmds.referenceQuery(ref, filename=True).split('{')[0]
            if 'char_' in ref:
                self.createListItem(charListWidget, filename)
            elif 'env_' in ref:
                self.createListItem(envListWidget, filename)

    def addToList(self, refName, refPath, listWidget):
        self.createListItem(listWidget, refPath)
        cmds.file(refPath, r=True, namespace=refName)

    def createListItem(self, listWidget, filename):
        listItem = QtGui.QListWidgetItem(listWidget)
        label = MyLabel()
        label.setText(filename)
        listWidget.setItemWidget(listItem, label)


class AssetSelector(QtGui.QDialog):

    assetAdd = QtCore.Signal(str, str)

    def __init__(self, parent=None, namespace=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('Select an Asset')
        self.setLayout(QtGui.QVBoxLayout())
        self.buildUI(namespace)

    def buildUI(self, namespace):
        refLayout = QtGui.QGridLayout()
        refLayout.addWidget(QtGui.QLabel('Name:'), 0, 0)
        self.refNameEdit = QtGui.QLineEdit()
        refLayout.addWidget(self.refNameEdit, 0, 1)
        self.layout().addLayout(refLayout)

        refLayout.addWidget(QtGui.QLabel('Path: '), 1, 0)
        self.refPathEdit = QtGui.QLineEdit()
        refLayout.addWidget(self.refPathEdit, 1, 1)

        refBrowseBtn = QtGui.QToolButton()
        refBrowseBtn.setText('...')
        refLayout.addWidget(refBrowseBtn, 1, 2)
        refBrowseBtn.clicked.connect(self.openFileDialog)

        assetList = QtGui.QListWidget()
        assetList.setSortingEnabled(True)
        assetList.itemClicked.connect(self.itemSelected)
        assetNames = self.populateAssets()
        for key in assetNames.keys():
            item = QtGui.QListWidgetItem()
            item.setText(key)
            item.setData(QtCore.Qt.UserRole, assetNames[key])
            assetList.addItem(item)
        self.layout().addWidget(assetList)

        acceptBtn = QtGui.QPushButton('OK')
        acceptBtn.clicked.connect(lambda : self.acceptAsset(namespace))
        self.layout().addWidget(acceptBtn)

    def populateAssets(self):
        session = ftrack_utils2.startANewSession()
        if 'FTRACK_TASKID' in os.environ:
            taskid = os.environ['FTRACK_TASKID']
        else:
            taskid = ''
        if taskid == '':
            return {}
        task = session.query('Task where id is %s' % taskid).one()
        # all modeling tasks
        tasks = session.query('Task where project.name is %s and name is modeling' %
                              task['project']['name']).all()
        publishedTasks = [task for task in tasks if 'publish_model' in task['metadata']]
        assetNameDict = {}
        for publishTask in publishedTasks:
            assetNameDict[publishTask['parent']['name']] = publishTask['metadata']['publish_model']
        return assetNameDict

    def itemSelected(self, item):
        self.refNameEdit.setText(str(item.text()).replace(' ', '_'))
        self.refPathEdit.setText(item.data(QtCore.Qt.UserRole))

    def openFileDialog(self):
        filename, fileType = QtGui.QFileDialog.getOpenFileName(self, "Select Reference File",
                                                               '', "*.mb *.ma",
                                                               options=QtGui.QFileDialog.DontUseNativeDialog)
        if filename:
            self.refPathEdit.setText(filename)

    def acceptAsset(self, namespace):
        refText = str(self.refNameEdit.text())
        if refText == '':
            QtGui.QMessageBox.warning(self, 'Warning', 'Please name the reference!')
        else:
            refName = '%s_%s' % (namespace, refText)
            refPath = str(self.refPathEdit.text())
            self.assetAdd.emit(refName, refPath)
            self.close()


class MyLabel(QtGui.QLabel):

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), QtCore.Qt.ElideLeft, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)


def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = ReferenceGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
