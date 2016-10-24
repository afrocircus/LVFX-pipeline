import pyblish.api
import pymel.core
from maya import cmds


@pyblish.api.log
class ValidateRig(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['scene']
    label = 'Validate Rig'

    def process(self, instance):

        assemblies = pymel.core.ls(assemblies=True)
        rigInstances = []
        for each in assemblies:
            if any(ext in each.name().lower() for ext in ['grp']):
                rigInstances.append(each.name())

        if len(rigInstances) != 1:
            self.log.error('There should be only one parent group in the scene')
            raise pyblish.api.ValidationError

        rigMembers = cmds.listRelatives(rigInstances[0], children=True)
        rigs = []
        for each in rigMembers:
            if any(ext in each.lower() for ext in ['geo', 'rig']):
                rigs.append(each)

        if len(rigs) != 2:
            self.log.error('There should be 2 child groups called geo and rig')
            raise pyblish.api.ValidationError

        instance.set_data('rig', value=rigInstances[0])
