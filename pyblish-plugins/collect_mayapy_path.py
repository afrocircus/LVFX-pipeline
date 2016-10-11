import pyblish.api
import sys
from maya import cmds


@pyblish.api.log
class CollectMayapyPath(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Mayapy Path"

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, context):
        mayaVersion = cmds.about(version=True)

        if sys.platform == 'linux2':
            mayaPy = '/usr/autodesk/maya%s/bin/mayapy' % mayaVersion
        else:
            mayaPy = ''

        context.set_data('mayapy', value=mayaPy)
