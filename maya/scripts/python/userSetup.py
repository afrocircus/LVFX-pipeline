import maya.cmds as mc
import ftrack_api
import os

from maya.utils import executeDeferred

print "loading custom plugins! ..."

def loadAndInit():
    mc.loadPlugin('locoVFXPlugins.py', quiet=True)
    mc.spLocoVFXPlugin()


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


mc.evalDeferred("loadAndInit()")
executeDeferred("addQuitAppCallback()")
