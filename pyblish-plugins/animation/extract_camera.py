import os
import pyblish.api
import maya.cmds as cmds


@pyblish.api.log
class ExtractCamera(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Export Camera Abc'
    families = ['scene']
    optional = True
    active = False

    def process(self, instance):
        shotAssetsDir = instance.data['shotAssetPath']

        versionDir = instance.data['vprefix'] + instance.data['version']

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

        try:
            cmds.AbcExport(j=params)
        except Exception:
            self.log.error('Error during camera extraction')
            raise pyblish.api.ExtractionError

        # Create a symlink to the latest camera publish
        if os.path.exists(cameraSymLink):
            os.remove(cameraSymLink)
        os.symlink(cameraFile, cameraSymLink)

        metadata = instance.data['metadata']
        metadata['renderCam'] = cameraSymLink

        # Export Nuke Cam if it exists
        cameraNode = cmds.ls('renderCamNuke')
        if len(cameraNode) != 0:
            cmds.select('renderCamNuke')
            import maya.mel as mel
            cameraMayaFile = os.path.join(cameraDir, 'renderCamNuke.mb')
            cameraNukeFile = os.path.join(cameraDir, 'renderCamNuke.nk')
            result = mel.eval('source pass2nuke; openMotion("%s","mayaBinary")' % cameraMayaFile)
            if result == 1:
                os.rename(cameraMayaFile, cameraNukeFile)
                metadata['nukeCam'] = cameraNukeFile
            else:
                self.log.warn('Unable to export the nuke camera.')
