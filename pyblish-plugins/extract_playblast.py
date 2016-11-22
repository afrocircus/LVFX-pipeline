import os
import pyblish.api
import ftrack
import json
import datetime
from Utils import capture
import maya.cmds as cmds


def load_preset(path):
    """Load options json from path"""
    with open(path, "r") as f:
        return json.load(f)


@pyblish.api.log
class ExtractPlayblast(pyblish.api.InstancePlugin):

    order = pyblish.api.ExtractorOrder
    hosts = ['maya']
    label = 'Extract Playblast'
    families = ['scene']
    optional = True

    def process(self, instance):

        task = ftrack.Task(instance.context.data['taskid'])
        taskName = task.getType().getName().lower()
        if taskName not in ['animation', 'layout']:
            self.log.info('Skipping playblast for %s' % taskName)
            return

        playblastDir = os.path.join(instance.data['workPath'], 'playblast')
        if not os.path.exists(playblastDir):
            os.makedirs(playblastDir)
        version = instance.data['vprefix'] + instance.data['version']
        shotName = task.getParent().getName()

        users = [user.get('firstname') for user in task.getUsers()]
        usernames = ', '.join(users)
        projectName = task.getProject().getName()
        self.shotInfo = '{0} | {1} | {2} | {3} | {4}'.format(projectName, shotName,
                                                             taskName, version, usernames)

        outFile = os.path.join(playblastDir, '{0}_{1}_playblast.mov'.format(shotName, version))
        instance.set_data('playblastFile', value=outFile)

        presetName = 'default'

        presetPath = os.path.join(os.path.dirname(capture.__file__),
                                  'capture_presets',
                                  (presetName + '.json'))
        preset = load_preset(presetPath)
        preset['camera'] = 'renderCam'

        self.addHUD()

        capture.capture(filename=outFile,
                        overwrite=True,
                        quality=70, compression='jpeg',
                        **preset)
        self.removeHUD()

        self.log.info('extract playblast')

    def getShotInfo(self, *args):
        shotInfo = self.shotInfo
        return shotInfo

    def getDate(self, *args):
        today = datetime.datetime.today()
        dateStr = '%02d-%02d-%d' % (today.day, today.month, today.year)
        return dateStr

    def getFrame(self, *args):
        frameCount = cmds.currentTime(q=True)
        return frameCount

    def addHUD(self):
        self.removeHUD()
        cmds.displayColor('headsUpDisplayLabels', 18, dormant=True)
        cmds.headsUpDisplay('leftTopHUD', section=0, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getShotInfo, atr=True)
        cmds.headsUpDisplay('rightTopHUD', section=4, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getDate, atr=True)
        cmds.headsUpDisplay('rightBottomHUD', section=9, block=1, blockSize='medium', dataFontSize='large',
                       command=self.getFrame, atr=True)

    def removeHUD(self):
        headsUpDisplayList = cmds.headsUpDisplay(lh=True)
        for headDisplay in headsUpDisplayList:
            cmds.headsUpDisplay(headDisplay, rem=True)