import os
import re
import xmlrpclib
import getpass


def getHQServerProxy(hq_host, hq_port):
    hq_server = xmlrpclib.ServerProxy('{0}:{1}'.format(hq_host, hq_port))
    try:
        hq_server.ping()
    except:
        hq_server = None
    return hq_server


def submitNoChunk(hq_server, jobname, vrayCmd, priority, tries, group, vrayRestart, pythonPath,
                  slackToken, slackUser, dependent):
    if 'LOGNAME' in os.environ.keys():
        submitter = os.environ['LOGNAME']
    else:
        submitter = getpass.getuser()
    job_spec = {
        'name': jobname,
        'shell': 'bash',
        'command': vrayCmd,
        'tags': ['single'],
        'submittedBy': submitter,
        'triesLeft': tries,
        'priority': priority,
        'onSuccess': 'export PYTHONPATH=%s ;'
                     'export SLACK_BOT_TOKEN=%s ;'
                     'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                     'Success "%s" "%s"' % (pythonPath, slackToken, slackUser, submitter),
        'onError': 'export PYTHONPATH=%s ;'
                   'export SLACK_BOT_TOKEN=%s ;'
                   'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                   'Fail "%s" "%s"' % (pythonPath, slackToken, slackUser, submitter)
    }
    if vrayRestart:
        job_spec['onError'] = 'export PYTHONPATH=%s ;' \
                              'export SLACK_BOT_TOKEN=%s ;' \
                              'python2.7 /data/production/pipeline/linux/scripts/renderFarm/vray_restart_onError.py ;' \
                              'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py ' \
                              'Fail "%s" "%s"' % (pythonPath, slackToken, slackUser, submitter)
    if group:
        job_spec['conditions'] = [{"type" : "client", "name": "group", "op": "==", "value": group}, ]
    if dependent:
        job_spec['childrenIds'] = [dependent]
    job_ids = hq_server.newjob(job_spec)
    return job_ids


def submitVRayStandalone(hq_server, jobname, filename, imgFile, vrCmd, startFrame, endFrame,
                         step, chunk, multiple, group, priority, review, pythonPath, slackToken,
                         slackUser, dependent, progressive, taskid):
    jobList = []
    if 'LOGNAME' in os.environ.keys():
        submitter = os.environ['LOGNAME']
    else:
        submitter = getpass.getuser()
    if step > 1 or multiple or progressive > 0:
        vrayCmdList = []
        for x in range(startFrame, endFrame+1, step):
            frameStart = x
            if multiple:
                newFilename = filename.replace('#', '%04d' % frameStart)
            else:
                newFilename = filename
            vrayCmd = '{0} -sceneFile={1} -frames={2}-{2}'.format(vrCmd, newFilename, frameStart)
            vrayCmdList.append(vrayCmd)

        if progressive > 0:
            # reorder list for progressive rendering.
            tmpList = []
            for i in range(0, progressive):
                for j in range(i, len(vrayCmdList), progressive):
                    tmpList.append(vrayCmdList[j])
            vrayCmdList = tmpList

        for y in range(0, len(vrayCmdList), chunk):
            command = ' ; '.join(vrayCmdList[y:y+chunk])
            frameFinder = re.findall('frames=(\d+)-(\d+)', command)
            job_spec = {
                'name': jobname+ ' Frames:{0}-{1}'.format(frameFinder[0][0], frameFinder[-1][0]),
                'shell': 'bash',
                'command': command,
                'submittedBy': submitter,
                'tags': ['single'],
                'priority': priority,
                'triesLeft': 1,
                'onError': 'python2.7 /data/production/pipeline/linux/scripts/renderFarm/vray_restart_onError.py'
            }
            if group != '':
                job_spec['conditions'] = [{"type" : "client", "name": "group", "op": "==", "value": group}, ]
            if dependent != 0:
                job_spec['childrenIds'] = [dependent]
            jobList.append(job_spec)
    else:
        for x in range(startFrame, endFrame+1, chunk):
            frameStart = x
            if x+chunk-1 > endFrame:
                frameEnd = endFrame
            else:
                frameEnd = x+chunk-1
            job_spec = {
                'name': jobname + ' Frames:{0}-{1}'.format(frameStart, frameEnd),
                'shell': 'bash',
                'command': '{0} -sceneFile={1} -frames={2}-{3},{4}'.format(vrCmd, filename,
                                                                           frameStart, frameEnd, step),
                'submittedBy': submitter,
                'tags': ['single'],
                'priority': priority,
                'triesLeft': 1,
                'onError': 'python2.7 /data/production/pipeline/linux/scripts/renderFarm/vray_restart_onError.py'
            }
            if group != '':
                job_spec['conditions'] = [{"type" : "client", "name": "group", "op": "==", "value": group}, ]
            if dependent != 0:
                job_spec['childrenIds'] = [dependent]
            jobList.append(job_spec)

    mainJob = {
        'name': jobname,
        'shell': 'bash',
        'command': 'export PYTHONPATH=%s ;' % pythonPath,
        'tags' : 'single',
        'priority': priority,
        'submittedBy': submitter,
        'children': jobList,
        'onChildError': 'export PYTHONPATH=%s ;'
                   'export SLACK_BOT_TOKEN=%s ;'
                   'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                   'Fail "%s" "%s"' % (pythonPath, slackToken, slackUser, submitter),
        'onSuccess': 'export PYTHONPATH=%s ;'
                     'export SLACK_BOT_TOKEN=%s ;'
                     'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                     'Success "%s" "%s"' % (pythonPath, slackToken, slackUser, submitter),
        'onError': 'export PYTHONPATH=%s ;'
                   'export SLACK_BOT_TOKEN=%s ;'
                   'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                   'Fail "%s" "%s"' % (pythonPath, slackToken, slackUser, submitter)
    }
    if review:
        movFile = os.path.join(os.path.dirname(imgFile), os.path.basename(filename).split('.')[0] + '.mov')
        mainJob['command'] += 'python2.7 /data/production/pipeline/linux/scripts/mov_create_upload.py ' \
                              '-f "%s" -t %s -d "%s"' % (movFile, taskid, imgFile)
        print mainJob['command']

    jobs_ids = hq_server.newjob(mainJob)
    return jobs_ids
