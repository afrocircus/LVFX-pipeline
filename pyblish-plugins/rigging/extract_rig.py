import os
import ftrack
import pyblish.api
from maya import cmds
from pyblish_maya import maintained_selection


@pyblish.api.log
class ExtractRig(pyblish.api.InstancePlugin):

    families = ['scene']
    label = 'Extract Rig'
    hosts = ['maya']
    order = pyblish.api.ExtractorOrder

    def process(self, instance):

        node = instance.data['rig']
        versionDir = instance.data['vprefix'] + instance.data['version']
        publishDir = os.path.join(instance.data['publishDir'], versionDir)
        if not os.path.exists(publishDir):
            os.makedirs(publishDir)

        metadata = instance.data['metadata']
        metadata['version'] = versionDir

        task = ftrack.Task(instance.context.data['taskid'])
        assetName = task.getParent().getName().lower()

        assetFile = os.path.join(publishDir, '%s_rig.mb' % assetName)
        refFile = os.path.join(instance.data['publishDir'], '%s_rig.mb' % assetName)
        metadata['publish_rig'] = refFile

        with maintained_selection():
            cmds.select(node, noExpand=True)
            cmds.file(assetFile,
                      force=True,
                      typ='mayaBinary',
                      exportSelected=True,
                      preserveReferences=False,
                      constructionHistory=True)

        if os.path.exists(refFile):
            os.remove(refFile)
        os.symlink(assetFile, refFile)
        self.log.info('Extraction completed successfully')
