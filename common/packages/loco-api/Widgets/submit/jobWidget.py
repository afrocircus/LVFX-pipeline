import os
import json
import PySide.QtGui as QtGui
from PySide.QtCore import Signal


class JobWidget(QtGui.QWidget):

    rendererChanged = Signal(int)

    def __init__(self, renderer):
        super(JobWidget, self).__init__()
        self.setLayout(QtGui.QVBoxLayout())
        jobBox = QtGui.QGroupBox('Job Set')
        jobBoxLayout = QtGui.QGridLayout()
        jobBox.setLayout(jobBoxLayout)
        self.layout().addWidget(jobBox)
        self.layout().setContentsMargins(0, 0, 0, 0)
        jobBoxLayout.addWidget(QtGui.QLabel('Renderer:'), 0, 0)
        self.rendererBox = QtGui.QComboBox()
        self.setRendererDrop(renderer)
        self.rendererBox.currentIndexChanged.connect(self.emitRendererChangedSignal)
        jobBoxLayout.addWidget(self.rendererBox, 0, 1)
        jobBoxLayout.addWidget(QtGui.QLabel('Priority:'), 1, 0)
        self.priorityBox = QtGui.QSpinBox()
        self.priorityBox.setMinimum(1)
        self.priorityBox.setMaximum(10)
        self.priorityBox.setValue(5)
        self.priorityBox.setMaximumWidth(50)
        jobBoxLayout.addWidget(self.priorityBox, 1, 1)
        jobBoxLayout.addWidget(QtGui.QLabel('Dependent Job:'), 1, 2)
        self.dependJobLineEdit = QtGui.QLineEdit()
        jobBoxLayout.addWidget(self.dependJobLineEdit, 1, 3)
        self.dependJobLineEdit.setText('')
        jobBoxLayout.addWidget(QtGui.QLabel('Frame Split Mode:'), 2, 0)
        self.splitmodeDrop = QtGui.QComboBox()
        self.setSplitModeDrop()
        self.splitmodeDrop.activated[int].connect(self.splitModeSelected)
        jobBoxLayout.addWidget(self.splitmodeDrop, 2, 1)
        hlayout = QtGui.QHBoxLayout()
        hlayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        hlayout.addWidget(QtGui.QLabel('Count:'))
        jobBoxLayout.addLayout(hlayout, 2, 2)
        self.countBox = QtGui.QSpinBox()
        self.countBox.setValue(5)
        jobBoxLayout.addWidget(self.countBox, 2, 3)
        self.countLabel = QtGui.QLabel('frames/chunk')
        jobBoxLayout.addWidget(self.countLabel, 2, 4)
        jobBoxLayout.addWidget(QtGui.QLabel('Client Pool:'), 3, 0)
        self.poolDrop = QtGui.QComboBox()
        self.setPoolsDrop()
        jobBoxLayout.addWidget(self.poolDrop, 3, 1)

    def emitRendererChangedSignal(self):
        self.rendererChanged.emit(int(self.rendererBox.currentIndex()))

    def setRendererDrop(self, renderer):
        if os.path.exists(os.environ['SHOT_SUBMIT_CONFIG']):
            jd = open(os.environ['SHOT_SUBMIT_CONFIG']).read()
            data = json.loads(jd)
            options = data['Renderers'][renderer]
            for option in options:
                self.rendererBox.addItem(option)

    def setPoolsDrop(self):
        if os.path.exists(os.environ['SHOT_SUBMIT_CONFIG']):
            jd = open(os.environ['SHOT_SUBMIT_CONFIG']).read()
            data = json.loads(jd)
            options = data['Pools']
            for option in options:
                self.poolDrop.addItem(option)

    def setSplitModeDrop(self):
        self.splitmodeDrop.addItem('No Splitting')
        self.splitmodeDrop.addItem('Split into X total pieces')
        self.splitmodeDrop.addItem('Split into X frames per chunk')
        self.splitmodeDrop.setCurrentIndex(2)

    def splitModeSelected(self, index):
        if index == 0:
            self.countLabel.setText('')
            self.countBox.setValue(0)
            self.countBox.setEnabled(False)
        elif index == 1:
            self.countBox.setEnabled(True)
            self.countBox.setValue(2)
            self.countLabel.setText('total pieces')
        else:
            self.countBox.setEnabled(True)
            self.countBox.setValue(5)
            self.countLabel.setText('frames/chunk')

    def getRenderer(self):
        return str(self.rendererBox.currentText())

    def getClientPools(self):
        return str(self.poolDrop.currentText())

    def getSplitMode(self):
        splitMode = str(self.splitmodeDrop.currentIndex())
        count = str(self.countBox.text())
        return '%s,%s' % (splitMode, count)

    def getDependentJob(self):
        return str(self.dependJobLineEdit.text())
