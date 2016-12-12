import os
import threading
import subprocess
import ftrack
import logging


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class FileSync(ftrack.Action):

    label = 'File Sync'
    identifier = 'com.ftrack.fileSync'
    description = 'Sync files/folders between JBH & CPT'

    def __init__(self):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    @async
    def cptSync(self, xferFile, xferValue, user):
        # Remove trailing '/'
        print user
        xferFile = xferFile.rstrip('/')
        rsyncCmd = ''

        job = ftrack.createJob(
            'Syncing {0}'.format(xferFile),
            'queued', user)
        job.setStatus('running')

        if xferValue == 0:
            # CPT -> JHB
            jhbDir = os.path.dirname(xferFile)
            if not os.path.exists(jhbDir):
                os.makedirs(jhbDir)
            rsyncCmd = 'rsync -avuzrh server@192.168.2.5:%s %s/' % (xferFile, jhbDir)
        elif xferValue == 1:
            # JHB -> CPT
            cptDir = os.path.dirname(xferFile)
            rsyncCmd = 'rsync -avuzrh --rsync-path="mkdir -p %s && rsync" %s server@192.168.2.5:%s/' % (
                cptDir, xferFile, cptDir)
        print '\n' + rsyncCmd
        process = subprocess.Popen(rsyncCmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        logging.info(out)
        exitcode = process.returncode
        if str(exitcode) != '0':
            job.setDescription('Sync Failed for {0}'.format(xferFile))
            job.setStatus('failed')
        else:
            job.setDescription('Sync Complete')
            job.setStatus('done')

    def register(self):
        """Register discover actions on logged in user."""
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover',
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
                self.identifier
            ),
            self.launch
        )

    def discover(self, event):
        """
        Return action config if triggered on a single selection.
        """
        selection = event['data'].get('selection', [])

        if not selection:
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon': 'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-events/icons/repeat-1.png'
            }]
        }

    def launch(self, event):
        """
        Called when action is executed
        """
        selection = event['data'].get('selection', [])
        user = ftrack.User(id=event['source']['user']['id'])

        if 'values' in event['data']:
            values = event['data']['values']
            path = values['file_path']
            value = values['xfer_loc']
            #if os.path.exists(path):
            self.cptSync(path, value, user)
            return {
                'success': True,
                'message': 'Starting File Sync'
            }
            '''else:
                return {
                    'success': False,
                    'message': 'Unable to start sync'
                }'''


        return {
            'items': [{
                    'value': '##{0}##'.format('Enter a file/folder to transfer.'.capitalize()),
                    'type': 'label'
                }, {
                    'label': 'Path:',
                    'type': 'text',
                    'value': '',
                    'name': 'file_path'
                }, {
                    'label':'Transfer Location:',
                    'type':'enumerator',
                    'value': 0,
                    'name':'xfer_loc',
                    'data':[{
                        'label': 'CPT -> JHB',
                        'value': 0
                    }, {
                        'label': 'JHB -> CPT',
                        'value': 1
                    }]
                }]
            }




def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.fileSync'
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

    action = FileSync()
    action.register()


logging.basicConfig(level=logging.INFO)
ftrack.setup()
action = FileSync()
action.register()

# Wait for events
ftrack.EVENT_HUB.wait()