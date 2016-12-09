import pyblish.api
import pymel.core


@pyblish.api.log
class ValidateMeshes(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['scene']
    label = 'Validate Meshes'
    print "running"

    def process(self, instance):

        assemblies = pymel.core.ls(assemblies=True)
        modelInstances = []
        for each in assemblies:
            if any(ext in each.name().lower() for ext in ['grp', 'fur']):
                modelInstances.append(each.name())

        furCount = 0
        if len(modelInstances) == 2:
            for each in modelInstances:
                if 'fur' in each.lower():
                    furCount += 1

        if len(modelInstances) > 2 or len(modelInstances) == 0:
            self.log.error('Invalid groups in the scene.')
            raise pyblish.api.ValidationError

        if len(modelInstances) == 2 and furCount != 1:
            self.log.error('Invalid groups in the scene.')
            raise pyblish.api.ValidationError

        instance.set_data('model', value=modelInstances)
