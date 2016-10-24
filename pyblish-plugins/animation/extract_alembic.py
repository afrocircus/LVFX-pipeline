import os
import pyblish.api
import maya.cmds as cmds


@pyblish.api.log
class ExtractAlembic(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Alembic export'
    families = ['scene']

    def process(self, instance):
        shotAssetsDir = instance.data['shotAssetPath']

        versionDir = instance.data['vprefix'] + instance.data['version']

        animGroups = instance.data['anim']

        failed = False

        for each in animGroups:
            charRefFile = cmds.referenceQuery(each, filename=True)
            charRefFile = charRefFile.split('{')[0]
            charName = each.split(':')[0].split('char_')[1]
            charDir = os.path.join(shotAssetsDir, charName, versionDir)
            charFile = os.path.join(charDir, charName + '.abc')

            if not os.path.exists(charDir):
                os.makedirs(charDir)

            char = cmds.ls(each)[0]
            frameRange = '-fr {0} {1}'.format(instance.data['startFrame'], instance.data['endFrame'])
            cameraNode = '-root {0}'.format(char)
            filename = '-file {0}'.format(charFile)

            params = '{0} {1} -uvWrite -ws -ef -writeVisibility ' \
                     '-dataFormat ogawa {2}'.format(frameRange, cameraNode, filename)

            try:
                cmds.AbcExport(j=params)
            except Exception:
                self.log.error('Error during alembic export for %s' % charName)
                failed = True

            metadata = instance.data['metadata']
            metadata['version'] = versionDir
            metadata['publish_%s' % charName] = charFile
            metadata['ref_%s' % charName] = charRefFile
            metadata['mayanode_%s' % charName] = each

        if failed:
            raise pyblish.api.ExtractionError

        self.log.info('Animation Alembic Export Successful.')
