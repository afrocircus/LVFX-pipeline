import os
import pyblish.api
from Utils import pyblish_utils
from maya import cmds


@pyblish.api.log
class CollectScene(pyblish.api.ContextPlugin):
    """
    Finds values for scene variables.
    Gets version number, Ftrack Task ID
    """
    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Scene Details"

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, context):

        currentFile = context.data('currentFile')
        filename = os.path.basename(currentFile)
        currentDir = os.path.dirname(currentFile)

        # Check if the current dir is modeling/maya
        if os.path.split(currentDir)[1] == 'maya':
            currentDir = os.path.dirname(currentDir)

        publishDir = os.path.join(currentDir, 'publish')
        instance = context.create_instance(name=filename)

        instance.set_data('family', value='scene')
        instance.set_data('workPath', value=currentDir)
        instance.set_data('publishDir', value=publishDir)

        # Get Shot Asset Dir
        fileParts = currentFile.split('scene')
        if len(fileParts) == 1:
            shotAssetDir = os.path.join(currentDir, 'shotAssets')
        else:
            shotAssetDir = os.path.join(fileParts[0], 'shotAssets')

        instance.set_data('shotAssetPath', value=shotAssetDir)

        # version data
        try:
            (prefix, version) = pyblish_utils.version_get(filename, 'v')
            instance.set_data('version', value=version)
            instance.set_data('vprefix', value=prefix)
        except:
            self.log.warning('Cannot publish workfile which is not versioned.')

        # Get scene frame range
        startFrame = cmds.playbackOptions(q=True, minTime=True)
        endFrame = cmds.playbackOptions(q=True, maxTime=True)

        instance.set_data('startFrame', value=startFrame)
        instance.set_data('endFrame', value=endFrame)

        #self.log.info('Scene Version: %s' % context.data('version'))

        # Setting the metadata dictionary
        metadata = {'filename': context.data('currentFile')}
        instance.set_data('metadata', value=metadata)

        # Get Ftrack Task ID
        if 'FTRACK_TASKID' in os.environ:
            context.set_data('taskid', value=os.environ['FTRACK_TASKID'])
            self.log.info('Task ID: %s' % context.data('taskid'))
