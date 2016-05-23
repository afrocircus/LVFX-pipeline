import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.mel as mm
import maya.cmds as cmds

kPluginCmdName = "spLoadSubmitPlugin"

# Command
class scriptedCommand(OpenMayaMPx.MPxCommand):
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)

    # Invoked when the command is run.
    def doIt(self,argList):
        gMainWindow = mm.eval('$temp1=$gMainWindow')
        if cmds.menu('LocoVFX', exists=True):
            cmds.deleteUI('LocoVFX')
        showMyMenuCtrl = cmds.menu('LocoVFX', parent=gMainWindow, tearOff=False, label='LocoVFX')
        cmd = self.constructShotSubmitCmd()
        cmds.menuItem(parent=showMyMenuCtrl, label='ShotSubmit', command=cmd)

    def constructShotSubmitCmd(self):
        cmd = 'from shot_submit import submitUI\n'
        cmd += 'form = submitUI.ShotSubmitUI()\n'
        cmd += 'form.createDockLayout()'
        return cmd

# Creator
def cmdCreator():
    return OpenMayaMPx.asMPxPtr( scriptedCommand() )

# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerCommand( kPluginCmdName, cmdCreator )
    except:
        sys.stderr.write( "Failed to register command: %sn" % kPluginCmdName )
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %sn" % kPluginCmdName )
