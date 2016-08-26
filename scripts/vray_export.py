import sys
import os
import argparse
import getpass
import xmlrpclib
from renderFarm import config


hq_server = xmlrpclib.ServerProxy('{0}:{1}'.format(config.hq_host, config.hq_port))
try:
    hq_server.ping()
except:
    print "HQueue server is down."
    sys.exit(2)


def submitJob(mayaFile, proj, start, end, step, camera, renderLayers, separate, vrscene,
              user, group, priority):
    jobname = 'VRay - '+ os.path.split(mayaFile)[-1]
    if 'LOGNAME' in os.environ.keys():
        submitter = os.environ['LOGNAME']
    else:
        submitter = getpass.getuser()
    vrayCmd = 'export MAYA_DISABLE_CIP=1 ; ' \
              'source /root/.bashrc ;' \
              '"/usr/autodesk/maya2016/bin/Render" -r vray -proj "{0}" -noRender -exportCompressed ' \
              '-s {1} -e {2} -b {3} -exportFileName "{4}" '.format(proj, start, end, step, vrscene)
    if camera:
        vrayCmd += '-cam {0} '.format(camera)
    if renderLayers:
        vrayCmd += '-rl {0} '.format(renderLayers)
    if separate:
        vrayCmd += '-exportFramesSeparate '
    vrayCmd += mayaFile
    mainJob = {
        'name': jobname,
        'shell': 'bash',
        'command': vrayCmd,
        'tags' : 'single',
        'priority': priority,
        'submittedBy': submitter,
        'triesLeft': 1,
        'onSuccess': 'export PYTHONPATH=%s ;'
                     'export SLACK_BOT_TOKEN=%s ;'
                     'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                     'Success "%s" "%s"' % (config.python_path, config.slack_bot_token, user, submitter),
        'onError': 'export PYTHONPATH=%s ;'
                   'export SLACK_BOT_TOKEN=%s ;'
                   'python2.7 /data/production/pipeline/linux/scripts/renderFarm/vray_restart_onError.py ;'
                   'python2.7 /data/production/pipeline/linux/scripts/renderFarm/slack_message.py '
                   'Fail "%s" "%s"' % (config.python_path, config.slack_bot_token, user, submitter)
    }
    if group:
        mainJob['conditions'] = [{"type" : "client", "name": "group", "op": "==", "value": group}, ]
    jobs_ids = hq_server.newjob(mainJob)
    return jobs_ids


def main(argv):
    parser = argparse.ArgumentParser(description='Submits a VR Export Job to HQueue.')
    parser.add_argument('-scene', help='Input Maya scene file', required=True)
    parser.add_argument('-proj', help='VRScene output folder. Defaults to <maya scene dir>/vrscene')
    parser.add_argument('-start', help='Start frame', required=True)
    parser.add_argument('-end', help='End frame', required=True)
    parser.add_argument('-step', help='Step', default=1)
    parser.add_argument('-cam', help='Camera to be rendered')
    parser.add_argument('-rl', help='Render Layers to be rendered. Comma separated list')
    parser.add_argument('-ex', help='Exported VRscene file name', required=True)
    parser.add_argument('-sep', help='Export separate vrscene files per frame.', nargs='?', const='True',
                        default=False)
    parser.add_argument('-user', help='Send post render to slack user', default='#render-updates')
    parser.add_argument('-group', help='HQueue client group name')
    parser.add_argument('-priority', help='HQueue render priority', default=0)

    args = parser.parse_args()
    mayaFile = args.scene
    proj = args.proj
    if not proj:
        proj = os.path.join(os.path.dirname(mayaFile), 'vrscene')
        if not os.path.exists(proj):
            os.makedirs(proj)
    start = args.start
    end = args.end
    step = args.step
    camera = args.cam
    renderLayers = args.rl
    separate = args.sep
    vrscene = args.ex
    user = args.user
    group = args.group
    priority = args.priority
    jobIds = submitJob(mayaFile, proj, start, end, step, camera, renderLayers, separate, vrscene,
                      user, group, priority)
    print 'Job Submit Successful. Job Id = {0}'.format(jobIds)

if __name__ == '__main__':
    main(sys.argv[1:])
