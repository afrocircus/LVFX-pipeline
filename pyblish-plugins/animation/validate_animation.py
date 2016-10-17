import pyblish.api
import pymel.core
from maya import cmds


@pyblish.api.log
class ValidateAnimation(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder
    hosts = ['maya']
    families = ['scene']
    label = 'Validate Animation Scene'

    def process(self, instance):

        # Get all top level assemblies
        assemblies = pymel.core.ls(assemblies=True)
        invalid = []
        valid = []

        for each in assemblies:
            # If env in group name, then skip processing it.
            if 'env_' in each.name().lower():
                continue
            # Valid group must have 'grp' in the top level name
            if 'grp' in each.name().lower():
                # Get the children
                members = cmds.listRelatives(each.name(), children=True)
                geoMembers = []
                for member in members:
                    # Get all children that have 'geo' in the name
                    if 'geo' in member:
                        geoMembers.append(member)
                # Invalid if there are more than 1 'geo' groups
                if len(geoMembers) == 1:
                    valid.append(geoMembers[0])
                else:
                    invalid.append(each.name())

        if len(invalid) > 0:
            self.log.error('There should only be 1 "geo" group under a parent group')
            raise pyblish.api.ValidationError
        elif len(invalid) == 0 and len(valid) == 0:
            self.log.error('No group found. Nothing to export.')
            raise pyblish.api.ValidationError

        instance.set_data('anim', value=valid)
        print valid
