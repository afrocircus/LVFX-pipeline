# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
import getpass
import sys
import pprint
import logging
import re

import ftrack
import ftrack_connect.application


class LaunchAction(object):
    '''ftrack connect legacy plugins discover and launch action.'''

    identifier = 'ftrack-connect-legacy-launch-application'

    def __init__(self, applicationStore, launcher):
        '''Initialise action with *applicationStore* and *launcher*.

        *applicationStore* should be an instance of
        :class:`ftrack_connect.application.ApplicationStore`.

        *launcher* should be an instance of
        :class:`ftrack_connect.application.ApplicationLauncher`.

        '''
        super(LaunchAction, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.applicationStore = applicationStore
        self.launcher = launcher

    def isValidSelection(self, selection):
        '''Return true if the selection is valid.

        Legacy plugins can only be started from a single Task.

        '''
        if (
            len(selection) != 1 or
            selection[0]['entityType'] != 'task'
        ):
            return False

        entity = selection[0]
        task = ftrack.Task(entity['entityId'])

        if task.getObjectType() != 'Task':
            return False

        return True

    def register(self):
        '''Override register to filter discover actions on logged in user.'''
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
        '''Return discovered applications.'''
        if not self.isValidSelection(
            event['data'].get('selection', [])
        ):
            return

        items = []
        applications = self.applicationStore.applications
        applications = sorted(
            applications, key=lambda application: application['label']
        )

        for application in applications:
            applicationIdentifier = application['identifier']
            label = application['label']
            items.append({
                'actionIdentifier': self.identifier,
                'label': label,
                'icon': application.get('icon', 'default'),
                'applicationIdentifier': applicationIdentifier
            })

        return {
            'items': items
        }

    def launch(self, event):
        '''Handle *event*.

        event['data'] should contain:

            *applicationIdentifier* to identify which application to start.

        '''
        # Prevent further processing by other listeners.
        event.stop()

        if not self.isValidSelection(
            event['data'].get('selection', [])
        ):
            return

        applicationIdentifier = (
            event['data']['applicationIdentifier']
        )

        context = event['data'].copy()
        context['source'] = event['source']

        applicationIdentifier = event['data']['applicationIdentifier']
        context = event['data'].copy()
        context['source'] = event['source']

        return self.launcher.launch(
            applicationIdentifier, context
        )


class LegacyApplicationStore(ftrack_connect.application.ApplicationStore):
    '''Discover and store available applications on this host.'''

    def _discoverApplications(self):
        '''Return a list of applications that can be launched from this host.

        An application should be of the form:

            dict(
                'identifier': 'name_version',
                'label': 'Name version',
                'path': 'Absolute path to the file',
                'version': 'Version of the application',
                'icon': 'URL or name of predefined icon'
            )

        '''
        applications = []

        if sys.platform == 'darwin':
            prefix = ['/', 'Applications']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Autodesk', 'maya.+', 'Maya.app'],
                label='Maya {version}',
                applicationIdentifier='maya_{version}',
                icon='maya'
            ))

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Hiero\d.+', 'Hiero\d.+.app'],
                label='Hiero {version}',
                applicationIdentifier='hiero_{version}',
                icon='hiero'
            ))

        elif sys.platform == 'win32':
            prefix = ['C:\\', 'Program Files.*']

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Autodesk', 'Maya.+', 'bin', 'maya.exe'],
                label='Maya {version}',
                applicationIdentifier='maya_{version}',
                icon='maya'
            ))

            applications.extend(self._searchFilesystem(
                expression=prefix + ['Hiero\d.+', 'hiero.exe'],
                label='Hiero {version}',
                applicationIdentifier='hiero_{version}',
                icon='hiero'
            ))

            # Somewhere along the way The Foundry changed the default install directory.
            # Add the old directory as expression to find old installations of Hiero
            # as well.
            #
            # TODO: Refactor this once ``_searchFilesystem`` is more sophisticated.
            applications.extend(self._searchFilesystem(
                expression=prefix + ['The Foundry', 'Hiero\d.+', 'hiero.exe'],
                label='Hiero {version}',
                applicationIdentifier='hiero_{version}',
                icon='hiero'
            ))

        elif sys.platform == 'linux2':
            maya_version_expression = re.compile(
                r'maya(?P<version>\d{4})'
            )

            applications.extend(self._searchFilesystem(
                expression=['/', 'usr', 'autodesk', 'maya.+', 'bin', 'maya$'],
                versionExpression=maya_version_expression,
                label='Maya {version}',
                applicationIdentifier='maya_{version}',
                icon='maya'
            ))

            applications.extend(self._searchFilesystem(
                versionExpression=r'Hiero(?P<version>.*)\/.+$',
                expression=['/', 'usr', 'local', 'Hiero.*', 'bin', 'Hiero\d.+'],
                label='Hiero {version}',
                applicationIdentifier='hiero_{version}',
                icon='hiero'
            ))

        self.logger.debug(
            'Discovered applications:\n{0}'.format(
                pprint.pformat(applications)
            )
        )

        return applications


