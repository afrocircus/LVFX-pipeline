import sys
import os
import xmlrpclib
import getopt
import getpass
import re
from renderFarm import config


hq_server = xmlrpclib.ServerProxy('{0}:{1}'.format(config.hq_host, config.hq_port))
try:
    hq_server.ping()
except:
    print "HQueue server is down."
    sys.exit(2)


def submitJob(filename, imgFile, startFrame, endFrame, step, chunk, multiple, group,
              priority, user, review, dependent):
    jobList = []
    jobname = 'VRay - '+ os.path.split(filename)[-1]
    if not os.path.exists(imgFile):
        os.makedirs(imgFile)
    if 'LOGNAME' in os.environ.keys():
        submitter = os.environ['LOGNAME']
    else:
        submitter = getpass.getuser()
    if step > 1 or multiple:
        vrayCmdList = []
        for x in range(startFrame, endFrame+1, step):
            frameStart = x
            if multiple:
                newFilename = filename.replace('#', '%04d' % frameStart)
            else:
                newFilename = filename
            vrayCmd = '"/usr/autodesk/maya2016/vray/bin/vray" -display=0 -interactive=0 ' \
                      '-verboseLevel=3 -sceneFile={0} -imgFile={1} ' \
                      '-frames={2}-{2}'.format(newFilename, imgFile, frameStart)
            vrayCmdList.append(vrayCmd)
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
                'command': '"/usr/autodesk/maya2016/vray/bin/vray" -display=0 -interactive=0 '
                           '-verboseLevel=3 -sceneFile={0} -imgFile={1} '
                           '-frames={2}-{3},{4}'.format(filename, imgFile,frameStart, frameEnd, step),
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
        'command': 'export PYTHONPATH=%s ;' % config.python_path,
        'tags' : 'single',
        'priority': priority,
        'submittedBy': submitter,
        'children': jobList,
        'onChildError': 'export PYTHONPATH=%s ;'
                        'export SLACK_BOT_TOKEN=%s ;'
                        'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                        'Fail "%s" "%s"' % (config.python_path, config.slack_bot_token, user, submitter),
        'onSuccess': 'export PYTHONPATH=%s ;'
                     'export SLACK_BOT_TOKEN=%s ;'
                     'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                     'Success "%s" "%s"' % (config.python_path, config.slack_bot_token, user, submitter),
        'onError': 'export PYTHONPATH=%s ;'
                   'export SLACK_BOT_TOKEN=%s ;'
                   'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                   'Fail "%s" "%s"' % (config.python_path, config.slack_bot_token, user, submitter)
    }
    if review:
        mainJob['command'] += 'python2.7 /data/production/pipeline/linux/scripts/mov_create_upload.py ' \
                             '-f %s -d %s' % (filename, imgFile)

    jobs_ids = hq_server.newjob(mainJob)
    return jobs_ids

def main(argv):
    filename = ''
    imgFile = ''
    start = 1
    end = 1
    step = 1
    chunk = 5
    multiple = False
    group = ''
    priority = 0
    user = '#render-updates'
    review = False
    dependent = 0

    try:
        opts, args = getopt.getopt(argv, 'hv:i:f:l:s:c:mg:p:u:rd:', ['vrscene=', 'imgFile=', 'first=',
                                                                     'last=', 'step=', 'chunk=', 'multiple=',
                                                                     'group=', 'priority=', 'slackuser=',
                                                                     'review=', 'dependent='])
    except getopt.GetoptError:
        print 'vrscene_submit -v <filename> -i <imgFile> -f <startFrame> -e <endFrame> -s <step>' \
              '-c <chunk> -m -g <group> -p <priority> -u <username> -r -d <jobID>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print '\nUsage: vrscene_submit -v <vrscene> -i <imgFile> -f <firstFrame> -l <lastFrame> -s <step> ' \
                  '-c <chunk> -m\n' \
                  'Submits vrscene file for render to hqueue \n' \
                  'vrscene = Full filepath. When submitting multiple vrscene files, replace frame with # \n' \
                  'eg. /data/production/ftrack_test/shots/REEL3/REEL3_sh010/scene/lighting/test.#.vrscene \n' \
                  'imgFile = Full path to output img file \n' \
                  'first = first Frame\n' \
                  'last = last Frame\n' \
                  'step = frame step. Default = 1\n' \
                  'chunk = chunk size. Default = 5\n' \
                  'multiple = multiple VR scene files. Default = False\n' \
                  'group = name of group to submit to \n' \
                  'priority = priority of job. 0 is lowest. Default is 0\n' \
                  'slackuser = slack username. Default=#render-updates channel\n' \
                  'review = Create movie and upload to ftrack. Default = False\n' \
                  'dependent = Job ID of the dependent job' \
                  '\n ---Multiple VRScene File Example--- \n' \
                  'vrscene_submit -v /data/production/ftrack_test/shots/REEL3/REEL3_sh010/scene/' \
                  'lighting/vrscene/stagBeetleTest_#.vrscene -i /data/production/ftrack_test/shots/' \
                  'REEL3/REEL3_sh010/scene/lighting/vrscene/renders/stagBeetleTest.#.exr -f 1 -l 15 ' \
                  '-s 4 -c 5 -r -m\n' \
                  '\n ---Single VRScene File Example--- \n' \
                  'vrscene_submit -v /data/production/ftrack_test/shots/REEL3/REEL3_sh010/scene/' \
                  'lighting/vrscene/stagBeetleTest.vrscene -i /data/production/ftrack_test/shots/' \
                  'REEL3/REEL3_sh010/scene/lighting/vrscene/renders/stagBeetleTest.#.exr -f 1 -l 15 ' \
                  '-s 1 -c 5 -r'

            sys.exit()
        elif opt in ('-v', '--vrscene'):
            filename = arg
        elif opt in ('-i', '--imgFile'):
            imgFile = arg
        elif opt in ('-f', '--first'):
            start = int(arg)
        elif opt in ('-l', '--last'):
            end = int(arg)
        elif opt in ('-s', '--step'):
            step = int(arg)
        elif opt in ('-c', '--chunk'):
            chunk = int(arg)
        elif opt in ('-m', '--multiple'):
            multiple = True
        elif opt in ('-g', '--group'):
            group = arg
        elif opt in ('-p', '--priority'):
            priority = int(arg)
        elif opt in ('-u', '--slackuser'):
            user = '@' + arg
        elif opt in ('-r', '--review'):
            review = True
        elif opt in ('-d', '--dependent'):
            dependent = int(arg)
    if filename == '':
        print "Please specify a valid vrscene file."
        sys.exit(2)
    elif imgFile == '':
        print "Please specify a valid output file."
        sys.exit(2)
    jobIds = submitJob(filename, imgFile, start, end, step, chunk, multiple, group, priority,
                       user, review, dependent)
    print 'Job Submit Successful. Job Id = {0}'.format(jobIds)

if __name__ == '__main__':
    main(sys.argv[1:])