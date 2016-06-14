import logging
import ftrack
import ftrack_api


logger = logging.getLogger()


def start_time_on_launch(event):
    """Modify the application environment and start timer for the task."""
    data = event['data']

    username = event['source']['user']['username']

    session = ftrack_api.Session()
    # Get user from username
    user = session.query('User where username is "{}"'.format(username)).one()
    taskid = None
    # Try getting taskid from event selection
    try:
        taskid = data['context']['selection'][0]['entityId']
    except:
        logger.info('Unable to determine task. Timer not starting')

    if taskid:
        task = session.query('Task where id is {}'.format(taskid)).one()
        logger.info('Starting timer for task: ' + task['name'])
        user.start_timer(task, force=True)


def register(registry, **kw):
    """Register location plugin."""

    # Validate that registry is the correct ftrack.Registry. If not,
    # assume that register is being called with another purpose or from a
    # new or incompatible API and return without doing anything.
    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    ftrack.EVENT_HUB.subscribe(
        'topic=ftrack.connect.application.launch',
        start_time_on_launch
    )