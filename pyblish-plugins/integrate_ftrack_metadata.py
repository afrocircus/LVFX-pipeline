import ftrack
import pyblish.api


@pyblish.api.log
class IntegrateFtrackMeta(pyblish.api.InstancePlugin):
    """
    Integrate metadata with ftrack
    """
    order = pyblish.api.IntegratorOrder
    label = "Integrate metadata with Ftrack"
    families = ['scene']

    hosts = ['maya']
    version = (0, 1, 0)

    def process(self, instance):

        metadata = instance.data['metadata']
        taskid = instance.context.data['taskid']
        task = ftrack.Task(taskid)
        task.setMeta(metadata)

        try:
            task.set('description', 'Published on %s' % instance.context.data['date'])
        except:
            self.log.warn('Unable to set task description.')

        if 'renderCam' in metadata:
            shot = task.getParent()
            shot.set('shot_cam', metadata['renderCam'])

        self.log.info('Integrated metadata with Ftrack')
