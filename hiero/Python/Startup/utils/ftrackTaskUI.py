import PySide.QtGui as QtGui
import PySide.QtCore as QtCore
import hiero.ui
import hiero.core
import ftrackTask
import FnAssetAPI.ui
import assetmgr_hiero.utils as cmdUtils

from assetmgr_hiero.ui.widgets import TrackItemTimingOptionsWidget
from assetmgr_hiero.ui.widgets import AdvancedHieroItemSpreadsheet
from FnAssetAPI.specifications import ShotSpecification


class FtrackTaskUI(hiero.ui.TaskUIBase):
    def __init__(self, preset):
        """Initialize"""
        hiero.ui.TaskUIBase.__init__(self, ftrackTask.FtrackTask, preset, "Ftrack Project")
        #hiero.core.events.registerInterest("kShowContextMenu/kTimeline", self.test)

    def populateUI(self, widget, exportTemplate):
        if exportTemplate:
            print exportTemplate.exportRootPath()
            self._exportTemplate = exportTemplate
            '''layout = QtGui.QVBoxLayout()
            widget.setLayout(layout)
            self.initUI()
            self.buildUI(layout)
            self._connectUI()

    def initUI(self):
        self.kTargetEntityRef = 'targetEntityRef'
        self.kManagerOptionsShot = 'managerOptionsShot'
        self.kSetShotTimings = 'setShotTimings'
        self._session = FnAssetAPI.ui.UISessionManager.currentSession()
        self._context = self._session.createContext()
        self.__shotItems = []

        self.__updatingOptions = False

        self.__options = {
            self.kTargetEntityRef : '',
            self.kSetShotTimings : True
        }

        self._context.access = self._context.kWriteMultiple

        # We'll need to keep track of some lookups to avoid excess traffic
        self._parentEntity = None
        self._newShots = []
        self._existingShots = []
        self._conflictingShots = []

    def buildUI(self, layout):
        specification = ShotSpecification()

        pickerCls = self._session.getManagerWidget(
                    FnAssetAPI.ui.constants.kInlinePickerWidgetId, instantiate=False)
        parentPickerLayout = QtGui.QHBoxLayout()
        layout.addLayout(parentPickerLayout)
        parentPickerLayout.addWidget(QtGui.QLabel("Create Under:"))
        self._shotParentPicker = pickerCls(specification, self._context)
        parentPickerLayout.addWidget(self._shotParentPicker)

        shotsWidget = self.buildShotsTab()
        layout.addWidget(shotsWidget)

    def buildShotsTab(self):

        l = FnAssetAPI.l
        # > Shots Tab

        shotsWidget = QtGui.QWidget()
        shotsWidget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        shotsWidgetLayout = QtGui.QVBoxLayout()
        shotsWidgetLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        shotsWidget.setLayout(shotsWidgetLayout)

        self._tickIcon = QtGui.QIcon("icons:TagGood.png")
        self._actionIcon = QtGui.QIcon("icons:Add.png")

        self._shotsList = AdvancedHieroItemSpreadsheet()
        self._shotsList.setAlternatingRowColors(True)
        self._shotsList.setIcons(self._actionIcon, self._tickIcon)
        self._shotsList.setHiddenProperties(("nameHint",))
        self._shotsList.setForcedProperties(
            ("startFrame", "endFrame", "inFrame", "outFrame"))
        self._shotsList.setStatusText(l("New {shot}"), l("Existing {shot}"))

        self._shotsList.setDisabledCallback(self.__shotItemIsDisabled)
        shotsWidgetLayout.addWidget(self._shotsList)

        shotSpec = ShotSpecification()
        self._managerOptionsShot = self._session.getManagerWidget(
            FnAssetAPI.ui.constants.kRegistrationManagerOptionsWidgetId,
            throw=False, args=(shotSpec, self._context))
        if self._managerOptionsShot:
          shotsWidgetLayout.addWidget(self._managerOptionsShot)
          shotsWidgetLayout.addSpacing(10)

        self._shotLengthGBox = QtGui.QGroupBox("Set Shot Timings from Hiero")
        self._shotLengthGBox.setCheckable(True)
        self._shotLengthGBox.setChecked(False)
        slGbLayout = QtGui.QHBoxLayout()
        self._shotLengthGBox.setLayout(slGbLayout)

        self._shotLengthOptionsWidget = TrackItemTimingOptionsWidget()
        slGbLayout.addWidget(self._shotLengthOptionsWidget)
        slGbLayout.addStretch()

        self.refresh()
        shotsWidgetLayout.addWidget(self._shotLengthGBox)
        return shotsWidget

    def eventHandler(self, event):
        if hasattr(event.sender, 'getSelection') and event.sender.getSelection() is not None and len( event.sender.getSelection() ) != 0:
            self.__trackItems = event.sender.getSelection()

    def _connectUI(self):

        self._shotParentPicker.selectionChanged.connect(
            lambda v: self.__updateOption(self.kTargetEntityRef, v[0] if v else ''))

        self._shotLengthOptionsWidget.optionsChanged.connect(self.__timingOptionsChanged)

        self._shotLengthGBox.toggled.connect(self.__timingOptionsChanged)

    def __timingOptionsChanged(self):

        if self.__updatingOptions:
            return

        self.__options.update(self._shotLengthOptionsWidget.getOptions())
        self.__options[self.kSetShotTimings] = bool(self._shotLengthGBox.isChecked())
        # Force a full refresh
        self.__shotItems = []
        self._parentEntity = None
        self.refresh()

    def __updateOption(self, option, value, refresh=True, clearParent=False, clearItems=False):
        if self.__updatingOptions:
            return

        self.__options[option] = value
        if refresh:
            if clearParent:
                self._parentEntity = None
            if clearItems:
                self.__shotItems = []
            self.refresh()

    def _readOptions(self):

        self.__updatingOptions = True

        # Update main picked value
        targetEntityRef = self.__options.get(self.kTargetEntityRef, '')
        try:
            self._shotParentPicker.setSelectionSingle(targetEntityRef)
        except Exception as e:
                FnAssetAPI.logging.debug(e)

        # Manager Options

        managerOptionsShot = self.__options.get(self.kManagerOptionsShot, None)
        if managerOptionsShot and self._managerOptionsShot:
            self._managerOptionsShot.setOptions(managerOptionsShot)

        # Shot length options are read directly in the widget
        setTimings = self.__options.get(self.kSetShotTimings, True)
        self._shotLengthGBox.setChecked(setTimings)

        self.__updatingOptions = False

    def sizeHint(self):
        return QtCore.QSize(600, 400)

    def setTrackItems(self, trackItems):

        self.__trackItems = []

        self.__trackItems = trackItems
        self.__shotItems = [] # Clear cache
        self.refresh()

    def getTrackItems(self):
        return self.__trackItems

    def getOptions(self):

        options = dict(self.__options)

        managerOptionsShot = {}
        if self._managerOptionsShot:
            managerOptionsShot = self._managerOptionsShot.getOptions()
        options[self.kManagerOptionsShot] = managerOptionsShot

        options.update(self._shotLengthOptionsWidget.getOptions())
        self._preset._properties['ftrack_options'] = options
        self._preset._properties['trackItems'] = [item for item in self.__trackItems]
        return options

    def setOptions(self, options):

        self.__options.update(options)
        self._readOptions()

        self._shotLengthOptionsWidget.setOptions(options)

        if self._managerOptionsShot:
            managerOptions = options.get(self.kManagerOptionsShot, {})
            self._managerOptionsShot.setOptions(managerOptions)

        self.refresh()

    def __shotItemIsDisabled(self, item):
        return item in self._existingShots

    # This refreshes the UI based on its current state, it doesn't re-read the
    # options dict directly. If required, call _readOptions() first
    def refresh(self):

        session = FnAssetAPI.SessionManager.currentSession()
        if not session:
            raise RuntimeError("No Asset Management session available")

        if not self.__shotItems:

            self.__shotItems = cmdUtils.object.trackItemsToShotItems(self.__trackItems,
                self.getOptions(), coalesseByName=True)

        # Update Shot Creation

        parentRef = self.__options.get(self.kTargetEntityRef, None)

        # Ensure we don't waste time repeatedly looking under the same parent
        if not self._parentEntity or self._parentEntity.reference != parentRef:

            self._parentEntity = session.getEntity(parentRef, mustExist=True, throw=False)

            if self._parentEntity:
                newShots, existingShots, unused = cmdUtils.shot.analyzeHieroShotItems(
                    self.__shotItems, self._parentEntity, self._context,
                    adopt=True, checkForConflicts=False)

                self._newShots = newShots
                self._existingShots = existingShots

            self._shotsList.setItems(self.__shotItems)
            self._shotsList.setEnabled(bool(self._parentEntity))

    def __refreshClips(self):

        self.__clipItems, self.__sharedClipItems = \
            cmdUtils.shot.analyzeHeiroShotItemClips(self.__shotItems, asItems=True)

        if self.__options.get(self.kIgnorePublishedClips, True):
              itemFilter = lambda i : not i.getEntity()
              self.__clipItems = filter(itemFilter, self.__clipItems)
              self.__sharedClipItems = filter(itemFilter, self.__sharedClipItems)

        customClipName = None
        if self.__options.get(self.kClipsUseCustomName, False):
            customClipName = self.__options.get(self.kCustomClipName, None)
        if customClipName:
            for c in self.__clipItems:
                c.nameHint = customClipName

        # Update Clip publishing

        self._clipsGroup.setVisible(bool(self.__clipItems))
        self._clipsList.setItems(self.__clipItems)

        self._sharedClipsGroup.setVisible(bool(self.__sharedClipItems))
        self._sharedClipsList.setItems(self.__sharedClipItems)

        haveClips = bool(self.__sharedClipItems) or bool(self.__clipItems)
        self._noMedia.setVisible(not haveClips)


    def getButtonState(self):
        create = bool(self._newShots) and bool(self.__options[self.kTargetEntityRef])
        return "Create", create'''

hiero.ui.taskUIRegistry.registerTaskUI(ftrackTask.FtrackPreset, FtrackTaskUI)
