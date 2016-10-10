import pyblish.api
from maya import cmds


class CollectFrameRange(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Frame Range"

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, context):
        startFrame = cmds.playbackOptions(q=True, minTime=True)
        endFrame = cmds.playbackOptions(q=True, maxTime=True)

        context.set_data('startFrame', value=startFrame)
        context.set_data('endFrame', value=endFrame)
