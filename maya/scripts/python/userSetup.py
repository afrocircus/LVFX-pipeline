import maya.cmds as mc
import maya.mel as mel
import pymel.core as pm
import maya.OpenMaya
import ftrack_api
import os
import pyblish.api
import pyblish_maya
from maya.utils import executeDeferred

print "loading custom plugins! ..."

def loadAndInit():
    setupPrefs()
    mc.loadPlugin('locoVFXPlugins.py', quiet=True)
    mc.spLocoVFXPlugin()
    if 'PROJECT_DIR' in os.environ:
        mel.eval('setProject "%s"' % os.environ['PROJECT_DIR'])

    # Load Pyblish plugins
    pyblish.api.register_gui('pyblish_lite')
    pyblish_maya.setup()

def setupPrefs():
    #set the current options on load of maya (incase someone manually changed them it their settings)
    pm.grid(size=1000, spacing=100, divisions=10)

    #setting the grid settings
    pm.optionVar (fv=("gridDivisions",10))
    pm.optionVar (fv=("gridSize",1000))
    pm.optionVar (fv=("gridSpacing",100))

    mc.displayColor('gridAxis', 2, dormant=True)
    mc.displayColor('gridHighlight', 1, dormant=True)
    mc.displayColor('grid', 3, dormant=True)

    #setting the units
    pm.optionVar (sv=("workingUnitLinear", "cm"))
    pm.optionVar (sv=("workingUnitLinearDefault", "cm"))


def onClose():
    if 'FTRACK_TASKID' in os.environ.keys():
        session = ftrack_api.Session(
            server_url=os.environ['FTRACK_SERVER'],
            api_user=os.environ['FTRACK_API_USER'],
            api_key=os.environ['FTRACK_API_KEY']
        )
        task = session.query('Task where id is %s' % os.environ['FTRACK_TASKID'])
        user = session.query('User where username is %s' % os.environ['FTRACK_API_USER']).one()
        user.stop_timer()


def addQuitAppCallback():
    mc.scriptJob(e=["quitApplication", "onClose()"])


if maya.OpenMaya.MGlobal.mayaState() == 0:
    mc.evalDeferred("loadAndInit()")
    executeDeferred("addQuitAppCallback()")
