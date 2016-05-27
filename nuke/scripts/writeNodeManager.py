import nukescripts
import nuke
import os
from datetime import datetime


def getRootDir():
    nukeFile = nuke.scriptName()
    return nukeFile.split('compscript')[0]


def getFilename():
    nukeFile = nuke.root().name()
    return nukeFile.split('/')[-1].split('.')[0]


def getFilenameMatte():
    filename = getFilename()
    return filename.replace('comp', 'matte')


def getOutputFile():
    node = nuke.thisNode()
    return node.knob('file').value()


def getDate():
    today = datetime.today()
    date = '%d_%02d_%02d' % (today.year, today.month, today.day)
    return date


def getShotName():
    nukeFile = nuke.root().name()
    shotname = nukeFile.split('/')[4]
    return shotname


def getProjectName():
    nukeFile = nuke.root().name()
    projname = nukeFile.split('/')[1]
    if projname == 'bg_tlf':
        projname = 'TLF'
    return projname


def getProjectDir():
    nukeFile = nuke.root().name()
    parts = nukeFile.split('/')
    projDir = os.path.join(parts[0], '/%s' % parts[1])
    return projDir


def getVersion():
    filename = getFilename()
    version = filename.split('_')[-1]
    return int(version.split('v')[-1])


def makeFolders(folder):
    folder = folder.replace('/', '\\')
    if not os.path.exists(folder):
        os.makedirs(folder)


def getFinalQuickTimeFolder():
    rootDir = '%s/production/deliveries/locovfx_%s_a' % (getProjectDir(), getDate())
    filename = getFilename()
    qtFolder = '%s/_quicktime/comp/%s' % (rootDir, filename)
    makeFolders(qtFolder)
    return qtFolder


def getQuickTimeFolder():
    rootDir = '%s/production/approvals/bg/locovfx_%s_a' % (getProjectDir(), getDate())
    filename = getFilename()
    qtFolder = '%s/_quicktime/comp/%s' % (rootDir, filename)
    makeFolders(qtFolder)
    return qtFolder


def getDPXRoot():
    rootDir = '%s/production/deliveries/locovfx_%s_a' % (getProjectDir(), getDate())
    dpxRoot = '%s/_dpx/' % rootDir
    return dpxRoot


def getDPXComp():
    dpxRoot = getDPXRoot()
    filename = getFilename()
    dpxComp = '%s/comp/%s' % (dpxRoot, filename)
    makeFolders(dpxComp)
    return dpxComp


def getDPXMatte():
    dpxRoot = getDPXRoot()
    filename = getFilenameMatte()
    dpxMatte = '%s/matte/%s' % (dpxRoot, filename)
    makeFolders(dpxMatte)
    return dpxMatte


def copyNukeFile():
    rootDir = '%s/production/deliveries/locovfx_%s_a' % (getProjectDir(), getDate())
    shotname = getShotName()
    filename = getFilename()
    nkFolder = '%s/_nk/%s/compscript/%s' % (rootDir, shotname, filename)
    makeFolders(nkFolder)
    nukeFile = nuke.root().name()
    import shutil
    shutil.copy(nukeFile, nkFolder)


def setOutputPath(type):
    filename = nuke.scriptName()
    filepath, file = os.path.split(filename)
    fname, fext = os.path.splitext(file)
    version = fname.split('_')[-1]
    shotDir = filename.split('scene')[0]
    compDir = os.path.join(shotDir, 'img/comps/%s' % version)
    outDir = os.path.join(compDir, type)
    thisNode = nuke.thisNode()
    fileType = thisNode.knob('file_type').value()
    if type == 'img':
        outFile = os.path.join(outDir, '%s.####.%s' % (fname, fileType))
    elif type == 'mov':
        outFile = os.path.join(outDir, '%s.%s' % (fname, fileType))
    return outFile
