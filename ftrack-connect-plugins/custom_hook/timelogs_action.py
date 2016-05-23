# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import os
import sys
import threading
import logging
import datetime
import time
import calendar
from operator import itemgetter
import uuid

import ftrack

def async(fn):
    '''Run *fn* asynchronously.'''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper

def getEntity(entityType=None, entityId=None):
        if entityType is None or entityId is None:
            return None
        if entityType == 'user':
            return ftrack.User(entityId)
        if entityType == 'show':
            return ftrack.Project(entityId)
        elif entityType == 'task':
            return ftrack.Task(entityId)
        elif entityType == 'list':
            return ftrack.List(entityId)
        elif entityType == 'reviewsession':
            return ftrack.ReviewSession(entityId)
        else:
            return None

def getEntityPath(entityType=None, entity=None):
    if entity is None:
        return

    if entityType == 'user':
        return ' **' + entity.getName()  + '**  *(' + entityType + ')*'

    path=''
    parents=[]

    try:
        parents = entity.getParents()
    except:
        pass
    for i in parents:
        path = (i.getName()) + " / " + path
    path='  **' + path + entity.get('name') + '**  *(' + (entityType if entityType != 'show' else 'project') + ')*'
    return path

def getTasks(entityType=None, entity=None, users=[]):
    '''Get tasks for entity'''
    if entityType == 'list':
        return entity.getObjects()
    return entity.getTasks(includeChildren=True, users=users)

def getName(entity):
    return entity.get('name')

def getWeek(date):
    start = date - datetime.timedelta(days = date.weekday())
    end = start + datetime.timedelta(days = 6)
    return start, end

def getMonth(date):
    first_day = date.replace(day = 1)
    last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
    return first_day, last_day

def getUsers(entityType=None, entity=None):
    if entityType == 'user':
        return [{'label': entity.getName(), 'value':'none'}]
    users = ftrack.getUsers()
    l = [{'label': 'All users', 'value':'all'}]
    for user in users:
        try:
            l.append({'label': user.getName(), 'value':user.getId()})
        except:
            pass
    return l

@async
def create(userId=None, entityType=None, entity=None, values=None):
    return createTimelogBreakdown(userId=userId,entityType=entityType, entity=entity, values=values)

