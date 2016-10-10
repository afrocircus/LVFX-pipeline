import pyblish.api

from maya import cmds


@pyblish.api.log
class ValidateCamera(pyblish.api.ContextPlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    label = 'Validate Render Camera'

    def process(self, context):
        cameraNode = cmds.ls('renderCam')
        if len(cameraNode) == 0:
            self.log.error('Valid renderCam not found.')
            raise pyblish.api.ValidationError
        self.log.info('renderCam validated')