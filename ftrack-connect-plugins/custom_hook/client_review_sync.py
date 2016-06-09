import os
import ftrack_api
import threading
import logging
import json
import time


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


def startRemoteSession():
    remoteSession = ftrack_api.Session(
        server_url='https://locovfx.ftrackapp.com',
        api_user='djw.ninedegrees@gmail.com',
        api_key='d8d1dee0-2ca9-11e6-b627-f23c91df2148'
    )
    return remoteSession


class ReviewSync(object):

    label = 'Review Sync'
    identifier = 'com.ftrack.reviewSync'
    description = 'Sync Client Review Session to cloud account'

    def __init__(self, session):
        """Initialise action handler"""
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = session

    def getFileToUpload(self, metadata):
        filename = ''
        if 'source_file' in metadata:
            filename = str(metadata['source_file'])
        if os.path.exists(filename):
            return filename
        return None

    @async
    def prepRemoteSession(self, reviewSession):
        """Prep cloud ftrack server with project name and review session"""
        # TODO: Job notification should show for multiple users
        user = self.session.query('User where username is Natasha').one()
        localJob = self.session.create('Job', {
            'user': user,
            'status': 'running',
            'data': json.dumps({
                'description': 'Sync Started'
            })
        })
        self.session.commit()
        remoteSession = startRemoteSession()
        project = reviewSession['project']

        try:
            remoteProject = remoteSession.query('Project where name is {0}'.format(project['name'])).one()
        except Exception:
            remoteProject = remoteSession.create('Project', {
                'name': project['name'],
                'full_name': project['full_name'],
                'project_schema': project['project_schema']
            })
            remoteSession.commit()

        try:
            remoteFolder = remoteSession.query('Folder where name is "{0}" and '
                                               'parent.id is {1}'.format(reviewSession['name'],
                                                                         remoteProject['id'])).one()
        except Exception:
            remoteFolder = remoteSession.create('Folder', {
                'name': reviewSession['name'],
                'parent': remoteProject
            })

        # TODO: Possibly delete older existing session before creating new one?
        remoteReviewSession = remoteSession.create('ReviewSession', {
            'name': reviewSession['name'],
            'description': reviewSession['description'],
            'project': remoteProject
        })
        remoteSession.commit()

        for reviewObject in reviewSession['review_session_objects']:
            self.uploadToRemoteFtrack(remoteSession, reviewObject, remoteProject,
                                      remoteFolder, remoteReviewSession, localJob)
        localJob['status'] = 'done'
        self.session.commit()

    def uploadToRemoteFtrack(self, remoteSession, reviewObject, remoteProject,
                             remoteFolder, remoteReviewSession, localJob):
        """Upload asset versions to remote cloud account"""

        assetVersion = reviewObject['asset_version']
        fileToUpload = self.getFileToUpload(assetVersion['metadata'])
        if not fileToUpload:
            localJob['data'] = json.dumps({'description':'file not found'})
            localJob['status'] = 'failed'
            self.session.commit()
            return
        defaultShotStatus = remoteProject['project_schema'].get_statuses('Shot')[0]
        # Create a shot under remoteFolder
        try:
            remoteShot = remoteSession.query('Shot where name is "{0}" and '
                                             'parent.name is "{1}"'.format(reviewObject['name'],
                                                                         remoteFolder['name'])).one()
        except Exception:
            remoteShot = remoteSession.create('Shot', {
                'name': reviewObject['name'],
                'parent': remoteFolder,
                'status': defaultShotStatus
            })

        assetType = remoteSession.query('AssetType where name is Upload').one()
        # Create an asset called Client Review
        try:
            remoteAsset = remoteSession.query('Asset where name is "Client Review" and '
                                              'parent.id is {0}'.format(remoteShot['id'])).one()
        except Exception:
            remoteAsset = remoteSession.create('Asset', {
                'name': 'Client Review',
                'parent': remoteShot,
                'type': assetType
            })
        remoteVersion = remoteSession.create('AssetVersion', {
            'asset': remoteAsset,
            'comment': 'Version for client review'
        })
        versionMeta = {
            'source_asset_id': assetVersion['id']
        }
        remoteVersion['metadata'] = versionMeta
        remoteSession.commit()

        try:
            self.uploadAndAddToReview(remoteSession, fileToUpload, remoteVersion, remoteReviewSession,
                                      remoteShot)
        except Exception:
            localJob['status'] = 'failed'
            self.session.commit()

    @async
    def uploadAndAddToReview(self, remoteSession, fileToUpload, remoteVersion,
                             remoteReviewSession, remoteShot):

        #Upload file
        job = remoteSession.encode_media(fileToUpload)
        jobData = job['data']
        jobId = job['id']
        jobStatus = job['status']

        while jobStatus != 'done':
            time.sleep(1)
            remoteSession.reset()
            j = remoteSession.query('Job where id is {0}'.format(jobId)).one()
            jobStatus = j['status']
            print jobStatus
        job_data = json.loads(jobData)
        for output in job_data['output']:
            component = remoteSession.get('FileComponent', output['component_id'])

            # Add component to version.
            component['version_id'] = remoteVersion['id']

            if output['format'] == 'image/jpeg':
                remoteVersion['thumbnail_id'] = output['component_id']

        #Add version to review session
        remoteReviewSessionObj = remoteSession.create('ReviewSessionObject',{
            'review_session': remoteReviewSession,
            'asset_version': remoteVersion,
            'name': remoteShot['name'],
            'version': 'Version {0}'.format(remoteVersion['version'])
        })
        remoteSession.commit()

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
                    'actionIdentifier': self.identifier
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

        self.prepRemoteSession(reviewSession)

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
    action = ReviewSync(session)
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events
    session.event_hub.wait()
