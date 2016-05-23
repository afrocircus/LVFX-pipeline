import re
import subprocess


SUBMITTER = '/opt/rprccmd/rprccmd'


def buildCommand(jobName, renderer, pool, splitmode, rendererParams, filename):
    cmd = SUBMITTER + ' -nj_name "%s" -nj_renderer "%s" -nj_pools "%s" -nj_splitmode %s -retnjid' % \
                      (jobName, renderer, pool, splitmode)
    cmd = cmd + ' ' + rendererParams + ' ' + filename
    return cmd


def submitRender(jobName, renderer, pool, splitmode, rendererParams, filename):
    cmd = buildCommand(jobName, renderer, pool, splitmode, rendererParams, filename)
    process = subprocess.Popen(cmd, shell=True, bufsize=64, stdout=subprocess.PIPE)
    outputStr = process.stdout.read()
    return outputStr
