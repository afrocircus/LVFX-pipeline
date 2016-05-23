__author__ = 'Natasha'

import os
import logging
import shlex
import subprocess


'''def openRepoBrowser():
    cmd = '"%s" /command:repobrowser /outfile:%s' % (tortoiseSVN, outfile)
    result = subprocess.Popen(cmd)
    result.wait()'''
def rabbitCheckout(path):
    repo = 'http://192.168.0.105:6001/repos/newrep/'
    cmd = 'rabbitvcs checkout %s %s' % (path, repo)
    args = shlex.split(cmd)
    subprocess.call(args)


def getSelectedRepo():
    f = open(outfile, 'r')
    repoPath = f.readline()
    return repoPath.strip()


def checkout(url, path):
    cmd = 'svn checkout "%s" "%s"' % (url, path)
    args = shlex.split(cmd)
    result = subprocess.call(args)
    if result != 0:
        logging.error('SVN Checkout error: url=%s path=%s' % (url, path))


def add(path):
    cmd = 'svn add "%s"' % (path)
    args = shlex.split(cmd)
    result = subprocess.call(args)
    if result != 0:
        logging.error('SVN Add error: path=%s' % path)


def commit(path, message):
    cmd = 'svn commit -m "%s" "%s"' % (message, path)
    args = shlex.split(cmd)
    result = subprocess.call(args)
    if result != 0:
        logging.error('SVN checkin error: path=%s' % path)


def status(path):
    textStatus = ''
    if os.path.isdir(path):
        cmd = 'svn status --depth empty -v "%s"' % (path)
    else:
        cmd = 'svn status -v "%s"' % (path)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    out, err = process.communicate()
    #process.kill()
    fields = out.split()
    if fields:
        if not fields[0].isdigit():
            if fields[0] == 'M':
                textStatus = 'modified'
            elif fields[0] == 'A':
                textStatus = 'added'
            elif fields[0] == '?':
                textStatus = 'unversioned'
        else:
            textStatus = 'versioned'
    if err:
        textStatus = 'not added'
    return textStatus


def update(path):
    cmd = 'svn update "%s"' % (path)
    args = shlex.split(cmd)
    result = subprocess.call(args)
    if result != 0:
        logging.error('SVN update error: path=%s' % path)


def getVersionNumber(path):
    revNo = None
    cmd = 'svn status -v "%s"' % (path)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True)
    out, err = process.communicate()
    #process.kill()
    fields = out.split()
    for f in fields:
        if f.isdigit():
            revNo = f
            break
    return revNo