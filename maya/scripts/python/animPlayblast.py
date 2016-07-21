from pymel.core import *
import datetime

class UI(object):

    def __init__(self, *args):
        self.win = 'window2'
        if window(self.win, q=True, ex=True):
            deleteUI(self.win)

    def buildUI(self):
        self.showHUD()
        template = uiTemplate('PlayblastTemplate', force=True)
        template.define(button, width=100, height=30, align='left')
        template.define(frameLayout, borderVisible=True, labelVisible=False)

        with window(s=True, title='Animation Playblast') as win:
            # start the template block
            with template:
                with columnLayout(adj=True):
                    text('')
                    with frameLayout():
                        with horizontalLayout(spacing=5):
                            button(label='Show HUD', bgc=(0.5, 0.2, 0.5), command=self.showHUD)
                            button(label='HIDE HUD', bgc=(0.1, 0.6, 0.9), command=self.hideHUD)
                    text(' ')
                    with frameLayout():
                        with columnLayout(rowSpacing=2, adj=True):
                            button(label='Playblast', bgc=(0.2, 0.2, 0.2))
                            with horizontalLayout():
                                button(label='Load Latest Playblast', bgc=(0.2, 0.2, 0.1))
                                button(label='Load Selected Playblast', bgc=(0.2, 0.2, 0.1))
                            with horizontalLayout():
                                button(label='Upload Latest to Dailies', bgc=(0.5, 0.5, 0.1))
                                button(label='Upload Selected to Dailies', bgc=(0.5, 0.5, 0.1))

    def getShotInfo(self, *args):
        return 'project | shot | task | ver | user'

    def getDate(self, *args):
        today = datetime.datetime.today()
        dateStr = '%02d-%02d-%d' % (today.day, today.month, today.year)
        return dateStr

    def getFrame(self, *args):
        return 3


    def HUD(self):
        displayColor('headsUpDisplayLabels', 18, dormant=True)
        headsUpDisplay('leftTopHUD', section=0, block=1, blockSize='medium', dataFontSize='large', command=self.getShotInfo, atr=True)
        headsUpDisplay('rightTopHUD', section=4, block=1, blockSize='medium', dataFontSize='large', command=self.getDate, atr=True)
        headsUpDisplay('rightBottomHUD', section=9, block=1, blockSize='medium', dataFontSize='large', command=self.getFrame, atr=True)

    def showHUD(self, *args):
        headsUpDisplayList = headsUpDisplay(lh=True)
        if headsUpDisplayList:
            for headDisplay in headsUpDisplayList:
                headsUpDisplay(headDisplay, rem=True)
        self.HUD()

    def hideHUD(self, *args):
        headsUpDisplayList = headsUpDisplay(lh=True)
        for headDisplay in headsUpDisplayList:
            headsUpDisplay(headDisplay, rem=True)

ui = UI()
ui.buildUI()