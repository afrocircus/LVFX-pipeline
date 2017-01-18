import os
import re
import ftrack_api
import threading
import logging
import json
import time
import urllib
import getpass


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

    def getComponentFilename(self, location, component, assetVersionId, ext):
        try:
            url = location.get_url(component)
            testFile = urllib.URLopener()
            filename = '/tmp/{0}.{1}'.format(assetVersionId, ext)
            testFile.retrieve(url, filename)
        except Exception:
            filename = ''
        return filename

    def version_get(self, string, prefix):
        """
        Extract version information from filenames.
        Code from Foundry's nukescripts.version_get()
        """
        if string is None:
            raise ValueError("Empty version string - no match")

        regex = "[/_.]"+prefix+"\d+"
        matches = re.findall(regex, string, re.IGNORECASE)
        if not len(matches):
            msg = "No \"_"+prefix+"#\" found in \""+string+"\""
            raise ValueError(msg)
        return (matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group())

    def getFileToUpload(self, metadata, assetVersion):
        filename = ''
        location = self.session.query('Location where name is "ftrack.server"').one()
        if 'source_file' in metadata and os.path.exists(str(metadata['source_file'])):
            filename = str(metadata['source_file'])
        else:
            for component in assetVersion['components']:
                if component['name'] == 'ftrackreview-mp4':
                    filename = self.getComponentFilename(location, component, assetVersion['id'], 'mov')
                    break
                if component['name'] == 'ftrackreview-image':
                    filename = self.getComponentFilename(location, component, assetVersion['id'], 'jpeg')
                    break
        if os.path.exists(filename):
            try:
                version = 'v' + self.version_get(filename, 'v')[1]
            except Exception:
                version = 'v01'
            return version, filename
        return None, None

    @async
    def prepRemoteSession(self, reviewSession, username):
        """Prep cloud ftrack server with project name and review session"""
        user = self.session.query('User where username is {0}'.format(username)).one()
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

        # Delete older existing session before creating new one
        try:
            remoteReviewSession = remoteSession.query('ReviewSession where name is "{0}"'.format(
                reviewSession['name']
            )).one()
            remoteSession.delete(remoteReviewSession)
        except Exception:
            logging.info( "Creating a new review session")

        remoteReviewSession = remoteSession.create('ReviewSession', {
            'name': reviewSession['name'],
            'description': reviewSession['description'],
            'project': remoteProject
        })
        remoteSession.commit()

        for reviewObject in reviewSession['review_session_objects']:
            localJob['data'] = json.dumps({'description': 'Syncing {0}'.format(reviewObject['name'])})
            self.session.commit()
            self.uploadToRemoteFtrack(remoteSession, reviewObject, remoteProject,
                                      remoteFolder, remoteReviewSession, localJob)

        if localJob['status'] != 'failed':
            localJob['status'] = 'done'
            localJob['data'] = json.dumps({
                'description': 'Sync Completed'
            })
        self.session.commit()

    def uploadToRemoteFtrack(self, remoteSession, reviewObject, remoteProject,
                             remoteFolder, remoteReviewSession, localJob):
        """Upload asset versions to remote cloud account"""

        assetVersion = reviewObject['asset_version']
        version, fileToUpload = self.getFileToUpload(assetVersion['metadata'], assetVersion)
        if not fileToUpload:
            localJob['data'] = json.dumps({'description':'file not found'})
            localJob['status'] = 'failed'
            self.session.commit()
            return
        defaultShotStatus = remoteProject['project_schema'].get_statuses('Shot')[0]
        # Create a shot under remoteFolder
        try:
            remoteShot = remoteSession.query('Shot where name is "{0}_{1}" and '
                                             'parent.name is "{2}"'.format(reviewObject['name'],
                                                                           version, remoteFolder['name'])).one()
        except Exception:
            remoteShot = remoteSession.create('Shot', {
                'name': '{0}_{1}'.format(reviewObject['name'], version),
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

        try:
            remoteSession.commit()
        except Exception:
            localJob['status'] = 'failed'
            self.session.commit()
            logging.error("serverError for {0}_{1}".format(reviewObject['name'], version))

        try:
            self.uploadAndAddToReview(remoteSession, fileToUpload, remoteVersion, remoteReviewSession,
                                      remoteShot)
        except Exception:
            localJob['status'] = 'failed'
            self.session.commit()

    def uploadAndAddToReview(self, remoteSession, fileToUpload, remoteVersion,
                             remoteReviewSession, remoteShot):

        #Upload file
        print "encoding %s" % fileToUpload
        job = remoteSession.encode_media(fileToUpload)
        jobData = job['data']
        jobId = job['id']
        jobStatus = job['status']

        while jobStatus != 'done':
            time.sleep(1)
            remoteSession.reset()
            j = remoteSession.query('Job where id is {0}'.format(jobId)).one()
            jobStatus = j['status']
            logging.info(jobStatus)
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
                    'actionIdentifier': self.identifier,
                    'icon': 'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-events/icons/cloud-computing-13.png'
                }]
            }
        else:
            return

    def launch(self, event):
        """
        Called when action is executed
        """
        selection = event['data']['selection']
        username = event['source']['user']['username']

        reviewSession = self.session.query('ReviewSession where id is {0}'.format(
            selection[0]['entityId'])).one()

        self.prepRemoteSession(reviewSession, username)

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
    action = ReviewSync(session)
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
