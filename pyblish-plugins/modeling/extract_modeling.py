import os
import ftrack
import pyblish.api
import pymel.core


@pyblish.api.log
class ExtractModeling(pyblish.api.InstancePlugin):

    families = ['scene']
    label = 'Extract Model'
    hosts = ['maya']
    order = pyblish.api.ExtractorOrder


    def process(self, instance):

        node = instance.data['model']
        versionDir = instance.data['vprefix'] + instance.data['version']
        publishDir = os.path.join(instance.data['publishDir'], versionDir)

        if not os.path.exists(publishDir):
            os.makedirs(publishDir)

        metadata = instance.data['metadata']
        metadata['version'] = versionDir

        task = ftrack.Task(instance.context.data['taskid'])
        assetName = task.getParent().getName().lower()

        assetFile = os.path.join(publishDir, '%s_ref.mb' % assetName)
        refFile = os.path.join(instance.data['publishDir'], '%s_ref.mb' % assetName)
        metadata['publish_model'] = refFile

        pymel.core.select(node)
        pymel.core.system.exportSelected(assetFile,
                                         constructionHistory=False,
                                         preserveReferences=True,
                                         shader=True,constraints=False,
                                         force=True)
        if os.path.exists(refFile):
            os.remove(refFile)
        os.symlink(assetFile, refFile)
        self.log.info('Extraction completed successfully')
