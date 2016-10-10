import os
import pyblish.api
from maya import cmds


class CollectLayoutPublishDir(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Layout Publish Dir"

    hosts = ['maya']

    def process(self, context):
        """Inject the current working file"""
        current_file = cmds.file(sceneName=True, query=True)
        dirname = os.path.dirname(current_file)

        layoutPublishDir = os.path.join(dirname, 'publish')

        # Maya returns forward-slashes by default
        normalised = os.path.normpath(layoutPublishDir)

        context.set_data('layoutPublishDir', value=normalised)
        print normalised
