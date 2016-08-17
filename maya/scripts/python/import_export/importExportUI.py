import os
import PySide.QtGui as QtGui
import maya.cmds as cmds
import maya.mel as mm

from Utils import ftrack_utils2
from exportWidget import ExportWidget
from importWidget import ImportWidget


class ImportExportUI(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setObjectName('ImportExportUI')
        self.setLayout(QtGui.QVBoxLayout())
        filename = cmds.file(q=True, sn=True)
        shot = shotAssetPath = session = None
        if filename:
            session = ftrack_utils2.startANewSession()
            shot = self.getShot(session, filename)
            shotAssetPath = self.getShotAssetDir(filename)
        self.exportWidget = ExportWidget(session, shotAssetPath, shot)
        self.importWidget = ImportWidget(shotAssetPath, shot)
        tabWidget = QtGui.QTabWidget()
        self.layout().addWidget(tabWidget)
        tabWidget.addTab(self.exportWidget, 'Export Options')
        tabWidget.addTab(self.importWidget, 'Import Options')
        self.layout().addItem(QtGui.QSpacerItem(10, 10, QtGui.QSizePolicy.Minimum,
                                                QtGui.QSizePolicy.Expanding))

    def getShotAssetDir(self, filename):
        shotPath = filename.split('scene')[0]
        shotAssetPath = os.path.join(shotPath, 'shotAssets')
        if not os.path.exists(shotAssetPath) and os.path.exists(shotPath):
            os.makedirs(shotAssetPath)
        return shotAssetPath

    def getShot(self, session, filename):
        taskid = None
        if 'FTRACK_TASKID' in os.environ:
            taskid = os.environ['FTRACK_TASKID']
        task = ftrack_utils2.getTask(session, taskid, filename)
        return task['parent']

    def createDockLayout(self):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        columnLay = cmds.paneLayout(parent=gMainWindow, width=500)
        dockControl = cmds.dockControl(l='ImportExportUI', allowedArea='all',
                                       area='right', content=columnLay, width=500)
        cmds.control(str(self.objectName()),e=True,p=columnLay)

'''def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    gui = ImportExportUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()'''