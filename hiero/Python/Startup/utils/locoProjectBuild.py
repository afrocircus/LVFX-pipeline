import hiero.core

from PySide.QtGui import *
from exportUI import ExportDialog


class ExportAction(QAction):

    def __init__(self):
        QAction.__init__(self, "Multi Export", None)
        self.triggered.connect(self.doit)
        hiero.core.events.registerInterest("kShowContextMenu/kBin", self.eventHandler)
        self._selectedPresets = []

    class CustomItemWrapper:

        def __init__(self, item):
            self._item = item

            if isinstance(self._item, hiero.core.BinItem):
                self._item = self._item.activeItem()

        def isNull(self):
            return self._item == None

        def sequence(self):
            if isinstance(self._item, hiero.core.Sequence):
                return self._item
            return None

        def clip(self):
            if isinstance(self._item, hiero.core.Clip):
                return self._item
            return None

        def trackItem(self):
            if isinstance(self._item, hiero.core.TrackItem):
                return self._item
            return None

        def name(self):
            return self._item.name()

    def doit(self):
        # Prepare list of selected items for export
        selection = [ExportAction.CustomItemWrapper(item) for item in hiero.ui.activeView().selection()]

        # Create dialog
        dialog = ExportDialog(selection, self._selectedPresets)
        # If dialog returns true
        if dialog.exec_():
            # Grab list of selected preset names
            self._selectedPresets = dialog.presets()
            for presetName in self._selectedPresets:
                # Grab preset from registry
                preset = hiero.core.taskRegistry.processorPresetByName(presetName)
                # Launch export
                hiero.core.taskRegistry.createAndExecuteProcessor(preset, selection)

    def eventHandler(self, event):
        if not hasattr(event.sender, 'selection'):
            # Something has gone wrong, we shouldn't only be here if raised
            # by the timeline view which will give a selection.
            return
        s = event.sender.selection()
        if s is None:
            s = ()  # We disable on empty selection.
        title = "Loco Export"
        self.setText(title)
        if len(s) > 0:
            event.menu.addAction(self)
