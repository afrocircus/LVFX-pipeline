import ftrack_api
import logging
import threading
import urllib
import os
import sys


'''RESOURCE_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'resource')
)

if RESOURCE_DIRECTORY not in sys.path:
    sys.path.append(RESOURCE_DIRECTORY)


import config'''


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


def startRemoteSession():
    remoteSession = ftrack_api.Session(
        server_url=os.environ['REMOTE_FTRACK_SERVER'],
        api_user=os.environ['REMOTE_FTRACK_API_USER'],
        api_key=os.environ['REMOTE_FTRACK_API_KEY']
    )
    return remoteSession


class TransferFeedback(object):

    label = 'Feedback Sync'
    identifier = 'com.ftrack.feedbackSync'
    description = 'Sync client feedback from cloud account'

    def __init__(self, session):
        """Initialise action handler"""
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = session

    @async
    def startTransfer(self, reviewSession):

        remoteSession = startRemoteSession()
        try:
            remoteReviewSession = remoteSession.query('ReviewSession where name is "{0}"'.format(
                reviewSession['name'])).one()
        except Exception:
            print "No such review session found"
            return

        remoteReviewObjects = remoteReviewSession['review_session_objects']

        for remoteObject in remoteReviewObjects:
            remoteVersion = remoteObject['asset_version']
            localVersionId = remoteVersion['metadata']['source_asset_id']
            localVersion = self.session.query('AssetVersion where id is {0}'.format(localVersionId)).one()
            category = self.session.query('NoteCategory where name is "Client"').first()
            # Using David as the author for all client notes.
            user = self.session.query('User where username is djw').one()
            remoteNotes = remoteVersion['notes']
            remoteLocation = remoteSession.query('Location where name is "ftrack.server"').one()
            localLocation = self.session.query('Location where name is "ftrack.server"').one()
            localApprovedStatusObj = self.session.query('Status where name is Approved').one()
            localReviewStatusObj = self.session.query('Status where name is "Review Changes"').one()

            # Add all notes from remote asset version to the corresponding local asset version.
            for remoteNote in remoteNotes:
                # Don't add note if it's a reply
                if remoteNote['in_reply_to']:
                    break
                # Create a new note
                note = self.session.create('Note', {
                    'content': remoteNote['content'],
                    'author': user,
                    'category': category
                })
                # Add note to the beginning of the list
                localVersion['notes'].insert(0,note)
                # If the remote note has attachments then transfer those as well
                for remoteNoteComponent in remoteNote['note_components']:
                    try:
                        # Get the URL of the remote attachment
                        remoteURL = remoteLocation.get_url(remoteNoteComponent['component'])
                        testFile = urllib.URLopener()
                        saveFile = '/tmp/note.jpg'
                        # Download the attachment
                        testFile.retrieve(remoteURL, saveFile)
                        # Create a new component and with the new attachment
                        component = self.session.create(
                            saveFile,
                            data={'name':remoteNoteComponent['component']['name']},
                            location = localLocation
                        )
                        # add this component to the note on the local asset version.
                        self.session.create(
                            'NoteComponent',
                            {'component_id': component['id'], 'note_id': note['id']}
                        )
                        if os.path.exists(saveFile):
                            os.remove(saveFile)
                    except Exception:
                        print "Note not found at location"

            # Update the task status to that of the asset version.
            if len(remoteObject['statuses']) > 0:
                status = remoteObject['statuses'][-1]['status'] #latest status
                if status == 'approved':
                    statusObj = localApprovedStatusObj
                else:
                    statusObj = localReviewStatusObj

                localVersion['status'] = statusObj
                if localVersion['task']:
                    localVersion['task']['status'] = statusObj

        self.session.commit()

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

        if selection[0]['entityType'] == 'reviewsession':
            return {
                'items': [{
                    'label': self.label,
                    'actionIdentifier': self.identifier,
                    'icon': 'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-events/icons/cloud-computing-14.png'
                }]
            }
        else:
            return

    def launch(self, event):
        """
        Called when action is executed
        """
        selection = event['data']['selection']

        reviewSession = self.session.query('ReviewSession where id is {0}'.format(
            selection[0]['entityId'])).one()

        self.startTransfer(reviewSession)

        return {
            'success': True,
            'message': 'Action completed successfully'
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
    action = TransferFeedback(session)
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
