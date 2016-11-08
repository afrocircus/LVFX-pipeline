import sys
import os
import getpass
import logging
import ftrack
import threading
import subprocess
import json

def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class RefClipUploader(ftrack.Action):
    """
    Creates a reference clip from the plates in <shots>/<sq>/<shot>/img/plates/*.dpx
    and the uploads it to the corresponding shot as a reference clip for the artists.
    """
    label = 'Upload Reference'
    identifier = 'com.ftrack.uploadRef'
    description = 'Uploads a reference clip to a shot'

    def __init__(self):
        """
        Initialize action handler
        """
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def getProject(self, showid):
        show = ftrack.Project(id=showid)
        return show


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


    def getShotPlatesFolder(self, shot):
        project = self.getProject(shot.get('showid'))
        projectFolder = self.getProjectFolder(project)
        sequenceName = shot.getParent().getName()
        shotName = shot.getName()
        imgFolder = os.path.join(projectFolder, 'shots', sequenceName, shotName, 'img')
        platesFolder = os.path.join(imgFolder, 'plates')
        if not os.path.exists(platesFolder):
            platesFolder = os.path.join(platesFolder, 'proxy')
        return platesFolder


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


    def createThumbnail(self, inputFile, outputFile):
        cmd = 'ffmpeg -y -i "%s" -vf  "thumbnail,scale=640:360" -frames:v 1 "%s"' % (inputFile, outputFile)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
        process.wait()


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


    def deleteFiles(self, outfilemp4, outfilewebm, thumbnail):
        if os.path.exists(outfilemp4):
            os.remove(outfilemp4)
        if os.path.exists(outfilewebm):
            os.remove(outfilewebm)
        if os.path.exists(thumbnail):
            os.remove(thumbnail)

    def upload(self, ff, lf, inputFile, outfilemp4, outfilewebm, thumnbail, metadata, shot, fps):

        result = self.convertFiles(inputFile, outfilemp4, outfilewebm)
        if result:
            self.createThumbnail(outfilemp4, thumnbail)
            asset = self.getAsset(shot, 'reference')
            version = asset.createVersion('Reference Clip Upload')
            self.createAttachment(version, 'ftrackreview-mp4', outfilemp4, ff, lf, fps, metadata)
            self.createAttachment(version, 'ftrackreview-webm', outfilewebm, ff, lf, fps, metadata)
            version.createComponent(name='movie', path=inputFile)
            version.publish()
            if os.path.exists(thumnbail):
                attachment = version.createThumbnail(thumnbail)
                shot.setThumbnail(attachment)
        self.deleteFiles(outfilemp4, outfilewebm, thumnbail)


    def uploadToFtrack(self, movieFile, firstFrame, lastFrame, shot):
        show = self.getProject(shot.get('showid'))
        fps = int(show.get('fps'))
        project = show.getName()
        sqName = shot.getParent().getName()
        shotName = shot.getName()
        tasks = shot.getTasks()
        if len(tasks) == 0:
            return
        task = tasks[0].getName()
        print '%s / %s / %s / %s' % (project, sqName, shotName, task)
        try:
            shot.set('fstart', float(firstFrame))
            shot.set('fend', float(lastFrame))
        except Exception:
            print 'Unable to set frame range firstFrame:%s, lastFrame:%s' % (firstFrame, lastFrame)

        outfilemp4, outfilewebm, thumbnail, metadata = self.prepMediaFiles(movieFile)
        self.upload(firstFrame, lastFrame, movieFile,
               outfilemp4, outfilewebm, thumbnail, metadata, shot, fps)


    @async
    def makeMovie(self, shot, user):

        job = ftrack.createJob(
            'Creating Reference Clip for shot {0}'.format(shot.getName()),
            'queued', user)
        job.setStatus('running')
        platesFolder = self.getShotPlatesFolder(shot)
        fps = int(shot.getProject().get('fps'))
        if not os.path.exists(platesFolder):
            job.setStatus('failed')
            job.setDescription('No plates found')
            return
        files = [f for f in os.listdir(platesFolder) if f.endswith('.dpx')]
        if len(files) == 0:
            # if no dpx images found then check for jpegs
            files = [f for f in os.listdir(platesFolder) if f.endswith('.jpeg')]
            if len(files) == 0:
                # if no jpegs found then return
                job.setStatus('failed')
                job.setDescription('No plates found')
                return
        if files:
            files.sort()
            plateName = files[0].split('.')[0]
            firstFrame = files[0].split('.')[-2]
            lastFrame = files[-1].split('.')[-2]
            frameLen = len(firstFrame)
            filename = files[0].replace(firstFrame, '%%0%sd' % frameLen)
            fullFile = os.path.join(platesFolder, filename)
            outputFile = os.path.join(platesFolder, '%s.mov' % plateName)
            tmpFile = os.path.join(platesFolder, 'output.mov')
            cmd = 'ffmpeg -y -start_number %s -an -i "%s" -vcodec prores -profile:v 2 -r %s "%s"' % (
                    firstFrame, fullFile, fps, tmpFile)
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
            process.wait()

            if os.path.exists(tmpFile):
                cmd = 'ffmpeg -i "%s" -vcodec prores -profile:v 2 ' \
                      '-vf "drawtext=fontfile=/usr/share/fonts/dejavu/DejaVuSans.ttf:' \
                      'fontsize=32:text=%%{n}: x=(w-tw)-50: y=h-(2*lh): ' \
                      'fontcolor=white: box=1: boxcolor=0x00000099" -y "%s"' % (tmpFile, outputFile)
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
                process.wait()
                os.remove(tmpFile)

            if os.path.exists(outputFile):
                job.setDescription('Reference Clip created successfully. Uploading...')
                job.setStatus('running')
                try:
                    self.uploadToFtrack(outputFile, firstFrame, lastFrame, shot)
                    job.setStatus('done')
                    job.setDescription('Uploaded reference clip successfully')
                except Exception:
                    job.setStatus('failed')
                    job.setDescription('Uploading to ftrack failed')
                    return
            else:
                job.setStatus('failed')
                job.setDescription('Could not create reference clip')
        else:
            job.setStatus('failed')
            job.setDescription('No plates found')

    @async
    def makeAllShots(self, sequence, user):
        shots = sequence.getShots()
        for shot in shots:
            print shot.getName()
            self.makeMovie(shot, user)

    def register(self):
        """
        Register action
        """
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
        """
        Return action config
        """
        selection = event['data'].get('selection', [])
        selectionType = ''

        if not selection:
            return

        if selection[0]['entityType'] == 'task':
            selectionType = self.getTaskType(selection[0]['entityId'])

        if selectionType == 'Sequence' or selectionType == 'Shot':
            return {
                'items': [{
                    'label': self.label,
                    'actionIdentifier': self.identifier,
                    'icon': 'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-connect-plugins/icons/browser-13.png'
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
        result = 1
        selectionType = ''

        if selection[0]['entityType'] == 'task':
            selectionType = self.getTaskType(selection[0]['entityId'])

        if selectionType == 'Sequence':
            sequence = ftrack.Sequence(id=selection[0]['entityId'])
            self.makeAllShots(sequence, user)

        if selectionType == 'Shot':
            shot = ftrack.Shot(id=selection[0]['entityId'])
            self.makeMovie(shot, user)

        return {
                'success': True,
                'message': 'Action launched successfully.'
            }

    def getTaskType(self, entityId):
        task = ftrack.Task(id=entityId)
        if 'objecttypename' in task.keys():
            return task.get('objecttypename')


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.projCreate'
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

    action = RefClipUploader()
    action.register()
