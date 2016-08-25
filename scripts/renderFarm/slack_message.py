import os
import sys
import xmlrpclib
import config
from slacker import Slacker

botId = os.environ['SLACK_BOT_TOKEN']
slack = Slacker(botId)

hq_server = xmlrpclib.ServerProxy('{0}:{1}'.format(config.hq_host, config.hq_port))
jobId = os.environ['JOBID']
job = hq_server.getJob(int(jobId))

if len(sys.argv) > 3:
    arg = sys.argv[1]
    user = sys.argv[2]
    submitter = sys.argv[3]
    if arg == 'Success':
        message = 'Job ID: {0}\n' \
                  'Job Name: {1}\n' \
                  'Submitted By: {2}\n' \
                  'Status: Success :+1:'.format(jobId, job['name'], submitter)
    elif arg == 'Fail':
        message = 'Job ID: {0}\n' \
                  'Job Name: {1}\n' \
                  'Submitted By: {2}\n' \
                  'Status: Fail :-1:'.format(jobId, job['name'], submitter)
    else:
        message = 'Incorrect argument passed to slack_message.py :confused:'
    slack.chat.post_message(user, message, as_user='@renderbot')
