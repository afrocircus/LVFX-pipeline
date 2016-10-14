import pyblish.api
import pymel.core


@pyblish.api.log
class ValidateMeshes(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['scene']
    label = 'Validate Meshes'

    def process(self, instance):

        assemblies = pymel.core.ls(assemblies=True)
        modelInstances = []
        for each in assemblies:
            if any(ext in each.name().lower() for ext in ['grp']):
                modelInstances.append(each.name())

        if len(modelInstances) > 1:
            self.log.error('There should be only one parent group in the scene')
            raise pyblish.api.ValidationError

        instance.set_data('model', value=modelInstances[0])
