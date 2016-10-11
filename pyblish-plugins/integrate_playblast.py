import threading
import pyblish.api
from Utils import ftrack_utils2


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


@pyblish.api.log
class IntegratePlayblast(pyblish.api.InstancePlugin):
    """
    Integrate metadata with ftrack
    """
    order = pyblish.api.IntegratorOrder
    label = "Playblast Upload"
    families = ['playblast']

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, instance):

        metadata = instance.data['metadata']
        taskid = instance.context.data['taskid']
        playblast = instance.data['playblastFile']
        currentFile = instance.context.data['currentFile']
        startFrame = instance.data['startFrame']
        endFrame = instance.data['endFrame']
        self.uploadToFtrack(taskid, playblast, currentFile, metadata,
                            startFrame, endFrame)

    @async
    def uploadToFtrack(self, taskid, playblast, currentFile, metadata,
                       startFrame, endFrame):

        session = ftrack_utils2.startSession()
        task = ftrack_utils2.getTask(session, taskid, currentFile)
        ftrack_utils2.addMetadata(session, task, metadata)

        ftrack_utils2.copyToApprovals(playblast, task['project'])
        outfilemp4, outfilewebm, thumbnail, metadata = ftrack_utils2.prepMediaFiles(playblast)

        result = ftrack_utils2.convertFiles(playblast, outfilemp4, outfilewebm, thumbnail)
        if result:
            asset = ftrack_utils2.getAsset(session, task, 'ReviewAsset')
            status = ftrack_utils2.getStatus(session, 'Pending Internal Review')
            try:
                ftrack_utils2.createAndPublishVersion(session, task, asset,
                                                      status,'Upload for Internal Review',
                                                      thumbnail, playblast, outfilemp4,
                                                      outfilewebm, metadata, startFrame,
                                                      endFrame, 24)
                ftrack_utils2.deleteFiles(outfilemp4, outfilewebm, thumbnail)
                pyblish.api.emit("published")
            except Exception:
                pyblish.api.emit("pluginFailed")
        else:
            pyblish.api.emit("pluginFailed")