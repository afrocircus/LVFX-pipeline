import os
import re
import math
import hiero.core
import hiero.core.nuke as nuke
import _nuke
import hiero.exporters.FnScriptLayout

from hiero.exporters.FnReformatHelpers import reformatNodeFromPreset
from hiero.exporters.FnExportUtil import trackItemTimeCodeNodeStartFrame


def _toNukeViewerLutFormat(hieroViewerLut):
    """ Return the specified hiero viewer lut in the nuke format.
    Since hiero formats are specified by 'family/colourspace' while
    nuke formats are expected to be 'colourspace (family)'.
    """
    lutParts = hieroViewerLut.split("/")
    assert(0 < len(lutParts) <= 2)
    hasFamilyName = len(lutParts) == 2
    if hasFamilyName:
        viewerLut = "%s (%s)" % (lutParts[1], lutParts[0])
    else:
        viewerLut = lutParts[0]

    return viewerLut


class LocoNukeShotExporterTask(hiero.core.TaskBase):
    def __init__(self, initDict):
        hiero.core.TaskBase.__init__(self, initDict)

        self._tag_guid = None
        self._parentSequence = None
        self._collate = False
        # Handles from the collated sequence.  This is set as a tuple if a collated sequence is created
        self._collatedSequenceHandles = None

        # If skip offline is True and the input track item is offline, return
        if isinstance(self._item, hiero.core.TrackItem):
            if not self._source.isMediaPresent() and self._skipOffline:
                return

        # All clear.
        self._nothingToDo = False

        self._fixExtensionForNukeScriptsPath()

    def _changeExtension(self, filepath):
        """ Returns the filepath with new extension."""
        return re.sub('\.nk$', '.nknc', filepath)

    def _fixExtensionForNukeScriptsPath(self):
        """ Checks if the nuke script extensions in the preset are correct according
        to the application mode"""
        if _nuke.env['nc']:
            if self._exportPath.endswith('.nk'):
                self._exportPath = self._changeExtension(self._exportPath)

    def writingSequence(self):
        """ Check if we're writing a single clip or a sequence.
        This is the case if the object was initialised with a sequence,
        or if the collate option is set. """
        return isinstance(self._item, hiero.core.Sequence) or self._collate

    def _createWriteNodes(self, firstFrame, start, end, framerate, rootNode):

        # To add Write nodes, we get a task for the paths with the preset
        # (default is the "Nuke Write Node" preset) and ask it to generate the Write node for
        # us, since it knows all about codecs and extensions and can do the token
        # substitution properly for that particular item.
        # And doing it here rather than in taskStep out of threading paranoia.
        writeNodes = []

        firstWriteNode = True

        # Create a stack to prevent multiple write nodes inputting into each other
        stackId = "ScriptEnd"
        writeNodes.append(nuke.SetNode(stackId, 0))

        writePaths = self._preset.properties()["writePaths"]

        for (itemPath, itemPreset) in self._exportTemplate.flatten():
            for writePath in writePaths:
                if writePath == itemPath:
                    # Generate a task on same items as this one but swap in the shot path that goes with this preset.
                    taskData = hiero.core.TaskData(itemPreset,
                                                   self._item,
                                                   self._exportRoot,
                                                   itemPath,
                                                   self._version,
                                                   self._exportTemplate,
                                                   project=self._project,
                                                   cutHandles=self._cutHandles,
                                                   retime=self._retime,
                                                   startFrame=firstFrame,
                                                   resolver=self._resolver,
                                                   skipOffline=self._skipOffline,
                                                   shotNameIndex=self._shotNameIndex)
                    task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)
                    if hasattr(task, "nukeWriteNode"):

                        # Push to the stack before adding the write node
                        writeNodes.append(nuke.PushNode(stackId))

                        try:
                            reformatNode = reformatNodeFromPreset(itemPreset)
                            if reformatNode:
                                writeNodes.append(reformatNode)
                        except Exception as e:
                            self.setError(str(e))

                        # Add Burnin group (if enabled)
                        burninGroup = task.addBurninNodes(script=None)
                        if burninGroup is not None:
                            writeNodes.append(burninGroup)

                        try:
                            writeNode = task.nukeWriteNode(framerate, project=self._project)
                            writeNode.setKnob("first", start)
                            writeNode.setKnob("last", end)
                            if writeNode.knob('file_type') == 'mov':
                                writeNode.setKnob('file',"[python writeNodeManager.setOutputPath('mov')]")
                                writeNode.setKnob('afterRender', 'ftrackUpload.uploadToFtrack()')
                            else:
                                writeNode.setKnob('file',"[python writeNodeManager.setOutputPath('img')]")
                            writeNodes.append(writeNode)

                            # Set the first write node in the list as the one to be shown/rendered in the timeline
                            if firstWriteNode:
                                firstWriteNode = False
                                rootNode.setKnob(nuke.RootNode.kTimelineWriteNodeKnobName, writeNode.knob("name"))

                        except RuntimeError as e:
                            # Failed to generate write node, set task error in export queue
                            # Most likely because could not map default colourspace for format settings.
                            self.setError(str(e))

        return writeNodes

    def writeSequence(self, script, addToScriptCommonArgs):
        """ Write the collated sequence to the script. """
        sequenceDisconnected = self.writingSequenceDisconnected()

        script.pushLayoutContext("sequence", self._sequence.name(), disconnected=sequenceDisconnected)
        # When building a collated sequence, everything is offset by 1000
        # This gives head room for shots which may go negative when transposed to a
        # custom start frame. This offset is negated during script generation.
        offset = -LocoNukeShotExporterTask.kCollatedSequenceFrameOffset if self._collate else 0

        additionalNodes = []

        self._sequence.addToNukeScript(script,
                                       includeRetimes=True,
                                       additionalNodes=additionalNodes,
                                       retimeMethod=self._preset.properties()["method"],
                                       offset=offset,
                                       skipOffline=self._skipOffline,
                                       disconnected=sequenceDisconnected,
                                       masterTrackItem=self._masterTrackItemCopy,
                                       includeAnnotations=self.includeAnnotations(),
                                       outputToFormat=self._collatedSequenceOutputFormat,
                                       **addToScriptCommonArgs)
        script.popLayoutContext()

    def addCustomReadPaths(self, script, addToScriptCommonArgs, firstFrame):
        """ If other export items are selected as Read nodes, add those to the script.  This allows for e.g. using the output
            of the copy exporter as the path for the read node.

            Returns True if any read paths were set. """

        readPathsAdded = False
        # Build read nodes for selected entries in the shot template
        readPaths = self._preset.properties()["readPaths"]
        for (itemPath, itemPreset) in self._exportTemplate.flatten():
            for readPath in readPaths:
                if itemPath == readPath:

                    # Generate a task on same items as this one but swap in the shot path that goes with this preset.
                    taskData = hiero.core.TaskData(itemPreset, self._item, self._exportRoot, itemPath, self._version, self._exportTemplate,
                                                    project=self._project, cutHandles=self._cutHandles, retime=self._retime, startFrame=self._startFrame, resolver=self._resolver, skipOffline=self._skipOffline)
                    task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)

                    readNodePath = task.resolvedExportPath()
                    itemStart, itemEnd = task.outputRange()
                    itemFirstFrame = firstFrame
                    if self._startFrame:
                        itemFirstFrame = self._startFrame

                    if hiero.core.isVideoFileExtension(os.path.splitext(readNodePath)[1].lower()):
                        # Don't specify frame range when media is single file
                        newSource = hiero.core.MediaSource(readNodePath)
                        itemEnd = itemEnd - itemStart
                        itemStart = 0

                    else:
                        # File is image sequence, so specify frame range
                        newSource = hiero.core.MediaSource(readNodePath + (" %i-%i" % task.outputRange()))

                    newClip = hiero.core.Clip(newSource, itemStart, itemEnd)


                    readPathsAdded = True

                    if self._cutHandles is None:
                        newClip.addToNukeScript(script,
                                                firstFrame=itemFirstFrame,
                                                trimmed=True,
                                                nodeLabel=self._item.parent().name(),
                                                **addToScriptCommonArgs)
                    else:
                        # Copy track item and replace source with new clip (which may be offline)
                        newTrackItem = hiero.core.TrackItem(self._item.name(), self._item.mediaType())

                        for tag in self._item.tags():
                            newTrackItem.addTag(tag)

                        # Handles may not be exactly what the user specified. They may be clamped to media range
                        inHandle, outHandle = 0, 0
                        if self._cutHandles:
                            # Get the output range without handles
                            inHandle, outHandle = task.outputHandles()
                            hiero.core.log.debug( "in/outHandle %s %s", inHandle, outHandle )


                        newTrackItem.setSource(newClip)

                        # Set the new track item's timeline range
                        newTrackItem.setTimelineIn(self._item.timelineIn())
                        newTrackItem.setTimelineOut(self._item.timelineOut())

                        # Set the new track item's source range.  This is the clip range less the handles.
                        # So if the export is being done with, say, 10 frames of handles, the source in should be 10
                        # (first frame of clip is always 0), and the source out should be (duration - 1 - 10) (there's
                        # a 1 frame offset since the source out is the start of the last frame that should be read).
                        newTrackItem.setSourceIn(inHandle)
                        newTrackItem.setSourceOut((newClip.duration() -1 )- outHandle)

                        # Add track item to nuke script
                        newTrackItem.addToNukeScript(script,
                                                  firstFrame=itemFirstFrame,
                                                  includeRetimes=self._retime,
                                                  retimeMethod=self._preset.properties()["method"],
                                                  startHandle=self._cutHandles,
                                                  endHandle=self._cutHandles,
                                                  nodeLabel=self._item.parent().name(),
                                                  **addToScriptCommonArgs)

        return readPathsAdded


    def writeTrackItem(self, script, addToScriptCommonArgs, firstFrame):
        """ Write the track item to the script. """

        script.pushLayoutContext("clip", self._item.name())

        # If this flag is True, a read node pointing at the original media will be added
        originalMediaReadNode = True

        # First add any custom read paths if the user selected them.  If True, don't add the original clip to the script.
        if self.addCustomReadPaths(script, addToScriptCommonArgs, firstFrame):
            originalMediaReadNode = False

        if originalMediaReadNode:
            clip = self._item.source()

            # Add a Read Node for this Clip.

            # If cut handles is None, add the full clip range to the script
            if self._cutHandles is None:
                clip.addToNukeScript(script,
                                  firstFrame=firstFrame,
                                  trimmed=True,
                                  nodeLabel=self._item.parent().name(),
                                  **addToScriptCommonArgs)

            # Otherwise add the track item, which will include the item's timeline range + any handles selected
            else:

                # Some care is needed when dealing with soft effects and annotations.  If there are sequence-level effects, then the format which is input to
                # them must be sequence format.  If the track item reformat state is set to 'Disabled' or 'Scale', this means we need to reformat to sequence,
                # add the effects with the 'cliptype' knob set to 'bbox', then modify the format back to what the user asked for.

                # This is further complicated because TrackItem.addToNukeScript adds any linked effects, and does this reformatting itself.
                # So: if there are any non-linked effects/annotations, ask the TrackItem to output to Sequence format, which it will do by adding a Reformat
                # if necessary, then add the extra reformat back to clip format.

                # TODO Some of this code is duplicated in TrackItem.addToNukeScript(), it needs to be cleaned up

                itemReformatState = self._item.reformatState()
                keepSourceFormat = (itemReformatState.type() in (nuke.ReformatNode.kDisabled, nuke.ReformatNode.kToScale))

                startHandle, endHandle = self.outputHandles()

                nodes = self._item.addToNukeScript(script,
                                              firstFrame=firstFrame,
                                              includeRetimes=self._retime,
                                              startHandle=startHandle,
                                              endHandle=endHandle,
                                              nodeLabel=self._item.parent().name()
                                              **addToScriptCommonArgs)

        script.popLayoutContext()


    def updateItem(self, originalItem, localtime):
        """updateItem - This is called by the processor prior to taskStart, crucially on the main thread.\n
          This gives the task an opportunity to modify the original item on the main thread, rather than the copy."""

        # Don't add the tag if this task isn't going to do anything
        if self._nothingToDo:
            return

        import time

        existingTag = None
        for tag in originalItem.tags():
            if tag.metadata().hasKey("tag.presetid") and tag.metadata()["tag.presetid"] == self._presetId:
                existingTag = tag
                break

        if existingTag:
            # Update the script name to the one we just wrote.  This makes it easier
            # for the caller to do any post-export processing (e.g. for Create Comp)
            existingTag.metadata().setValue("tag.script", self.resolvedExportPath())

            # Ensure the startframe/duration tags are updated
            start, end = self.outputRange(clampToSource=False)
            existingTag.metadata().setValue("tag.startframe", str(start))
            existingTag.metadata().setValue("tag.duration", str(end-start+1))

            # Move the tag to the end of the list.
            originalItem.removeTag(existingTag)
            originalItem.addTag(existingTag)
            return

        timestamp = self.timeStampString(localtime)
        tag = hiero.core.Tag("Nuke Project File " + timestamp, "icons:Nuke.png", False)

        tag.metadata().setValue("tag.pathtemplate", self._exportPath)
        tag.metadata().setValue("tag.description", "Loco Nuke Project File")

        writePaths = []

        rootFormat = self.rootFormat()
        writeFormats = []

        # Need to instantiate each of the selected write path tasks and resolve the path
        for (itemPath, itemPreset) in self._exportTemplate.flatten():
            for writePath in self._preset.properties()["writePaths"]:
                if writePath == itemPath:
                    # Generate a task on same items as this one but swap in the shot path that goes with this preset.
                    taskData = hiero.core.TaskData(itemPreset, self._item, self._exportRoot, itemPath, self._version, self._exportTemplate,
                                                    project=self._project, cutHandles=self._cutHandles, retime=self._retime, startFrame=self._startFrame, resolver=self._resolver, skipOffline=self._skipOffline)
                    task = hiero.core.taskRegistry.createTaskFromPreset(itemPreset, taskData)

                    resolvedPath = task.resolvedExportPath()

                    # Ensure enough padding for output range
                    output_start, output_end = task.outputRange(ignoreRetimes=False, clampToSource=False)
                    count = len(str(max(output_start, output_end)))
                    resolvedPath = hiero.core.util.ResizePadding(resolvedPath, count)

                    writePaths.append(resolvedPath)

                    writeReformat = reformatNodeFromPreset(itemPreset)
                    # If there is a reformat specified in the preset and it is 'to format', store that, otherwise use
                    # the root format.
                    if writeReformat and "format" in writeReformat.knobs():
                        writeFormats.append(writeReformat.knob("format"))
                    else:
                        writeFormats.append(str(rootFormat))

        tag.metadata().setValue("tag.path", ";".join(writePaths))
        tag.metadata().setValue("tag.format", ";".join(writeFormats))

        # Right now don't add the time to the metadata
        # We would rather store the integer time than the stringified time stamp
        # tag.setValue("time", timestamp)
        tag.metadata().setValue("tag.script", self.resolvedExportPath())
        tag.metadata().setValue("tag.localtime", str(localtime))
        if self._presetId:
            tag.metadata().setValue("tag.presetid", self._presetId)

        start, end = self.outputRange(clampToSource=False)
        tag.metadata().setValue("tag.startframe", str(start))
        tag.metadata().setValue("tag.duration", str(end-start+1))

        if isinstance(self._item, hiero.core.TrackItem):
            tag.metadata().setValue("tag.sourceretime", str(self._item.playbackSpeed()))

        # Store if retimes were applied in the export.  If exporting a collated sequence, retimes are always applied
        # If self._cutHandles is None,  we are exporting the full clip and retimes are never applied whatever the
        # value of self._retime
        applyingRetime = (self._retime and self._cutHandles is not None) or self._collate
        appliedRetimesStr = "1" if applyingRetime else "0"
        tag.metadata().setValue("tag.appliedretimes", appliedRetimesStr)

        frameoffset = self._startFrame if self._startFrame else 0

        # Only if write paths have been set
        if len(writePaths) > 0:
            # Video file formats are not offset, so set frameoffset to zero
            if hiero.core.isVideoFileExtension(os.path.splitext(writePaths[0])[1].lower()):
                frameoffset = 0

        tag.metadata().setValue("tag.frameoffset", str(frameoffset))

        # Handles aren't included if the item is a freeze frame
        isFreezeFrame = isinstance(self._item, hiero.core.TrackItem) and self._item.playbackSpeed() == 0.0

        # Note: if exporting without cut handles, i.e. the whole clip, we do not try to determine  the handle values,
        # just writing zeroes.  The build track classes need to treat this as a special case.
        # There is an interesting 'feature' of how tags work which means that if you create a Tag with a certain name,
        # the code tries to find a previously created instance with that name, which has any metadata keys that were set before.
        # This means that when multiple shots are being exported, they inherit the tag from the previous one.  To avoid problems
        # always set these keys.
        startHandle, endHandle = 0, 0
        if self._cutHandles and not isFreezeFrame:
          startHandle, endHandle = self.outputHandles()


        tag.metadata().setValue("tag.starthandle", str(startHandle))
        tag.metadata().setValue("tag.endhandle", str(endHandle))

        originalItem.addTag(tag)

        # The guid of the tag attached to the trackItem is different from the tag instance we created
        # Get the last tag in the list and store its guid
        self._tag_guid = originalItem.tags()[-1].guid()

    def taskStep(self):
        try:
            return self._taskStep()
        except:
            hiero.core.log.exception("NukeShotExporter.taskStep")

    def _taskStep(self):
        hiero.core.TaskBase.taskStep(self)
        if self._nothingToDo:
            return False

        script = nuke.ScriptWriter()
        start, end = self.outputRange(ignoreRetimes=True, clampToSource=False)
        unclampedStart = start
        hiero.core.log.debug( "rootNode range is %s %s %s", start, end, self._startFrame )

        firstFrame = start
        if self._startFrame is not None:
            firstFrame = self._startFrame

         # if startFrame is negative we can only assume this is intentional
        if start < 0 and (self._startFrame is None or self._startFrame >= 0):
            # We dont want to export an image sequence with negative frame numbers
            self.setWarning("%i Frames of handles will result in a negative frame index.\nFirst frame clamped to 0." % self._cutHandles)
            start = 0
            firstFrame = 0

        framerate = self._sequence.framerate()
        dropFrames = self._sequence.dropFrame()
        if self._clip and self._clip.framerate().isValid():
            framerate = self._clip.framerate()
            dropFrames = self._clip.dropFrame()
        fps = framerate.toFloat()

        showAnnotations = False

        # Create the root node, this specifies the global frame range and frame rate
        rootNode = nuke.RootNode(start, end, fps, showAnnotations)
        rootNode.addProjectSettings(self._projectSettings)
        dailiesScriptCheck = 'writeNodeManager.checkDailiesTab()'
        rootNode.setKnob("onScriptLoad", dailiesScriptCheck)
        script.addNode(rootNode)

        if isinstance(self._item, hiero.core.TrackItem):
            rootNode.addInputTextKnob("shot_guid", value=hiero.core.FnNukeHelpers._guidFromCopyTag(self._item),
                                        tooltip="This is used to identify the master track item within the script",
                                        visible=False)
            inHandle, outHandle = self.outputHandles(self._retime != True)
            rootNode.addInputTextKnob("in_handle", value=int(inHandle), visible=False)
            rootNode.addInputTextKnob("out_handle", value=int(outHandle), visible=False)

        # Set the format knob of the root node
        rootNode.setKnob("format", str(self.rootFormat()))

        # BUG 40367 - proxy_type should be set to 'scale' by default to reflect
        # the custom default set in Nuke. Sadly this value can't be queried,
        # as it's set by nuke.knobDefault, hence the hard coding.
        rootNode.setKnob("proxy_type","scale")

        # Project setting for using OCIO nodes for colourspace transform
        useOCIONodes = self._project.lutUseOCIOForExport()

        # A dict of arguments which are used when calling addToNukeScript on any clip/sequence/trackitem
        addToScriptCommonArgs = { 'useOCIO' : useOCIONodes }

        writeNodes = self._createWriteNodes(firstFrame, start, end, framerate, rootNode)

        if not writeNodes:
            # Blank preset is valid, if preset has been set and doesn't exist, report as error
            self.setWarning(str("NukeShotExporter: No write node destination selected"))

        if self.writingSequence():
            self.writeSequence(script, addToScriptCommonArgs)

            # Write out the single track item
        else:
            self.writeTrackItem(script, addToScriptCommonArgs, firstFrame)

        script.pushLayoutContext("write", "%s_Render" % self._item.name())

        metadataNode = nuke.MetadataNode(metadatavalues=[("hiero/project", self._projectName), ("hiero/project_guid", self._project.guid()), ("hiero/shot_tag_guid", self._tag_guid) ] )

        # Add sequence Tags to metadata
        metadataNode.addMetadataFromTags( self._sequence.tags() )
        metadataNode.addMetadata([("hiero/sequence", self._sequence.name())])
        metadataNode.addMetadata([("hiero/shot", self._clip.name())])

        # Apply timeline offset to nuke output
        if isinstance(self._item, hiero.core.TrackItem):
            if self._cutHandles is None:
                # Whole clip, so timecode start frame is first frame of clip
                timeCodeNodeStartFrame = unclampedStart
            else:
                startHandle, endHandle = self.outputHandles()
                timeCodeNodeStartFrame = trackItemTimeCodeNodeStartFrame(unclampedStart, self._item, startHandle, endHandle)
            timecodeStart = self._clip.timecodeStart()
        else:
            # Exporting whole sequence/clip
            timeCodeNodeStartFrame = unclampedStart
            timecodeStart = self._item.timecodeStart()

        script.addNode(nuke.AddTimeCodeNode(timecodeStart=timecodeStart, fps=framerate, dropFrames=dropFrames, frame=timeCodeNodeStartFrame))
        # The AddTimeCode field will insert an integer framerate into the metadata, if the framerate is floating point, we need to correct this
        metadataNode.addMetadata([("input/frame_rate",framerate.toFloat())])

        script.addNode(metadataNode)

        # Add the delivery gizmo
        deliveryNode = nuke.Node('delivery')
        writeNodes.append(nuke.PushNode("ScriptEnd"))
        writeNodes.append(deliveryNode)

        # Generate Write nodes for nuke renders.

        # Bug 45843 - Branch the viewer when using OCIO nodes so
        # the OCIOColorSpace node created for the writer doesn't
        # get used when rendering the viewer.
        branchViewer = useOCIONodes
        if branchViewer:
            branchStackId = "OCIOWriterBranch"
            script.addNode(nuke.SetNode(branchStackId, 0))
            assert(isinstance(writeNodes[-1], nuke.WriteNode))
            ocioNodes = [node for node in writeNodes[-1].getNodes() if node.type() == "OCIOColorSpace"]
            assert(len(ocioNodes))
            ocioNode = ocioNodes[0]
            ocioNode.setAlignToNode(metadataNode)

        scriptFilename = self.resolvedExportPath()

        for node in writeNodes:
            if node.knobs().has_key('file_type'):
                if node.knob('file_type') == 'mov':
                    slateNode = nuke.Node('slate')
                    script.addNode(slateNode)
            node.setInputNode(0, metadataNode)
            script.addNode(node)

        if branchViewer:
            script.addNode(nuke.PushNode(branchStackId))

        # add a viewer
        viewerNode = nuke.Node("Viewer")
        # Bug 45914: If the user has for some reason selected a custom OCIO config, but then set the 'Use OCIO nodes when export' option to False,
        # don't set the 'viewerProcess' knob, it's referencing a LUT in the OCIO config which Nuke doesn't know about
        setViewerProcess = True
        if not self._projectSettings['lutUseOCIOForExport'] and self._projectSettings['ocioConfigPath']:
            setViewerProcess = False

        if setViewerProcess:
            # Bug 45845 - default viewer lut should be set in the comp
            viewerLut = _toNukeViewerLutFormat(self._projectSettings['lutSettingViewer'])
            viewerNode.setKnob("viewerProcess", viewerLut)

        script.addNode( viewerNode )

        hiero.core.log.debug( "Writing Script to: %s", scriptFilename )

        script.popLayoutContext()

        # Layout the script
        #hiero.exporters.FnScriptLayout.scriptLayout(script)

        script.writeToDisk(scriptFilename)

        # Nothing left to do, return False.
        return False

    def startTask(self):
        hiero.core.TaskBase.startTask(self)
        return self._taskStep()

    def finishTask(self):
        hiero.core.TaskBase.finishTask(self)

    def _outputHandles(self, ignoreRetimes):
        """ Override from TaskBase.  This deals with handles in collated sequence export
            as well as individual items. """
        startH, endH = self.outputRange(ignoreHandles = False, ignoreRetimes=ignoreRetimes, clampToSource=False)
        start, end = self.outputRange(ignoreHandles = True, ignoreRetimes=ignoreRetimes)
        return int(round(start - startH)), int(round(endH - end))

    def rootFormat(self):
        """ Get the format that should be set on the Root node. """
        if isinstance(self._item, hiero.core.Sequence) or self._collate:
            return self._sequence.format()
        elif isinstance(self._item, hiero.core.TrackItem):
            return self._item.parentSequence().format()

    def outputRangeForCollatedSequence(self, ignoreHandles):
        """ Get the output range for the collated sequence, with or without handles. """
        start = 0
        end = 0

        if self._startFrame: # Custom start frame specified
            start = self._startFrame
            end = start + self._sequence.duration() - 1

        try:
            start = self._sequence.inTime()
        except RuntimeError:
            # This is fine, no in time set
            pass

        try:
            end = self._sequence.outTime()
        except RuntimeError:
            # This is fine, no out time set
            pass

        # If handles are being ignored, offset the start and end by the handles
        if ignoreHandles and self._collatedSequenceHandles:
            start += self._collatedSequenceHandles[0]
            end -= self._collatedSequenceHandles[1]

        return start, end

    def outputRangeForTrackItem(self, ignoreHandles=False, ignoreRetimes=True, clampToSource=True):
        """ Get the output range for the single track item case. """

        # Get input frame range
        ignoreRetimes = True
        start, end = self.inputRange(ignoreHandles=ignoreHandles, ignoreRetimes=ignoreRetimes, clampToSource=clampToSource)

        if self._retime and isinstance(self._item, hiero.core.TrackItem) and ignoreRetimes:
            # end should always be > start.  abs these values to ensure we don't report a -ve duration.
            srcDuration = abs(self._item.sourceDuration())
            playbackSpeed = abs(self._item.playbackSpeed())

            # If the clip is a freeze frame, then playbackSpeed will be 0.  Handle the resulting divide-by-zero error and set output range to duration
            # of the clip.
            try:
                end = (end - srcDuration) + (srcDuration / playbackSpeed) + (playbackSpeed - 1.0)
            except:
                end = start + self._item.duration() - 1

        start = int(math.floor(start))
        end = int(math.ceil(end))

        # If the task is configured to output to sequence time, map the start and end into sequence time.
        if self.outputSequenceTime():
            offset = self._item.timelineIn() - int(self._item.sourceIn() + self._item.source().sourceIn())

            start = max(0, start + offset) # Prevent start going negative
            end = end + offset

        # Offset by custom start time
        elif self._startFrame is not None:
            startFrame = self._startFrame

            # If a custom start time is specified, this includes the handles.  To get the range without handles, we need to offset this
            if ignoreHandles and self._cutHandles:
                inputRangeWithHandles = self.inputRange(ignoreHandles=False, ignoreRetimes=ignoreRetimes, clampToSource=clampToSource)
                startFrame = startFrame + start - inputRangeWithHandles[0]

            end = startFrame + (end - start)
            start = startFrame

        return start, end

    def outputRange(self, ignoreHandles=False, ignoreRetimes=True, clampToSource=True):
        """outputRange(self)
          Returns the output file range (as tuple) for this task, if applicable"""
        start = 0
        end  = 0

        if isinstance(self._item, hiero.core.Sequence) or self._collate:
            start, end = self.outputRangeForCollatedSequence(ignoreHandles)
        elif isinstance(self._item, hiero.core.TrackItem):
            start, end = self.outputRangeForTrackItem(ignoreHandles, ignoreRetimes, clampToSource)

        return (start, end)


class LocoNukeShotExporterPreset(hiero.core.TaskPresetBase):
    def __init__(self, name, properties):
        hiero.core.TaskPresetBase.__init__(self, LocoNukeShotExporterTask, name)
        self.properties()['writePaths'] = []
        self.properties()['readPaths'] = []
        self.properties()["method"] = "Blend"

    def addCustomResolveEntries(self, resolver):
        if _nuke.env['nc']:
            resolver.addResolver("{ext}", "Extension of the file to be output", "nknc")
        else:
            resolver.addResolver("{ext}", "Extension of the file to be output", "nk")

    def supportedItems(self):
        return hiero.core.TaskPresetBase.kAllItems

    def pathChanged(self, oldPath, newPath):
        for pathlist in (self.properties()["readPaths"], self.properties()["writePaths"]):
            for path in pathlist:
                if path == oldPath:
                    pathlist.remove(oldPath)
                    pathlist.append(newPath)


hiero.core.log.debug( "Registering LocoNukeShotExporter" )
hiero.core.taskRegistry.registerTask(LocoNukeShotExporterPreset, LocoNukeShotExporterTask)