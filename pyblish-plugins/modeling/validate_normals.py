import pyblish.api
import maya.cmds as cmds


class ValidateStarterNormals(pyblish.api.InstancePlugin):
    """Normals of a model may not be locked
    Locked normals shading during interactive use to behave
    unexpectedly. No part of the pipeline take advantage of
    the ability to lock normals.
    """

    label = "Normals"
    order = pyblish.api.ValidatorOrder
    hosts = ["maya"]
    families = ['scene']

    def process(self, instance):

        invalid = list()
        for mesh in cmds.ls(type="mesh", long=True):
            faces = cmds.polyListComponentConversion(mesh, toVertexFace=True)
            if faces:
                locked = cmds.polyNormalPerVertex(faces,
                                                  query=True,
                                                  freezeNormal=True)

                invalid.append(mesh) if any(locked) else None

        # On locked normals, indicate that validation has failed
        # with a friendly message for the user.
        #assert not invalid, (
        #    "Meshes found with locked normals: %s" % invalid)
        if len(invalid) > 0:
            self.log.warning("Meshes found with locked normals: %s" % invalid)
        else:
            self.log.info("The normals of \"%s\" are correct." % instance.data['model'])
