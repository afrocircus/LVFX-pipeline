import maya.cmds as cmds
import maya.mel as mel
import shiboken
from PySide import QtGui
import maya.OpenMayaUI as apiUI
import maya.OpenMaya as om
from PySide.QtGui import QMainWindow
from PySide.QtGui import QWidget

## Global variables

currentPanel = cmds.getPanel(wf=1)

mp4Layout = cmds.formLayout(currentPanel ,q=1,fpn=1)
renderViews = cmds.getPanel( sty = 'renderWindowPanel' )
formX = cmds.formLayout(mp4Layout,q=True,w=True)
formY = cmds.formLayout(mp4Layout,q=True,h=True)
formY = formY-20 #icons bar

currentRender = cmds.getAttr('defaultRenderGlobals.currentRenderer')

reRenderVals = []

if "Viewport_RenderShape" not in cmds.ls(ca=1):
	oldRez = []

# GET CAMERA INFO
cameraNew1 = cmds.modelPanel(cmds.getPanel(wf=True), q=True, cam=True)

if "Viewport_RenderShape" not in cmds.ls(ca=1):
	camera1 = cmds.modelPanel(cmds.getPanel(wf=True), q=True, cam=True) # ex: 'persp'
	camera0 = cmds.listRelatives(camera1)[0] # ex: 'perspShape'

if cameraNew1 != camera1 and cameraNew1 != "Viewport_RenderShape":
	allMpanels = cmds.getPanel(typ='modelPanel')
	for i in allMpanels:
		if cmds.modelPanel(i,q=1,cam=1) == "Viewport_RenderShape":
			newPanel = i

	dropActive()

	camera1 = cameraNew1
	camera0 = cmds.listRelatives(cameraNew1)[0]

	setToolBegin()

# UI MARGINS
activeView = apiUI.M3dView.active3dView()

xUtil = om.MScriptUtil()
xUtil.createFromInt(0)
xPtr = xUtil.asIntPtr()
yUtil = om.MScriptUtil()
yUtil.createFromInt(0)
yPtr = yUtil.asIntPtr()
activeView.getScreenPosition(xPtr, yPtr)

marLeft = om.MScriptUtil.getInt(xPtr)
marTop = om.MScriptUtil.getInt(yPtr)


## Functions

def getMayaWindow():
	ptr = apiUI.MQtUtil.mainWindow()
	if ptr is not None:
		return shiboken.wrapInstance(long(ptr), QtGui.QMainWindow)

def getPanelAttach(form):
	ptr2 = apiUI.MQtUtil.findControl(form)
	if ptr2 is not None:
		return shiboken.wrapInstance(long(ptr2), QWidget)


def mk_view(name,values):

	mw = QMainWindow(getMayaWindow())
	mw.setObjectName(name)

	# clean renderview controls
	cmds.optionVar( iv=('renderViewDisplayToolbar',0))
	cmds.scriptedPanel(renderViews , e=True, mbv=0 )
	cmds.renderWindowEditor(renderViews,e=1,cap=0)
	cmds.renderWindowEditor(renderViews,e=1,rs=1)

	form = cmds.formLayout('ViewportRenderForm')
	pane = cmds.paneLayout(configuration='single',bgc=(0.1,0.1,0.1))

	cmds.formLayout(form, e=1, af = [(pane,'top',1),(pane,'left',1),(pane,'right',1),
	(pane,'bottom',1)] )

	cmds.scriptedPanel(renderViews[0],e=1,p=pane)

	closeBtn = cmds.button('myClosebtn', label="x", w=20, h=20, p=form, c=dropTool,	ebg=0, bgc=(0,0,0) )
	bReRender = cmds.button('bReRender', label="r", w=20, h=20, p=form, c=reRender )
	iprR = cmds.button('iprR', label="ir", w=20, h=20, p=form, c=iprRender )

	cmds.formLayout(form,e=True, af=[(closeBtn, 'top', 5), (closeBtn, 'left', 5)] )
	cmds.formLayout(form,e=True, af=[(bReRender, 'top', 5), (bReRender, 'left', 30)] )
	cmds.formLayout(form,e=True, af=[(iprR, 'top', 5), (iprR, 'left', 55)] )

	cmds.formLayout(form,e=True, af=[(closeBtn, 'top', 5), (closeBtn, 'left', 5)] )

	panel = getPanelAttach(form)
	mw.setCentralWidget(panel)
	mw.setWindowTitle(name)
	#mw.setWindowFlags(QtCore.Qt.Tool|QtCore.Qt.FramelessWindowHint)

	leftW = marLeft+values[0]
	topW = marTop + (formY-values[1])

	resoX = values[2] - values[0]
	resoY = values[1] - values[3]

	mw.setGeometry(leftW, topW, resoX,resoY)
	mw.update()

	return mw


