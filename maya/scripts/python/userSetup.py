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
    mc.loadPlugin('locoVFXPlugins.py', quiet=True)
    mc.spLocoVFXPlugin()
    if 'PROJECT_DIR' in os.environ:
        mel.eval('setProject "%s"' % os.environ['PROJECT_DIR'])

    # Load Pyblish plugins
    pyblish.api.register_gui('pyblish_lite')
    pyblish_maya.setup()
    setupPrefs()

def getFPSpreset(fps):
    if fps == '15.0':
        return 'game'
    elif fps == '24.0':
        return 'film'
    elif fps == '25.0':
        return 'pal'
    elif fps == '30.0':
        return 'ntsc'
    elif fps == '48.0':
        return 'show'
    elif fps == '50.0':
        return 'palf'
    elif fps == '60.0':
        return 'ntscf'
    else:
        return 'film'

def setupPrefs():
    #set the current options on load of maya (incase someone manually changed them it their settings)
    pm.playbackOptions(min=1, max=120)
    pm.currentTime(1)
    if 'FS' in os.environ and 'FE' in os.environ:
        first = os.environ['FS']
        last = os.environ['FE']
        fps = os.environ['FPS']
        fpsPreset = getFPSpreset(fps)
        mc.currentUnit(time=fpsPreset)
        if not first == '1' and not last == '2':
            pm.playbackOptions(minTime=first, maxTime=last, animationStartTime=first,
                               animationEndTime=last)
            pm.currentTime(first)

    '''pm.grid(size=1000, spacing=100, divisions=10)
    pm.optionVar (fv=("playbackMax",120))
    pm.optionVar (fv=("playbackMaxDefault",120))
    pm.optionVar (fv=("playbackMaxRange",120))
    pm.optionVar (fv=("playbackMaxRangeDefault",120))
    pm.optionVar (fv=("playbackMin",1))
    pm.optionVar (fv=("playbackMinDefault",1))
    pm.optionVar (fv=("playbackMinRange",1))
    pm.optionVar (fv=("playbackMinRangeDefault",1))'''

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
