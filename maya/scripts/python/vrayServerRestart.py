import subprocess
import json
import pymel.core as pm

serverConfig = '/data/production/pipeline/linux/common/config/server.json'
jsonFile = open(serverConfig).read()
data = json.loads(jsonFile)
password = data['password']

cmd = 'sshpass -p "%s" ssh root@192.168.0.208 ' \
      '/usr/ChaosGroup/VRLService/linux_x64/bin/vrlsvcctl restart' % password
process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
outputStr = process.stdout.readlines()
if outputStr:
    if 'Starting V-Ray license service...done\n' in outputStr:
        pm.confirmDialog(t= 'Server Restart', m = 'Vray Server Successfully Restarted!', b='OK')
    else:
        pm.confirmDialog(t= 'Server Restart', m = 'Unable to restart the VRay server!', b='OK')
else:
    pm.confirmDialog(t= 'Server Restart', m = 'Unable to restart the VRay server!', b='OK')