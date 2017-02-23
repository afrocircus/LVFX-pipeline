import maya.cmds as cmds


class CustomCamera(object):
    def __init__(self):
        print "creating custom camera..."

    def createCamera(self):
        # Create a camera named renderCam
        camObj = cmds.camera()
        cmds.rename(camObj[0], 'renderCam')
        selection = cmds.ls(sl=True)
        return selection[0]

    def customizeCamera(self, camera):
        cmds.lookThru(camera)
        cmds.addAttr(camera, ln="Overlay", at="enum", en="No Overlay:Grid:SpiralTopRight:SpiralTopLeft:SpiralBottomRight:SpiralBottomLeft")
        cmds.addAttr(camera, ln="Overlay_Value", at="long")
        cmds.setAttr(camera + '.Overlay', e=True, keyable=True)
        cmds.setAttr(camera + '.Overlay_Value', e=True, keyable=True)
        cmds.expression(s='int $a=%s.Overlay;\r\n' % camera +
                          '%s.Overlay_Value=$a;' % camera+
                          'switch($a) { \r\n' +
                          '  case 0: \r\n' +
                          '    python("camera_overlays.Overlay_Function().noOverlay()"); \r\n' +
                          '    break;\r\n' +
                          '  case 1: \r\n' +
                          '    python("camera_overlays.Overlay_Function().toggleThirdsGrid()"); \r\n' +
                          '    break;\r\n' +
                          '  case 2: \r\n' +
                          '    python("camera_overlays.Overlay_Function().toggleGoldenSprialTopRight()"); \r\n' +
                          '    break;\r\n' +
                          '  case 3: \r\n' +
                          '    python("camera_overlays.Overlay_Function().toggleGoldenSprialTopLeft()"); \r\n' +
                          '    break;\r\n' +
                          '  case 4: \r\n' +
                          '    python("camera_overlays.Overlay_Function().toggleGoldenSprialBottomRight()"); \r\n' +
                          '    break;\r\n' +
                          '  case 5: \r\n' +
                          '    python("camera_overlays.Overlay_Function().toggleGoldenSprialBottomLeft()"); \r\n' +
                          '}select %s;\r' % camera, ae=False, o="renderCam")

    def createCustomCamera(self):
        camera = self.createCamera()
        self.customizeCamera(camera)


