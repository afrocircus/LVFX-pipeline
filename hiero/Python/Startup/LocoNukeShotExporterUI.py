import PySide.QtGui
import hiero.ui
import LocoNukeShotExporterTask


class LocoNukeShotExporterUI(hiero.ui.TaskUIBase):
    def __init__(self, preset):
        hiero.ui.TaskUIBase.__init__(self, LocoNukeShotExporterTask.LocoNukeShotExporterTask,
                                     preset, "Loco Nuke Project")
        self._uiProperties = []
        self._tags = []

    def initialise(self, preset, exportStructure):
        paths = preset.properties()["readPaths"] + preset.properties()["writePaths"]
        for path in paths:
            element = exportStructure.childElement(path)

            if element is not None:
                element.addCallback(preset.pathChanged)

    def readPresetChanged (self, topLeft, bottomRight):
        hiero.core.log.debug( "readPresetChanged" )
        presetValue = self._preset.properties()["readPaths"] = []
        model = self._readModel
        for row in range(0, model.rowCount()):
            item = model.item(row, 0)
            if item.data(PySide.QtCore.Qt.CheckStateRole) == PySide.QtCore.Qt.Checked:
                presetValue.append(item.text())
                element = self._exportTemplate.childElement(item.text())
                if element is not None:
                    element.addCallback(self._preset.pathChanged)

        hiero.core.log.debug( "readPaths (%s)" % str(presetValue) )

    def writePresetChanged (self, topLeft, bottomRight):
        hiero.core.log.debug( "writePresetChanged" )
        presetValue = self._preset.properties()["writePaths"] = []

        model = self._writeModel
        for row in range(0, model.rowCount()):
            item = model.item(row, 0)
            if item.data(PySide.QtCore.Qt.CheckStateRole) == PySide.QtCore.Qt.Checked:
                presetValue.append(item.text())
                element = self._exportTemplate.childElement(item.text())
                if element is not None:
                    element.addCallback(self._preset.pathChanged)

        hiero.core.log.debug( "writePaths (%s)" % str(presetValue) )

    def populateUI(self, widget, exportTemplate):
        if exportTemplate:
            self._exportTemplate = exportTemplate
            properties = self._preset.properties()

            layout = PySide.QtGui.QFormLayout()
            self._readList = PySide.QtGui.QListView()
            self._writeList = PySide.QtGui.QListView()

            self._readList.setMinimumHeight(50)
            self._writeList.setMinimumHeight(50)
            self._readList.resize(200,50)
            self._writeList.resize(200,50)

            self._readModel = PySide.QtGui.QStandardItemModel()
            self._writeModel = PySide.QtGui.QStandardItemModel()

            for model, presetValue in ((self._readModel, properties["readPaths"]),
                                       (self._writeModel, properties["writePaths"])):
                for path, preset in exportTemplate.flatten():
                    if preset is self._preset:
                        continue

                    if model is self._readModel:
                        if not 'plates' in path:
                            continue

                    if model is self._writeModel:
                        if not 'img/comps' in path and not 'img/renders' in path:
                            continue
                        if not hasattr(preset._parentType, 'nukeWriteNode'):
                            continue

                    item = PySide.QtGui.QStandardItem(path)
                    item.setFlags(PySide.QtCore.Qt.ItemIsUserCheckable | PySide.QtCore.Qt.ItemIsEnabled)

                    item.setData(PySide.QtCore.Qt.Unchecked, PySide.QtCore.Qt.CheckStateRole)
                    if path in presetValue:
                        item.setData(PySide.QtCore.Qt.Checked, PySide.QtCore.Qt.CheckStateRole)

                    model.appendRow(item)

            self._readList.setModel(self._readModel)
            self._writeList.setModel(self._writeModel)

            readNodeListToolTip = """Select multiple entries within the shot template to be used as inputs for the read nodes (i.e. symlink, transcode.. etc).\n No selection will mean that read nodes are created in the nuke script pointing directly at the source media.\n"""
            writeNodeListToolTip = """Add one or more "Nuke Write Node" tasks to your export structure to define the path and codec settings for the nuke script.\nIf no write paths are selected, no write node will be added to the nuke script."""

            self._readList.setToolTip(readNodeListToolTip)
            self._writeList.setToolTip(writeNodeListToolTip)
            self._readModel.dataChanged.connect(self.readPresetChanged)
            layout.addRow("Read Nodes:", self._readList)
            self._writeModel.dataChanged.connect(self.writePresetChanged)
            layout.addRow("Write Nodes:", self._writeList)
            widget.setLayout(layout)

hiero.ui.taskUIRegistry.registerTaskUI(LocoNukeShotExporterTask.LocoNukeShotExporterPreset, LocoNukeShotExporterUI)
