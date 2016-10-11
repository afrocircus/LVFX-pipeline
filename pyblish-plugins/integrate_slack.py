import ftrack
import pyblish.api
from Utils import slack_utils


@pyblish.api.log
class IntegrateSlack(pyblish.api.ContextPlugin):
    """
    Integrate metadata with ftrack
    """
    order = pyblish.api.IntegratorOrder
    label = "Send Slack Message"

    hosts = ['maya']
    version = (0, 1, 0)
    active = False

    def process(self, context):

        taskid = context.data['taskid']
        task = ftrack.Task(taskid)
        shot = task.getParent().getName()
        project = task.getProject().getName()

        message = "Project: {0}\nShot: {1}\nStatus: New Publish from {2} ".format(project,
                                                                                  shot, task.getName())
        if 'nextTask' in context.data:
            nextTask = context.data['nextTask']
        else:
            nextTask = ''

        try:
            slack_utils.findTask(task, nextTask, message)
        except Exception:
            self.log.info('Unable to send slack message')
            return

        print nextTask

        self.log.info('Slack message sent successfully')
