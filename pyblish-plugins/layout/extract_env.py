import os
import pyblish.api
import maya.cmds as cmds


@pyblish.api.log
class ExtractEnv(pyblish.api.ContextPlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Extract Environment File'

    def process(self, context):
        try:
            cmds.select('env_*:*')
        except ValueError:
            self.log.warning('No environment elements to extract.')
            return

        versionDir = context.data['vprefix'] + context.data['version']
        publishDir = os.path.join(context.data['layoutPublishDir'], versionDir)
        if not os.path.exists(publishDir):
            os.makedirs(publishDir)

        exportFile = os.path.join(publishDir, 'env.mb')
        # Export selection to a <filedir>/publish/env.mb
        try:
            cmds.file(exportFile, pr=True, es=True, force=True, type='mayaBinary')
        except RuntimeError:
            pyblish.api.ExtractionError