# -*- coding: utf-8 -*-

# This piece of code is taken from trelby http://www.trelby.org/

import sys
from lxml import etree


# linebreak types

LB_SPACE = 1

# we don't use this anymore, but we have to keep it in order to be able to
# load old scripts
LB_SPACE2 = 2

LB_NONE = 3
LB_FORCED = 4
LB_LAST = 5

# line types
SCENE = 1
ACTION = 2
CHARACTER = 3
DIALOGUE = 4
PAREN = 5
TRANSITION = 6
SHOT = 7
NOTE = 8
ACTBREAK = 9

# mapping from character to linebreak
_char2lb = {
    '>': LB_SPACE,
    '+': LB_SPACE2,
    '&': LB_NONE,
    '|': LB_FORCED,
    '\n': LB_LAST
    }

# reverse to above
_lb2char = {}

for k, v in _char2lb.items():
    _lb2char[v] = k

# what string each linebreak type should be mapped to.
_lb2str = {
    LB_SPACE: " ",
    LB_SPACE2: "  ",
    LB_NONE: "",
    LB_FORCED: "\n",
    LB_LAST: "\n"
    }

# mapping from character to TypeInfo
_char2ti = {}

# mapping from line type to TypeInfo
_lt2ti = {}

# translate table for converting strings to only contain valid input
# characters
_input_tbl = ""

_fancy_unicode_map = {
    ord(u"‘"): u"'",
    ord(u"’"): u"'",
    ord(u"“"): u'"',
    ord(u"”"): u'"',
    ord(u"—"): u"--",
    ord(u"–"): u"-",
    }


def toPath(s):
    if sys.platform == 'win32':
        return s
    else:
        return s.encode("UTF-8")


# load at most maxSize (all if -1) bytes from 'filename', returning the
# data as a string or None on errors. pops up message boxes with 'frame'
# as parent on errors.
def loadFile(filename, maxSize=-1):
    try:
        f = open(toPath(filename), "rb")
        try:
            ret = f.read(maxSize)
        finally:
            f.close()

    except IOError, (errno, strerror):
        print "Error loading file '%s': %s" % (filename, strerror)
        ret = None
    return ret


def removeFancyUnicode(s):
    return s.translate(_fancy_unicode_map)


def toLatin1(s):
    return s.encode("ISO-8859-1", "ignore")


def cleanInput(s):
    return toLatin1(removeFancyUnicode(s))


def toInputStr(s):
    return s.translate(_input_tbl, "\f")


def importFDX(fileName):
    elemMap = {
        "Action": ACTION,
        "Character": CHARACTER,
        "Dialogue": DIALOGUE,
        "Parenthetical": PAREN,
        "Scene Heading": SCENE,
        "Shot": SHOT,
        "Transition": TRANSITION,
    }

    # the 5 MB limit is arbitrary, we just want to avoid getting a
    # MemoryError exception for /dev/zero etc.
    data = loadFile(fileName, 5000000)

    if data is None:
        return None

    if len(data) == 0:
        print "Error: File is empty"

        return None

    try:
        root = etree.XML(data)
        lines = []

        def addElem(eleType, eleText):
            lns = eleText.split("\n")

            # if elem ends in a newline, last line is empty and useless;
            # get rid of it
            if not lns[-1] and (len(lns) > 1):
                lns = lns[:-1]

            for s in lns[:-1]:
                lines.append(Line(
                        LB_FORCED, eleType, cleanInput(s)))

            lines.append(Line(
                    LB_LAST, eleType, cleanInput(lns[-1])))

        for para in root.xpath("Content//Paragraph"):
            addedNote = False
            et = para.get("Type")

            # Check for script notes
            s = u""
            for notes in para.xpath("ScriptNote/Paragraph/Text"):
                if notes.text:
                    s += notes.text

                # FD has AdornmentStyle set to "0" on notes with newline.
                if notes.get("AdornmentStyle") == "0":
                    s += "\n"

            if s:
                addElem(NOTE, s)
                addedNote = True

            # "General" has embedded Dual Dialogue paragraphs inside it;
            # nothing to do for the General element itself.
            #
            # If no type is defined (like inside scriptnote), skip.
            if (et == "General") or (et is None):
                continue

            s = u""
            for text in para.xpath("Text"):
                # text.text is None for paragraphs with no text, and +=
                # blows up trying to add a string object and None, so
                # guard against that
                if text.text:
                    s += text.text

            # don't remove paragraphs with no text, unless that paragraph
            # contained a scriptnote
            if s or not addedNote:
                lt = elemMap.get(et, ACTION)
                addElem(lt, s)

        if len(lines) == 0:
            print "Error: The file contains no importable lines"
            return None

        return lines

    except etree.XMLSyntaxError, e:
        print "Error parsing file: %s" % e
        return None


def getElemFirstIndexFromLine(line, lines):
    ls = lines

    while 1:
        tmp = line - 1

        if tmp < 0:
            break

        if ls[tmp].lb == LB_LAST:
            break

        line -= 1

    return line


def removeDanglingElement(line, lt, lastBreak, lines):
    ls = lines
    startLine = line

    while 1:
        if line < (lastBreak + 2):
            break

        ln = ls[line]

        if ln.lt != lt:
            break

        # only remove one element at most, to avoid generating
        # potentially thousands of pages in degenerate cases when
        # script only contains scenes or characters or something like
        # that.
        if (line != startLine) and (ln.lb == LB_LAST):
            break

        line -= 1

    return line


