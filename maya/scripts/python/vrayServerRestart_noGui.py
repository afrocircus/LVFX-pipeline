import subprocess
import json

serverConfig = '/data/production/pipeline/linux/common/config/server.json'
jsonFile = open(serverConfig).read()
data = json.loads(jsonFile)

cmd = 'sshpass -p "%s" ssh %s@%s ' \
      '/usr/ChaosGroup/VRLService/linux_x64/bin/vrlsvcctl restart' % (data['password'], data['user'],
                                                                      data['host'])
process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
outputStr = process.stdout.readlines()
print outputStr
if outputStr:
    if 'Starting V-Ray license service...done\n' in outputStr:
        print "VRay Server restarted successfully"
    else:
        print "Unable to restart the VRay Server"
else:
    print "Unable to restart the VRay Server"