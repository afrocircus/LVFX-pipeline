import re
from PySide import QtGui


class Find(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.parent = parent
        self.lastMatch = None

        self.initUI()

    def initUI(self):

        # Button to search the document for something
        findButton = QtGui.QPushButton('Find', self)
        findButton.clicked.connect(self.find)

        # Button to replace the last finding
        replaceButton = QtGui.QPushButton("Replace",self)
        replaceButton.clicked.connect(self.replace)

        # Button to remove all findings
        allButton = QtGui.QPushButton("Replace all",self)
        allButton.clicked.connect(self.replaceAll)

        # Normal mode - radio button
        self.normalRadio = QtGui.QRadioButton("Normal",self)
        self.normalRadio.toggled.connect(self.normalMode)

        # Regular Expression Mode - radio button
        self.regexRadio = QtGui.QRadioButton("RegEx",self)
        self.regexRadio.toggled.connect(self.regexMode)

        # The field into which to type the query
        self.findField = QtGui.QTextEdit(self)
        self.findField.resize(250,50)

        # The field into which to type the text to replace the
        # queried text
        self.replaceField = QtGui.QTextEdit(self)
        self.replaceField.resize(250,50)

        optionsLabel = QtGui.QLabel("Options: ",self)

        # Case Sensitivity option
        self.caseSens = QtGui.QCheckBox("Case sensitive",self)

        # Whole Words option
        self.wholeWords = QtGui.QCheckBox("Whole words",self)

        # Layout the objects on the screen
        layout = QtGui.QGridLayout()

        layout.addWidget(self.findField,1,0,1,4)
        layout.addWidget(self.normalRadio,2,2)
        layout.addWidget(self.regexRadio,2,3)
        layout.addWidget(findButton,2,0,1,2)

        layout.addWidget(self.replaceField,3,0,1,4)
        layout.addWidget(replaceButton,4,0,1,2)
        layout.addWidget(allButton,4,2,1,2)

        # Add some spacing
        spacer = QtGui.QWidget(self)

        spacer.setFixedSize(0,10)

        layout.addWidget(spacer,5,0)

        layout.addWidget(optionsLabel,6,0)
        layout.addWidget(self.caseSens,6,1)
        layout.addWidget(self.wholeWords,6,2)

        self.setGeometry(300,300,360,250)
        self.setWindowTitle("Find and Replace")
        self.setLayout(layout)

        # By default the normal mode is activated
        self.normalRadio.setChecked(True)

    def find(self):
        # Grab the parent's text
        text = self.parent.text.toPlainText()
        # Grab the text to find
        query = self.findField.toPlainText()

        # If the 'Whole Words' checkbox is checked, we need to append and
        # prepend a non-alphanumeric character

        if self.wholeWords.isChecked():
            query = r'\W' + query + r'\W'

        # By default regexes are case sensitive but our search isn't case sensitive
        # by default, so we need to switch this around.
        flags = 0 if self.caseSens.isChecked() else re.I

        # Compile the pattern
        pattern = re.compile(query, flags)

        # If the last match was successful, start at position after the last
        # match's start, else at 0
        start = self.lastMatch.start() + 1 if self.lastMatch else 0

        # The actual search
        self.lastMatch = pattern.search(text, start)

        if self.lastMatch:
            start = self.lastMatch.start()
            end = self.lastMatch.end()

            # If 'Whole words' is checked, the selection would include the two
            # non-alphanumeric characters we included in the search, which need
            # to be removed before marking them.
            if self.wholeWords.isChecked():
                start += 1
                end -= 1

            self.moveCursor(start, end)
        else:
            # We set the cursor to the end if the search was unsuccessful
            self.parent.text.moveCursor(QtGui.QTextCursor.End)

    def replace(self):
        # Grab the text cursor
        cursor = self.parent.text.textCursor()

        # Security
        if self.lastMatch and cursor.hasSelection():
            # Insert new text which will override the selected text
            cursor.insertText(self.replaceField.toPlainText())
            # set the new cursor
            self.parent.text.setTextCursor(cursor)

    def replaceAll(self):
        # Set lastMatch to None so the search starts at the beginning of the document.
        self.lastMatch = None
        self.find()

        # Replace and find untill find is None again
        while self.lastMatch:
            self.replace()
            self.find()

    def regexMode(self):
        # First uncheck the checkboxes
        self.caseSens.setChecked(False)
        self.wholeWords.setChecked(False)

        # Then disable them
        self.caseSens.setEnabled(False)
        self.wholeWords.setEnabled(False)

    def normalMode(self):
        # Enable checkboxes
        self.caseSens.setEnabled(True)
        self.wholeWords.setEnabled(True)

    def moveCursor(self, start, end):
        # We retrieve the QTextCursor object from the parent's QTextEdit
        cursor = self.parent.text.textCursor()

        # set the position the beginning of the last match
        cursor.setPosition(start)

        # We move the Cursor by over the match and pass the KeepAnchor parameter
        # which will make the cursor select the the match's text
        cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, end - start)

        # Set cursor as parent
        self.parent.text.setTextCursor(cursor)