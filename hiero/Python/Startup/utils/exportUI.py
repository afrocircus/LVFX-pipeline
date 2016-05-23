import hiero.core
import hiero.ui

from PySide.QtGui import *
from PySide.QtCore import *


class ExportDialog(QDialog):

    def __init__(self,  selection, selectedPresets, parent=None):
        super(ExportDialog, self).__init__(parent)
        self.setWindowTitle("Export")
        self.setSizeGripEnabled(True)

        self._exportTemplate = None
        layout = QVBoxLayout()
        formLayout = QFormLayout()

        presetNames = [preset.name() for preset in hiero.core.taskRegistry.localPresets()]

        # List box for track selection
        presetListModel = QStandardItemModel()
        presetListView = QListView()
        presetListView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        presetListView.setModel(presetListModel)
        for preset in presetNames:
            item = QStandardItem(preset)
            if preset in selectedPresets:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

            item.setCheckable(True)
            presetListModel.appendRow(item)

        self._presetListModel = presetListModel
        presetListView.clicked.connect(self.presetSelectionChanged)

        formLayout.addRow("Presets:", presetListView)

        layout.addLayout(formLayout)

        self._exportTemplate = hiero.core.ExportStructure2()
        self._exportTemplateViewer = hiero.ui.ExportStructureViewer(self._exportTemplate)

        layout.addWidget(self._exportTemplateViewer)

        # Add the standard ok/cancel buttons, default to ok.
        self._buttonbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._buttonbox.button(QDialogButtonBox.StandardButton.Ok).setText("Export")
        self._buttonbox.button(QDialogButtonBox.StandardButton.Ok).setDefault(True)
        self._buttonbox.button(QDialogButtonBox.StandardButton.Ok).setToolTip("Executes exports on selection for each selected preset")
        self._buttonbox.accepted.connect(self.acceptTest)
        self._buttonbox.rejected.connect(self.reject)
        layout.addWidget(self._buttonbox)

        self.setLayout(layout)

    def acceptTest(self):
        self.accept()

    def presetSelectionChanged(self, index):
        if index.isValid():
            item = self._presetListModel.itemFromIndex(index)
            presetName = item.text()
            checked = item.checkState() == Qt.Checked

        if presetName:
            self._preset = hiero.core.taskRegistry.processorPresetByName(presetName)
            self._exportTemplate.restore(self._preset._properties["exportTemplate"])
            if self._preset._properties["exportRoot"] != "None":
                self._exportTemplate.setExportRootPath(self._preset._properties["exportRoot"])
            self._exportTemplateViewer.setExportStructure(self._exportTemplate)
            self._resolver = self._preset.createResolver().addEntriesToExportStructureViewer(self._exportTemplateViewer)

    def presets(self):
        presets = []
        for row in range(0, self._presetListModel.rowCount()):
            item = self._presetListModel.item(row)
            presetName = item.text()
            checked = item.checkState() == Qt.Checked
            if checked:
                presets.append(presetName)

        return presets
