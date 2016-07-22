import logging
import datetime
import re
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
        thumbnail = os.path.splitext(outputFile)[0]+ '_thumbnail' + '.png'
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

    def publishImage(self, filename, taskid, shot, job):
        asset = self.getAsset(shot, 'ReviewAsset')
        status = ftrack.Status('Pending Internal Review')
        meta = {
            'source_file': filename
        }
        version = asset.createVersion('Upload for Internal Review', taskid)
        location = ftrack.Location('ftrack.server')
        try:
            component = version.createComponent(name='ftrackreview-image', path=filename, location=location)
            metaData = json.dumps({
                'format': 'image'
            })
            component.setMeta(key='ftr_meta', value=metaData)
            version.setMeta(meta)
            version.createComponent(name='movie', path=filename)
            version.publish()
        except:
            job.setDescription('Failed to Upload Media')
            job.setStatus('failed')
            return
        version.setStatus(status)
        try:
            attachment = version.createThumbnail(filename)
            task = ftrack.Task(taskid)
            task.setThumbnail(attachment)
        except:
            job.setDescription('Failed to Upload Thumbnail')
            job.setStatus('failed')
            return
        job.setDescription('Upload complete for shot {0}'.format(shot.getName()))
        job.setStatus('done')

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
        return matches[-1:][0][1], re.search("\d+", matches[-1:][0]).group()

    def addSlateToMedia(self, filename, taskid, shot, user):
        # Create a slate
        projectName = shot.getProject().getName()
        shotName = shot.getName()
        taskName = ftrack.Task(taskid).getName()
        try:
            version = 'v' + self.version_get(filename, 'v')[1]
        except:
            version = 'v01'
        artist = user.getUsername()
        today = datetime.datetime.today()
        date = '%d-%02d-%02d' % (today.year, today.month, today.day)
        shotInfo = '{0} | {1} | {2} | {3} | {4}'.format(projectName, shotName, taskName, version, artist)
        slateFolder, outfileName = os.path.split(filename)
        fname,fext = os.path.splitext(outfileName)

        # get Img size
        ffprobecmd = 'ffprobe -v error -of flat=s=_ -select_streams v:0 ' \
                     '-show_entries stream=height,width {0}'.format(filename)
        process = subprocess.Popen(ffprobecmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        try:
            output = process.communicate()[0]
            parts = output.split('\n')
            width = parts[0].split('=')[-1]
            height = parts[1].split('=')[-1]
        except:
            width = 1920
            height = 1080
        size = '{0}x{1}'.format(width, height)

        # generate slate
        slate = os.path.join(slateFolder, 'slate.png')
        slateCmd = 'convert -size {0} xc:transparent -font Palatino-Bold -pointsize 32 ' \
                   '-fill white -gravity NorthWest -annotate +25+25 "{1}" ' \
                   '-gravity NorthEast -annotate +25+25 "{2}" -gravity SouthEast ' \
                   '{3}'.format(size, shotInfo, date, slate)
        process = subprocess.Popen(slateCmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        process.wait()

        # overlay slate on movie
        slateMov = os.path.join(slateFolder, '{0}_slate{1}'.format(fname, fext))
        ffmpegSlate = 'ffmpeg -y -i {0} -i {1} -filter_complex "overlay=5:5" {2}'.format(filename,
                                                                                      slate, slateMov)
        process = subprocess.Popen(ffmpegSlate, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        process.wait()

        if fext in ['.jpeg', '.jpg', '.png', '.bmp', '.dpx']:
            if os.path.exists(slate):
                os.remove(slate)
            return slateMov

        #overlay frame nos
        slateMovFinal = os.path.join(slateFolder, '{0}_slate_final{1}'.format(fname, fext))
        ffmpegFrames = 'ffmpeg -y -i %s -vf "drawtext=fontfile=/usr/share/fonts/dejavu/DejaVuSans.ttf:' \
                       'fontsize=32:text=%%{n}: x=(w-tw)-50: y=h-(2*lh):fontcolor=white: box=1:' \
                       'boxcolor=0x00000099" %s' % (slateMov, slateMovFinal)

        process = subprocess.Popen(ffmpegFrames, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        process.wait()

        if os.path.exists(slate):
            os.remove(slate)
        if os.path.exists(slateMov):
            os.remove(slateMov)
        return slateMovFinal


    @async
    def uploadToFtrack(self, filename, addSlate, taskid, shot, user):
        job = ftrack.createJob(
            'Uploading media for shot {0}'.format(shot.getName()),
            'queued', user)
        job.setStatus('running')
        filename = '/' + filename.strip('file:/')
        fname, fext = os.path.splitext(filename)

        if addSlate == 'Yes':
            job.setDescription('Adding slate for shot {0}'.format(shot.getName()))
            slateFile = self.addSlateToMedia(filename, taskid, shot, user)
            if os.path.exists(slateFile):
                filename = slateFile
                job.setDescription('Uploading media for shot {0}'.format(shot.getName()))

        # If file is an image
        if fext in ['.jpeg', '.jpg', '.png', '.bmp', '.dpx']:
            self.publishImage(filename, taskid, shot, job)
            return

        # if file is a movie
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
                    task = ftrack.Task(taskid)
                    task.setThumbnail(attachment)
                except:
                    job.setDescription('Failed to Upload Thumbnail')
                    job.setStatus('failed')
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
                    'actionIdentifier': self.identifier,
                    'icon': 'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-events/icons/image-13.png'
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
            self.uploadToFtrack(values['file_path'], values['add_slate'], selection[0]['entityId'], shot, user)
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
                }, {
                    'label':'Add Slate',
                    'type':'enumerator',
                    'value': 'Yes',
                    'name':'add_slate',
                    'data':[{
                        'label': 'Yes',
                        'value': 'Yes'
                    }, {
                        'label': 'No',
                        'value': 'No'
                    }]
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