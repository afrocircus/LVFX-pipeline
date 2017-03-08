import os
import ftrack
import json
from slacker import Slacker


botId = os.environ['SLACK_BOT_TOKEN']
slack = Slacker(botId)


def sendSlackMessage(user, message):
    """
    Send a message to the user.
    :param user: slack username
    :param message: message string
    :return: None
    """
    slack.chat.post_message(user, message, as_user='@renderbot')


def getSlackUsers(user):
    """
    Gets slack user from the json file containing mapping of ftrack username to slack username
    :param user: Ftrack username
    :return: slackUsername: Slack username or '#general' channel if no matching username found.
    """
    slackUser = '#general'
    if 'CONFIG_DIR' in os.environ:
        slackFile = os.path.join(os.environ['CONFIG_DIR'], 'slack_ftrack_users.json')
        jd = open(slackFile).read()
        data = json.loads(jd)
        if user in data:
            slackUser = data[user]
    return slackUser


def findTask(task, newTaskType):
    """
    Find the correct lighting or compositing task, get its assignee and send them a message.
    :param task: The task whose status has been changed
    :param newTaskType: Either 'Lighting' or 'Compositing' based on status change
    :return: None
    """
    # Get the parent shot
    shot = task.getParent()
    project = task.getProject().getName()

    # Get the lighting task, If not send message to # general
    found = False
    for t in shot.getTasks():
        if t.getType().getName().lower() == newTaskType.lower():
            found = True
            break
    if found:
        # Get the user assigned to the task. If not send message to #general
        users = t.getUsers()
        message = "Project: {0}\nShot: {1}\nStatus: Ready for {2} ".format(project, shot.getName(), newTaskType)
        for user in users:
            slackUser = getSlackUsers(user.getUsername())
            sendSlackMessage(slackUser, message)
        if not users:
            slackGroup = getSlackUsers(project)
            sendSlackMessage(slackGroup, message)
    else:
        tt = ftrack.TaskType(newTaskType)
        shot.createTask('Lighting', taskType=tt)
        message = "Project: {0}\nShot: {1}\nStatus: Ready for {2}\n" \
                  "Note: Task {2} was created as it did not exist".format(project, shot.getName(), newTaskType)
        sendSlackMessage('#general', message)


def callback(event):
    """
    Status Handler. Sets status of task to the updated status of the asset version.
    If status of task or asset version is updated to "Ready for Lighting" or "Ready for Comp",
    sends a message to the assigned user.
    """
    for entity in event['data'].get('entities', []):

        entityType = entity.get('entityType')
        if entityType == 'assetversion' and entity['action'] == 'update':
            if 'keys' not in entity or 'statusid' not in entity.get('keys'):
                return
            version = ftrack.AssetVersion(id=entity['entityId'])
            status = version.getStatus()

            # Set the task status to that of the asset version.
            task = version.getTask()
            task.setStatus(status)

            if status.getName() == 'Ready for Lighting':
                findTask(task, 'Lighting')
            elif status.getName() == 'Ready for Comp':
                findTask(task, 'Compositing')

        elif entityType == 'task' and entity['action'] == 'update':
            if 'keys' not in entity or 'statusid' not in entity.get('keys'):
                return
            task = ftrack.Task(id=entity['entityId'])
            status = task.getStatus()
            if status.getName() == 'Ready for Lighting':
                findTask(task, 'Lighting')
            elif status.getName() == 'Ready for Comp':
                findTask(task, 'Compositing')



# Subscribe to events with the update topic.
ftrack.setup()
ftrack.EVENT_HUB.subscribe('topic=ftrack.update', callback)
ftrack.EVENT_HUB.wait()
