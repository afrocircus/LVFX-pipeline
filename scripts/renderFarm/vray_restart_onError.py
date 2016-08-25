import os
import xmlrpclib
import re
import subprocess
import json
import config

serverConfig = '/data/production/pipeline/linux/common/config/server.json'
jsonFile = open(serverConfig).read()
data = json.loads(jsonFile)

hq_server = xmlrpclib.ServerProxy('{0}:{1}'.format(config.hq_host, config.hq_port))

if 'JOBID' in os.environ.keys():
    jobId = int(os.environ['JOBID'])
    output = hq_server.getJobOutput(jobId)
    m = re.findall('Could not obtain a license \(1002\)', output)
    if m and len(m) > 0:
        cmd = 'sshpass -p "%s" ssh %s@%s ' \
              '/usr/ChaosGroup/VRLService/linux_x64/bin/vrlsvcctl restart' % (data['password'],
                                                                              data['user'],data['host'])
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        outputStr = process.stdout.readlines()
        print outputStr
else:
    output = 'Job id not found'
    print output
