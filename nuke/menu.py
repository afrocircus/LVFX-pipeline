# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

# Import to bootstrap foundry api.
import sys
import nuke
from nukescripts import panels
from plugins.shot_submit import submitUI
from plugins.NukeProResPlugin import nukeProRes
from scripts import ftrackUpload
from scripts import writeNodeManager
from scripts import slate
from scripts import easySave


def addCustomPanel1():
    pythonPanel = panels.registerWidgetAsPanel('submitUI.ShotSubmitUI', 'Shot Submit', 'locovfx.shotSubmit.plugin', True)
    return pythonPanel.addToPane()

def addCustomPanel2():
    pythonPanel = panels.registerWidgetAsPanel('nukeProRes.NukeProResWindow', 'ProRes Tool', 'locovfx.prores.plugin', True)
    return pythonPanel.addToPane()

nuke.pluginAddPath('')
nuke.menu('Nuke').addCommand('File/LVFX-Save New Version', easySave.save, 'Alt+Shift+S')
menubar = nuke.menu("Nuke")
toolbar = menubar.addMenu("LocoVFX")
m = toolbar.addMenu('gizmos')
m.addCommand("Slate", "nuke.createNode(\"slate\")", icon="V_Slate.png")
nuke.menu('Nuke').addCommand('LocoVFX/Shot Submit', addCustomPanel1)
panels.registerWidgetAsPanel('submitUI.ShotSubmitUI', 'Shot Submit', 'locovfx.shotSubmit.plugin')
nuke.menu('Nuke').addCommand('LocoVFX/ProRes Tool', addCustomPanel1)
panels.registerWidgetAsPanel('nukeProRes.NukeProResWindow', 'ProRes Tool', 'locovfx.prores.plugin')
