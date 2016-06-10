import os
import nuke
import PySide.QtGui as QtGui
from Utils.submit.submit import *
from Widgets.submit.jobWidget import JobWidget


class ShotSubmitUI(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setLayout(QtGui.QVBoxLayout())
        renderBox = QtGui.QGroupBox('Render Set')
        renderBoxLayout = QtGui.QGridLayout()
        renderBox.setLayout(renderBoxLayout)
        self.layout().addWidget(renderBox)
        renderBoxLayout.addWidget(QtGui.QLabel('Filename:'), 0, 0)
        self.fileTextBox = QtGui.QLineEdit()
        self.fileTextBox.setReadOnly(True)
        try:
            filename = nuke.scriptName()
        except RuntimeError:
            filename = ''
        self.fileTextBox.setText(filename)
        browseButton = QtGui.QToolButton()
        browseButton.setText('...')
        browseButton.clicked.connect(self.openFileBrowser)
        renderBoxLayout.addWidget(self.fileTextBox, 0, 1)
        renderBoxLayout.addWidget(browseButton, 0, 2)
        renderBoxLayout.addWidget(QtGui.QLabel('Frame Range:'), 1, 0)
        self.frameBox = QtGui.QLineEdit()
        renderBoxLayout.addWidget(self.frameBox, 1, 1)
        renderBoxLayout.addWidget(QtGui.QLabel('Frame Step:'), 2, 0)
        self.frameStepBox = QtGui.QLineEdit()
        renderBoxLayout.addWidget(self.frameStepBox, 2, 1)
        renderBoxLayout.addWidget(QtGui.QLabel('Write Node:'), 3, 0)
        self.writeNodeBox = QtGui.QComboBox()
        self.populateWriteNodes()
        renderBoxLayout.addWidget(self.writeNodeBox, 3, 1)
        self.jobWidget = JobWidget('Nuke')
        self.layout().addWidget(self.jobWidget)
        self.jobWidget.splitmodeDrop.setCurrentIndex(0)
        self.jobWidget.poolDrop.setCurrentIndex(1)
        hlayout = QtGui.QHBoxLayout()
        submitButton = QtGui.QPushButton('Submit')
        submitButton.clicked.connect(self.submitRender)
        hlayout.addWidget(submitButton)
        hlayout.addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum))
        self.layout().addLayout(hlayout)
        self.layout().addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

    def populateWriteNodes(self):
        writeNodes = nuke.allNodes('Write')
        for node in writeNodes:
            self.writeNodeBox.addItem(node.name())

    def openFileBrowser(self):
        dialog = QtGui.QFileDialog()
        filename, fileType = dialog.getOpenFileName(self, "Select File",
                                                    os.path.dirname(self.fileTextBox.text()),
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        self.fileTextBox.setText(str(filename))

    def getRendererParams(self):
        renderParams = ''
        if str(self.frameBox.text()) is not '':
            renderParams = '%s -frames %s' % (renderParams, str(self.frameBox.text()))
        else:
            renderParams = '%s -frames %s-%s' % (renderParams, nuke.tcl('frames first'), nuke.tcl('frames last'))
        if str(self.frameStepBox.text()) is not '':
            renderParams = '%s -fstep %s' % (renderParams, str(self.frameStepBox.text()))
        renderParams = '%s -writenode %s' % (renderParams, str(self.writeNodeBox.currentText()))
        return renderParams

    def submitRender(self):
        filename = str(self.fileTextBox.text())
        if filename is '' or not os.path.exists(filename):
            nuke.message('Please select a valid file to render!')
            return
        fileDir, fname = os.path.split(filename)
        jobName = 'Nuke - %s' % fname
        renderer = self.jobWidget.getRenderer()
        splitMode = self.jobWidget.getSplitMode()
        pool = self.jobWidget.getClientPools()
        rendererParams = self.getRendererParams()
        result = submitRender(jobName, renderer, pool, splitMode, rendererParams, filename)
        nuke.message(result)
