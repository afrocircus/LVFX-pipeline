import os
import json
import PySide.QtGui as QtGui
from PySide.QtCore import Signal
from Utils.submit import hqueue_submit

if 'SHOT_SUBMIT_CONFIG' in os.environ.keys():
    configFile = os.environ['SHOT_SUBMIT_CONFIG']
else:
    configFile = '/data/production/pipeline/linux/common/config/shot_submit_config.json'
jd = open(configFile).read()
config = json.loads(jd)


class HQueueWidget(QtGui.QWidget):

    rendererChanged = Signal(int)

    def __init__(self, renderer):
        super(HQueueWidget, self).__init__()
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
        jobBoxLayout.addWidget(QtGui.QLabel('Progressive Step:'), 0, 2)
        self.progLineEdit = QtGui.QLineEdit()
        self.progLineEdit.setValidator(QtGui.QIntValidator())
        self.progLineEdit.setText('0')
        jobBoxLayout.addWidget(self.progLineEdit, 0, 3)
        jobBoxLayout.addWidget(QtGui.QLabel('Priority:'), 1, 0)
        self.priorityBox = QtGui.QSpinBox()
        self.priorityBox.setMinimum(1)
        self.priorityBox.setMaximum(10)
        self.priorityBox.setValue(5)
        self.priorityBox.setMaximumWidth(50)
        jobBoxLayout.addWidget(self.priorityBox, 1, 1)
        jobBoxLayout.addWidget(QtGui.QLabel('Dependent On:'), 1, 2)
        self.dependJobLineEdit = QtGui.QLineEdit()
        jobBoxLayout.addWidget(self.dependJobLineEdit, 1, 3)
        self.dependJobLineEdit.setText('')
        jobBoxLayout.addWidget(QtGui.QLabel('Frame Split Mode:'), 2, 0)
        self.splitmodeDrop = QtGui.QComboBox()
        self.setSplitModeDrop()
        self.splitmodeDrop.activated[int].connect(self.splitModeSelected)
        jobBoxLayout.addWidget(self.splitmodeDrop, 2, 1)
        jobBoxLayout.addWidget(QtGui.QLabel('Chunk Size:'), 2, 2)
        self.countBox = QtGui.QSpinBox()
        self.countBox.setValue(0)
        self.countBox.setEnabled(False)
        self.progLineEdit.setEnabled(False)
        jobBoxLayout.addWidget(self.countBox, 2, 3)
        jobBoxLayout.addWidget(QtGui.QLabel('Client Pool:'), 3, 0)
        self.poolDrop = QtGui.QComboBox()
        self.setPoolsDrop()
        jobBoxLayout.addWidget(self.poolDrop, 3, 1)
        jobBoxLayout.addWidget(QtGui.QLabel('Slack User:'), 3, 2)
        self.userEdit = QtGui.QLineEdit()
        self.userEdit.setText('#render-updates')
        jobBoxLayout.addWidget(self.userEdit, 3, 3)

    def emitRendererChangedSignal(self):
        rendererIndex = int(self.rendererBox.currentIndex())
        if rendererIndex == 0:
            self.splitmodeDrop.setCurrentIndex(0)
            self.countBox.setValue(0)
            self.countBox.setEnabled(False)
            self.progLineEdit.setEnabled(False)
        else:
            self.splitmodeDrop.setCurrentIndex(1)
            self.countBox.setValue(5)
            self.countBox.setEnabled(True)
            self.progLineEdit.setEnabled(True)
        self.rendererChanged.emit(rendererIndex)


    def setRendererDrop(self, renderer):
        options = config['Renderers'][renderer]
        for option in options:
            self.rendererBox.addItem(option)

    def setPoolsDrop(self):
        options = config['Pools']
        for option in options:
            self.poolDrop.addItem(option)

    def setSplitModeDrop(self):
        self.splitmodeDrop.addItem('No Splitting')
        self.splitmodeDrop.addItem('Split into X frames per chunk')
        self.splitmodeDrop.setCurrentIndex(0)

    def splitModeSelected(self, index):
        if index == 0:
            self.countBox.setValue(0)
            self.countBox.setEnabled(False)
        else:
            self.countBox.setEnabled(True)
            self.countBox.setValue(5)

    def getRenderer(self, type):
        renderer = str(self.rendererBox.currentText())
        renderPath = config['Renderers'][type][renderer]
        return renderPath

    def getClientPools(self):
        return str(self.poolDrop.currentText())

    def getSplitMode(self):
        count = int(self.countBox.text())
        return count

    def getDependentJob(self):
        return str(self.dependJobLineEdit.text())

    def getSlackUser(self):
        user = str(self.userEdit.text())
        if not user.startswith('@') and not user == '#render-updates':
            user = '@' + user
        return user

    def getPriority(self):
        return int(self.priorityBox.value())

    def getHQProxy(self):
        hq_server = hqueue_submit.getHQServerProxy(config['hq_host'], config['hq_port'])
        return hq_server

    def getProgressiveStep(self):
        return int(self.progLineEdit.text())

    def submitNoChunk(self, hq_server, jobname, cmd, priority, tries, group, vrayRestart,
                      slackUser, dependent):
        jobIds = hqueue_submit.submitNoChunk(hq_server, jobname, cmd, priority, tries, group,
                                             vrayRestart, config['python_path'], config['slack_bot_token'],
                                             slackUser, dependent)
        return jobIds

    def submitVRStandalone(self, hq_server, jobname, filename, imgFile, vrCmd, startFrame,
                           endFrame, step, chunk, multiple, group, priority, review,
                           slackUser, dependent, prog):
        jobsIds = hqueue_submit.submitVRayStandalone(hq_server, jobname, filename, imgFile, vrCmd,
                                                     startFrame, endFrame, step, chunk, multiple,
                                                     group, priority, review, config['python_path'],
                                                     config['slack_bot_token'], slackUser,
                                                     dependent, prog)
        return jobsIds
