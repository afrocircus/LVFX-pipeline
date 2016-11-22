import pyblish.api
import re

from maya import cmds


@pyblish.api.log
class ValidateReferencesa(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    label = 'Validate References'

    def process(self, instance):

        references = cmds.ls(rf=True)
        for reference in references:
            if 'char_' in reference or 'env_' in reference:
                filename = cmds.referenceQuery(reference, filename=True)
                query = 'v' + r'\d+'
                pattern = re.compile(query)
                match = pattern.findall(filename)
                assert not match, ("Invalid reference for %s" % reference)
        self.log.info('References validated')