def createTimelogBreakdown(entityType=None, entity=None, userId=None, values=None):
    description = u'Generating timelog report'
    job = ftrack.createJob(
        description=description,
        status='running',
        user=userId
    )

    try:
        html = ""
        range=values['date_range']
        report=values['report_type']
        filterOnUserId=values['user']

        today = datetime.date.today()
        date_range = (today - datetime.timedelta(days=1), today)
        if range == "yesterday":
            date_range = (today - datetime.timedelta(days=2), today - datetime.timedelta(days=1))
        if range == "this_week":
            date_range = getWeek(today)
        if range == "prev_week":
            date_range = getWeek(today - datetime.timedelta(weeks=1))
        if range == "this_month":
            date_range = getMonth(today)
        if range == "prev_month":
            date_range = getMonth(today.replace(day=1) - datetime.timedelta(days=1))
        if range == "this_year":
            date_range = (datetime.date(datetime.date.today().year, 1, 1), datetime.date(datetime.date.today().year, 12, 31))
        if range == "prev_year":
            date_range = (datetime.date(datetime.date.today().year-1, 1, 1), datetime.date(datetime.date.today().year-1, 12, 31))

        title = ''
        if filterOnUserId != 'all':
            title = entity.getName() + " <small>["  + ftrack.User(filterOnUserId).getName() + "] " + date_range[0].strftime('%d') + " " + date_range[0].strftime('%B') + ", " + date_range[0].strftime('%Y') + " - " + date_range[1].strftime('%d') + " " + date_range[1].strftime('%B') + ", " + date_range[1].strftime('%Y') + " </small>"
        else:
            title = entity.getName() + " <small>"+ date_range[0].strftime('%d') + " " + date_range[0].strftime('%B') + ", " + date_range[0].strftime('%Y') + " - " + date_range[1].strftime('%d') + " " + date_range[1].strftime('%B') + ", " + date_range[1].strftime('%Y') + " </small>"

        # HTML Header
        html = "  <html><head>\
                <style>\
                @page { padding: 10pt}\
                @page { margin: 20px; }\
                @page { size: A3}\
                @page { size: A3 landscape }\
                body{margin:30px; padding: 10px}\
                img { page-break-inside: avoid; }\
                .break { clear:both; page-break-after:always; }\
                td, th { page-break-inside: avoid; }\
                </style>\
                <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css'>\
                <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap-theme.min.css'>\
                <script type='text/javascript' src='https://www.google.com/jsapi'></script>"

        # Load Google charts
        html = html + "\
                <script type='text/javascript'>\
                google.load('visualization', '1.0', {'packages':['timeline', 'calendar', 'corechart']});\
                google.setOnLoadCallback(drawChart);"

        # Create Google Timeline object
        html = html + "\
                var chartTimeline = null;\
                var dataTableTimeline = null;\
                var optionsTimeline = null;\
                function drawChart() {\
                    var timeline = document.getElementById('timeline');\
                    chartTimeline = new google.visualization.Timeline(timeline);\
            \
                    dataTableTimeline = new google.visualization.DataTable();\
                    dataTableTimeline.addColumn({ type: 'string', id: 'Task' });\
                    dataTableTimeline.addColumn({ type: 'string', id: 'User' });\
                    dataTableTimeline.addColumn({ type: 'date', id: 'Start' });\
                    dataTableTimeline.addColumn({ type: 'date', id: 'End' });\
                    dataTableTimeline.addRows(["

        # Helpers to keep track of accumulated timelogs/duration
        accumulatedSecondsPerTask = {}
        accumulatedSecondsPerDay = {}
        accumulatedNonBillableSecondsPerDay = {}
        accumulatedSecondsPerUser = {}
        billable = 0
        totalSeconds = 0

        # If selection is a task/folder, add [filtered] timelog events.
        if entityType != 'user':
            tasks = []
            user=None
            if filterOnUserId != 'all':
                user = ftrack.User(filterOnUserId)
                tasks = getTasks(entityType=entityType, entity=entity)
                #tasks = getTasks(entityType=entityType, entity=entity, users=[user.getUsername()])
            else:
                tasks = getTasks(entityType=entityType, entity=entity)
            job.setDescription("Generating timelog report")
            numberOfTasks = len(tasks)
            for i, task in enumerate(tasks):
                if numberOfTasks > 100 and i % 10 == 0:
                    job.setDescription("Generating timelog report - {0:.2f}%".format((float(i)/numberOfTasks)*100))
                timelogs = task.getTimelogs(start=date_range[0], end=date_range[1], includeChildren=False)
                if len(timelogs) == 0:
                    continue

                taskname = task.getName()
                taskId = task.getId()
                isBillable = task.getType().get('isbillable')

                for timelog in timelogs:
                    u = timelog.getUser()
                    if user != None:
                        if u.getId() != filterOnUserId:
                            continue
                    start=timelog.get('start')
                    duration = timelog.get('duration')
                    end=start + datetime.timedelta(seconds = duration)

                    # a fail safe - Google charts will crash if end < start
                    if end < start:
                        end = start + datetime.timedelta(seconds = 60)

                    # accumulate helpers
                    totalSeconds += duration
                    if isBillable:
                        billable += duration
                    else:
                        if start.date() in accumulatedNonBillableSecondsPerDay:
                            accumulatedNonBillableSecondsPerDay[start.date()] += duration
                        else:
                            accumulatedNonBillableSecondsPerDay[start.date()] = duration

                    #create or update dictionary keys/values
                    if start.date() in accumulatedSecondsPerDay:
                        accumulatedSecondsPerDay[start.date()] += duration
                    else:
                        accumulatedSecondsPerDay[start.date()] = duration


                    if taskId in accumulatedSecondsPerTask:
                        accumulatedSecondsPerTask[taskId] += duration
                    else:
                        accumulatedSecondsPerTask[taskId] = duration

                    if u.getId() in accumulatedSecondsPerUser:
                        accumulatedSecondsPerUser[u.getId()] += duration
                    else:
                        accumulatedSecondsPerUser[u.getId()] = duration

                    # add row to timeline object
                    html=html + "\
                        [ '"+ taskname +"', '" + u.getName() + "', new Date(" + start.strftime('%Y') + "," + str(int(start.strftime('%m'))-1) + "," + start.strftime('%d') + ","+start.strftime('%H') + "," + start.strftime('%M') + "," + start.strftime('%S')+"), new Date(" + end.strftime('%Y') + "," +  str(int(end.strftime('%m'))-1) + "," + end.strftime('%d') + ","+end.strftime('%H') + "," + end.strftime('%M') + "," + end.strftime('%S')+")],"
                        #[ '{0}', '{1}', new Date({2},{3},{4},{5},{6},{7}), new Date({8},{9},{10},{11},{12},{13})],".format(taskname, u.getName(), start.strftime('%Y'), str(int(start.strftime('%m'))-1), start.strftime('%d'), start.strftime('%H'), start.strftime('%M'), start.strftime('%S'), end.strftime('%Y'), str(int(end.strftime('%m'))-1), end.strftime('%d'), end.strftime('%H'), end.strftime('%M'), end.strftime('%S'))
                        #[ '"+ taskname +"', '" + u.getName() + "', new Date(" + start.strftime('%Y') + "," + str(int(start.strftime('%m'))-1) + "," + start.strftime('%d') + ","+start.strftime('%H') + "," + start.strftime('%M') + "," + start.strftime('%S')+"), new Date(" + end.strftime('%Y') + "," +  str(int(end.strftime('%m'))-1) + "," + end.strftime('%d') + ","+end.strftime('%H') + "," + end.strftime('%M') + "," + end.strftime('%S')+")],"

        # If selection is a user, add [filtered] user timelog events.
        else:
            user = entity
            timelogs = user.getTimelogs(start=date_range[0], end=date_range[1], includeChildren=True)
            job.setDescription("Generating timelog report")
            for timelog in timelogs:
                try:
                    taskId = timelog.get('context_id')
                    task = ftrack.Task(taskId)
                    isBillable = task.getType().get('isbillable')
                    start=timelog.get('start')
                    duration = timelog.get('duration')
                    end=start + datetime.timedelta(seconds = duration)

                    # a fail safe - Google charts will crash if end < start
                    if end < start:
                        end = start + datetime.timedelta(seconds = 60)

                    # accumulate helpers
                    totalSeconds += duration
                    if isBillable:
                        billable += duration
                    else:
                        if start.date() in accumulatedNonBillableSecondsPerDay:
                            accumulatedNonBillableSecondsPerDay[start.date()] += duration
                        else:
                            accumulatedNonBillableSecondsPerDay[start.date()] = duration
                    #create or update dictionary keys/values
                    if start.date() in accumulatedSecondsPerDay:
                        accumulatedSecondsPerDay[start.date()] += duration
                    else:
                        accumulatedSecondsPerDay[start.date()] = duration

                    if taskId in accumulatedSecondsPerTask:
                        accumulatedSecondsPerTask[taskId] += duration
                    else:
                        accumulatedSecondsPerTask[taskId] = duration
                    if user.getId() in accumulatedSecondsPerUser:
                        accumulatedSecondsPerUser[user.getId()] += duration
                    else:
                        accumulatedSecondsPerUser[user.getId()] = duration

                    # add row to timeline object
                    html=html + "\
                        [ '{0}', '', new Date({1},{2},{3},{4},{5},{6}), new Date({7},{8},{9},{10},{11},{12})],".format(task.getName(), start.strftime('%Y'), str(int(start.strftime('%m'))-1), start.strftime('%d'), start.strftime('%H'), start.strftime('%M'), start.strftime('%S'), end.strftime('%Y'), str(int(end.strftime('%m'))-1), end.strftime('%d'), end.strftime('%H'), end.strftime('%M'), end.strftime('%S'))
                        #[ '" + task.getName() + "', '', new Date(" + start.strftime('%Y') + "," + str(int(start.strftime('%m'))-1) + "," + start.strftime('%d') + ","+start.strftime('%H') + "," + start.strftime('%M') + "," + start.strftime('%S')+"), new Date(" + end.strftime('%Y') + "," + str(int(end.strftime('%m'))-1) + "," + end.strftime('%d') + ","+end.strftime('%H') + "," + end.strftime('%M') + "," + end.strftime('%S')+")],"
                except:
                    pass
        html = html + "]);\
                        optionsTimeline = {\
                        timeline: { rowLabelStyle: {fontName: 'Helvetica', fontSize: 10, color: '#000000'}},\
                        avoidOverlappingGridLines: false,\
                        enableInteractivity: true,\
                    };\
                    chartTimeline.draw(dataTableTimeline, optionsTimeline);"

        # Create Google Pie chart options used by all Pie Charts in document
        html = html + "\
                    var optionsPieChart = {\
                        legend: {position: 'labeled'},\
                        is3D: false,\
                        pieHole: 0,\
                        chartArea:{width:'92%',height:'92%'},\
                        pieSliceText: 'value'\
                    };"

        # Create Google Pie chart object - Total hours
        html = html + "\
                    var dataBillable = google.visualization.arrayToDataTable([\
                    ['Task', 'Hours'],\
                    ['Billable', {0:.2f}],\
                    ['Non-billable',{1:.2f}]]);\
                    \
                    var chartBillable = new google.visualization.PieChart(document.getElementById('billable'));\
                    chartBillable.draw(dataBillable, optionsPieChart);".format(billable/3600, (totalSeconds-billable)/3600)

        # Create Google Pie chart object - User who've logged most hours
        html = html + "\
                    var dataUserMostHours = google.visualization.arrayToDataTable([\
                    ['User', 'Hours'],"
        # Loop through accumulatedSecondsPerUser and add records to chart
        u = sorted(accumulatedSecondsPerUser.items(),key=itemgetter(1),reverse=True)
        for i, t in enumerate(u):
            html = html + "\
                    ['{0}',{1:.2f}],".format(ftrack.User(t[0]).getName().encode('ascii', 'replace'), t[1]/3600)
            if i == 9:
                break

        html = html + "\
                    ]);\
                    var chartUserMostHours = new google.visualization.PieChart(document.getElementById('userMostHours'));\
                    chartUserMostHours.draw(dataUserMostHours, optionsPieChart);"

        # Create Google Pie chart object - Tasks with most hours logged
        html = html + "\
                    var dataTaskMostHours = google.visualization.arrayToDataTable([\
                    ['Task', 'Hours'],"
        # Loop through accumulatedSecondsPerTask and add records to chart
        l = sorted(accumulatedSecondsPerTask.items(),key=itemgetter(1),reverse=True)
        for i, t in enumerate(l):
            html = html + "\
                    ['{0}',{1:.2f}],".format(ftrack.Task(t[0]).getName(), t[1]/3600)
            if i == 9:
                break

        html = html + "\
                    ]);\
                    var chartTaskMostHours = new google.visualization.PieChart(document.getElementById('taskMostHours'));\
                    chartTaskMostHours.draw(dataTaskMostHours, optionsPieChart);"


        # Create Google Calendar object - Heatmap with hours per day
        html = html + "\
                    var dataTableCalendar = new google.visualization.DataTable();\
                    dataTableCalendar.addColumn({ type: 'date', id: 'Date' });\
                    dataTableCalendar.addColumn({ type: 'number', id: 'Won/Loss' });\
                    dataTableCalendar.addRows(["

        # Loop through accumulatedSecondsPerDay and add records to chart
        for day, duration in accumulatedSecondsPerDay.items():
            # adjusting months to match javascript months that starts on 0
            html=html + "\
                    [ new Date({0},{1},{2}),{3:.2f}],".format(day.strftime('%Y'), str(int(day.strftime('%m'))-1), day.strftime('%d'), duration/3600)

        html= html + "]);\
                    var chartCalendar = new google.visualization.Calendar(document.getElementById('calendar'));\
                    var optionsCalendar = {\
                        title: '',\
                        height: 200,\
                        yearLabel: 'none'\
                    };\
                    \
                    chartCalendar.draw(dataTableCalendar, optionsCalendar);"

        # Create Google Area Chart object - Show looged hours per day
        html= html + "\
                    var data = google.visualization.arrayToDataTable([\
                        ['Date', 'Total hours','Non-billable hours'],"
        for day, duration in sorted(accumulatedSecondsPerDay.items()):
            html=html + "\
                        ['{0}',{1:.2f}, {2:.2f}],".format(day.strftime('%d %b, %Y'), duration/3600, (accumulatedNonBillableSecondsPerDay[day]/3600 if day in accumulatedNonBillableSecondsPerDay.keys() else 0))
                        #[ new Date({0},{1},{2}),{3:.2f}, {4:.2f}],".format(day.strftime('%Y'), str(int(day.strftime('%m'))-1), day.strftime('%d'), duration/3600, (accumulatedNonBillableSecondsPerDay[day] if day in accumulatedNonBillableSecondsPerDay.keys() else 0))

        html=html + "\
                    ]);\
                    \
                    var optionsAreaChart = {\
                        vAxis: {minValue: 0},\
                        isStacked: false,\
                        curveType: 'function',\
                        legend: { position: 'bottom' }\
                    };\
                    \
                    var chartAreaChart = new google.visualization.SteppedAreaChart(document.getElementById('areachart'));\
                    chartAreaChart.draw(data, optionsAreaChart);"

        html = html + "\
                }"

        # add event listener to expand Timeline div based on SVG height attribute
        html = html + "\
                window.addEventListener('load', function(){\
                    var svglist = document.getElementsByTagName('svg');\
                    var svg = svglist[svglist.length-1];\
                    console.log(svg.clientHeight || svg.parentNode.clientHeight);\
                    document.getElementById('timeline').setAttribute('style','height:'+(svg.clientHeight+60 || svg.parentNode.clientHeight+60)+'px');\
                    chartTimeline.draw(dataTableTimeline, optionsTimeline);\
                });\
            </script>"

        # HTML Body
        html= html + "\
            </head><body>\
                <ol class='breadcrumb'>"
        # Create Boothstrap Breadcrum
        parents = []
        try:
            parents = entity.getParents()
            parents.reverse()
        except:
            pass
        for parent in parents:
            html = html + "<li>" + parent.getName() + "</li>"
        html= html + "\
                <li class='active'>" + entity.getName() + "</li>\
                </ol>\
                <div class='page-header'>\
                    <h1>"+title+"</h1>\
                </div>\
                <div class='row'>\
                    <div class='col-sm-6 col-md-4'>\
                        <div class='panel panel-default'>\
                            <div class='panel-heading'><h3 class='panel-title'>"+ '{:.2f}'.format(totalSeconds/3600) + " total hours</h3></div>\
                            <div class='panel-body'>\
                                <div id='billable' style='text-align:center'></div>\
                            </div>\
                        </div>\
                    </div>\
                    <div class='col-sm-6 col-md-4'>\
                        <div class='panel panel-default'>\
                            <div class='panel-heading'><h3 class='panel-title'>Who logged most hours?</h3></div>\
                            <div class='panel-body'>\
                                <div id='userMostHours' style='text-align:center'></div>\
                            </div>\
                        </div>\
                    </div>\
                    <div class='col-sm-6 col-md-4'>\
                        <div class='panel panel-default'>\
                            <div class='panel-heading'><h3 class='panel-title'>Task with most hours logged</h3></div>\
                            <div class='panel-body'>\
                                <div id='taskMostHours' style='text-align:center'></div>\
                            </div>\
                        </div>\
                    </div>\
                </div>\
                <div class='panel panel-default'>\
                  <div class='panel-heading'><h3 class='panel-title'>Calendar heatmap</h3></div>\
                  <div class='panel-body' style='overflow:hidden;'>\
                    <div id='calendar' style='margin:auto; width:920px;'></div>\
                  </div>\
                </div>\
                <div class='panel panel-default'>\
                  <div class='panel-heading'><h3 class='panel-title'>Hours logged per day</h3></div>\
                  <div class='panel-body' style='overflow:hidden;'>\
                    <div id='areachart' style=''></div>\
                  </div>\
                </div>\
                <div class='break'></div>\
                <div class='panel panel-default'>\
                    <div class='panel-heading'><h3 class='panel-title'>Timeline</h3></div>\
                    <div class='panel-body'>\
                        <div id='timeline' style='height:100%'></div>\
                    </div>\
                </div>\
            </body>\
        </html>"

        filename = "timelogs-{0}.html".format(str(uuid.uuid1()))
        html_file= open(filename,"w")
        html_file.write(html.encode("utf-8"))
        html_file.close()
        job.createAttachment(filename, fileName=filename)
        job.setDescription("Timelog report")
        job.setStatus('done')
        os.remove(filename)
    except:
        print 'Failed:'
        job.setDescription("Timelog report")
        job.setStatus('failed')


