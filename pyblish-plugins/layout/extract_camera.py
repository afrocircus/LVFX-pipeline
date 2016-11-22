import os
import pyblish.api
import maya.cmds as cmds


@pyblish.api.log
class ExtractCamera(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Export Camera Abc'
    families = ['scene']

    def process(self, instance):
        shotAssetsDir = instance.data['shotAssetPath']

        versionDir = instance.data['vprefix'] + instance.data['version']
        publishDir = os.path.join(instance.data['publishDir'], versionDir)
        if not os.path.exists(publishDir):
            os.makedirs(publishDir)
        cameraMayaFile = os.path.join(publishDir, 'renderCam.mb')

        cameraDir = os.path.join(shotAssetsDir, 'camera', versionDir)
        cameraFile = os.path.join(cameraDir, 'renderCam.abc')
        cameraSymLink = os.path.join(shotAssetsDir, 'camera', 'renderCam.abc')

        if not os.path.exists(cameraDir):
            os.makedirs(cameraDir)

        camera = cmds.ls('renderCam')[0]
        frameRange = '-fr {0} {1}'.format(instance.data['startFrame'], instance.data['endFrame'])
        cameraNode = '-root {0}'.format(camera)
        filename = '-file {0}'.format(cameraFile)

        params = '{0} {1} -ws -ef -dataFormat ogawa {2}'.format(frameRange, cameraNode, filename)

        cmds.select(camera)
        refFile = os.path.join(instance.data['publishDir'], 'renderCam.mb')
        # Export selection to a <filedir>/publish/env.mb
        try:
            cmds.file(cameraMayaFile, pr=True, es=True, force=True, type='mayaBinary')
        except RuntimeError:
            raise pyblish.api.ExtractionError

        try:
            cmds.AbcExport(j=params)
        except Exception:
            self.log.error('Error during camera extraction')
            raise pyblish.api.ExtractionError

        # Create a symlink to the latest camera publish
        if os.path.exists(cameraSymLink):
            os.remove(cameraSymLink)
        os.symlink(cameraFile, cameraSymLink)

        # Create a symlink to the latest env publish
        if os.path.exists(refFile):
            os.remove(refFile)
        os.symlink(cameraMayaFile, refFile)

        # Export Nuke Cam if it exists
        cameraNode = cmds.ls('renderCamNuke')
        if len(cameraNode) != 0:
            cmds.select('renderCamNuke')
            import maya.mel as mel
            cameraMayaFile = os.path.join(cameraDir, 'renderCamNuke.mb')
            cameraNukeFile = os.path.join(cameraDir, 'renderCamNuke.nk')
            result = mel.eval('source pass2nuke; openMotion("%s","mayaBinary")' % cameraMayaFile)
            if result == 1:
                metadata = instance.data['metadata']
                os.rename(cameraMayaFile, cameraNukeFile)
                metadata['nukeCam'] = cameraNukeFile
            else:
                self.log.warn('Unable to export the nuke camera.')
