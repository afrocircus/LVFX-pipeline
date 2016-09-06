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
    lookThruAndFrame(turnCam[0])
    return turnCam


def createLight(type, pos, centroid):
    """
    Create a new light, frame it so that all objects are in view.
    Then position the light correctly.
    :param type: Type of light to create eg. areaLight, spotLight etc.
    :param pos: Position of light eg. key, fill or rim
    :param centroid: Centroid of selected objects in the scene
    :return:
    """
    light = cmds.shadingNode('areaLight', asLight=True)
    lookThruAndFrame(light)
    cmds.xform(light, ws=True, piv=centroid)
    if pos == 'key':
        cmds.setAttr(light+'.rotateY', -45)
        cmds.setAttr(light+'.rotateZ', -45)
    elif pos == 'fill':
        cmds.setAttr(light+'.rotateY', 45)
        cmds.setAttr(light+'.rotateZ', 20)
        cmds.setAttr(light+'.intensity', 0.5)
    elif pos == 'rim':
        cmds.setAttr(light+'.rotateY', -135)
        cmds.setAttr(light+'.rotateZ', -45)
        cmds.setAttr(light+'.intensity', 0.7)
    cmds.xform(light, ws=True, cp=True)
    return light


def lookThruAndFrame(obj):
    """
    Looks through the given obj and moves the obj so that it frames the viewport objects.
    :param obj: The camera or light object.
    :return: None
    """
    cmds.lookThru(obj)
    # Position the active camera to view the active objects
    pm.viewFit()

    # Position cameraShape-1 to view all objects
    pm.viewFit(obj, all=True)

    # Fill 50 percent of the active view with active objects
    pm.viewFit(f=0.5)
    pm.viewFit(all=True)

def findCentroid(pivlist):
    """
    Finds the centroid of a set of points.
    :param pivlist: Set of pivot points
    :return: centroid: centroid of points.
    """
    centroid = [0.0, 0.0, 0.0]
    for p in pivlist:
        centroid[0] += p[0]
        centroid[1] += p[1]
        centroid[2] += p[2]

    centroid[0] /= len(pivlist)
    centroid[1] /= len(pivlist)
    centroid[2] /= len(pivlist)
    return centroid


def checkSelection(objs):
    if objs:
        polymeshes = cmds.filterExpand(objs, sm=12)
        if polymeshes:
            return polymeshes
    return None


def turntable():
    """
    Main function. Creates turntable. Requires a list of selected objects.
    :return: None
    """
    objs = cmds.ls(selection=True)
    meshes = checkSelection(objs)
    if not meshes:
        cmds.error('Please select a mesh object')
    pivlist = getSelectionPivot(meshes)
    turnCam = createCamera()
    centroid = findCentroid(pivlist)

    # change camera pivot to centroid
    cmds.xform(turnCam[0], ws=True, piv=centroid)

    # animate camera. rotate around y axis.
    firstFrame = str(cmds.playbackOptions(q=True, minTime=True))
    lastFrame = str(cmds.playbackOptions(q=True, maxTime=True))
    cmds.expression(name='TurnTableExpression',
                    string='{0}.rotateY=360*(frame-{1})/{2}-{1};'.format(turnCam[0],
                                                                         firstFrame, lastFrame))

    # create a 3 point light rig.
    keyLight = createLight('areaLight', 'key', centroid)
    fillLight = createLight('areaLight', 'fill', centroid)
    rimLight = createLight('areaLight', 'rim', centroid)
    cmds.lookThru(turnCam[0])