def getTypeOfNextElem(line, lines):
    line = getElemLastIndexFromLine(line, lines)
    line += 1

    if line >= len(lines):
        return None

    return lines[line].lt


def getElemLastIndexFromLine(line, lines):
    ls = lines

    while 1:
        if ls[line].lb == LB_LAST:
            break

        if (line + 1) >= len(ls):
            break

        line += 1

    return line


def paginate(lines):
    pages = [0]
    pagesNoAdjust = [-1]

    ls = lines

    length = len(ls)
    lastBreak = -1

    # fast aliases for stuff
    lbl = LB_LAST
    hdrLines = 2

    fontSize = 12
    h = 297.0  # paperheight
    # return how many mm tall given font size is.
    fs = (fontSize / 72.0) * 25.4
    linesOnPage = int(h / fs)

    i = 0
    while 1:
        lp = linesOnPage * 10

        if i != 0:
            lp -= hdrLines * 10

        # just a safeguard
        lp = max(50, lp)

        pageLines = 0
        if i < length:
            pageLines = 10

            # advance i until it points to the last line to put on
            # this page (before adjustments)

            while i < (length - 1):
                pageLines += 10
                if ls[i].lb == lbl:
                    pageLines += 20
                else:
                    pageLines += 20

                if pageLines > lp:
                    break
                i += 1

        if i >= (length - 1):
            if pageLines != 0:
                pages.append(length - 1)
                pagesNoAdjust.append(length - 1)

            break

        pagesNoAdjust.append(i)

        line = ls[i]

        if line.lt == SCENE:
            i = removeDanglingElement(i, SCENE, lastBreak, ls)

        elif line.lt == SHOT:
            i = removeDanglingElement(i, SHOT, lastBreak, ls)
            i = removeDanglingElement(i, SCENE, lastBreak, ls)

        elif line.lt == ACTION:
            if line.lb != LB_LAST:
                first = getElemFirstIndexFromLine(i, lines)

                if first > (lastBreak + 1):
                    linesOnThisPage = i - first + 1
                    if linesOnThisPage < 2:
                        i = first - 1

                    i = removeDanglingElement(i, SCENE, lastBreak, ls)

        elif line.lt == CHARACTER:
            i = removeDanglingElement(i, CHARACTER, lastBreak, ls)
            i = removeDanglingElement(i, SCENE, lastBreak, ls)

        elif line.lt in (DIALOGUE, PAREN):

            if line.lb != LB_LAST or getTypeOfNextElem(i, ls) in (DIALOGUE, PAREN):

                cutDialogue = False
                cutParen = False
                while 1:
                    oldI = i
                    line = ls[i]

                    if line.lt == PAREN:
                        i = removeDanglingElement(i, PAREN, lastBreak, ls)
                        cutParen = True

                    elif line.lt == DIALOGUE:
                        if cutParen:
                            break

                        first = getElemFirstIndexFromLine(i, ls)

                        if first > (lastBreak + 1):
                            linesOnThisPage = i - first + 1

                            # do we need to reserve one line for (MORE)
                            reserveLine = not (cutDialogue or cutParen)

                            val = 2
                            if reserveLine:
                                val += 1

                            if linesOnThisPage < val:
                                i = first - 1
                                cutDialogue = True
                            else:
                                if reserveLine:
                                    i -= 1
                                break
                        else:
                            # leave space for (MORE)
                            i -= 1
                            break

                    elif line.lt == CHARACTER:
                        i = removeDanglingElement(i, CHARACTER, lastBreak, ls)
                        i = removeDanglingElement(i, SCENE, lastBreak, ls)

                        break

                    else:
                        break

                    if i == oldI:
                        break

        # make sure no matter how buggy the code above is, we always
        # advance at least one line per page
        i = max(i, lastBreak + 1)

        pages.append(i)
        lastBreak = i

        i += 1
    return pages


# one line in a screenplay
class Line:
    def __init__(self, lb=LB_LAST, lt=ACTION, text=""):

        # line break type
        self.lb = lb

        # line type
        self.lt = lt

        # text
        self.text = text

    def getLine(self):
        return self.lb2char(self.lb) + self.text

    def _conv(self, dict, key, raiseException=True):
        val = dict.get(key)
        if (val is None) and raiseException:
            raise EnvironmentError("key '%s' not found from '%s'" % (key, dict))

        return val

    def lb2char(self, lb):
        return self._conv(_lb2char, lb)

    def lt2char(self, lt):
        return self._conv(_lt2ti, lt).char


# non-changing information about an element type
class TypeInfo:
    def __init__(self, lt, char, name):

        # line type, e.g. screenplay.ACTION
        self.lt = lt

        # character used in saved scripts, e.g. "."
        self.char = char

        # textual name, e.g. "Action"
        self.name = name


for lt, char, name in ((SCENE,      "\\", "Scene"),
                       (ACTION,     ".",  "Action"),
                       (CHARACTER,  "_",  "Character"),
                       (DIALOGUE,   ":",  "Dialogue"),
                       (PAREN,      "(",  "Parenthetical"),
                       (TRANSITION, "/",  "Transition"),
                       (SHOT,       "=",  "Shot"),
                       (ACTBREAK,   "@",  "Act break"),
                       (NOTE,       "%",  "Note")):
    ti = TypeInfo(lt, char, name)

    _lt2ti[lt] = ti
    _char2ti[char] = ti
