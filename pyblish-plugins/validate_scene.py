import pyblish.api


@pyblish.api.log
class ValidateCurrentFile(pyblish.api.ContextPlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    label = 'Validate Scene'

    def process(self, context):

        currentFile = context.data['currentFile']
        if currentFile == '.':
            self.log.error('Filename is not valid.')
            raise pyblish.api.ValidationError

        if not 'version' in context.data:
            self.log.error('File is not versioned.')
            raise pyblish.api.ValidationError

        self.log.info('Filename validated.')