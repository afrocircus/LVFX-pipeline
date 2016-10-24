import os
import pyblish.api
import maya.cmds as cmds


@pyblish.api.log
class ExtractEnv(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Extract Environment File'
    families = ['scene']

    def process(self, instance):
        try:
            cmds.select('env_*:*')
        except ValueError:
            self.log.warning('No environment elements to extract.')
            return

        versionDir = instance.data['vprefix'] + instance.data['version']
        publishDir = os.path.join(instance.data['publishDir'], versionDir)

        if not os.path.exists(publishDir):
            os.makedirs(publishDir)

        exportFile = os.path.join(publishDir, 'env.mb')
        refFile = os.path.join(instance.data['publishDir'], 'env.mb')
        # Export selection to a <filedir>/publish/env.mb
        try:
            cmds.file(exportFile, pr=True, es=True, force=True, type='mayaBinary')
        except RuntimeError:
            raise pyblish.api.ExtractionError

        # Create a symlink to the latest env publish
        if os.path.exists(refFile):
            os.remove(refFile)
        os.symlink(exportFile, refFile)