class Timelogs(ftrack.Action):
    '''Timelogs breakdown on entities and users.'''

    label = 'Timelogs details'
    identifier = 'com.ftrack.timelogs'

    def discover(self, event):
        '''Return action config if triggered on a single selection.'''
        data = event['data']
        selection = data.get('selection', [])
        entityType = selection[0]['entityType']
        # If selection contains more than one item return early since
        # this action can only handle a single version.
        selection = data.get('selection', [])
        self.logger.info('Got selection: {0}'.format(selection))
        if len(selection) != 1 or entityType == 'reviewsession':
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon':"https://www.ftrack.com/wp-content/uploads/googledocs.png"
            }]
        }

    def launch(self, event):
        userId = event['source']['user']['id']
        data = event['data']
        selection = data.get('selection', [])
        entityId = selection[0]['entityId']
        entityType = selection[0]['entityType']
        entity = getEntity(entityType=entityType, entityId=entityId)
        if 'values' in event['data']:
            # Do something with the values or return a new form.
            values = event['data']['values']
            ftrack.EVENT_HUB.publishReply(
                event,
                data={
                    'success': True,
                    'message': 'Action was successful'
                }
            )
            create(userId=userId, entityType=entityType, entity=entity, values=values)
            return

        return {
            'items': [
                {
                    'type': 'label',
                    'value': 'Your selection: ' + getEntityPath(entityType=entityType, entity=entity)
                }, {
                    'type': 'label',
                    'value': '___'
                },{
                    'type': 'label',
                    'value': 'Select any project, list, task or other encapsulating \
                    folders to tasks, for any selection you can further filter by user.\
                     You can also select a user (bring in sidebar with User) to get a breakdown on hours logged'
                },{
                    'type': 'label',
                    'value': '___'
                }, {
                    'label': 'Date range',
                    'type': 'enumerator',
                    'name': 'date_range',
                    'value':'prev_month',
                    'data': [
                {
                    'label': 'Today',
                    'value': 'today'
                },{
                    'label': 'Yesterday',
                    'value': 'yesterday'
                },{
                    'label': 'This week',
                    'value': 'this_week'
                },{
                    'label': 'Previous Week',
                    'value': 'prev_week'
                },{
                    'label': 'This month',
                    'value': 'this_month'
                },{
                    'label': 'Previous month',
                    'value': 'prev_month'
                },{
                    'label': 'This year',
                    'value': 'this_year'
                },{
                    'label': 'Previous year',
                    'value': 'prev_year'
                }
                ]
                },{
                    'type': 'label',
                    'value': '___'
                },{
                    'label': 'Report type',
                    'type': 'enumerator',
                    'name': 'report_type',
                    'value':'detailed',
                    'data': [
                    {
                    'label': 'Detailed',
                    'value': 'detailed'
                }, {
                    'label': 'Simple (Tasks collapsed to parent folder)',
                    'value': 'simple'
                }
                ]
                },{
                    'label': 'Filter on user',
                    'type': 'enumerator',
                    'name': 'user',
                    'value':'all',
                    'data': getUsers(entityType=entityType, entity=entity)
                }
            ]
        }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.timelogs'
    )

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    action = Timelogs()
    action.register()


def main():
    '''Register action and listen for events.'''
    logging.basicConfig(level=logging.INFO)

    ftrack.setup()
    action = Timelogs()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    main()