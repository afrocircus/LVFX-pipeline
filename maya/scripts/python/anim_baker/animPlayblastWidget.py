import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore

from animPlayblast import AnimPlayblast


class AnimPlayblastUI(QtGui.QWidget):
    def __init__(self):
        super(AnimPlayblastUI, self).__init__()
        self.animPlayblast = AnimPlayblast()
        self.animPlayblast.showHUD()
        self.animPlayblast.moviePlayFail.connect(self.showMoviePlayFailDialog)
        self.animPlayblast.movieUploadFail.connect(self.showUploadFailDialog)
        self.animPlayblast.movieUploadUpdate.connect(self.updateProgressBar)

        self.setLayout(QtGui.QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        hudLayout = QtGui.QHBoxLayout()
        hudFrame = QtGui.QFrame()
        hudFrame.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        #hudFrame.setFixedHeight(50)
        hudFrame.setLayout(hudLayout)
        showHudButton = QtGui.QPushButton('Show HUD')
        showHudButton.clicked.connect(self.animPlayblast.showHUD)
        hideHudButton = QtGui.QPushButton('Hide HUD')
        hideHudButton.clicked.connect(self.animPlayblast.hideHUD)
        hudLayout.addWidget(showHudButton)
        hudLayout.addWidget(hideHudButton)
        self.layout().addWidget(hudFrame)

        playblastLayout = QtGui.QVBoxLayout()
        playblastFrame = QtGui.QFrame()
        playblastFrame.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        #playblastFrame.setFixedHeight(100)
        playblastFrame.setLayout(playblastLayout)
        sliderLayout = QtGui.QGridLayout()
        qualitySlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        qualitySlider.setRange(0,100)
        qualitySlider.setValue(70)
        qualityTxtBox = QtGui.QLineEdit('70')
        qualityTxtBox.setFixedWidth(40)
        qualitySlider.valueChanged.connect(lambda: self.setQtySliderValue(qualitySlider.value(),
                                                                               qualityTxtBox))
        sliderLayout.addWidget(QtGui.QLabel('Quality:'), 0, 0)
        sliderLayout.addWidget(qualityTxtBox, 0, 1)
        sliderLayout.addWidget(qualitySlider, 0, 2)
        scaleSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        scaleSlider.setRange(0, 100)
        scaleSlider.setSingleStep(1)
        scaleSlider.valueChanged.connect(lambda: self.setScaleSliderValue(scaleSlider.value(),
                                                                          scaleTxtBox))
        scaleTxtBox = QtGui.QLineEdit()
        scaleSlider.setValue(70)
        scaleTxtBox = QtGui.QLineEdit('0.70')
        scaleTxtBox.setFixedWidth(40)
        sliderLayout.addWidget(QtGui.QLabel('Scale:'), 1, 0)
        sliderLayout.addWidget(scaleTxtBox, 1, 1)
        sliderLayout.addWidget(scaleSlider, 1, 2)
        playblastButton = QtGui.QPushButton('Playblast')
        playblastButton.clicked.connect(lambda: self.animPlayblast.playBlast(int(qualityTxtBox.text()),
                                                                             float(scaleTxtBox.text())))
        playblastLayout.addLayout(sliderLayout)
        playblastLayout.addWidget(playblastButton)
        self.layout().addWidget(playblastFrame)

        playFrame = QtGui.QFrame()
        playFrame.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        #playFrame.setFixedHeight(50)
        playLayout = QtGui.QHBoxLayout()
        playFrame.setLayout(playLayout)
        playCurrentButton = QtGui.QPushButton('Play Current Version')
        playCurrentButton.clicked.connect(self.playCurrentMovie)
        playSelectedButton = QtGui.QPushButton('Play Selected Version')
        playSelectedButton.clicked.connect(self.playSelectedMovie)
        playLayout.addWidget(playCurrentButton)
        playLayout.addWidget(playSelectedButton)
        self.layout().addWidget(playFrame)

        uploadFrame = QtGui.QFrame()
        uploadFrame.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Plain)
        #uploadFrame.setFixedHeight(50)
        uploadLayout = QtGui.QHBoxLayout()
        uploadFrame.setLayout(uploadLayout)
        uploadCurrentButton = QtGui.QPushButton('Upload Current Version')
        uploadCurrentButton.clicked.connect(self.uploadToDailies)
        uploadSelectedButton = QtGui.QPushButton('Upload Selected Version')
        uploadSelectedButton.clicked.connect(self.uploadSelectedToDailies)
        uploadLayout.addWidget(uploadCurrentButton)
        uploadLayout.addWidget(uploadSelectedButton)
        progressLayout = QtGui.QHBoxLayout()
        self.progressLabel = QtGui.QLabel('')
        progressLayout.addWidget(self.progressLabel)
        self.progressBar = QtGui.QProgressBar()
        progressLayout.addWidget(self.progressBar)
        self.layout().addWidget(uploadFrame)
        self.layout().addLayout(progressLayout)
        self.setProgressBar(False)

    def setProgressBar(self, visible):
        self.progressLabel.setText('')
        self.progressLabel.setVisible(visible)
        self.progressBar.reset()
        self.progressBar.setVisible(visible)

    def setQtySliderValue(self, value, txtBox):
        txtBox.setText(str(value))

    def setScaleSliderValue(self, value, txtBox):
        scaledValue = float(value)/100
        txtBox.setText(str(scaledValue))

    def playCurrentMovie(self):
        filename = self.animPlayblast.getCurrentVersion()
        self.animPlayblast.playMovie(filename)

    def playSelectedMovie(self):
        dialog = QtGui.QFileDialog()
        filename, fileType = dialog.getOpenFileName(self, "Select File",
                                                    os.path.dirname(self.animPlayblast.getCurrentMayaFile()),
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        self.animPlayblast.playMovie(str(filename))

    def showMoviePlayFailDialog(self):
        QtGui.QMessageBox.critical(self, 'Movie Player Error', "Could not play movie!")

    def uploadToDailies(self):
        self.setProgressBar(True)
        filename = self.animPlayblast.getCurrentVersion()
        mayaFile = self.animPlayblast.getCurrentMayaFile()
        self.animPlayblast.uploadToFtrack(filename, mayaFile)

    def uploadSelectedToDailies(self):
        self.setProgressBar(True)
        dialog = QtGui.QFileDialog()
        filename, fileType = dialog.getOpenFileName(self, "Select File",
                                                    os.path.dirname(self.animPlayblast.getCurrentMayaFile()),
                                                    options=QtGui.QFileDialog.DontUseNativeDialog)
        mayaFile = self.animPlayblast.getCurrentMayaFile()
        self.animPlayblast.uploadToFtrack(filename, mayaFile)

    def showUploadFailDialog(self, error):
        QtGui.QMessageBox.critical(self, 'Upload Error', error)
        self.setProgressBar(False)

    def updateProgressBar(self, value, text):
        self.progressBar.setValue(value)
        self.progressLabel.setText(text)
