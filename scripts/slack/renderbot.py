import os
import time
import xmlrpclib
import logging
from slackclient import SlackClient


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s:\n%(message)s')

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")
hq_server = xmlrpclib.ServerProxy(os.environ['HQ_SERVER'])

# constants
AT_BOT = "<@" + BOT_ID + ">:"
HELP_COMMAND = "help"
LOG_COMMAND = "getlog"
FAILED_COMMAND = "getfailed"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ['SLACK_BOT_TOKEN'])


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the " + HELP_COMMAND + \
               " to get available commands"
    if command.startswith(HELP_COMMAND):
        response = "Try some of these commands:\n" \
                   "`getLog` _job_id_ ```Gets the output log of job_id```\n" \
                   "`getFailed` _job_id_ ```Gets all the failed child jobs of job_id```"
    elif command.startswith(LOG_COMMAND):
        jobId = command.strip(LOG_COMMAND).strip()
        text = ':runner: Let me go get that log for you!'
        slack_client.api_call("chat.postMessage", channel=channel,
                              text=text, as_user=True)
        try:
            response = hq_server.getJobOutput(int(jobId))
        except Exception, e:
            logging.error(e)
            response = "%s job id is not valid. Or could not find it's output log" % jobId
    elif command.startswith(FAILED_COMMAND):
        jobId = command.strip(FAILED_COMMAND).strip()
        failedJobs = []
        text = ':thinking_face: Hmmm... this may take a few minutes '
        slack_client.api_call("chat.postMessage", channel=channel,
                              text=text, as_user=True)
        try:
            childJobs = hq_server.getJob(int(jobId), ['children'])
            for child in childJobs['children']:
                childStatus = hq_server.getJob(child, ['status'])
                if childStatus['status'] == 'failed':
                    failedJobs.append(str(child))
            response = 'Failed Child Jobs = *{0}*'.format(', '.join(failedJobs))
        except Exception, e:
            logging.error(e)
            response = "%s job id is not valid. Or could not find it's output log" % jobId
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        logging.info("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        logging.info("Connection failed. Invalid Slack token or bot ID?")