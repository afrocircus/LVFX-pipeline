import pyblish.api


class TestAction(pyblish.api.Action):
    label = "This is a test action"
    icon = "close"

    def process(self, context, plugin):
        self.log.info('I am a test action')


@pyblish.api.log
class ValidateCurrentFile(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['scene']
    label = 'Validate Scene'

    def process(self, instance):

        currentFile = instance.data['workPath']
        # Check if the filename is valid.
        if currentFile == '.':
            self.log.error('Filename is not valid.')
            raise pyblish.api.ValidationError

        # Check if the file is versioned
        if not 'version' in instance.data:
            self.log.error('File is not versioned.')
            raise pyblish.api.ValidationError

        # Check if the file has a valid Ftrack Task id
        if not 'taskid' in instance.context.data:
            self.log.error('Valid TaskID not found')
            raise pyblish.api.ValidationError

        self.log.info('Filename validated.')
