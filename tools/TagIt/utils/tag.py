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

    def initMenu(self):
        """
        Dynamically build context menu based on tagDict
        :return: None
        """
        self.clear()
        for taskType in TASK_TYPES:
            taskAction = QtGui.QAction(taskType, self, checkable=True)
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

    def onTaskTriggered(self, action):
        """
        Slot activated when task action signal triggered.
        Updates scene information in tagDict
        :param action: Task action selected
        :return: None
        """
        taskName = action.text()
        color = QtGui.QColor(170, 170, 0)
        self.parent.setTextBackgroundColor(color)
        sceneNo, sceneDesc = self.findScene()
        pageNo = self.findPage()
        d = self.tagDict[sceneNo]
        d['page'] = pageNo
        d['desc'] = sceneDesc
        if 'tasks' in d:
            d['tasks'].append(taskName)
        else:
            d['tasks'] = [taskName]

    def findScene(self):
        """
        Find the scene based on current selection.
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
        color = QtGui.QColor(0, 140, 40)
        self.parent.setTextBackgroundColor(color)

        sceneDesc = self.parent.textCursor().selectedText().encode("utf-8")
        # Get line number of the scene
        scenePos = self.parent.textCursor().blockNumber() + 1
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
