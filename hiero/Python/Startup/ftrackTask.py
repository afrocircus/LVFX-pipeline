import hiero.core
import utils.ftrackHelper as ftrackHelper


class FtrackTask(hiero.core.TaskBase):
    def __init__(self, initDict):
        """Initialize"""
        hiero.core.TaskBase.__init__(self, initDict)

    def startTask(self):
        hiero.core.TaskBase.startTask(self)
        trackItems = self._preset.properties()['trackItems']
        options = self._preset.properties()['ftrack_options']
        try:
            result = ftrackHelper.createShotsFromTrackItemsUI(trackItems, options)
        except Exception, e:
            self.setError("Error: Cannot export shots to ftrack. \n %s" % e)

        self.updateShotMetadata()

    def updateShotMetadata(self):
        for (itemPath, itemPreset) in self._exportTemplate.flatten():
            if itemPreset.name() == 'LocoNukeShotExporterTask.LocoNukeShotExporterTask':
                taskData = hiero.core.TaskData(itemPreset, self._item, self._exportRoot, itemPath, self._version, self._exportTemplate,
                                                    project=self._project, cutHandles=self._cutHandles, retime=self._retime, startFrame=self._startFrame, resolver=self._resolver, skipOffline=self._skipOffline)
                task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)

                resolvedPath = task.resolvedExportPath()


    def finishTask(self):
        hiero.core.TaskBase.finishTask(self)


class FtrackPreset(hiero.core.TaskPresetBase):

    def __init__(self, name, properties):
        hiero.core.TaskPresetBase.__init__(self, FtrackTask, name)
        self._properties = {}
        self._properties['ftrack_options'] = {}
        self._properties.update(properties)

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems

hiero.core.log.debug( "Registering FtrackTask" )
hiero.core.taskRegistry.registerTask(FtrackPreset, FtrackTask)
