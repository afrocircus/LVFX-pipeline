__author__ = 'Natasha'

"""
This script creates a turntable for the selected objects in the maya scene.
"""

import pymel.core as pm
import maya.cmds as cmds


def getSelectionPivot(objs):
    """
    Gets a list of pivot points from selection
    :param objs: List of selected objects.
    :return: pivlist: List of pivot points.
    """
    pivlist = []
    for obj in objs:
        piv = cmds.xform(obj+'.scalePivot', q=True, ws=True, t=True)
        pivlist.append(piv)
    return pivlist


def createCamera():
    """
    Creates a new camera and positions it so that it frames all the objects in the scene.
    :return: turnCam: Created turntable camera object.
    """

    turnCam = cmds.camera()
    cmds.lookThru( turnCam[0] )
    # Position the active camera to view the active objects
    pm.viewFit()

    # Position cameraShape-1 to view all objects
    pm.viewFit( turnCam[1], all=True )

    # Fill 50 percent of the active view with active objects
    pm.viewFit( f=0.5 )

    pm.viewFit( all=True )
    return turnCam


def findCentroid(pivlist):
    """
    Finds the centroid of a set of points.
    :param pivlist: Set of pivot points
    :return: centroid: centroid of points.
    """
    centroid = [0.0,0.0,0.0]
    for p in pivlist:
        centroid[0]+=p[0]
        centroid[1]+=p[1]
        centroid[2]+=p[2]

    centroid[0] /= len(pivlist)
    centroid[1] /= len(pivlist)
    centroid[2] /= len(pivlist)
    return centroid

def checkSelection(objs):
    if objs:
        polymeshes = cmds.filterExpand(objs, sm=12)
        print polymeshes
        if polymeshes:
            return polymeshes
    return None


def turntable():
    """
    Main function. Creates turntable. Requires a list of selected objects.
    :return: None
    """
    objs = cmds.ls(selection = True)
    meshes = checkSelection(objs)
    if not meshes:
        cmds.error('Please select a mesh object')
    pivlist = getSelectionPivot(meshes)
    turnCam = createCamera()
    centroid = findCentroid(pivlist)

    # change camera pivot to centroid
    cmds.xform(turnCam[0], ws=True, piv=centroid)

    # animate camera. rotate around y axis.
    firstFrame = int(cmds.playbackOptions(q=True, minTime=True))
    lastFrame = int(cmds.playbackOptions(q=True, maxTime=True))
    step = int(lastFrame-firstFrame)/10
    rot = cmds.getAttr(turnCam[0]+'.rotateY')
    for frame in xrange(firstFrame, lastFrame, step):
        cmds.setAttr(turnCam[0]+'.rotateY', rot)
        cmds.setKeyframe(turnCam[0], attribute='rotateY', t=frame)
        rot  += 36
    cmds.setKeyframe(turnCam[0], attribute='rotateY', t=lastFrame)


# bring in light rigs (?)

