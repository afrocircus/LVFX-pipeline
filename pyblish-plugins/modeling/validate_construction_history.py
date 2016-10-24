import pyblish.api
import maya.cmds as cmds
import pymel


class ValidateConstructionHistory(pyblish.api.InstancePlugin):
    """ Ensure no construction history exists on the nodes in the instance """

    order = pyblish.api.ValidatorOrder
    families = ['scene']
    optional = True
    label = 'Construction History'

    def process(self, instance):
        """Process all the nodes in the instance """

        check = True

        for node in cmds.ls(type='transform'):
            # skipping references
            if not pymel.core.PyNode(node).isReferenced():

                history = cmds.listHistory(node, pruneDagObjects=True)
                if history:
                    for h in history:
                        if not pymel.core.PyNode(h).isReferenced():
                            msg = 'Node "%s" has construction' % node
                            msg += ' history: %s' % h
                            self.log.error(msg)
                            check = False

        if not check:
            self.log.warning('Nodes in the scene has construction history.')
