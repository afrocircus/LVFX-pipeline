from flask import render_template, request
from TimeTracker import app
from ftrack import *
import json


@app.route('/')
def index():
    projectNames = getProjects()
    return render_template('home.html', project_list=projectNames)


@app.route('/change_sequence', methods=['POST'])
def setSequence():
    sequences = getSequences(request.form['project'])
    ret = '<option value=all>all</option>'
    for sequence in sequences:
        ret += '<option value="%s">%s</option>' % (sequence, sequence)
    return ret


@app.route('/change_shot', methods=['POST'])
def setShot():
    shots = getShots(request.form['project'], request.form['sequence'])
    ret = '<option value=all>all</option>'
    for shot in shots:
        ret += '<option value="%s">%s</option>' % (shot, shot)
    return ret


@app.route('/load_chart', methods=['POST'])
def loadChart():
    project = request.form['project']
    sequence = request.form['sequence']
    shot = request.form['shot']

    if sequence == 'all':
        dataArr, userArr, logArr = getSequenceChart(project)
    elif shot == 'all':
        dataArr, userArr, logArr = getShotChart(project, sequence)
    else:
        dataArr, userArr, logArr = getTaskChart(project, sequence, shot)
    newArr = [dataArr, userArr, logArr]
    return json.dumps(newArr)


@app.route('/export_data', methods=['POST'])
def exportData():
    project = request.form['project']
    try:
        exportFile = exportCVSData(project)
        return exportFile
    except Exception, e:
        print e
