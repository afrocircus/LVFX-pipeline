import os
import pyblish.api
import maya.cmds as cmds


@pyblish.api.log
class ExtractChar(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Extract Character File'

    def process(self, instance):
        try:
            cmds.select('char_*:*')
        except ValueError:
            self.log.warning('No characters to extract.')
            return

        versionDir = instance.data['vprefix'] + instance.data['version']
        publishDir = os.path.join(instance.data['publishDir'], versionDir)
        if not os.path.exists(publishDir):
            os.makedirs(publishDir)

        exportFile = os.path.join(publishDir, 'char.mb')
        # Export selection to a <filedir>/publish/env.mb
        try:
            cmds.file(exportFile, pr=True, es=True, force=True, type='mayaBinary')
        except RuntimeError:
            raise pyblish.api.ExtractionError