def main(values):

	if ( cmds.window("vpRenderWindow", exists=True) ):
		cmds.deleteUI("vpRenderWindow")

	leftW = marLeft+values[0]
	topW = marTop + (formY-values[1])
	resoX = values[2] - values[0]
	resoY = values[1] - values[3]

	mk_view("vpRenderWindow",values).show()
	cmds.window("vpRenderWindow",e=1,bgc=(0,0,0))

	cmds.setFocus('renderView')

	return 0


def getRegion(rrStart_x,rrStart_y,rrLast_x,rrLast_y):

	values = [rrStart_x,rrStart_y,rrLast_x,rrLast_y]

	camOverscan = cmds.camera(camera0,q=1,ovr=1)

	if LockedAttr() == 'locked':
		cmds.warning('Unlock you camera\'s main attributtes')
		return False

	if cmds.window("vpRenderWindow", exists=1) == False:
		getRvStatus()
		getPaneLayoutStatus()

	if values[3] < 0:
		values[3] = 0

	if values[2] > formX:
		values[2] = formX

	if values[2]-values[0]<20 or values[1]-values[3]<20:
		cmds.warning('Region is too small')
	else:
		leftW = marLeft+values[0]
		topW = marTop + (formY-values[1])
		resoX = values[2] - values[0]
		resoY = values[1] - values[3]

		main(values)

		if "Viewport_RenderShape" not in cmds.ls(ca=1):
			setToolBegin()
		else:
			cmds.setAttr('defaultResolution.width', resoX)
			cmds.setAttr('defaultResolution.height', resoY)

			aspRatio = float(cmds.getAttr('defaultResolution.width'))/float(cmds.getAttr('defaultResolution.height'))
	
			cmds.setAttr('defaultResolution.deviceAspectRatio', aspRatio)

		ScaleToCrop = float(formX)/resoX
		ScaleToCrop2 = float(formY)/resoY

		cmds.setAttr(camera0 + '.preScale',float(ScaleToCrop)/camOverscan )

		if 'OverScanExpression' not in cmds.ls(et='expression'):
			cmds.expression( name='OverScanExpression' ,s=camera0+'.overscan = Viewport_RenderShape.overscan',o=camera0,ae=1 )

		# Pixel Offset
		pixoffX = (float(formX)/2) - (values[0] + float(resoX)/2)
		pixoffY = (float(formY)/2) - (formY - values[1]) - (float(resoY)/2)

		# Film Translate
		FxOff = float(pixoffX) / (formX/2)
		FxOff = FxOff*ScaleToCrop

		if FxOff > 0:
			FxOff = FxOff * -1
		else:
			FxOff = -FxOff

		cmds.setAttr(camera0 + '.filmTranslateH', FxOff)

		unitY = float(formY)/2 * float(formX)/formY
		FyOff = float(pixoffY) / unitY
		FyOff = FyOff*ScaleToCrop

		cmds.setAttr(camera0 + '.filmTranslateV', FyOff)


		cmds.setAttr('defaultResolution.width', resoX)
		cmds.setAttr('defaultResolution.height', resoY)

		aspRatio = float(cmds.getAttr('defaultResolution.width'))/float(cmds.getAttr('defaultResolution.height'))
		cmds.setAttr('defaultResolution.deviceAspectRatio', aspRatio)


		cmds.layout('scrollBarForm',e=1,vis=0)

		cmds.renderWindowEditor( renderViews, e=True, snp=(currentPanel,resoX,resoY) )
		cmds.renderWindowEditor( renderViews, e=True, rs=True, cap=0,pca=0)
		cmds.renderWindowEditor(renderViews,e=1,cl=(resoX,resoY,0,0,0) )

		if currentRender == 'arnold':
			cmds.arnoldRender(cam=camera1)

		elif currentRender == 'vray':

			if cmds.getAttr("vraySettings.vfbOn") == 1:
				cmds.setAttr("vraySettings.vfbOn",0)

			cmds.setAttr('vraySettings.width',resoX)
			cmds.setAttr('vraySettings.height',resoY)
			mel.eval('vraySetPixelDeviceAspect();')

			vrendCommand = 'vrend -camera %s' % (camera0)
			mel.eval (vrendCommand)

		elif currentRender == 'mentalRay':

			cmds.Mayatomr(pv=True, cam=camera0)

		else:
			cmds.warning( 'Render engine not supported. Rendering using Maya Software renderer.' )
			cmds.render(camera1, x=resoX, y=resoY)

		reRenderVals.append(resoX)
		reRenderVals.append(resoY)



