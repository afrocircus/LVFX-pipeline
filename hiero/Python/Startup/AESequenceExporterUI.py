# Copyright (c) 2013 Matt Brealey
#v1.2

#Newness :

#v1.2
#Removed references to hiero.core.debug as they were unnecessary and the method has been moved.

#v1.1
#Added in support for AE CS5.5
#Added in support for Hiero 1.7

import os.path
import PySide.QtCore
import PySide.QtGui
import hiero

import hiero.ui
import AESequenceTask
from hiero.ui.FnUIProperty import UIPropertyFactory


class AESequenceUI(hiero.ui.TaskUIBase):
  def __init__(self, preset):
    """Initialize"""
    hiero.ui.TaskUIBase.__init__(self, AESequenceTask.AESequenceTask, preset, "AE Project")
    
    self._uiProperties = []
    
  def initialise(self, preset, exportStructure):
    """When Parent ExportStructure is opened in the ui,
    initialise is called for each preset. Register any callbacks here"""
    paths = preset.properties()["writePaths"]
    for path in paths:
      element = exportStructure.childElement(path)

      if element is not None:
        element.addCallback(preset.pathChanged)
            
  def writePresetChanged (self, topLeft, bottomRight):
    presetValue = self._preset._properties["writePaths"] = []

    model = self._writeModel
    for row in range(0, model.rowCount()):
      item = model.item(row, 0)
      if item.data(PySide.QtCore.Qt.CheckStateRole) == PySide.QtCore.Qt.Checked:
        presetValue.append(item.text())
        element = self._exportTemplate.childElement(item.text())
        if element is not None:
          element.addCallback(self._preset.pathChanged)

  def populateUI(self, widget, exportTemplate):
    if exportTemplate:
        self._exportTemplate = exportTemplate
        properties = self._preset.properties()
      
        layout = PySide.QtGui.QFormLayout()
        layout.setContentsMargins(9, 0, 9, 0)
        widget.setLayout(layout)
        layout.addRow(PySide.QtGui.QLabel("Note : Created Render Modules can only currently be set to TIFF."))
        
        #Add auto-save checkbox
        key, value, label = "autoSaveProject", True, "Auto-Save Project"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label+":", tooltip=label)
        
        layout.addRow(label+":", uiProperty)
        uiProperty.setToolTip("Auto-saves the newly generated project as a .aep file inside the export directory.")
        self._uiProperties.append(uiProperty)
        
        #Add create folders checkbox
        key, value, label = "createFolders", True, "Create Folders"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label+":", tooltip=label)
        layout.addRow(label+":", uiProperty)
        uiProperty.setToolTip("Automatically organises all media into relevant folders inside your AE project.")
        self._uiProperties.append(uiProperty)
        
        #Add timecode layer checkbox
        key, value, label = "addTimecodeLayer", True, "Add Timecode Layer"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label+":", tooltip=label)
        layout.addRow(label+":", uiProperty)
        uiProperty.setToolTip("Adds a 'Timecode' effect to the original plate. This will be created as a 'Guide' layer (i.e. it will not be rendered).")
        self._uiProperties.append(uiProperty)
        
        #Add log>lin layer checkbox
        key, value, label = "addLogLin", True, "Add Log>Lin Layer"
        uiProperty = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=self._preset._properties, label=label+":", tooltip=label)
        layout.addRow(label+":", uiProperty)
        uiProperty.setToolTip("Adds a 'Cineon Converter' effect to the original plate. Useful when viewing .dpx files at gamma 2.2.")
        self._uiProperties.append(uiProperty)
        
        #Add write options
        self._writeList = PySide.QtGui.QListView()
        self._writeList.setMinimumHeight(20)
        self._writeList.resize(160,20)
        self._writeList.setToolTip("Render modules will be created for every ticked entry in this list.<br><br>NOTE : Currently only .tiff files are setup for immediate render.")
        
        self._readModel = PySide.QtGui.QStandardItemModel()
        self._writeModel = PySide.QtGui.QStandardItemModel()
        
        # Default to the empty item unless the preset has a value set.
        for path, preset in exportTemplate.flatten():
            
            #If it's not a nukeWriteNode, continue
            if preset._parentType.__module__ != 'hiero.exporters.FnExternalRender':
                continue
        
            #Make item
            item = PySide.QtGui.QStandardItem(path)
            item.setFlags(PySide.QtCore.Qt.ItemIsUserCheckable | PySide.QtCore.Qt.ItemIsEnabled)
            item.setData(PySide.QtCore.Qt.Unchecked, PySide.QtCore.Qt.CheckStateRole)
            
            #If it needs to be checked, make it checked.
            if path in properties["writePaths"]:
                item.setData(PySide.QtCore.Qt.Checked, PySide.QtCore.Qt.CheckStateRole)
            
            #Append item
            self._writeModel.appendRow(item)

        self._writeList.setModel(self._writeModel)
        self._writeModel.dataChanged.connect(self.writePresetChanged)
        layout.addRow("Render Item Paths :", self._writeList)
        
    
hiero.ui.taskUIRegistry.registerTaskUI(AESequenceTask.AESequencePreset, AESequenceUI)
