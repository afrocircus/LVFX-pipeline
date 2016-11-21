import maya.cmds as cmds
import logging

cameraNode = cmds.ls('renderCam')
if len(cameraNode) == 0:
    logging.error('Valid renderCam not found.')
else:
    # Duplicate renderCam and rename to renderCamNuke
    nukeCam = cmds.duplicate('renderCam', rr=True, n='renderCamNuke')

    # Change rotateOrder on renderCamNuke to 5 (zyx)
    cmds.setAttr('%s.rotateOrder' % nukeCam[0], 5)

    # point constrain renderCam and renderCamNuke
    cmds.pointConstraint('renderCam', nukeCam[0], o=[0,0,0], mo=False, w=1)
    # orient constrain renderCam and renderCamNuke
    cmds.orientConstraint('renderCam', nukeCam[0], o=[0,0,0], mo=False, w=1)

    startFrame = cmds.playbackOptions(q=True, minTime=True)
    endFrame = cmds.playbackOptions(q=True, maxTime=True)

    # Select translate rotate in channel box of renderCamNuke and bake keys
    cmds.bakeResults(nukeCam[0], simulation=True, t=(startFrame, endFrame), sampleBy=1,
                     disableImplicitControl=True, preserveOutsideKeys=True, sparseAnimCurveBake=False,
                     removeBakedAttributeFromLayer=False, removeBakedAnimFromLayer=False,
                     bakeOnOverrideLayer=False, minimizeRotation=True, at=["tx","ty","tz","rx","ry","rz"])
