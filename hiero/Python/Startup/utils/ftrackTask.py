import hiero.core
#import ftrackHelper


class FtrackTask(hiero.core.TaskBase):
    def __init__(self, initDict):
        """Initialize"""
        print "ftrackTask"
        hiero.core.TaskBase.__init__(self, initDict)

    def startTask(self):
        hiero.core.TaskBase.startTask(self)
        trackItems = self._preset.properties()['trackItems']
        options = self._preset.properties()['ftrack_options']
        #result = ftrackHelper.createShotsFromTrackItemsUI(trackItems, options)
        #if result == []:
          #  self.setError("Error: Cannot export shots to ftrack")

    def finishTask(self):
        hiero.core.TaskBase.finishTask(self)
        print "end of task"


class FtrackPreset(hiero.core.TaskPresetBase):

    def __init__(self, name, properties):
        print "ftrackPreset"
        hiero.core.TaskPresetBase.__init__(self, FtrackTask, name)
        self._properties = {}
        #self._properties['ftrack_options'] = {}
        self._properties.update(properties)

    #def supportedItems(self):
     #   return hiero.core.TaskPresetBase.kAllItems

hiero.core.log.debug( "Registering FtrackTask" )
hiero.core.taskRegistry.registerTask(FtrackPreset, FtrackTask)
