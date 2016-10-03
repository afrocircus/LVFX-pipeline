"""PJC - Camera Overlay for Maya 2015

#====================================================
#	PJC - Camera Overlay for Maya 2015
#
#	This allows users to create a Golden Spiral or
#	Rule of Thirds overlay for thier viewport within
#	Maya 2015.
#
#	Version 0.4
#
#====================================================
"""
__author__ = "PeJayCee"
__version__ = "0.4"

#====================================================
#	Imports
#====================================================

import maya.cmds as cmds
import math

#====================================================
#	Class for creating Camera Overlays
#====================================================

class Overlay_Function(object):
    def __init__(self):
        print "running overlay"
        self.currentOverlay = ""

    #====================================================
    #	Method for getting camera data
    #====================================================

    def cameraQuery(self, **kwargs):
        return cmds.camera(self.camera, query=True, **kwargs)

    #====================================================
    #	Method for defining camera properties
    #====================================================

    def cameraProperties(self): ###Code from Chris Zurbrigg (http://zurbrigg.com), Shot Mask
        self.camera = Overlay_Function.active_camera()
        self.near_clip = self.cameraQuery(nearClipPlane=True)
        if self.near_clip < 0.1:
            self.near_clip = 0.1
        self.nearClipOffset = self.near_clip + (self.near_clip * 0.2)###Mulitpled by 0.2 as that worked with orthogrphic cameras
        self.film_fit = self.cameraQuery(filmFit=True)
        self.aspect_ratio = cmds.getAttr("defaultResolution.deviceAspectRatio")
        self.camera_aspect_ratio = self.cameraQuery(aspectRatio=True)

        if self.cameraQuery(orthographic=True):
            self.width = self.cameraQuery(orthographicWidth=True)
            self.height = self.width / self.aspect_ratio
            self.label_plane_width = self.width
            self.label_plane_height = self.height
        else:
            scale = 1.0
            if self.film_fit == "horizontal":
                fov = math.radians(self.cameraQuery(horizontalFieldOfView=True))
            elif self.film_fit == "vertical":
                fov = math.radians(self.cameraQuery(verticalFieldOfView=True))
            elif self.film_fit == "fill":
                fov = math.radians(self.cameraQuery(horizontalFieldOfView=True))
                if self.camera_aspect_ratio > self.aspect_ratio:
                    scale = self.aspect_ratio / self.camera_aspect_ratio
            elif self.film_fit == "overscan":
                fov = math.radians(self.cameraQuery(horizontalFieldOfView=True))
                if self.camera_aspect_ratio < self.aspect_ratio:
                    scale = self.aspect_ratio / self.camera_aspect_ratio

            if self.film_fit == "vertical":
                self.height = 2 * math.tan(fov * 0.5) * self.nearClipOffset * scale
                self.width = self.height * self.aspect_ratio
                self.label_plane_height = 2 * math.tan(fov * 0.5) * self.nearClipOffset * scale
                self.label_plane_width = self.label_plane_height * self.aspect_ratio
            else:
                self.width = 2 * math.tan(fov * 0.5) * self.nearClipOffset * scale
                self.height = self.width / self.aspect_ratio
                self.label_plane_width = 2 * math.tan(fov * 0.5) * self.nearClipOffset * scale
                self.label_plane_height = self.label_plane_width / self.aspect_ratio

    #====================================================
    #	Method for creating Rule of Thirds Grid
    #====================================================

    def createThirdsGrid(self):
        self.cameraProperties()
        groupName = self.camera + "_thirds_Grid" ###Names based on cameras so each camera cna have its own overlay
        self.currentOverlay = groupName
        if cmds.objExists(groupName): cmds.delete(groupName)
        self.plane_Name = self.camera + "_Plane_Test_001"
        self.planeTopH = self.camera + "_H_Top_Line_001"
        self.planeBaseH = self.camera + "_H_Base_Line_001"
        self.planeLeftV = self.camera + "_V_Left_Line_001"
        self.planeRightV = self.camera + "_V_Right_Line_001"
        self.lines = (self.planeTopH, self.planeBaseH, self.planeLeftV, self.planeRightV)
        cmds.createNode("transform", name = groupName)
        self.widthPixels = cmds.getAttr("defaultResolution.width")
        self.heightPixels = cmds.getAttr("defaultResolution.height")

        for line in self.lines:
            if "_H_" in line:
                cmds.curve(ep=[(self.width/2, 0, 0), (-self.width/2, 0, 0)], name = line)
            elif "_V_" in line:
                cmds.curve(ep=[(0, 0, self.height/2), (0, 0, -self.height/2)], name = line)
            cmds.parent(line, groupName)
            heightSixth = self.height/6
            widthSixth = self.width/6
            if "_Top_Line_001" in line:
                cmds.move(0, 0, -heightSixth, line)
            elif "_Base_Line_001" in line:
                cmds.move(0, 0, heightSixth, line)
            elif "_Left_Line_001" in line:
                cmds.move(-widthSixth, 0, 0, line)
            elif "_Right_Line_001" in line:
                cmds.move(widthSixth, 0, 0, line)

        cmds.parentConstraint(self.camera, groupName, name="positionMatch_parentConstraint")
        cmds.delete("positionMatch_parentConstraint")
        cmds.rotate(90, 0, 0, groupName, relative=True, objectSpace=True)
        cmds.move(0, -self.nearClipOffset, 0, groupName, relative=True, objectSpace=True)
        cmds.parentConstraint(self.camera, groupName, maintainOffset=True)
        cmds.setAttr(groupName + ".overrideEnabled", 1)
        cmds.setAttr(groupName + ".overrideDisplayType", 2)
        cmds.setAttr(groupName + ".hiddenInOutliner", True)
        cmds.select(clear=True)

    #====================================================
    #	Method for creating Golden Spiral
    #====================================================

    def createGoldenSprial(self, position = "topRight"):
        ###Technocally it's the fibonacci spiral, but it makes little difference
        self.cameraProperties()
        lineName = self.camera + "_goldenSpiral"
        groupName = self.camera + "_goldenSpiral_GRP"
        rectName = self.camera + "_rectGuide"
        self.currentOverlay = groupName
        if cmds.objExists(groupName): cmds.delete(groupName)
        spiral = [[24.0, 0.0, 105.0], [18.18431634044607, 0.0, 105.0], [6.520717642368542, 0.0, 103.85257921630085], [-10.27721821557151, 0.0, 98.75531247827209], [-25.76479766304041, 0.0, 90.47784123163812], [-39.338095564734445, 0.0, 79.33809556473445], [-50.47784123163818, 0.0, 65.76479766304038], [-58.75531247827203, 0.0, 50.27721821557151], [-63.85257921630085, 0.0, 33.47928235763141], [-65.0, 0.0, 16.0], [-65.0, 0.0, 12.406038187916112], [-64.29091974041066, 0.0, 5.1981962958457295], [-61.1409234416288, 0.0, -5.182550582656557], [-56.02563222179889, 0.0, -14.753526645699132], [-49.141519731015684, 0.0, -23.141519731015677], [-40.75352664569914, 0.0, -30.025632221798872], [-31.18255058265658, 0.0, -35.14092344162877], [-20.801803704154278, 0.0, -38.29091974041066], [-10.0, 0.0, -39.0], [-7.77827815252996, 0.0, -39.0], [-3.322521346522819, 0.0, -38.56165947589022], [3.0946676329149643, 0.0, -36.61438903664323], [9.011271017341269, 0.0, -33.452209009839294], [14.196575833718772, 0.0, -29.196575833718782], [18.452209009839294, 0.0, -24.011271017341272], [21.61438903664324, 0.0, -18.094667632914962], [23.561659475890206, 0.0, -11.677478653477182], [24.0, 0.0, -5.0], [24.005876601429442, 0.0, -3.706886690924809], [23.777412722891853, 0.0, -1.1132035754530578], [22.725648103755358, 0.0, 2.6428499013860374], [21.00074561066001, 0.0, 6.142702307822074], [18.661528357191525, 0.0, 9.265192323173274], [15.787950237524708, 0.0, 11.904212983392663], [12.477613553125305, 0.0, 13.969624931029786], [8.845207686558368, 0.0, 15.390812517336583], [5.0, 0.0, 16.0], [4.072031773535475, 0.0, 16.14455275501771], [2.178234471274524, 0.0, 16.23193299826233], [-0.6188927288192801, 0.0, 15.747973105934456], [-3.2474216220209264, 0.0, 14.672714373118492], [-5.582182864322244, 0.0, 13.056364843448742], [-7.513966991581316, 0.0, 10.97504171949949], [-8.95190740736182, 0.0, 8.526027051197591], [-9.828515227699702, 0.0, 5.826083259151342], [-10.0, 0.0, 3.0], [-10.0, 0.0, 2.4772419182423433], [-9.89686105315064, 0.0, 1.428828552123016], [-9.438679773327824, 0.0, -0.08109826656822744], [-8.694637414079837, 0.0, -1.4732402393744184], [-7.693311960875005, 0.0, -2.6933119608750067], [-6.47324023937442, 0.0, -3.694637414079835], [-5.081098266568228, 0.0, -4.438679773327824], [-3.571171447876985, 0.0, -4.896861053150637], [-2.0, 0.0, -5.000000000000001], [-1.6732761989014646, 0.0, -5.0], [-1.0180178450768846, 0.0, -4.935538158219152], [-0.07431358339485825, 0.0, -4.649174858329889], [0.7957751496090115, 0.0, -4.184148383799899], [1.55831997554688, 0.0, -3.558319975546878], [2.1841483837998963, 0.0, -2.7957751496090113], [2.6491748583298893, 0.0, -1.925686416605141], [2.935538158219149, 0.0, -0.9819821549231146], [3.0, 0.0, 0.0], [3.0, 0.0, 0.19603428065912115], [2.96132289493149, 0.0, 0.5891892929538691], [2.7895049149979334, 0.0, 1.1554118499630852], [2.5104890302799383, 0.0, 1.6774650897654066], [2.134991985328128, 0.0, 2.1349919853281283], [1.6774650897654064, 0.0, 2.510489030279938], [1.1554118499630845, 0.0, 2.7895049149979334], [0.5891892929538686, 0.0, 2.961322894931488]]
        rectangle = [[24, 0, 105], [-65, 0, 105], [-65, 0, -39], [24, 0, -39], [24, 0, 105]]
        shapes = [spiral, rectangle]
        for shape in shapes:
            scaledShape=[]
            for coords in shape:
                if self.aspect_ratio > 1.6180339887:###If greater than golden Ratio
                    multiplied = tuple([x*self.height*0.011236 for x in coords]) ###Then match to height
                else:
                    multiplied = tuple([x*self.width*0.0069444 for x in coords]) ###Else match to width
                scaledShape.append(multiplied)

            if cmds.objExists(lineName):
                cmds.curve(p = scaledShape, d = 1, name = rectName)
            else:
                cmds.curve(p = scaledShape, d = 3, name = lineName)

        cmds.xform(lineName, centerPivots = True)
        cmds.xform(rectName, centerPivots = True)
        cmds.createNode("transform", name = groupName)
        cmds.addAttr(longName = "position", dataType = "string")
        cmds.parent(lineName, groupName)
        cmds.parent(rectName, groupName)
        cmds.xform(groupName, centerPivots = True)
        cmds.parentConstraint(self.camera, groupName, name="positionMatch_parentConstraint")
        cmds.delete("positionMatch_parentConstraint")
        cmds.rotate(-90, 0, 0, groupName, relative=True, objectSpace=True)
        cmds.rotate(0, -90, 0, groupName, relative=True, objectSpace=True)
        cmds.move(0, self.nearClipOffset, 0, groupName, relative=True, objectSpace=True)

        if position == "topRight":
            cmds.setAttr(groupName + ".position", "topRight", type = "string")
        elif position == "topLeft":
            cmds.scale(1, 1, -1, groupName, relative=True, objectSpace=True)
            cmds.setAttr(groupName + ".position", "topLeft", type = "string")
        elif position == "bottomRight":
            cmds.scale(-1, 1, 1, groupName, relative=True, objectSpace=True)
            cmds.setAttr(groupName + ".position", "bottomRight", type = "string")
        elif position == "bottomLeft":
            cmds.scale(-1, 1, -1, groupName, relative=True, objectSpace=True)
            cmds.setAttr(groupName + ".position", "bottomLeft", type = "string")
        cmds.parentConstraint(self.camera, groupName, maintainOffset=True)
        cmds.setAttr(groupName + ".overrideEnabled", 1)
        cmds.setAttr(groupName + ".overrideDisplayType", 2)
        cmds.setAttr(groupName + ".hiddenInOutliner", True)
        cmds.select(clear=True)

    #====================================================
    #	Method for Toggling Rule of Thirds Grid
    #====================================================

    def toggleThirdsGrid(self):
        if Overlay_Function.active_camera() == None:
            raise Exception("No active camera  viewport")
        cmds.undoInfo(stateWithoutFlush = False)
        self.cameraProperties()
        self.checkCurrentOverlay()
        groupName = self.camera + "_thirds_Grid"
        if self.currentOverlay == groupName:
            cmds.delete(groupName)
        else:
            try:
                cmds.delete(self.currentOverlay)
            except:
                pass
            self.createThirdsGrid()
        cmds.undoInfo(stateWithoutFlush = True)

    #====================================================
    #	Methods for Toggling Golden Spiral
    #====================================================

    def toggleGoldenSprial(self, position = "None"):
        if Overlay_Function.active_camera() == None:
            raise Exception("No active camera  viewport")
        cmds.undoInfo(stateWithoutFlush = False)
        self.cameraProperties()
        self.checkCurrentOverlay()
        groupName = self.camera + "_goldenSpiral_GRP"
        try:
            positionAttr = groupName + ".position"
            positionValue = cmds.getAttr(positionAttr)

            if self.currentOverlay == groupName:
                if position == "None":
                    cmds.delete(groupName)
                elif position == positionValue:
                    cmds.delete(groupName)
                else:
                    self.createGoldenSprial(position)

            else:
                try:
                    cmds.delete(self.currentOverlay)
                except:
                    pass
                self.createGoldenSprial(position = "topRight")
        except:
            try:
                cmds.delete(self.currentOverlay)
            except:
                pass
            if position == "None":
                self.createGoldenSprial(position = "topRight")
            else:
                self.createGoldenSprial(position)
        cmds.undoInfo(stateWithoutFlush = True)


    def toggleGoldenSprialTopRight(self):
        self.toggleGoldenSprial(position = "topRight")

    def toggleGoldenSprialTopLeft(self):
        self.toggleGoldenSprial(position = "topLeft")

    def toggleGoldenSprialBottomRight(self):
        self.toggleGoldenSprial(position = "bottomRight")

    def toggleGoldenSprialBottomLeft(self):
        self.toggleGoldenSprial(position = "bottomLeft")

    def noOverlay(self):
        self.cameraProperties()
        self.checkCurrentOverlay()
        try:
            cmds.delete(self.currentOverlay)
        except:
            pass


    #====================================================
    #	Method for Checking for existing Overlays
    #====================================================

    def checkCurrentOverlay(self):
        # Provided the names haven't been changed
        goldenName = self.camera + "_goldenSpiral_GRP"
        gridName = self.camera + "_thirds_Grid"
        if cmds.objExists(goldenName):
            self.currentOverlay = goldenName
        elif cmds.objExists(gridName):
            self.currentOverlay = gridName

    @classmethod
    def active_camera(cls):
        selection = cmds.ls(sl=True)
        if cmds.nodeType(cmds.listRelatives(selection, s=True)) == 'camera':
            camera = selection[0]
        #panel = cmds.getPanel(withFocus=True)
        #if (cmds.getPanel(typeOf=panel) == "modelPanel"):
        #    camera = cmds.modelEditor(panel, q=True, camera=True)
        else:
            return None
        return camera
