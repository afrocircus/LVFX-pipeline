import re
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore


TASK_TYPES = ['Texturing', 'Generic', 'Animation', 'Modeling', 'Previz',
              'Lookdev', 'FX', 'Lighting', 'Compositing', 'Tracking', 'Rigging',
              'Matte Painting', 'Layout', 'Rotoscoping', 'VFX Supervision']


class Tag(QtGui.QMenu):
    def __init__(self, parent=None, tagDict=None):
        # Initialize context menu
        QtGui.QMenu.__init__(self, parent)
        self.installEventFilter(self)
        self.parent = parent
        self.tagDict = tagDict

    def initMenu(self, tagDict):
        """
        Dynamically build context menu based on tagDict
        :return: None
        """
        self.tagDict = tagDict
        self.clear()
        selectionLine = self.parent.textCursor().blockNumber()+1
        selectionText = self.parent.textCursor().selectedText()
        for taskType in TASK_TYPES:
            taskAction = QtGui.QAction(taskType, self, checkable=True)
            if self.taskFound(selectionLine, taskType, selectionText):
                taskAction.setChecked(True)
            else:
                taskAction.setChecked(False)
            taskAction.triggered.connect(lambda arg=taskAction: self.onTaskTriggered(arg))
            self.addAction(taskAction)

    def eventFilter(self, obj, event):
        if event.type() in [QtCore.QEvent.MouseButtonRelease]:
            if isinstance(obj, QtGui.QMenu):
                if obj.activeAction():
                    if not obj.activeAction().menu():  # if selected action does not have submenu
                        # eat event but trigger the function
                        obj.activeAction().trigger()
                    return True
        return QtGui.QMenu.eventFilter(self, obj, event)

    def taskFound(self, selectionLineNo, taskType, taskDesc):
        """
        Find if the selected text has a task associated with it already.
        :param selectionLineNo: Selection line number
        :param taskType: task name
        :return: True or False based on if task is found
        """
        if self.tagDict:
            # Find the scene number closest to the selected line number
            sceneNumber = [item for item in sorted(self.tagDict.iterkeys())
                           if item <= selectionLineNo][-1]
            # Check if the scene dict has the associated task
            if 'tasks' in self.tagDict[sceneNumber]:
                for task, taskLine, taskDesc in self.tagDict[sceneNumber]['tasks']:
                    if task == taskType and taskLine == selectionLineNo:
                        return True
        return False

    def onTaskTriggered(self, action):
        """
        Slot activated when task action signal triggered.
        Updates scene information in tagDict
        :param action: Task action selected
        :return: None
        """
        taskName = action.text()
        cursor = self.parent.textCursor()
        taskNo = cursor.blockNumber() + 1

        # Get current selection
        selectionStart = cursor.selectionStart()
        selectionEnd = cursor.selectionEnd()
        taskDesc = cursor.selectedText().encode("utf-8")

        if self.allActionsUnchecked():
            color = QtGui.QColor(255, 255, 255)
        else:
            color = QtGui.QColor(204, 217, 201)
        self.parent.setTextBackgroundColor(color)
        sceneNo, sceneDesc = self.findScene(selectionStart, selectionEnd)
        pageNo = self.findPage()
        d = self.tagDict[sceneNo]
        d['page'] = pageNo
        d['desc'] = sceneDesc
        if action.isChecked():
            if 'tasks' in d:
                d['tasks'].append((taskName, taskNo, taskDesc))
            else:
                d['tasks'] = [(taskName, taskNo, taskDesc)]
        elif (taskName, taskNo, taskDesc) in d['tasks']:
            d['tasks'].remove((taskName, taskNo, taskDesc))

    def allActionsUnchecked(self):
        unchecked = True
        for action in self.actions():
            if action.isChecked():
                unchecked = False
        return unchecked

    def findScene(self, selectionStart, selectionEnd):
        """#CCD9C9 #9EBFE2 #92A8D2 #486A5D #A8E79A
        Find the scene based on current selection.
        :param selectionStart: Starting position of current selection
        :param selectionEnd: Ending position of current selection
        :return: scenePos: Scene Line Number
                 sceneDesc: Scene Description
        """
        cursor = self.parent.textCursor()
        allText = self.parent.toPlainText()

        # Grab the text from start of document to end of selection.
        end = cursor.selectionEnd()
        text = allText[:end]

        # Find the scene.
        # Assumption: Scenes have INT or EXT in their description
        query = r'\b' + 'INT|EXT' + r'\b'
        pattern = re.compile(query)
        matches = [m.span() for m in pattern.finditer(text)]
        matchStart, matchEnd = matches[-1]

        # Select the scene description
        cursor.setPosition(matchStart, QtGui.QTextCursor.MoveAnchor)
        cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor, matchEnd-matchStart)
        self.parent.setTextCursor(cursor)

        # Change the color
        color = QtGui.QColor(168, 231, 154)
        self.parent.setTextBackgroundColor(color)

        sceneDesc = self.parent.textCursor().selectedText().encode("utf-8")
        # Get line number of the scene
        scenePos = self.parent.textCursor().blockNumber() + 1
        cursor.setPosition(selectionStart, QtGui.QTextCursor.MoveAnchor)
        cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor,
                            selectionEnd-selectionStart)
        self.parent.setTextCursor(cursor)
        return scenePos, sceneDesc

    def findPage(self):
        """
        Find the page number based on current selection.
        :return: pageNo: Integer page number.
        """
        # Grab the parent's cursor
        cursor = self.parent.textCursor()
        allText = self.parent.toPlainText()

        # Grab the text from start of document to end of selection.
        end = cursor.selectionEnd()
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
