import os
import sys
import ftrack
import logging
import getpass
import re
import glob
import shutil
import subprocess
import threading


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class GetLatestPublish(ftrack.Action):

    label = 'Get Latest Publish'
    identifier = 'com.ftrack.getLatestPublish'

    def version_get(self, string, prefix, suffix=None):
        """Extract version information from filenames.  Code from Foundry's nukescripts.version_get()"""

        if string is None:
            raise ValueError, "Empty version string - no match"

        regex = "[/_.]" + prefix + "\d+"
        matches = re.findall(regex, string, re.IGNORECASE)
        if not len(matches):
            msg = "No \"_" + prefix + "#\" found in \"" + string + "\""
            raise ValueError, msg
        return matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group()

    def getShotFolder(self, task):
        shotFolder = ''
        parents = task.getParents()
        parents.reverse()
        for parent in parents:
            if 'objecttypename' in parent.keys():
                shotFolder = os.path.join(shotFolder, parent.getName())
        return shotFolder

    def getProjectFolder(self, project):
        projFolder = project.get('root')
        if projFolder == '':
            disk = ftrack.Disk(project.get('diskid'))
            rootFolder = ''
            if sys.platform == 'win32':
                rootFolder = disk.get('windows')
            elif sys.platform == 'linux2':
                rootFolder = disk.get('unix')
            projFolder = os.path.join(rootFolder, project.getName())
        return projFolder

    def copyFromLayoutPublish(self, taskFolder, taskName):
        layoutDir = os.path.join(taskFolder.split(taskName)[0], 'layout', 'publish')
        publishFile = ''
        # If the layout publish dir exists
        if os.path.exists(layoutDir):
            versions = []
            # get the latest published version
            for each in os.listdir(layoutDir):
                versionDir = os.path.join(layoutDir, each)
                if os.path.isdir(versionDir):
                    try:
                        versions.append(self.version_get(versionDir, 'v')[1])
                    except ValueError:
                        continue
            versions.sort()
            latestVersion = os.path.join(layoutDir, 'v' + versions[-1])
            publishFile = os.path.join(latestVersion, 'animation_publish.mb')
        return publishFile

    def getTaskFolder(self, task):
        taskName = task.getName().lower()
        project = task.getProject()
        projFolder = self.getProjectFolder(project)

        shotsFolder = os.path.join(projFolder, 'shots')
        shotFolder = self.getShotFolder(task)
        sceneFolder = os.path.join(shotsFolder, shotFolder, 'scene')
        taskFolder = os.path.join(sceneFolder, taskName)
        return taskFolder

    @async
    def buildLightingScene(self, mayapy, task, folder, user, filename, shotName):
        job = ftrack.createJob('Building Lighting scene file for shot '
                               '{0}'.format(shotName), 'queued', user)
        job.setStatus('running')
        cmd = '%s /home/natasha/dev/LVFX-pipeline/scripts/lt_build_scene.py ' \
              '-taskid %s -taskDir %s' % (mayapy, task, folder)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        print cmd
        process.wait()
        if os.path.exists(filename):
            job.setStatus('done')
        else:
            job.setStatus('failed')

    def register(self):
        '''Register discover actions on logged in user.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

    def discover(self, event):
        '''Return action config if triggered on a single selection.'''
        selection = event['data'].get('selection', [])

        if not selection:
            return

        entityType = selection[0]['entityType']

        if entityType == 'task':
            task = ftrack.Task(selection[0]['entityId'])
            if task.get('objecttypename') == 'Task':
                taskType = task.getType().getName().lower()
                if taskType == 'animation' or taskType == 'previz' or taskType == 'lighting':
                    taskFolder = self.getTaskFolder(task)
                    shotName = task.getParent().getName()
                    newFilePath = os.path.join(taskFolder, '%s_v01.mb' % shotName)
                    if not os.path.exists(newFilePath):
                        return {
                            'items': [{
                                'label': self.label,
                                'actionIdentifier': self.identifier,
                                'icon': 'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-connect-plugins/icons/send.png'
                            }]
                        }
            else:
                return

    def launch(self, event):
        """
        Called when action is executed
        """
        selection = event['data'].get('selection', [])
        task = ftrack.Task(selection[0]['entityId'])
        user = ftrack.User(id=event['source']['user']['id'])
        taskType = task.getType().getName().lower()

        taskFolder = self.getTaskFolder(task)
        if not os.path.exists(taskFolder):
            os.makedirs(taskFolder)

        shotName = task.getParent().getName()
        publishFile = ''
        newFilePath = os.path.join(taskFolder, '%s_v01.mb' % shotName)

        if taskType == 'previz':
            publishFile = self.copyFromLayoutPublish(taskFolder, 'previz')
            if os.path.exists(publishFile) and not os.path.exists(newFilePath):
                shutil.copy(publishFile, newFilePath)
            os.chmod(newFilePath, 0666)
        elif taskType == 'animation':
            previzDir = os.path.join(taskFolder.split('animation')[0], 'previz')
            previzFiles = [f for f in glob.glob(os.path.join(previzDir, '*_v[0-9]*.mb'))]
            # get latest previz file
            if previzFiles:
                maxVersion = 1
                for f in previzFiles:
                    try:
                        version = int(self.version_get(f, 'v')[1])
                    except ValueError:
                        continue
                    if version >= maxVersion:
                        publishFile = f
                        maxVersion = version
                publishFile = os.path.join(previzDir, publishFile)
            # Else get latest layout publish file
            else:
                publishFile = self.copyFromLayoutPublish(taskFolder, 'animation')
            # Copy over the latest publish file.
            if os.path.exists(publishFile) and not os.path.exists(newFilePath):
                shutil.copy(publishFile, newFilePath)
            os.chmod(newFilePath, 0666)
        elif taskType == 'lighting':
            mayapy = '/usr/autodesk/maya2016/bin/mayapy'
            if os.path.exists(mayapy):
                self.buildLightingScene(mayapy, task.getId(), taskFolder, user, newFilePath, shotName)

        metadata = task.getMeta()
        metadata['filename'] = newFilePath
        task.setMeta(metadata)

        return {
                'success': True,
                'message': 'Action launched successfully.'
            }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.getLatestPublish'
    )

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    action = GetLatestPublish()
    action.register()