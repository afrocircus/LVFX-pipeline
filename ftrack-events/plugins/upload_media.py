import logging
import os
import threading
import ftrack
import subprocess
import json


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class UploadMedia(ftrack.Action):

    label = 'Upload Media'
    identifier = 'com.ftrack.uploadMedia'
    description = 'Upload media to task'

    def __init__(self):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def deleteFiles(self, outfilemp4, outfilewebm, thumbnail):
        if os.path.exists(outfilemp4):
            os.remove(outfilemp4)
        if os.path.exists(outfilewebm):
            os.remove(outfilewebm)
        if os.path.exists(thumbnail):
            os.remove(thumbnail)

    def createThumbnail(self, inputFile, outputFile):
        cmd = 'ffmpeg -y -i "%s" -vf  "thumbnail,scale=640:360" -frames:v 1 "%s"' % (inputFile, outputFile)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        process.wait()

    def convertMp4Files(self, inputFile, outfilemp4):
        mp4cmd = 'ffmpeg -y -i "%s" -ac 2 -b:v 2000k -c:a aac -c:v libx264 ' \
                 '-pix_fmt yuv420p -g 30 -vf scale="trunc((a*oh)/2)*2:720" ' \
                 '-b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 "%s"' % (inputFile, outfilemp4)
        process = subprocess.Popen(mp4cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        process.wait()


    def convertWebmFiles(self, inputFile, outfilewebm):
        webmcmd = 'ffmpeg -y -i "%s" -qscale:a 6 -g 30 -ac 2 -c:a libvorbis ' \
                  '-c:v libvpx -pix_fmt yuv420p -b:v 2000k -vf scale="trunc((a*oh)/2)*2:720" ' \
                  '-crf 5 -qmin 0 -qmax 50 -f webm "%s"' % (inputFile, outfilewebm)
        process = subprocess.Popen(webmcmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        process.wait()

    def getFrameLength(self, filename):
        cmd = 'ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames ' \
              '-of default=nokey=1:noprint_wrappers=1 {0}'.format(filename)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        output = process.communicate()
        firstFrame = 1
        lastFrame = firstFrame + int(output[0])
        return firstFrame, lastFrame

    def createAttachment(self, version, name, outfile, framein, frameout, framerate, meta):
        location = ftrack.Location('ftrack.server')
        component = version.createComponent(name=name, path=outfile, location=location)
        metaData = json.dumps({
            'frameIn': framein,
            'frameOut': frameout,
            'frameRate': framerate
        })
        component.setMeta(key='ftr_meta', value=metaData)
        version.setMeta(meta)
        version.publish()

    def prepMediaFiles(self, outputFile):
        outfilemp4 = os.path.splitext(outputFile)[0] + '.mp4'
        outfilewebm = os.path.splitext(outputFile)[0] + '.webm'
        thumbnail = os.path.join(os.path.split(outputFile)[0], 'thumbnail.png')
        metadata = {
            'source_file': outputFile
            }
        return outfilemp4, outfilewebm, thumbnail, metadata

    def convertFiles(self, inputFile, outfilemp4, outfilewebm):
        self.convertMp4Files(inputFile, outfilemp4)
        self.convertWebmFiles(inputFile, outfilewebm)
        if os.path.exists(outfilemp4) and os.path.exists(outfilewebm):
            return True
        else:
            return False

    def getAsset(self, shot, assetName):
        assetType = ftrack.AssetType('Upload')
        try:
            asset = shot.getAsset(assetName, assetType)
        except:
            asset = shot.createAsset(assetName, assetType)
        return asset

    @async
    def uploadToFtrack(self, filename, taskid, shot, user):
        job = ftrack.createJob(
            'Uploading media for shot {0}'.format(shot.getName()),
            'queued', user)
        job.setStatus('running')
        filename = '/' + filename.strip('file:/')
        outfilemp4, outfilewebm, thumbnail, metadata = self.prepMediaFiles(filename)
        ff, lf = self.getFrameLength(filename)
        result = self.convertFiles(filename, outfilemp4, outfilewebm)
        status = ftrack.Status('Pending Internal Review')
        if result:
            self.createThumbnail(outfilemp4, thumbnail)
            asset = self.getAsset(shot, 'ReviewAsset')
            version = asset.createVersion('Upload for Internal Review', taskid)
            try:
                self.createAttachment(version, 'ftrackreview-mp4', outfilemp4, ff, lf, 24, metadata)
                self.createAttachment(version, 'ftrackreview-webm', outfilewebm, ff, lf, 24, metadata)
            except:
                job.setDescription('Failed to Upload Media')
                job.setStatus('failed')
                return
            version.createComponent(name='movie', path=filename)
            version.publish()
            version.setStatus(status)
            if os.path.exists(thumbnail):
                try:
                    attachment = version.createThumbnail(thumbnail)
                    shot.setThumbnail(attachment)
                except:
                    job.setDescription('Failed to Upload Thumbnail')
                    self.deleteFiles(outfilemp4, outfilewebm, thumbnail)
                    return
        self.deleteFiles(outfilemp4, outfilewebm, thumbnail)
        job.setDescription('Upload complete for shot {0}'.format(shot.getName()))
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

        task = ftrack.Task(id=selection[0]['entityId'])
        if selection[0]['entityType'] == 'task' and task.get('objecttypename') == 'Task':
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
        selection = event['data'].get('selection', [])
        user = ftrack.User(id=event['source']['user']['id'])
        task = ftrack.Task(id=selection[0]['entityId'])
        shot = task.getParent()

        if 'values' in event['data']:
            values = event['data']['values']
            self.uploadToFtrack(values['file_path'], selection[0]['entityId'], shot, user)
            return {
                'success': True,
                'message': 'Action completed successfully'
            }

        return {
            'items': [{
                    'value': '##{0}##'.format('File Path'.capitalize()),
                    'type': 'label'
                }, {
                    'label': 'Name',
                    'type': 'text',
                    'value': '',
                    'name': 'file_path'
                }]
            }




def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.uploadMedia'
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

    action = UploadMedia()
    action.register()


logging.basicConfig(level=logging.INFO)
ftrack.setup()
action = UploadMedia()
action.register()

# Wait for events
ftrack.EVENT_HUB.wait()