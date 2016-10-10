import os
import pyblish.api
from shutil import copyfile
import subprocess


@pyblish.api.log
class ExtractAnimScene(pyblish.api.ContextPlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Publish Animation Scene'

    def process(self, context):
        shotAssetsDir = context.data['shotAssetPath']

        versionDir = context.data['vprefix'] + context.data['version']

        cameraDir = os.path.join(shotAssetsDir, 'camera', versionDir)
        cameraFile = os.path.join(cameraDir, 'renderCam.abc')

        publishDir = os.path.join(context.data['layoutPublishDir'], versionDir)

        envFile = os.path.join(publishDir, 'env.mb')
        charFile = os.path.join(publishDir, 'char.mb')
        animFile = os.path.join(publishDir, 'animation_publish.mb')

        if os.path.exists(animFile):
            os.remove(animFile)

        mayaScript = "import maya.cmds as cmds;" \
                     "import maya.standalone; " \
                     "maya.standalone.initialize('Python'); " \
                     "cmds.loadPlugin('AbcImport');"
        if os.path.exists(charFile):
            copyfile(charFile, animFile)
            mayaScript += "cmds.file('%s', o=True);" % animFile
        else:
            mayaScript += "cmds.file(new=True);" \
                          "cmds.file(rename=%s);" % animFile

        if os.path.exists(envFile):
            mayaScript += "cmds.file('%s', r=True);" % envFile

        if os.path.exists(cameraFile):
            mayaScript += "cmds.AbcImport('%s', mode='import');" % cameraFile

        mayaScript += "cmds.file(save=True, type='mayaBinary', force=True);" \
                      "cmds.quit();"

        mayapyPath = context.data['mayapy']
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
