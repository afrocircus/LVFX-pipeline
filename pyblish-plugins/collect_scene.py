import os
import pyblish.api
from Utils import pyblish_utils


class CollectSceneVersion(pyblish.api.ContextPlugin):
    """Finds version in the filename or passes the one found in the context
        Arguments:
        version (int, optional): version number of the publish
    """
    order = pyblish.api.CollectorOrder - 0.5
    label = "Collect Version"

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, context):

        filename = os.path.basename(context.data('currentFile'))

        # version data
        try:
            (prefix, version) = pyblish_utils.version_get(filename, 'v')
        except:
            self.log.warning('Cannot publish workfile which is not versioned.')
            return

        context.set_data('version', value=version)
        context.set_data('vprefix', value=prefix)

        self.log.info('Scene Version: %s' % context.data('version'))