class LegacyApplicationLauncher(
    ftrack_connect.application.ApplicationLauncher
):
    '''Launch applications with legacy plugin support.'''

    def __init__(self, applicationStore, legacyPluginsPath):
        '''Instantiate launcher with *applicationStore* of applications.

        *applicationStore* should be an instance of :class:`ApplicationStore`
        holding information about applications that can be launched.

        *legacyPluginsPath* should be the path where the legacy plugins are
        located.

        '''
        super(LegacyApplicationLauncher, self).__init__(applicationStore)
        self.legacyPluginsPath = legacyPluginsPath
        self.logger.debug('Legacy plugin path: {0}'.format(
            self.legacyPluginsPath
        ))

    def _getApplicationLaunchCommand(self, application, context=None):

        command = super(
            LegacyApplicationLauncher, self
        )._getApplicationLaunchCommand(
            application, context
        )

        applicationIdentifier = application['identifier']

        isMaya = applicationIdentifier.startswith('maya')
        if isMaya:
            entity = context['selection'][0]
            task = ftrack.Task(entity['entityId'])
            filename = self.getFilename(task)
            if filename:
                command.append('-file')
                command.append(filename)

        if os.path.exists('/usr/bin/optirun'):
            command.insert(0, '/usr/bin/optirun')
        return command

    def _getApplicationEnvironment(self, application, context):
        '''Modify and return environment with legacy plugins added.'''
        environment = super(
            LegacyApplicationLauncher, self
        )._getApplicationEnvironment(
            application, context
        )

        applicationIdentifier = application['identifier']

        isMaya = applicationIdentifier.startswith('maya')
        isHiero = (
            applicationIdentifier.startswith('hiero') and
            'player' not in applicationIdentifier
        )
        if (
            os.path.isdir(self.legacyPluginsPath) and
            (isMaya or isHiero)
        ):
            entity = context['selection'][0]
            task = ftrack.Task(entity['entityId'])
            taskParent = task.getParent()

            try:
                environment['FS'] = str(int(taskParent.getFrameStart()))
            except Exception:
                environment['FS'] = '1'

            try:
                environment['FE'] = str(int(taskParent.getFrameEnd()))
            except Exception:
                environment['FE'] = '1'

            environment['FTRACK_TASKID'] = task.getId()
            environment['FTRACK_SHOTID'] = task.get('parent_id')

            includeFoundryAssetManager = False

            # Append legacy plugin base to PYTHONPATH.
            environment = ftrack_connect.application.appendPath(
                self.legacyPluginsPath, 'PYTHONPATH', environment
            )

            # Load Hiero plugins if application is Hiero.
            if isHiero:
                hieroPluginPath = os.path.join(
                    self.legacyPluginsPath, 'ftrackHieroPlugin'
                )

                environment = ftrack_connect.application.appendPath(
                    hieroPluginPath, 'HIERO_PLUGIN_PATH', environment
                )

                includeFoundryAssetManager = True

            # Load Maya specific environment such as legacy plugins.
            if isMaya:
                mayaPluginPath = os.path.join(
                    self.legacyPluginsPath, 'ftrackMayaPlugin'
                )
                filename = self.getFilename(task)

                if filename:
                    environment['MAYA_FILE'] = filename
                    environment['PROJECT_DIR'] = os.path.dirname(os.path.dirname(filename))

                environment = ftrack_connect.application.appendPath(
                    mayaPluginPath, 'MAYA_PLUG_IN_PATH', environment
                )
                environment = ftrack_connect.application.appendPath(
                    mayaPluginPath, 'MAYA_SCRIPT_PATH', environment
                )
                environment = ftrack_connect.application.appendPath(
                    mayaPluginPath, 'PYTHONPATH', environment
                )

            # Add the foundry asset manager packages if application is
            # Nuke, NukeStudio or Hiero.
            if includeFoundryAssetManager:
                foundryAssetManagerPluginPath = os.path.join(
                    self.legacyPluginsPath, 'ftrackProvider'
                )

                environment = ftrack_connect.application.appendPath(
                    foundryAssetManagerPluginPath,
                    'FOUNDRY_ASSET_PLUGIN_PATH',
                    environment
                )

                foundryAssetManagerPath = os.path.join(
                    self.legacyPluginsPath,
                    'theFoundry'
                )

                environment = ftrack_connect.application.prependPath(
                    foundryAssetManagerPath, 'PYTHONPATH', environment
                )

        return environment

    def getFilename(self, task):
        metadata = task.getMeta()
        if 'filename' in metadata:
            return metadata['filename']
        else:
            return ''


def register(registry, **kw):
    '''Register hooks for ftrack connect legacy plugins.'''

    logger = logging.getLogger(
        'ftrack_plugin:ftrack_connect_legacy_plugins_hook.register'
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

    # Create store containing applications.
    applicationStore = LegacyApplicationStore()

    launcher = LegacyApplicationLauncher(
        applicationStore,
        legacyPluginsPath=os.environ.get(
            'FTRACK_PYTHON_LEGACY_PLUGINS_PATH',
            os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), '..'
                )
            )
        )
    )

    # Create action and register to respond to discover and launch events.
    action = LaunchAction(applicationStore, launcher)
    action.register()
