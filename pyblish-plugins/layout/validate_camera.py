import pyblish.api

from maya import cmds


@pyblish.api.log
class ValidateCamera(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    label = 'Validate Render Camera'

    def process(self, instance):
        cameraNode = cmds.ls('renderCam')
        if len(cameraNode) == 0:
            self.log.error('Valid renderCam not found.')
            raise pyblish.api.ValidationError

        camShapeNode = cmds.listRelatives(cameraNode, s=True, c=True)[0]
        sourceConnections = cmds.listConnections(camShapeNode + '.imagePlane',
                                                 source=True, type='imagePlane') or []
        if len(sourceConnections) > 0:
            instance.set_data('image_planes', value=sourceConnections)
        self.log.info('renderCam validated')