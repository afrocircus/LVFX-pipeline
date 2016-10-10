import os
import pyblish.api


class CollectShotAssetDir(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Shot Asset Dir"

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, context):
        """Inject the current working file"""
        currentFile = context.data['currentFile']
        fileDir = os.path.dirname(currentFile)
        shotPath = fileDir.split('scene')[0]
        shotAssetPath = os.path.join(shotPath, 'shotAssets')

        context.set_data('shotAssetPath', value=shotAssetPath)
