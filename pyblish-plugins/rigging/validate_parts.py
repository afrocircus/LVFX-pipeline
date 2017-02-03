import os
import pyblish.api
import ftrack
import subprocess
import pymel.core
from maya import cmds


@pyblish.api.log
class ValidateParts(pyblish.api.InstancePlugin):

    order = pyblish.api.ValidatorOrder + 0.2
    hosts = ['maya']
    families = ['scene']
    label = 'Validate Parts'
    optional = True

    def process(self, instance):

        task = ftrack.Task(instance.context.data['taskid'])
        asset = task.getParent()

        modelingTask = [t for t in asset.getTasks() if t.getName().lower() == 'modeling']
        if len(modelingTask) == 1:
            mTask = modelingTask[0]
            modelMeta = mTask.getMeta()
            if 'publish_model' in modelMeta:
                modelFile = modelMeta['publish_model']
            else:
                self.log.error('No valid model publish found.')
                raise pyblish.api.ValidationError
        else:
            self.log.error('Valid Modeling task not found')
            raise pyblish.api.ValidationError

        if not os.path.exists(modelFile):
            self.log.error('Published model file not found')
            raise pyblish.api.ValidationError

        rig = instance.data['rig']
        rigParts = []
        rigPartsFinal = []
        rigGeo = None
        for each in rig:
            children = cmds.listRelatives(each, children=True)
            for child in children:
                if 'geo' in child.lower():
                    rigParts = cmds.listRelatives(child, ad=True, type='mesh')
                    rigGeo = child
                    break

        if not rigParts or not rigGeo:
            self.log.error('Invalid Rig')
            raise pyblish.api.ValidationError

        # Ignore any intermediate objects if any
        for part in rigParts:
            if not cmds.getAttr(part+'.intermediateObject'):
                rigPartsFinal.append(part)

        mayapy = '/usr/autodesk/maya2016/bin/mayapy'
        cmd = '%s /data/production/pipeline/linux/scripts/getPartnames.py ' \
              '-file %s -group %s' % (mayapy, modelFile, rigGeo)

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        exitcode = process.returncode

        if str(exitcode) != '0':
            self.log.error('Error during part name comparison.')
            raise pyblish.api.ValidationError

        modelParts = err.split('GEO_PARTS: ')[-1].strip('\n').split(',')
        self.log.info('Model Parts: ' + ', '.join(modelParts))

        if rigPartsFinal == modelParts:
            self.log.info('Parts Validated with ref model.')
        else:
            self.log.error('Parts do no match ref model')
            raise pyblish.api.ValidationError

