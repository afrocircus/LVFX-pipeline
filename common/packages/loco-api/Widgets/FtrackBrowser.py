__author__ = 'natasha'

import os
import PySide.QtGui as QtGui
import Utils.ftrack_utils as ftrack_utils

from PySide.QtCore import Qt
from PySide.QtCore import Signal


class BrowserDialog(QtGui.QDialog):

    winClosed = Signal(str)

    def __init__(self, taskPath, parent=None, session=None):
        QtGui.QDialog.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        self.taskPath = taskPath
        viewerBox = QtGui.QGroupBox('Ftrack')
        self.layout().addWidget(viewerBox)
        vLayout = QtGui.QVBoxLayout()
        viewerBox.setLayout(vLayout)

        projList = QtGui.QListWidget()
        self.createProjList(session, projList)
        projList.itemClicked.connect(lambda: self.projItemClicked(session, projList.currentItem()))
        self.taskList = QtGui.QListWidget()
        self.taskList.itemClicked.connect(lambda: self.taskItemClicked(session, self.taskList.currentItem()))
        hLayout1 = QtGui.QHBoxLayout()
        hLayout1.addWidget(projList)
        hLayout1.addWidget(self.taskList)
        vLayout.addLayout(hLayout1)
        self.pathEdit = QtGui.QLineEdit()
        vLayout.addWidget(self.pathEdit)

        self.setButton = QtGui.QPushButton('Set')
        self.setButton.setDisabled(True)
        cancelButton = QtGui.QPushButton('Cancel')
        self.setButton.clicked.connect(self.setTaskPath)
        cancelButton.clicked.connect(self.closeWindow)
        hLayout2 = QtGui.QHBoxLayout()
        hLayout2.addItem(QtGui.QSpacerItem(10,10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        hLayout2.addWidget(self.setButton)
        hLayout2.addWidget(cancelButton)
        vLayout.addLayout(hLayout2)
        self.projPath = ''
        if not self.taskPath == '':
            self.pathEdit.setText(self.taskPath)
            self.createTaskList(session, self.taskPath)
            if ftrack_utils.isTask(session, taskPath):
                self.setProjPath(session)

    def createProjList(self, session, projList):
        projects = ftrack_utils.getAllProjectNames(session)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("%s/PNG/home.png" % os.environ['ICONS_PATH']))
        for project in projects:
            item = QtGui.QListWidgetItem(icon, project)
            projList.addItem(item)

    def projItemClicked(self, session, item):
        self.projPath = ''
        self.pathEdit.setText(str(item.text()))
        self.createTaskList(session, str(item.text()))
        self.setButton.setDisabled(True)

    def isAllTasks(self):
        for type, name in self.childList:
            if not type == 'task':
                return False
        return True

    def setProjPath(self, session):
        if self.isAllTasks():
            self.setButton.setDisabled(False)
            if self.projPath == '':
                tmpPath = str(self.pathEdit.text())
                self.projPath = tmpPath.split(' / ')[0]
                for p in tmpPath.split(' / ')[1:-1]:
                    self.projPath = '%s / %s' % (self.projPath, p)
                self.createTaskList(session, self.projPath)

    def taskItemClicked(self, session, item):
        pathtext = str(self.pathEdit.text())
        projPath = '%s / %s' % (pathtext, str(item.text()))
        if self.isAllTasks():
            if self.projPath == '':
                self.projPath = str(self.pathEdit.text())
            projPath = '%s / %s' % (self.projPath, str(item.text()))
            self.setButton.setDisabled(False)
        self.pathEdit.setText(projPath)
        self.createTaskList(session, projPath)

    def createTaskList(self, session, projPath):
        self.childList = ftrack_utils.getAllChildren(session, projPath)
        if not len(self.childList) == 0:
            self.taskList.clear()
            for type, name in self.childList:
                if type == 'assetbuild':
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap("%s/PNG/box.png" % os.environ['ICONS_PATH']))
                    item = QtGui.QListWidgetItem(icon, name)
                elif type == 'task':
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap("%s/PNG/signup.png" % os.environ['ICONS_PATH']))
                    item = QtGui.QListWidgetItem(icon, name)
                elif type == 'sequence':
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap("%s/PNG/movie.png" % os.environ['ICONS_PATH']))
                    item = QtGui.QListWidgetItem(icon, name)
                elif type == 'folder':
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap("%s/PNG/folder-open.png" % os.environ['ICONS_PATH']))
                    item = QtGui.QListWidgetItem(icon, name)
                else:
                    item = QtGui.QListWidgetItem(name)
                self.taskList.addItem(item)

    def setTaskPath(self):
        self.winClosed.emit(self.getTaskPath())
        self.close()

    def getTaskPath(self):
        return str(self.pathEdit.text())

    def closeWindow(self):
        self.close()