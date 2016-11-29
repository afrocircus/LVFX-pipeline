import os
import pyblish.api
from shutil import copyfile
import subprocess
import maya.cmds as cmds


@pyblish.api.log
class ExtractAnimScene(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Publish Animation Scene'
    families = ['scene']

    def process(self, instance):
        shotAssetsDir = instance.data['shotAssetPath']

        versionDir = instance.data['vprefix'] + instance.data['version']

        cameraFile = os.path.join(shotAssetsDir, 'camera', 'renderCam.abc')

        publishDir = os.path.join(instance.data['publishDir'], versionDir)

        envFile = os.path.join(instance.data['publishDir'], 'env.mb')
        charFile = os.path.join(publishDir, 'char.mb')
        animFile = os.path.join(publishDir, 'animation_publish.mb')

        metadata = instance.data['metadata']
        metadata['version'] = versionDir
        metadata['renderCam'] = cameraFile
        if os.path.exists(envFile):
            metadata['publish_env_file'] = envFile
        else:
            metadata['publish_env_file'] = ''
        if os.path.exists(charFile):
            metadata['publish_char_file'] = charFile
        else:
            metadata['publish_char_file'] = ''
        metadata['publish_anim_file'] = animFile
        instance.set_data('metadata', value=metadata)

        instance.context.set_data('nextTask', value='Animation')

        if os.path.exists(animFile):
            os.remove(animFile)

        mayaScript = "import maya.cmds as cmds;" \
                     "import maya.mel as mel;" \
                     "import maya.standalone; " \
                     "maya.standalone.initialize('Python'); " \
                     "cmds.loadPlugin('AbcImport');"
        if os.path.exists(charFile):
            copyfile(charFile, animFile)
            mayaScript += "cmds.file('%s', o=True, f=True);" % animFile
        else:
            mayaScript += "cmds.file(new=True, f=True);" \
                          "cmds.file(rename=%s);" % animFile

        audioNodes = cmds.ls(type='audio')
        if len(audioNodes) > 0:
            soundFile = cmds.sound(audioNodes[0], file=True, query=True)
            mayaScript += "cmds.file('%s', i=True, type='audio', options='o=0');" % soundFile

        if os.path.exists(envFile):
            mayaScript += "cmds.file('%s', r=True);" % envFile

        if os.path.exists(cameraFile):
            mayaScript += "cmds.AbcImport('%s', mode='import');" % cameraFile

        mayaScript += "cmds.file(save=True, type='mayaBinary', force=True);" \
                      "cmds.quit();" \
                      "os._exit(0)"

        print mayaScript

        mayapyPath = instance.context.data['mayapy']
        if mayapyPath == '' or not os.path.exists(mayapyPath):
            self.log.error('mayapy not found. Unable to publish file.')
            raise pyblish.api.ExtractionError

        maya = subprocess.Popen(mayapyPath + ' -c "%s"' % mayaScript, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
        out, err = maya.communicate()
        exitcode = maya.returncode
        if str(exitcode) != '0':
            self.log.error('Unable to publish file.')
            raise pyblish.api.ExtractionError
        else:
            self.log.info('Anim Publish Successful.')
