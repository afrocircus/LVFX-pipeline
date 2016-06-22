import ftrack_api
import os
import threading
import nuke
import time
import writeNodeManager
import shutil
import datetime
from Utils import ftrack_utils


_session = ftrack_api.Session(
        server_url=os.environ['FTRACK_SERVER'],
        api_user=os.environ['FTRACK_API_USER'],
        api_key=os.environ['FTRACK_API_KEY']
    )

def isValidTask(projPath):
    task = None
    try:
        task = ftrack_utils.getTask(_session, projPath)
    except Exception:
        return False, None
    return True, task


def getProjectDetails():
    node = nuke.toNode('TextFields')  # The name of the node inside the slate gizmo
    filename = nuke.scriptName()
    projectName = node.knob('plate_jobname').value()
    shotName = node.knob('plate_shotname').value()
    seqName = filename.split('/%s/' % shotName)[0].split('/')[-1]
    projPath = '%s / %s / %s / compositing' % (projectName, seqName, shotName)
    result, task = isValidTask(projPath)
    if not result:
        projPath = '%s / %s / %s / Compositing' % (projectName, seqName, shotName)
        result, task = isValidTask(projPath)
        if not result:
            print '%s is not a valid ftrack task' % projPath
            task = None
    return task, projPath


def getArtist():
    task, projPath = getProjectDetails()
    username = ''
    if task is not None:
        try:
            username = task['appointments'][0]['resource']['username']
        except:
            username = 'No user assigned'
    return username


def getLatestNote():
    task, projPath = getProjectDetails()
    latestNote = ''
    if task is not None:
        notesDict = {}
        for note in task['notes']:
            notesDict[note['date']] = note['content']

        if len(task['notes']) > 0:
            latestDate = sorted(notesDict.keys())[-1]
            latestNote = notesDict[latestDate]
    return latestNote


def getLineDict():
    note = getLatestNote()
    lines = {}
    if note is not '':
        parts = note.split('\n')
        i = 1
        for part in parts:
            if not part == '':
                if i <= 4:
                    lines[i] = part
                    i += 1
                else:
                    lines[4] = lines[4] + ' ' + part
    return lines


def getLine(lineno):
    lines = getLineDict()
    line = ''
    if lineno in lines:
        line = lines[lineno]
    return line


def getDate():
    today = datetime.datetime.today()
    date = '%d-%02d-%d' % (today.year, today.month, today.day)
    return date


def getVersion():
    filename = nuke.scriptName()
    nkDir, nkFile = os.path.split(filename)
    nkName, nkExt = os.path.splitext(nkFile)
    parts = nkName.split('_v')
    if len(parts) <= 1:
        version = 0
    else:
        version = int(parts[1])
    return version


def getShotName():
    filename = nuke.scriptName()
    filepath, file = os.path.split(filename)
    fname, fext = os.path.splitext(file)
    shotName = fname.split('_v')[0]
    return shotName


def getJobName():
    filename = nuke.scriptName()
    jobDir = filename.split('shots')[0]
    jobName = jobDir.split('/')[-2]
    return jobName


def getTaskName():
    task = None
    if 'FTRACK_TASKID' in os.environ.keys():
        try:
            task = _session.query('Task where id is {0}'.format(os.environ['FTRACK_TASKID'])).one()
        except:
            print 'No task found'
    if not task:
        task, projPath = getProjectDetails()
    if task:
        return task['name']
    else:
        return 'No task found'
