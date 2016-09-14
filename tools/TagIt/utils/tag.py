import re
import PySide.QtGui as QtGui
from collections import defaultdict


class Tag(QtGui.QMenu):
    def __init__(self, parent=None, tagDict=None):
        # Initalize context menu
        QtGui.QMenu.__init__(self, parent)
        self.parent = parent
        self.tagDict = tagDict
        self.lastMatch = None

    def initMenu(self):
        """
        Dynamically build context menu based on tagDict
        :return: None
        """
        self.clear()
        sceneAction = QtGui.QAction('New Scene', self)
        sceneAction.triggered.connect(self.onSceneTriggered)
        self.addAction(sceneAction)

        shotMenu = QtGui.QMenu()
        shotMenu.setTitle('New Shot in')
        for scene in sorted(self.tagDict.keys()):
            shotAction = QtGui.QAction(scene, self)
            shotAction.triggered.connect(lambda arg=shotAction: self.onShotTriggered(arg))
            shotMenu.addAction(shotAction)
        self.addMenu(shotMenu)

        descAction = QtGui.QAction('Description', self)
        descAction.triggered.connect(self.onSceneTriggered)
        self.addAction(descAction)

    def onSceneTriggered(self):
        """
        Slot triggered when scene action signal triggered.
        Creates/Updates the scene information in tagDict
        :return: None
        """
        if len(self.tagDict) > 0:
            lastScene = sorted(self.tagDict.keys())[-1]
            newScene = '%03d' % (int(lastScene) + 1)
        else:
            newScene = '001'
        d = self.tagDict[newScene]
        d['page'] = self.findPage()
        d['shots'] = defaultdict(dict)

    def onShotTriggered(self, action):
        """
        Slot triggered when shot action signal triggered.
        Creates/Updates the shot information in tagDict
        :return: None
        """
        scene = action.text()
        shotsDict = self.tagDict[scene]['shots']
        if len(shotsDict) > 0:
            lastShot = sorted(shotsDict.keys())[-1]
            shotNumber = lastShot.split('_')[-1]
            newShot = '%04d' % (int(shotNumber) + 10)
        else:
            newShot = '0010'
        shotName = '%s_%s' % (scene, newShot)
        d = shotsDict[shotName]
        d['page'] = self.findPage()

    def findPage(self):
        """
        Find the page number based on current selection.
        :return: pageNo: Integer page number.
        """
        # Grab the parent's cursor
        cursor = self.parent.textCursor()

        # Grab the text from start of document to end of selection.
        start = 0
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, end-start)
        self.parent.setTextCursor(cursor)
        text = cursor.selectedText()

        # Page numbers should be of the format "Page 1"
        query = 'Page ' + r'\d+'

        # Compile the pattern
        pattern = re.compile(query)
        # The actual search
        matches = pattern.findall(text)
        # If matches found, get the last match and convert it to int.
        pageNo = None
        if matches:
            page = matches[-1].split('Page ')
            if page:
                pageNo = int(page[-1])
        return pageNo