def dropTool(*args):

	cmds.undoInfo(swf=False)

	if currentRender == 'arnold':
	    if cmds.arnoldIpr(q=1, mode='start'):
		    cmds.arnoldIpr(mode='stop')

	#if currentRender == 'mentalRay':
		#iprRender()

	cmds.layout('scrollBarForm',e=1,vis=1)

	cmds.deleteUI('vpRenderWindow')

	cmds.optionVar( iv=('renderViewDisplayToolbar',1))
	cmds.scriptedPanel(renderViews , e=True, mbv=1 )

	cmds.setAttr(camera0 + '.preScale',1)
	cmds.setAttr(camera0 + '.filmTranslateH', 0)
	cmds.setAttr(camera0 + '.filmTranslateV', 0)

	# center of interest
	camPivot = cmds.getAttr('Viewport_RenderShape.centerOfInterest')
	cmds.setAttr(camera0 + '.centerOfInterest', camPivot)

	cmds.parent(camera1, w=True)
	cmds.delete('Viewport_Render')
	cmds.select(clear=True)

	mel.eval('lookThroughModelPanel '+camera1+' '+currentPanel+';')

	# delete expression if exists
	if cmds.camera(camera1,q=1,o=1):
		cmds.delete("vprexpression")

	cmds.delete("OverScanExpression")

	if oldRez != []:
		cmds.setAttr('defaultResolution.width',oldRez[0])
		cmds.setAttr('defaultResolution.height', oldRez[1])
		cmds.setAttr('defaultResolution.deviceAspectRatio', oldRez[2])

	if currentRender == 'vray':
		cmds.setAttr('vraySettings.width',oldRez[0])
		cmds.setAttr('vraySettings.height',oldRez[1])
		mel.eval('vraySetPixelDeviceAspect();')

		cmds.setAttr(camera0 + '.cameraScale',1 )
		cmds.setAttr(camera0 + ".horizontalFilmOffset", 0 )
		cmds.setAttr(camera0 + ".verticalFilmOffset", 0 )

	cmds.undoInfo(swf=True)

