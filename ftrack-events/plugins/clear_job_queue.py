import ftrack_api
import logging
import os


class ClearQueue(object):

    label = 'Clear Job Queue'
    identifier = 'com.ftrack.clearQueue'
    description = 'Clears the job queue'

    def __init__(self, session):
        """Initialise action handler"""
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = session

    def register(self):
        """Register discover actions on logged in user."""
        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover',
            self.discover
        )

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
                self.identifier
            ),
            self.launch
        )

    def discover(self, event):
        """
        Return action config if triggered on a single selection.
        """
        selection = event['data']['selection']

        if not selection:
            return

        return{
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon': 'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-events/icons/folder-10.png'
            }]
        }

    def launch(self, event):
        """
        Called when action is executed
        """
        user = event['source']['user']

        jobs = self.session.query('Job where status is running and user_id is %s' % user['id']).all()
        for job in jobs:
            job['status'] = 'done'

        self.session.commit()

        return {
            'success': True,
            'message': 'Action launched successfully'
        }


def register(session, **kw):
    """
    Register plugin.
    """

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    action = ClearQueue(session)
    action.register()


logging.basicConfig(level=logging.INFO)
session = ftrack_api.Session(
    server_url=os.environ['FTRACK_SERVER'],
    api_user=os.environ['FTRACK_API_USER'],
    api_key=os.environ['FTRACK_API_KEY']
)
register(session)

# Wait for events
session.event_hub.wait()