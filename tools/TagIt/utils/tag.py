import re
import PySide.QtGui as QtGui
from collections import defaultdict


TASK_TYPES = ['Texturing', 'Generic', 'Animation', 'Modeling', 'Previz',
             'Lookdev', 'FX', 'Lighting', 'Compositing', 'Tracking', 'Rigging',
             'Matte Painting', 'Layout', 'Rotoscoping', 'VFX Supervision']


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
        currentPage = self.findPage()
        sceneAction = QtGui.QAction('New Scene', self)
        sceneAction.triggered.connect(lambda arg=currentPage: self.onSceneTriggered(arg))
        self.addAction(sceneAction)

        shotMenu = QtGui.QMenu()
        shotMenu.setTitle('New Shot in')
        for scene in sorted(self.tagDict.keys()):
            shotAction = QtGui.QAction(scene, self)
            shotAction.triggered.connect(lambda arg=(shotAction, currentPage): self.onShotTriggered(arg))
            shotMenu.addAction(shotAction)
        self.addMenu(shotMenu)

        shotSceneList = self.getRelevantShots(currentPage)
        taskMenu = QtGui.QMenu()
        taskMenu.setTitle('Task Type')
        for taskType in TASK_TYPES:
            taskTypeMenu = QtGui.QMenu()
            taskTypeMenu.setTitle(taskType)
            for scene in sorted(shotSceneList):
                taskAction = QtGui.QAction(scene, self)
                taskAction.triggered.connect(lambda arg=(taskAction, taskTypeMenu.title()):
                                             self.onTaskTriggered(arg))
                taskTypeMenu.addAction(taskAction)
            taskMenu.addMenu(taskTypeMenu)
        self.addMenu(taskMenu)

    def onSceneTriggered(self, currentPage):
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
        d['page'] = currentPage
        d['shots'] = defaultdict(dict)
        d['description'] = self.parent.textCursor().selectedText().encode("utf-8")
        color = QtGui.QColor(255, 170, 0)
        self.parent.setTextBackgroundColor(color)

    def onShotTriggered(self, (action, currentPage)):
        """
        Slot triggered when shot action signal triggered.
        Creates/Updates the shot information in tagDict
        :param action: Action that has been selected.
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
        d['page'] = currentPage
        d['description'] = self.parent.textCursor().selectedText().encode("utf-8")
        d['task'] = []
        color = QtGui.QColor(255, 170, 127)
        self.parent.setTextBackgroundColor(color)

    def onTaskTriggered(self, (action, taskName)):
        """
        Slot activated when task action signal triggered.
        Updates shot information in tagDict
        :return: None
        """
        shotName = action.text()
        scene = shotName.split('_')[0]
        shotDict = self.tagDict[scene]['shots'][shotName]
        shotDict['task'].append(taskName)
        color = QtGui.QColor(170, 170, 0)
        self.parent.setTextBackgroundColor(color)

    def findPage(self):
        """
        Find the page number based on current selection.
        :return: pageNo: Integer page number.
        """
        # Grab the parent's cursor
        cursor = self.parent.textCursor()
        allText = self.parent.toPlainText()


        # Grab the text from start of document to end of selection.
        #start = 0
        end = cursor.selectionEnd()
        #cursor.setPosition(start)
        #cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, end-start)
        #self.parent.setTextCursor(cursor)
        text = allText[:end]

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

    def getRelevantShots(self, currentPage):
        # Scenes that are relevant to the current page
        #relevantList = [item[0] for item in self.tagDict.iteritems() if item[1]['page'] <= currentPage]
        relevantList = []
        # Shots that are relevant to the current page
        shotDicts = [item['shots'] for item in self.tagDict.itervalues()]
        for shotDict in shotDicts:
            shotList = [item[0] for item in shotDict.iteritems() if item[1]['page'] <= currentPage]
            relevantList.extend(shotList)
        return relevantList

    def getTagDict(self):
        return self.tagDict