def setToolBegin():

	

	if oldRez == []:
		oldRez.append( cmds.getAttr('defaultResolution.width') )
		oldRez.append( cmds.getAttr('defaultResolution.height') )
		oldRez.append( cmds.getAttr('defaultResolution.deviceAspectRatio') )

	selection = cmds.ls(camera1)

	cmds.duplicate(selection, n='Viewport_Render')
	cmds.hide(camera1)
	cmds.parent( selection, 'Viewport_Render')
	cmds.setAttr('Viewport_RenderShape'+'.visibility',0)

	if cmds.camera(camera1,q=1,o=1):
		cmds.expression( name='vprexpression' ,s=camera0+'.orthographicWidth = Viewport_RenderShape.orthographicWidth' )


	mel.eval('lookThroughModelPanel Viewport_Render '+currentPanel+';')

	cmds.select(clear=True)

def dropActive():

	if currentRender == 'arnold':
	    if cmds.arnoldIpr(q=1, mode='start'):
		    cmds.arnoldIpr(mode='stop')

	#if currentRender == 'mentalRay':
		#iprRender()

	cmds.setAttr(camera0 + '.preScale',1)
	cmds.setAttr(camera0 + '.filmTranslateH', 0)
	cmds.setAttr(camera0 + '.filmTranslateV', 0)

	# center of interest
	camPivot = cmds.getAttr('Viewport_RenderShape.centerOfInterest')
	cmds.setAttr(camera0 + '.centerOfInterest', camPivot)

	cmds.parent(camera1, w=True)
	cmds.delete('Viewport_Render')
	cmds.select(clear=True)

	mel.eval('lookThroughModelPanel '+camera1+' '+newPanel+';')

	if cmds.camera(camera1,q=1,o=1):
		cmds.delete("vprexpression")

	cmds.delete("OverScanExpression")


def getRvStatus():
	# has the renderview been opened already?
	if cmds.layout('editorForm',q=1,ex=1):

		## is it in a window or in a panel??
		rView = 'renderView'
		
		if rView in cmds.getPanel(vis=1):
			if cmds.panel(rView,q=1,to=1):
				# 'it is in a window!'
				cmds.deleteUI('renderViewWindow',wnd=1)
			else:
				#'is in a panel'
				
				rvv = cmds.getPanel( sty = 'renderWindowPanel' )
				visibleModelPanels = []
				camerasVisible = []
				allCameras = []
				possibleCams = []
				
				for i in cmds.ls(ca=1):
					allCameras.append( cmds.listRelatives(i,p=1)[0] )
				
				for i in cmds.getPanel(vis=1):
					if i in cmds.getPanel(typ="modelPanel"):
						visibleModelPanels.append(i)
				
				for i in visibleModelPanels:
					camerasVisible.append( cmds.modelPanel(i, q=True, cam=True) )
				
				
				for i in allCameras:
					if i not in camerasVisible:
						possibleCams.append(i)
				
				if possibleCams >= 1:
					mel.eval('lookThroughModelPanel '+ str(possibleCams[0]) +' '+str(rvv[0])+';')
				#else:

				cmds.scriptedPanel('renderView',e=1,up=1)
				cmds.scriptedPanel('renderView',q=1,ctl=1)
		else:

			cmds.scriptedPanel('renderView',e=1,up=1)
			cmds.scriptedPanel('renderView',q=1,ctl=1)

	else:
		return False



def getPaneLayoutStatus():

	visibleModelPanels = []
	camerasVisible = []
	camDuplicated = []
	allCameras = []
	possibleCams = []
	focusPanel = cmds.getPanel(wf=1)

	for i in cmds.ls(ca=1):
		allCameras.append( cmds.listRelatives(i,p=1)[0] )

	for i in cmds.getPanel(vis=1):
		if i in cmds.getPanel(typ="modelPanel"):
			visibleModelPanels.append(i)

	for i in visibleModelPanels:
		camerasVisible.append( cmds.modelPanel(i, q=True, cam=True) )

	for i in allCameras:
		if i not in camerasVisible:
			possibleCams.append(i)

	PanelsToReplace = []

	if len( camerasVisible ) != len( list(set(camerasVisible)) ):

		for i in visibleModelPanels:
			if camerasVisible.count( cmds.modelPanel(i, q=True, cam=True) ) > 1 and i != focusPanel:

				PanelsToReplace.append(i)

	if PanelsToReplace != []:
		for idx, item in enumerate( PanelsToReplace ):
			if idx <= ( len(possibleCams) - 1 ):
				mel.eval('lookThroughModelPanel '+ str(possibleCams[idx]) +' '+str(item)+';')


