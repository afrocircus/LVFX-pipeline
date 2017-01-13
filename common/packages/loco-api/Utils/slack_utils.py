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


def findTask(task, newTaskType, message, project=''):
    """
    Find the correct lighting or compositing task, get its assignee and send them a message.
    :param task: The task whose status has been changed
    :param newTaskType: Either 'Lighting' or 'Compositing' based on status change
    :return: None
    """
    # Get the parent shot
    shot = task.getParent()
    users = []

    # Get the lighting task, If not send message to # general
    found = False
    for t in shot.getTasks():
        if t.getType().getName().lower() == newTaskType.lower():
            found = True
            break
    if found:
        # Get the user assigned to the task. If not send message to #general
        users = t.getUsers()
        for user in users:
            slackUser = getSlackUsers(user.getUsername())
            sendSlackMessage(slackUser, message)
    if not users:
        slackGroup = getSlackUsers(project)
        sendSlackMessage(slackGroup, message)