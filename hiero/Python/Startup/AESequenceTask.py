# Copyright (c) 2013 Matt Brealey
#v1.2

#Newness :

#v1.2
#Removed references to hiero.core.debug as they were unnecessary and the method has been moved.

#v1.1
#Added in support for AE CS5.5
#Added in support for Hiero 1.7

#LIMITATIONS :
#Doesn't take across Audio tracks
#'Missing Frames' error might pop-up in AE. Just OK it for now. Needs to be handled better.
#TIFF is the only 'Write' format available due to AE's output module list not being scriptable.

import os.path
import os
import sys
import hiero

from hiero.core import *

class AESequenceTask(TaskBase):
    def __init__( self, initDict ):
        """Initialize"""
        TaskBase.__init__( self, initDict )
        
        self._finished = False
    
    def startTask(self):
        TaskBase.startTask(self)
        
        pass
    
    def taskStep(self):
          
        #Start generating AE script
        aeScript = """function hieroAESceneMain() {
        
    //create project if necessary
    if (!app.project){app.newProject();}"""
        
        
        
        #Add folders if required
        if self._preset.properties()["createFolders"]:
            aeScript += """
        
    //create folders
    var compFolder = app.project.items.addFolder("Comps"); 
    var platesFolder = app.project.items.addFolder("Plates");"""
    
    
    
        #Import file for Clips/Track Items
        
        #Handles
        handles = self._cutHandles if self._cutHandles is not None else 0
        print "\tHandles value is :", handles 
        
        if isinstance(self._item, (Clip, TrackItem)) :
        
            #Import file
            if isinstance(self._item, Clip) :
                source = self._item.mediaSource()
                frameRate = self._item.framerate().toFloat()
                timecodeStartFrame = self._item.timecodeStart()
                sourceDuration = int(self._item.mediaSource().duration())
                durSecs = (source.duration() / frameRate)
                inPointSecs = 0
                outPointSecs = durSecs
                startTime = 0
            else : 
                source = self._item.source().mediaSource()
                frameRate = self._item.source().framerate().toFloat()
                timecodeStartFrame = self._item.timelineIn() - handles #HANDLES
                durSecs = ((self._item.duration() + (handles*2)) / self._item.parent().parent().framerate().toFloat()) #HANDLES
                inPointFrames = int(self._item.sourceIn()) - handles #HANDLES
                outPointFrames = int(self._item.sourceOut()+1) + handles #Need to account for the difference in the way Hiero/AE displays last frames #HANDLES
                
                inPointSecs = inPointFrames / self._item.parent().parent().framerate().toFloat()
                outPointSecs = outPointFrames / self._item.parent().parent().framerate().toFloat()
                
                startTime = 0.0 - inPointSecs

                                
            if timecodeStartFrame != 0 :
                timecodeStartSecs = timecodeStartFrame/frameRate
            else : 
                timecodeStartSecs = 0
                
            width = int(source.width())
            height = int(source.height())
            pixelAsp = source.pixelAspect()
            
            aeScript += self.AE_importFile(source.firstpath(), frameRate, self._preset.properties()["createFolders"])
            
            #Create comp at file length
            aeScript += self.AE_createComp(self._item.name(), width, height, pixelAsp, durSecs, frameRate, self._preset.properties()["createFolders"], timecodeStartSecs)
            
            #Add layer
            aeScript += self.AE_addLayerToComp("newComp", "footage", self._item.name(), inPointSecs, outPointSecs, startTime)
            
            #Add retimes if required
            retimeCheck = bool(self._retime)
            if retimeCheck: 
                retimeValue = float(sourceDuration) / float(self._item.duration())
                if retimeValue != 1.0 :
                    aeScript += self.AE_addRetimeEffect(retimeValue)
    
            
        #Import files for Sequences
        elif isinstance(self._item, Sequence) :
            #Create comp at sequence length
            width = int(self._item.format().width())
            height = int(self._item.format().height())
            pixelAsp = self._item.format().pixelAspect()
            frameRate = self._item.framerate().toFloat()
            durSecs = (self._item.duration() / frameRate)
            timecodeStartFrame = int(self._item.timecodeStart()) 
            
            if timecodeStartFrame != 0 :
                timecodeStartSecs = timecodeStartFrame/frameRate
            else : 
                timecodeStartSecs = 0
            
            aeScript += self.AE_createComp(self._item.name(), width, height, pixelAsp,  durSecs, frameRate, self._preset.properties()["createFolders"], timecodeStartSecs)

            #For each track item
            for track in self._item.videoTracks() :
                for item in track.items() :
                                
                    #import
                    aeScript += self.AE_importFile(item.source().mediaSource().firstpath(), item.source().framerate().toFloat(), self._preset.properties()["createFolders"])
                    
                    #append to comp
                    if item.timelineIn() == 0 : 
                        timelineInSecs = 0
                    else : 
                        timelineInSecs = item.timelineIn() / frameRate
                        
                    inPointFrames = item.sourceIn()
                    outPointFrames = item.sourceOut() + 1 #To account for AE's blank final frames
                    
                    inPointSecs = inPointFrames / self._item.framerate().toFloat()
                    outPointSecs = outPointFrames / self._item.framerate().toFloat()
                    
                    startTime = timelineInSecs - inPointSecs
                        
                    aeScript += self.AE_addLayerToComp("newComp", "footage", item.name(), inPointSecs, outPointSecs, startTime)
                    
                
        #Add timecode layer if necessary
        if self._preset.properties()["addTimecodeLayer"]:
            aeScript += self.AE_addTimecodeLayer(width, height, pixelAsp, durSecs, frameRate, timecodeStartFrame)
            
        #Add logLin adjustment layer if necessary
        if self._preset.properties()["addLogLin"]:
            aeScript += self.AE_addLogLinLayer(width, height, pixelAsp, durSecs)
 
        #Add render modules as necessary
        for (itemPath, itemPreset) in self._exportTemplate.flatten():
            for writePath in self._preset.properties()['writePaths'] :
              if itemPath == writePath:
              
                taskData = hiero.core.TaskData(itemPreset, self._item, self._exportRoot, itemPath, self._version, self._exportTemplate, project=self._project, cutHandles=self._cutHandles, retime=self._retime, startFrame=self._startFrame, resolver=self._resolver)
                task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)
            
                writeNodePath = task.resolvedExportPath()
                
                #Fix path for AE
                pathSplit = writeNodePath.split("#")
                
                if len(pathSplit) > 1 : 
                    AEPath = pathSplit[0] + "[" + ("#" * (len(pathSplit)-1)) + "]" + pathSplit[-1]
                else : 
                    AEPath = test
                        
                aeScript += self.AE_addRenderOutput(AEPath)
        
        #Add hack to open comp
        aeScript += self.AE_hackyOpenComp()
        
        #Add save if needed
        if self._preset.properties()["autoSaveProject"]:
            aeScript += """
      
    //Auto save        
    app.project.save(File ("%s.aep") )""" % os.path.splitext(self.resolvedExportPath())[0]
                
                
        #Add final close
        aeScript += """

}
hieroAESceneMain();"""                
 
        #Write file
        self.AE_writeToJSX(aeScript)
        
        #Mark done and return
        self._finished = True
        return False

    
    def finishTask(self):
        pass
      
    def progress(self):
        progress = 0.0
    
        if self._finished:
            progress = 1.0
        else:
            pass
            
        return float(progress)
        
    def AE_importFile(self, firstPath, frameRate, createFolders) :
        importFileScript = """

    //Create file obj
    var theSeq = new ImportOptions();
    var theFile = '%s';
    theSeq.file = new File(theFile);
    
    //Set as sequence if not a movie
    if (theFile.indexOf('mov') == -1 && theFile.indexOf('mp4') == -1 && theFile.indexOf('r3d') == -1) {
        theSeq.sequence = true;
    }
    
    //Import and set framerate
    footage = app.project.importFile(theSeq);
    footage.mainSource.conformFrameRate = %s;""" % (firstPath, frameRate)
    
        if createFolders : 
            importFileScript += """
    footage.parentFolder = platesFolder;"""        
    
        return importFileScript
        
    def AE_createComp(self, name, width, height, pxAsp, durationSecs, fps, createFolders, startTimecodeSecs):        
        createCompScript = """
        
    //create comp - addComp(name, width, height, pixel aspect, duration (seconds),  fps)
    var newComp = app.project.items.addComp('%s', %s, %s, %s, %s, %s);
    newComp.displayStartTime = %s;""" % (name, width, height, pxAsp, durationSecs, fps, startTimecodeSecs)
        
        if createFolders :
            createCompScript += """
    newComp.parentFolder = compFolder;"""
	       
        return createCompScript
        
    def AE_addLayerToComp(self, compVar, footageVar, name, inPoint, outPoint, startTime) :
        addLayerScript = """
        
    //add plate to comp & rename
    var newLayer = %s.layers.add(%s);
    newLayer.name = "%s";
    newLayer.inPoint = %s;
    newLayer.outPoint = %s;
    newLayer.startTime = %s;""" % (compVar, footageVar, name, inPoint, outPoint, startTime)
    
        return addLayerScript
           
    def AE_addRetimeEffect(self, retimeValue) :
        retimeScript = """
        
    //add retimes
    var retimeEffect = newLayer.Effects.addProperty("Timewarp");
    retimeEffect.property(3).setValue(retimeValue);"""
    
        return retimeScript
    
        
    def AE_addTimecodeLayer(self, width, height, pxAsp, durationSecs, frameRate, timecodeStartFrame):
        addTimecodeScript = """
    
    //Add timecode layer
    var timecodeLayer = newComp.layers.addSolid([0, 0, 0], 'Timecode Layer', %s, %s, %s, %s);
    timecodeLayer.adjustmentLayer = true; 
    timecodeLayer.guideLayer = true;            
    timecodeLayer.locked = true;
    var tcEffect = timecodeLayer.Effects.addProperty("Timecode");

    if (parseFloat(app.version) >= 10.5) {
        tcEffect.property(2).setValue(3)
        tcEffect.property(4).setValue(%s);
        tcEffect.property(6).setValue(%s);
    } else {
        tcEffect.property(2).setValue(%s);
        tcEffect.property(4).setValue(%s);
    }
        """ % (width, height, pxAsp, durationSecs, frameRate, timecodeStartFrame, frameRate, timecodeStartFrame)
    
        
        return addTimecodeScript
        
    def AE_addLogLinLayer(self, width, height, pxAsp, durationSecs):
        addLogLinScript = """
    
    //Add log>lin layer
    var logLinLayer = newComp.layers.addSolid([0, 0, 0], 'Approximate Log>Lin', %s, %s, %s, %s);
    logLinLayer.adjustmentLayer = true;           
    logLinLayer.locked = true;
    var logLinEffect = logLinLayer.Effects.addProperty("Cineon Converter");
    logLinEffect.property(6).setValue(2.20);""" % (width, height, pxAsp, durationSecs)
        
        return addLogLinScript
        
    def AE_addRenderOutput(self, writePath) :
        addRenderOutput = """
        
    //Get render queue
    var rq = app.project.renderQueue;
    
    // Add comp to the render queue
    rqi = rq.items.add(newComp);
    
    //Find TIFF render template and apply
    for (x in rqi.outputModules[1].templates){
        if (rqi.outputModules[1].templates[x] == "TIFF Sequence with Alpha") {
            //alert(dir(rqi.outputModules[1]));
            rqi.outputModules[1].applyTemplate(rqi.outputModules[1].templates[x])
        }
    }
    
    //Set save name
    rqi.outputModules[1].file = File ('%s');""" % (writePath)
    
        return addRenderOutput
        
    def AE_hackyOpenComp(self) :
        hackyOpenCompScript = """
        
    //HACK to force open comp
    //get old duration and then set current duration to 2f
    var duration = newComp.workAreaDuration;
    newComp.workAreaDuration = newComp.frameDuration * 2;
    newComp.ramPreviewTest("",1,"");
    newComp.workAreaDuration = duration;"""
    
        return hackyOpenCompScript

                
    def AE_writeToJSX(self, data) :
        
        if data : 
        
            print "Directory :", os.path.dirname(self.resolvedExportPath())
        
            #Make directory if it doesn't exist
            if not os.path.exists(os.path.dirname(self.resolvedExportPath())):
            	os.makedirs(os.path.dirname(self.resolvedExportPath()))
            
            #Make write path	
            writePath = os.path.join(os.path.dirname(self.resolvedExportPath()), "%s.jsx" % os.path.splitext(self.resolvedExportPath())[0])
            print "WritePath :", writePath
            
            #Write to JSX
            jsx_file = open( writePath , "w" )
            jsx_file.write(str(data))	
            jsx_file.close()
            
            return False


class AESequencePreset(TaskPresetBase):
  def __init__(self, name, properties):
    TaskPresetBase.__init__(self, AESequenceTask, name)
    
    # Set any preset defaults here
    self._properties["autoSaveProject"] = True
    self._properties["createFolders"] = True
    self._properties["addTimecodeLayer"] = True
    self._properties["addLogLin"] = False
    self._properties["writePaths"] = []
    
    # Update preset with loaded data
    self._properties.update(properties)

  def addCustomResolveEntries(self, resolver):
    print "Adding custom resolver"
    resolver.addResolver("{ext}", "Extension of the file to be output", lambda keyword, task: "jsx")

  def supportedItems(self):
    return TaskPreset.kAllItems
    
  def pathChanged(self, oldPath, newPath):
    for pathlist in self._properties["writePaths"]:
      for path in pathlist:
        if path == oldPath:
          pathlist.remove(oldPath)
          pathlist.append(newPath)

hiero.core.taskRegistry.registerTask(AESequencePreset, AESequenceTask)