def LockedAttr():

	Attributes = ['.translateX', '.translateY', '.translateZ', '.rotateX','.rotateY', '.rotateZ', '.visibility']

	for i in Attributes:
		if cmds.getAttr(camera1+i,l=1):
			return 'locked'
			break


def reRender(*args):

	if currentRender == 'arnold':
		cmds.arnoldRender(cam=camera1)

	elif currentRender == 'vray':
		vrendCommand = 'vrend -camera %s' % (camera0)
		mel.eval (vrendCommand)

	elif currentRender == 'mentalRay':
		cmds.Mayatomr(pv=True, cam=camera0)

	else:
		cmds.warning( 'Render engine not supported. Rendering using Maya Software renderer.' )
		cmds.render(camera1)


jobList = []

def iprRender(*args):

	if currentRender == 'arnold':
		if cmds.arnoldIpr(q=1, mode='start'):
			cmds.arnoldIpr(mode='stop')
		else:
			cmds.arnoldIpr(cam=camera1, mode='start')
			cmds.arnoldIpr(mode='refresh')

	elif currentRender == 'vray':

		statusRT = mel.eval('vrayIsRunningIpr();') 

		if statusRT == 0:

			if cmds.camera(camera1,q=1,o=1):
				cmds.warning('ortographic views not supported by vrayRT')
			else:
				preScale = cmds.getAttr(camera0 + '.preScale')
				preScale = float(1)/float(preScale)

				ftrh = cmds.getAttr(camera0 + '.filmTranslateH')
				ftrv = cmds.getAttr(camera0 + '.filmTranslateV')

				unitfIxed = 0.709

				cmds.setAttr(camera0 + '.cameraScale',preScale )

				cmds.setAttr(camera0 + ".horizontalFilmOffset", ftrh*unitfIxed )
				cmds.setAttr(camera0 + ".verticalFilmOffset", ftrv*unitfIxed )

				mel.eval("vrend -ipr true -cam "+camera0+";")

		else:
			mel.eval("vrend -ipr false;")

	elif currentRender == 'mentalRay':

		if cmds.Mayatomr(q=1,imr=True):
			cmds.Mayatomr(imr=False)
			cmds.setAttr(camera0 + ".shakeEnabled",0)

			
			for x in jobList[:]:
				cmds.scriptJob(kill=x,force=True)
				jobList.remove(x)

		else:

			if cmds.camera(camera1,q=1,o=1):
				jobIprMr = cmds.scriptJob( attributeChange=['Viewport_Render.translate', forceIpr] )
				jobIprMr2 = cmds.scriptJob( attributeChange=['Viewport_Render.orthographicWidth', forceIpr] )

				jobList.append(jobIprMr)
				jobList.append(jobIprMr2)

			else:
				jobIprMr = cmds.scriptJob( attributeChange=['Viewport_Render.translate', forceIpr] )
				jobList.append(jobIprMr)


			cmds.Mayatomr(imr=True, cam=camera0)

	else:
		cmds.warning( 'Render engine not supported. Rendering using Maya Software renderer.' )
		cmds.render(camera1)


def forceIpr():
	xAttr = cmds.getAttr(camera0 + ".shakeEnabled")

	if xAttr == 0:
		cmds.setAttr(camera0 + ".shakeEnabled",1)
	else:
		cmds.setAttr(camera0 + ".shakeEnabled",0)
