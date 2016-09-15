import sys
import os
import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import HTMLConverter
from pdfminer.layout import LAParams
from collections import defaultdict
from utils import *


class Main(QtGui.QMainWindow):

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.filename = ''

        self.initUI()

    def initUI(self):

        # x and y coordinates on the screen, width, height
        self.setGeometry(100, 100, 1030, 800)
        self.setWindowTitle('Shot Editor')
        self.setWindowIcon(QtGui.QIcon('icons/icon.png'))

        self.statusbar = self.statusBar()
        self.text = QtGui.QTextEdit(self)
        self.text.setTabStopWidth(33)
        self.text.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.text.selectionChanged.connect(self.textSelectionChanged)
        self.text.customContextMenuRequested.connect(self.on_context_menu)
        self.text.cursorPositionChanged.connect(self.cursorPosition)
        self.setCentralWidget(self.text)

        # Intialize tag dictionary
        self.tagDict = defaultdict(dict)
        # Initialize context menu
        self.tagMenu = tag.Tag(self.text, self.tagDict)

        self.initToolBar()
        self.initFormatBar()
        self.initMenubar()

    def on_context_menu(self, point):
        cursor = self.text.textCursor()
        if cursor.hasSelection():
            self.tagMenu.exec_(self.text.mapToGlobal(point))

    def textSelectionChanged(self):
        # Update menu on text selection change.
        cursor = self.text.textCursor()
        if cursor.hasSelection():
            self.tagMenu.initMenu()

    def initToolBar(self):
        self.newAction = QtGui.QAction(QtGui.QIcon('icons/new.png'), 'New', self)
        self.newAction.setStatusTip('Create a new document.')
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.triggered.connect(self.new)

        self.openAction = QtGui.QAction(QtGui.QIcon('icons/open.png'), 'Open', self)
        self.openAction.setStatusTip('Create existing document.')
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.triggered.connect(self.open)

        self.saveAction = QtGui.QAction(QtGui.QIcon('icons/save.png'), 'Save', self)
        self.saveAction.setStatusTip('Save document.')
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.triggered.connect(self.save)

        self.exportAction = QtGui.QAction(QtGui.QIcon('icons/csv-export.png'), 'Export', self)
        self.exportAction.setStatusTip('Export CSV for tag-ed data.')
        self.exportAction.setShortcut('Ctrl+E')
        self.exportAction.triggered.connect(self.export)

        self.printAction = QtGui.QAction(QtGui.QIcon('icons/print.png'), 'Print', self)
        self.printAction.setStatusTip('Print document.')
        self.printAction.setShortcut('Ctrl+P')
        self.printAction.triggered.connect(self.printDoc)

        self.previewAction = QtGui.QAction(QtGui.QIcon("icons/preview.png"), "Page view", self)
        self.previewAction.setStatusTip("Preview page before printing")
        self.previewAction.setShortcut("Ctrl+Shift+P")
        self.previewAction.triggered.connect(self.preview)

        self.cutAction = QtGui.QAction(QtGui.QIcon("icons/cut.png"), "Cut to clipboard", self)
        self.cutAction.setStatusTip("Delete and copy text to clipboard")
        self.cutAction.setShortcut("Ctrl+X")
        self.cutAction.triggered.connect(self.text.cut)

        self.copyAction = QtGui.QAction(QtGui.QIcon("icons/copy.png"), "Copy to clipboard", self)
        self.copyAction.setStatusTip("Copy text to clipboard")
        self.copyAction.setShortcut("Ctrl+C")
        self.copyAction.triggered.connect(self.text.copy)

        self.pasteAction = QtGui.QAction(QtGui.QIcon("icons/paste.png"), "Paste from clipboard", self)
        self.pasteAction.setStatusTip("Paste text from clipboard")
        self.pasteAction.setShortcut("Ctrl+V")
        self.pasteAction.triggered.connect(self.text.paste)

        self.undoAction = QtGui.QAction(QtGui.QIcon("icons/undo.png"), "Undo last action", self)
        self.undoAction.setStatusTip("Undo last action")
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.triggered.connect(self.text.undo)

        self.redoAction = QtGui.QAction(QtGui.QIcon("icons/redo.png"), "Redo last undone thing", self)
        self.redoAction.setStatusTip("Redo last undone thing")
        self.redoAction.setShortcut("Ctrl+Y")
        self.redoAction.triggered.connect(self.text.redo)

        bulletAction = QtGui.QAction(QtGui.QIcon("icons/bullet.png"), "Insert bullet List", self)
        bulletAction.setStatusTip("Insert bullet list")
        bulletAction.setShortcut("Ctrl+Shift+B")
        bulletAction.triggered.connect(self.bulletList)

        numberedAction = QtGui.QAction(QtGui.QIcon("icons/number.png"), "Insert numbered List", self)
        numberedAction.setStatusTip("Insert numbered list")
        numberedAction.setShortcut("Ctrl+Shift+L")
        numberedAction.triggered.connect(self.numberList)

        self.findAction = QtGui.QAction(QtGui.QIcon('icons/find.png'), 'Find and replace', self)
        self.findAction.setStatusTip('Find and replace words in your document')
        self.findAction.setShortcut("Ctrl+F")
        self.findAction.triggered.connect(find.Find(self).show)

        self.toolbar = self.addToolBar('Options')
        self.toolbar.addAction(self.newAction)
        self.toolbar.addAction(self.openAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.exportAction)
        self.toolbar.addAction(self.printAction)
        self.toolbar.addAction(self.previewAction)
        self.toolbar.addSeparator()

        self.toolbar.addAction(self.cutAction)
        self.toolbar.addAction(self.copyAction)
        self.toolbar.addAction(self.pasteAction)
        self.toolbar.addAction(self.undoAction)
        self.toolbar.addAction(self.redoAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(bulletAction)
        self.toolbar.addAction(numberedAction)

        self.toolbar.addSeparator()

        self.toolbar.addAction(self.findAction)

        self.addToolBarBreak()

    def initFormatBar(self):

        fontBox = QtGui.QFontComboBox(self)
        fontBox.currentFontChanged.connect(self.fontFamily)

        fontSize = QtGui.QComboBox(self)
        fontSize.setEditable(True)

        # Minimum number of chars displayed
        fontSize.setMinimumContentsLength(3)
        fontSize.activated.connect(self.fontSize)

        # Typical font sizes
        fontSizes = ['6','7','8','9','10','11','12','13','14',
                     '15','16','18','20','22','24','26','28',
                     '32','36','40','44','48','54','60','66',
                     '72','80','88','96']

        fontSize.addItems(fontSizes)

        fontColor = QtGui.QAction(QtGui.QIcon("icons/font-color.png"), "Change font color", self)
        fontColor.triggered.connect(self.fontColor)

        backColor = QtGui.QAction(QtGui.QIcon("icons/highlight.png"), "Change background color", self)
        backColor.triggered.connect(self.highlight)

        boldAction = QtGui.QAction(QtGui.QIcon("icons/bold.png"), "Bold", self)
        boldAction.triggered.connect(self.bold)

        italicAction = QtGui.QAction(QtGui.QIcon("icons/italic.png"), "Italic", self)
        italicAction.triggered.connect(self.italic)

        underlAction = QtGui.QAction(QtGui.QIcon("icons/underline.png"), "Underline", self)
        underlAction.triggered.connect(self.underline)

        strikeAction = QtGui.QAction(QtGui.QIcon("icons/strike.png"), "Strike-out", self)
        strikeAction.triggered.connect(self.strike)

        superAction = QtGui.QAction(QtGui.QIcon("icons/superscript.png"), "Superscript", self)
        superAction.triggered.connect(self.superScript)

        subAction = QtGui.QAction(QtGui.QIcon("icons/subscript.png"), "Subscript", self)
        subAction.triggered.connect(self.subScript)

        alignLeft = QtGui.QAction(QtGui.QIcon("icons/align-left.png"), "Align left", self)
        alignLeft.triggered.connect(self.alignLeft)

        alignCenter = QtGui.QAction(QtGui.QIcon("icons/align-center.png"), "Align center", self)
        alignCenter.triggered.connect(self.alignCenter)

        alignRight = QtGui.QAction(QtGui.QIcon("icons/align-right.png"), "Align right", self)
        alignRight.triggered.connect(self.alignRight)

        alignJustify = QtGui.QAction(QtGui.QIcon("icons/align-justify.png"), "Align justify", self)
        alignJustify.triggered.connect(self.alignJustify)

        indentAction = QtGui.QAction(QtGui.QIcon("icons/indent.png"), "Indent Area", self)
        indentAction.setShortcut("Ctrl+Tab")
        indentAction.triggered.connect(self.indent)

        dedentAction = QtGui.QAction(QtGui.QIcon("icons/dedent.png"), "Dedent Area", self)
        dedentAction.setShortcut("Shift+Tab")
        dedentAction.triggered.connect(self.dedent)

        self.formatbar = self.addToolBar('Format')
        self.formatbar.addWidget(fontBox)
        self.formatbar.addWidget(fontSize)
        self.formatbar.addAction(fontColor)
        self.formatbar.addAction(backColor)
        self.formatbar.addSeparator()

        self.formatbar.addAction(boldAction)
        self.formatbar.addAction(italicAction)
        self.formatbar.addAction(underlAction)
        self.formatbar.addAction(strikeAction)
        self.formatbar.addAction(superAction)
        self.formatbar.addAction(subAction)

        self.formatbar.addSeparator()

        self.formatbar.addAction(alignLeft)
        self.formatbar.addAction(alignCenter)
        self.formatbar.addAction(alignRight)
        self.formatbar.addAction(alignJustify)

        self.formatbar.addSeparator()

        self.formatbar.addAction(indentAction)
        self.formatbar.addAction(dedentAction)


    def initMenubar(self):

        menubar = self.menuBar()
        file = menubar.addMenu('File')
        edit = menubar.addMenu('Edit')
        view = menubar.addMenu('View')

        file.addAction(self.newAction)
        file.addAction(self.openAction)
        file.addAction(self.saveAction)
        file.addAction(self.exportAction)
        file.addAction(self.printAction)
        file.addAction(self.previewAction)

        edit.addAction(self.undoAction)
        edit.addAction(self.redoAction)
        edit.addAction(self.cutAction)
        edit.addAction(self.copyAction)
        edit.addAction(self.pasteAction)
        edit.addAction(self.findAction)

    def cursorPosition(self):

        cursor = self.text.textCursor()

        # Mortals like 1-indexed things
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber()

        self.statusbar.showMessage('Line: {0} | Column: {1}'.format(line, col))

    def new(self):
        spawn = Main(self)
        spawn.show()

    def open(self):
        # Get filename and show only .pdf files
        self.filename, t = QtGui.QFileDialog.getOpenFileName(self, 'Open File', os.path.expanduser('~'))
        # Insert function here to read pdf file and display text.
        if self.filename:
            text = self.convertPDF(self.filename, [1,2,3])
            self.text.setText(text.decode("utf-8", "replace"))

    def export(self):
        # Export csv document
        filename, t = QtGui.QFileDialog.getSaveFileName(self, 'Export File',
                                                        os.path.expanduser('~'), '(*.csv)')
        tagDict = self.tagMenu.getTagDict()
        if not filename.endswith('.csv'):
            filename += ".csv"
        exportObj = export.Export(tagDict, filename)

    def save(self):
        # Only open dialog if there is no filename yet
        if not self.filename:
            self.filename, t = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        # Append extension if not there yet
        if not self.filename.endswith('.txt'):
            fname = os.path.splitext(self.filename)[0]
            self.filename = fname + ".txt"

        # We just store the contents of the text file along with the
        # format in html, which Qt does in a very nice way for us
        with open(self.filename,"wt") as file:
            text = self.text.toPlainText().encode("utf-8")
            file.write(text)

    def printDoc(self):
        # Open printing dialog
        dialog = QtGui.QPrintDialog()
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.text.document().print_(dialog.printer())

    def preview(self):
        # Open preview dialog
        preview = QtGui.QPrintPreviewDialog()

        # If a print is requested, open print dialog
        preview.paintRequested.connect(lambda p: self.text.print_(p))

        preview.exec_()

    def bulletList(self):
        cursor = self.text.textCursor()
        # Insert bullet list
        cursor.insertList(QtGui.QTextListFormat.ListDisc)

    def numberList(self):
        cursor = self.text.textCursor()
        # Insert list with numbers

        cursor.insertList(QtGui.QTextListFormat.ListDecimal)

    def convertPDF(self, fname, pages=None):
        if not pages:
            pagenos = set()
        else:
            pagenos = set(pages)
        caching = True
        outfp = StringIO()
        layoutmode = 'normal'
        laparams = LAParams()
        rotation = 0

        rsrcmgr = PDFResourceManager(caching=caching)
        device = HTMLConverter(rsrcmgr, outfp, codec='utf-8', scale=1,
                               layoutmode=layoutmode, laparams=laparams,
                               imagewriter=None)
        fp = file(fname, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(fp, pagenos,
                                      maxpages=0, password='',
                                      caching=caching, check_extractable=True):
            page.rotate = (page.rotate+rotation) % 360
            interpreter.process_page(page)
        fp.close()
        device.close()

        text = outfp.getvalue()
        outfp.close()
        return text

    def fontFamily(self, font):
        self.text.setCurrentFont(font)

    def fontSize(self, fontsize):
        self.text.setFontPointSize(fontsize)

    def fontColor(self):
        # Get a color from the color dialog
        color = QtGui.QColorDialog.getColor()

        # Set it as the new text color
        self.text.setTextColor(color)

    def highlight(self):
        color = QtGui.QColorDialog.getColor()
        self.text.setTextBackgroundColor(color)

    def bold(self):

        if self.text.fontWeight() == QtGui.QFont.Bold:
            self.text.setFontWeight(QtGui.QFont.Normal)
        else:
            self.text.setFontWeight(QtGui.QFont.Bold)

    def italic(self):
        state = self.text.fontItalic()
        self.text.setFontItalic(not state)

    def underline(self):
        state = self.text.fontUnderline()
        self.text.setFontUnderline(not state)

    def strike(self):
        # Grab the text's format
        fmt = self.text.currentCharFormat()

        # Set the fontStrikeOut property to its opposite
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())

        # Set the next char format
        self.text.setCurrentCharFormat(fmt)

    def superScript(self):
        # Grab the text's format
        fmt = self.text.currentCharFormat()

        # Get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QtGui.QTextCharFormat.AlignNormal:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)

    def subScript(self):
        # Grab the text's format
        fmt = self.text.currentCharFormat()

        # Get the vertical alignment property
        align = fmt.verticalAlignment()

        # Toggle the state
        if align == QtGui.QTextCharFormat.AlignNormal:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)

        # Set the new format
        self.text.setCurrentCharFormat(fmt)

    def alignLeft(self):
        self.text.setAlignment(QtCore.Qt.AlignLeft)

    def alignRight(self):
        self.text.setAlignment(QtCore.Qt.AlignRight)

    def alignCenter(self):
        self.text.setAlignment(QtCore.Qt.AlignCenter)

    def alignJustify(self):
        self.text.setAlignment(QtCore.Qt.AlignJustify)

    def indent(self):

        # Grab the cursor
        cursor = self.text.textCursor()

        if cursor.hasSelection():
            # Store the current line/block number
            temp = cursor.blockNumber()
            # Move the selection to the selection's last line
            cursor.setPosition(cursor.selectionEnd())
            # Calculate range of selction
            diff = cursor.blockNumber() - temp

            # Iterate over the lines
            for n in range(diff+1):
                # Move to start of each line
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                # Insert Tabbing
                cursor.insertText('\t')
                # Move back up
                cursor.movePosition(QtGui.QTextCursor.Up)
        else:
            cursor.insertText('\t')

    def dedent(self):
        cursor = self.text.textCursor()
        if cursor.hasSelection():
            # Store the current line/block number
            temp = cursor.blockNumber()
            # Move the selection to the selection's last line
            cursor.setPosition(cursor.selectionEnd())
            # Calculate range of selction
            diff = cursor.blockNumber() - temp
            # Iterate over the lines
            for n in range(diff+1):
                self.handleDedent(cursor)
                # Move back up
                cursor.movePosition(QtGui.QTextCursor.Up)
        else:
            self.handleDedent(cursor)


    def handleDedent(self, cursor):
        cursor.movePosition(QtGui.QTextCursor.StartOfLine)
        # Grab the current line
        line = cursor.block().text()
        # If the line starts with a tab character, delete it
        if line.startswith('\t'):
            cursor.deleteChar()
        # Else, delete all space until a non space character is met
        else:
            for char in line[:8]:
                if char != " ":
                    break
                cursor.deleteChar()


def main():

    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
