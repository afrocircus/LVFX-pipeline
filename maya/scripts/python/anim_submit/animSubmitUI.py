import PySide.QtGui as QtGui
import maya.cmds as cmds
import maya.mel as mm

from animPlayblastWidget import AnimPlayblastUI


class AnimSubmitUI(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName('AnimSubmitUI')
        self.setLayout(QtGui.QVBoxLayout())
        playblastBox = QtGui.QGroupBox('Playblast UI')
        playblastBoxLayout = QtGui.QVBoxLayout()
        playblastBox.setLayout(playblastBoxLayout)
        self.layout().addWidget(playblastBox)
        animPlayblastUI = AnimPlayblastUI()
        playblastBoxLayout.addWidget(animPlayblastUI)
        self.layout().addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding))

    def createDockLayout(self):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        columnLay = cmds.paneLayout(parent=gMainWindow, width=500)
        dockControl = cmds.dockControl(l='AnimSubmitUI', allowedArea='all',
                                       area='right', content=columnLay, width=500)
        cmds.control(str(self.objectName()),e=True,p=columnLay)

'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = AnimSubmitUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''
