import os
import sys
import ftrack
import logging
import collections
import threading
import shutil


TASK_TYPE_ENUMERATOR_OPTIONS = [
    {'label': task_type.getName(), 'value': task_type.getId()}
    for task_type in ftrack.getTaskTypes()
]


TASK_TYPE_LOOKUP = dict(
    (task_type.getId(), task_type.getName())
    for task_type in ftrack.getTaskTypes()
)


def async(fn):
    """Run *fn* asynchronously."""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


class BatchCreate(ftrack.Action):

    label = 'Batch Create'
    identifier = 'com.ftrack.batchCreate'
    numberOfTasks = 0
    structureType = 'show'

    def get_form(self, number_of_tasks, structure_type):
        """Return form from *number_of_tasks* and *structure_type*."""

        if structure_type == 'shot' and number_of_tasks == 0:
            return

        items = []

        items.extend([
            {
                'type': 'label',
                'value': '___'
            }
        ])

        if structure_type == 'show':
            items.extend([{
                        'value': '##{0}##'.format('Sequence'.capitalize()),
                        'type': 'label'
                    }, {
                        'label': 'Name',
                        'type': 'text',
                        'value': '001',
                        'name': 'sequence_name'
                    }, {
                        'type': 'label',
                        'value': '___'
                    }, {
                        'value': '##{0}##'.format('Shot'.capitalize()),
                        'type': 'label'
                    }, {
                        'label': 'Expression',
                        'type': 'text',
                        'value': '####',
                        'name': 'shot_expression'
                    }, {
                        'label': 'Incremental',
                        'type': 'text',
                        'value': '10-20:10',
                        'name': 'shot_incremental'
                    }, {
                        'label': 'Add seq prefix',
                        'type': 'enumerator',
                        'value': 'Yes',
                        'name': 'addSeqPrefix',
                        'data': [{
                                'label': 'Yes',
                                'value': 'yes'
                            }, {
                                'label': 'No',
                                'value': 'no'
                            }
                        ]
                    }, {
                        'type': 'label',
                        'value': '___'
                    }
                ]
            )
        elif structure_type == 'sequence':
            items.extend([{
                        'value': '##{0}##'.format('Shot'.capitalize()),
                        'type': 'label'
                    }, {
                        'label': 'Expression',
                        'type': 'text',
                        'value': '####',
                        'name': 'shot_expression'
                    }, {
                        'label': 'Incremental',
                        'type': 'text',
                        'value': '10-20:10',
                        'name': 'shot_incremental'
                    }, {
                        'label': 'Add seq prefix',
                        'type': 'enumerator',
                        'value': 'Yes',
                        'name': 'addSeqPrefix',
                        'data': [{
                                'label': 'Yes',
                                'value': 'yes'
                            }, {
                                'label': 'No',
                                'value': 'no'
                            }
                        ]
                    }, {
                        'type': 'label',
                        'value': '___'
                    }
                ]
            )

        for index in range(0, number_of_tasks):
            items.extend([{
                    'value': '##Template for Task{0}##'.format(index),
                    'type': 'label'
                }, {
                    'label': 'Type',
                    'type': 'enumerator',
                    'name': 'task_{0}_typeid'.format(index),
                    'data': TASK_TYPE_ENUMERATOR_OPTIONS
                }, {
                    'label': 'Bid',
                    'type': 'number',
                    'value': 0,
                    'name': 'task_{0}_bid'.format(index)
                }
            ])

        items.extend([{
                'type': 'label',
                'value': '___'
            }
        ])

        items.extend(
            [{
                'label': 'Create template folders on disk?',
                'type': 'enumerator',
                'value': 'Yes',
                'name': 'create_template',
                'data': [
                    {
                        'label': 'Yes',
                        'value': 'yes'
                    },
                    {
                        'label': 'No',
                        'value': 'no'
                    }
                ]
            }
            ]
        )

        if structure_type == 'show':
            items.extend([
                {
                    'label': 'Create another sequence?',
                    'type': 'enumerator',
                    'value': 'Yes',
                    'name': 'create_a_seq',
                    'data': [{
                            'label': 'Yes',
                            'value': 'yes'
                        }, {
                            'label': 'No',
                            'value': 'no'
                        }
                    ]
                }
            ])

        return {'items': items}

    def getNames(self, base_name, padding, start, end, incremental):
        """Return names from expression."""
        names = []
        for part in range(start, end + incremental, incremental):
            names.append(
                base_name + str(part).zfill(padding)
            )
        return names

    def generateStructure(self, values, entityId):
        """Return structure from *values*."""

        structure = []
        if 'sequence_name' in values:
            seqName = values['sequence_name']
            structure.append({
                'object_type': 'sequence',
                'data': [seqName]
            })
        else:
            seqName = ftrack.Task(entityId).getName()

        if 'shot_expression' in values:
            object_expression = values['shot_expression']
            object_incremental = values['shot_incremental']

            padding = object_expression.count('#')
            _range, incremental = object_incremental.split(':')
            start, end = _range.split('-')

            start = int(start)
            end = int(end)
            incremental = int(incremental)

            base_name = object_expression.replace('#', '')
            if values['addSeqPrefix'] == 'Yes':
                base_name = '%s_%s' % (seqName, base_name)

            logging.info(
                (
                    'Create from expression {expression} with {base_name}, '
                    '{padding} and {start}-{end}:{incremental}'
                ).format(
                    expression=object_expression,
                    base_name=base_name,
                    padding=padding,
                    start=start,
                    end=end,
                    incremental=incremental
                )
            )

            names = self.getNames(
                base_name=base_name,
                padding=padding,
                start=start,
                end=end,
                incremental=incremental
            )

            structure.append({
                'object_type': 'shot',
                'data': names
            })

        tasks = collections.defaultdict(dict)
        for name, value in values.iteritems():
            if name.startswith('task_'):
                _, index, key = name.split('_')
                if key == 'bid':
                    value = float(value) * 3600
                tasks[index][key] = value

        task_data = []
        structure.append({
            'object_type': 'task',
            'data': task_data
        })
        for task in tasks.values():
            task_data.append(task)
        return structure

    def createFoldersOnDisk(self, folder, create):
        if not os.path.exists(folder) and create == 'Yes':
            os.makedirs(folder)

    def createImgFolders(self, shotFolder, create):
        shotFolder = os.path.join(shotFolder, 'img')
        dirs = ['comps', 'plates', 'render']
        for item in dirs:
            folder = os.path.join(shotFolder, item)
            self.createFoldersOnDisk(folder, create)

    def copyTemplateFiles(self, templateFolder, task, taskFolder, shotName):
        taskName = task.getName().lower()
        for file in os.listdir(templateFolder):
            filepath = os.path.join(templateFolder, file)
            if os.path.isfile(filepath):
                if taskName in file:
                    fname, fext = os.path.splitext(file)
                    newFilepath = os.path.join(taskFolder, '%s_v01%s' % (shotName, fext))
                    if not os.path.exists(newFilepath):
                        shutil.copy(filepath, newFilepath)
                    metadata = {
                        'filename':newFilepath
                    }
                    task.setMeta(metadata)

    def getPath(self, parent, data):
        try:
            parents = parent.getParents()
            parents.reverse()
        except:
            parents = []
        path = []
        for p in parents:
            path.append(p.getName())
        path.append(parent.getName())
        path.append(data)
        return path


    @async
    def create(self, parent, structure, projectFolder, tmpFolder, createFolders, templateFolder):
        """Create *structure* under *parent*."""
        return self.create_from_structure(parent, structure, projectFolder,
                                          tmpFolder, createFolders, templateFolder)

    def create_from_structure(self, parent, structure, projectFolder, tmpFolder, createFolders, templateFolder):
        """Create *structure* under *parent*."""
        level = structure[0]
        children = structure[1:]
        object_type = level['object_type']

        for data in level['data']:
            if object_type == 'sequence':
                try:
                    new_object = parent.createSequence(data)
                except Exception:
                    logging.info('Sequence {0} already exists. Doing nothing'.format(data))
                    path = self.getPath(parent, data)
                    new_object = ftrack.getSequence(path)
                projectFolder = os.path.join(projectFolder, data)

            if object_type == 'shot':
                try:
                    new_object = parent.createShot(data)
                    tmpFolder = os.path.join(projectFolder, data)
                    self.createImgFolders(tmpFolder, createFolders)
                    tmpFolder = os.path.join(tmpFolder, 'scene')
                    self.createFoldersOnDisk(tmpFolder, createFolders)
                except Exception:
                    logging.info('Shot {0} already exists. Doing nothing'.format(data))
                    path = self.getPath(parent, data)
                    new_object = ftrack.getShot(path)
                    tmpFolder = os.path.join(projectFolder, data, 'scene')

            if object_type == 'task':
                taskType = ftrack.TaskType(id=data['typeid'])
                try:
                    new_object = parent.createTask(
                        TASK_TYPE_LOOKUP[data['typeid']],
                        taskType
                    )
                    new_object.set(data)
                    folder = os.path.join(tmpFolder, str(taskType.getName()).lower())
                    self.createFoldersOnDisk(folder,createFolders)
                    self.copyTemplateFiles(templateFolder, new_object, folder, parent.getName())
                except Exception:
                    logging.info('Task {0} already exists. Doing nothing'.format(
                        TASK_TYPE_LOOKUP[data['typeid']]))
                    new_object = ''

            logging.debug(
                'Created {new_object} on parent {parent}'.format(
                    parent=parent, new_object=new_object
                )
            )
            if children:
                self.create_from_structure(new_object, children, projectFolder,
                                           tmpFolder, createFolders, templateFolder)


    def getProjectFolder(self, project):
        projFolder = project.get('root')
        if projFolder == '':
            disk = ftrack.Disk(project.get('diskid'))
            rootFolder = ''
            if sys.platform == 'win32':
                rootFolder = disk.get('windows')
            elif sys.platform == 'linux2':
                rootFolder = disk.get('unix')
            projFolder = os.path.join(rootFolder, project.getName())
        return projFolder


    def getTaskType(self, entityId):
        task = ftrack.Task(entityId)
        return task.get('objecttypename')

    def register(self):
        """Register discover actions on logged in user."""
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover',
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and '
            'data.actionIdentifier={0}'.format(self.identifier),
            self.launch
        )

    def discover(self, event):
        """Return action config if triggered on a single selection."""
        selection = event['data'].get('selection', [])

        if not selection:
            return

        entityType = selection[0]['entityType']

        if entityType == 'task':
            entityType = self.getTaskType(selection[0]['entityId'])

        if entityType == 'show' or entityType == 'Episode' or \
                        entityType == 'Sequence' or entityType == 'Shot':
            return {
                'items': [{
                    'label': self.label,
                    'actionIdentifier': self.identifier,
                    'icon':'https://raw.githubusercontent.com/afrocircus/LVFX-pipeline/master/ftrack-events/icons/list.png'
                }]
            }
        else:
            return

    def getParentFolders(self, task, shotFolder):
        parents = task.getParents()
        parents.reverse()
        for parent in parents:
            if 'objecttypename' in parent.keys():
                shotFolder = os.path.join(shotFolder, parent.getName())
        return shotFolder


    def getFolders(self, entityType, entityId):
        if entityType == 'show':
            project = ftrack.Project(entityId)
            rootFolder = self.getProjectFolder(project)
            projectFolder = os.path.join(rootFolder, 'shots')
            shotsFolder = projectFolder
            parent = project
        else:
            task = ftrack.Task(entityId)
            project = ftrack.Project(task.get('showid'))
            rootFolder = self.getProjectFolder(project)
            projectFolder = os.path.join(rootFolder, 'shots')
            shotsFolder = self.getParentFolders(task, projectFolder)
            shotsFolder = os.path.join(shotsFolder, task.getName())
            if entityType == 'Shot':
                shotsFolder = os.path.join(shotsFolder, 'scene')
            parent = task

        templateFolder = os.path.join(rootFolder, 'template_files')
        return parent, projectFolder, shotsFolder, templateFolder

    def launch(self, event):
        selection = event['data'].get('selection', [])
        entityType = selection[0]['entityType']
        label = 'Sequence, Shot, Task'

        if entityType != 'show':
            entityType = self.getTaskType(selection[0]['entityId'])
        if entityType == 'show' or entityType == 'Episode':
            label = 'Sequence, Shot, Task'
            self.structureType = 'show'
        elif entityType == 'Sequence':
            label = 'Shot, Task'
            self.structureType = 'sequence'
        elif entityType == 'Shot':
            label = 'Task'
            self.structureType = 'shot'

        if 'values' in event['data']:
            values = event['data']['values']
            if 'number_of_tasks' in values and int(values['number_of_tasks']) >= 0:
                self.numberOfTasks = int(values['number_of_tasks'])
                form = self.get_form(
                    int(values['number_of_tasks']),
                    self.structureType
                )
                return form
            else:
                structure = self.generateStructure(values, selection[0]['entityId'])
                logging.debug('Creating structure "{0}"'.format(str(structure)))
                parent, projectFolder, shotsFolder, templateFolder = self.getFolders(
                    entityType, selection[0]['entityId']
                )
                self.create(parent, structure, shotsFolder, shotsFolder,
                            values['create_template'], templateFolder)
                if 'create_a_seq' in values:
                    if values['create_a_seq'] == 'Yes':
                        form = self.get_form(
                            self.numberOfTasks,
                            self.structureType
                        )
                        return form
            return {
                    'success': True,
                    'message': 'Action completed successfully'
                }

        return {
            'items': [{
                'type': 'label',
                'value': 'Structure: {0}'.format(label)
            }, {
                'label': 'Number of tasks',
                'type': 'number',
                'name': 'number_of_tasks',
                'value': 2
            }]
        }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.batchCreate'
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

    action = BatchCreate()
    action.register()


logging.basicConfig(level=logging.INFO)
ftrack.setup()
action = BatchCreate()
action.register()

# Wait for events
ftrack.EVENT_HUB.wait()
