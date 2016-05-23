import maya.cmds as mc

print "loading custom plugins ..."

def loadAndInit():
    mc.loadPlugin('shotSubmitPlugin.py', quiet=True)
    mc.spLoadSubmitPlugin()

mc.evalDeferred("loadAndInit()")
