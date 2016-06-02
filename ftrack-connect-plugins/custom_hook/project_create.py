import sys
import os
import ftrack
import logging
import threading
import collections
import shutil
import getpass


STRUCTURE_NAMES = ['episode', 'sequence', 'shot']


TASK_TYPE_ENUMERATOR_OPTIONS = [
    {'label': task_type.getName(), 'value': task_type.getId()}
    for task_type in ftrack.getTaskTypes()
]

TASK_TYPE_LOOKUP = dict(
    (task_type.getId(), task_type.getName())
    for task_type in ftrack.getTaskTypes()
)


def async(fn):
    '''Run *fn* asynchronously.'''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper


def get_names(base_name, padding, start, end, incremental):
    '''Return names from expression.'''
    names = []
    for part in range(start, end + incremental, incremental):
        names.append(
            base_name + str(part).zfill(padding)
        )
    return names


def generate_structure(values):
    '''Return structure from *values*.'''
    structure = []
    seqName = values['sequence_name']
    structure.append({
            'object_type': 'sequence',
            'data': [seqName]
        })

    for structure_name in STRUCTURE_NAMES:
        if (structure_name + '_expression') not in values:
            continue

        object_expression = values[structure_name + '_expression']
        object_incremental = values[structure_name + '_incremental']

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

        names = get_names(
            base_name=base_name,
            padding=padding,
            start=start,
            end=end,
            incremental=incremental
        )

        structure.append({
            'object_type': structure_name,
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


@async
def create(parent, structure, projectFolder, tmpFolder, createFolders, templateFolder):
    '''Create *structure* under *parent*.'''
    return create_from_structure(parent, structure, projectFolder, tmpFolder, createFolders, templateFolder)


def createFoldersOnDisk(folder, create):
    if not os.path.exists(folder) and create == 'Yes':
        os.makedirs(folder)


def createImgFolders(shotFolder, create):
    shotFolder = os.path.join(shotFolder, 'img')
    dirs = ['comps', 'plates', 'render']
    for item in dirs:
        folder = os.path.join(shotFolder, item)
        createFoldersOnDisk(folder, create)


def copyTemplateFiles(templateFolder, task, taskFolder, shotName):
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


def create_from_structure(parent, structure, projectFolder, tmpFolder, createFolders, templateFolder):
    '''Create *structure* under *parent*.'''
    level = structure[0]
    children = structure[1:]
    object_type = level['object_type']

    for data in level['data']:

        if object_type == 'sequence':
            new_object = parent.createSequence(data)
            projectFolder = os.path.join(projectFolder, data)

        if object_type == 'shot':
            new_object = parent.createShot(data)
            tmpFolder = os.path.join(projectFolder, data)
            createImgFolders(tmpFolder, createFolders)
            tmpFolder = os.path.join(tmpFolder, 'scene')
            createFoldersOnDisk(tmpFolder, createFolders)

        if object_type == 'task':
            taskType = ftrack.TaskType(id=data['typeid'])
            new_object = parent.createTask(
                TASK_TYPE_LOOKUP[data['typeid']],
                taskType
            )
            new_object.set(data)
            folder = os.path.join(tmpFolder, str(taskType.getName()).lower())
            createFoldersOnDisk(folder, createFolders)
            copyTemplateFiles(templateFolder, new_object, folder, parent.getName())

        logging.debug(
            'Created {new_object} on parent {parent}'.format(
                parent=parent, new_object=new_object
            )
        )
        if children:
            create_from_structure(new_object, children, projectFolder, tmpFolder, createFolders, templateFolder)


def get_form(number_of_tasks, structure_type):
    '''Return form from *number_of_tasks* and *structure_type*.'''

    items = []

    items.extend([
        {
            'type': 'label',
            'value': '___'
        }
    ])

    if structure_type == 'sequence':
        items.extend(
            [
                {
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

    for index in range(0, number_of_tasks):
        items.extend([{
                'value': '##Template for Task{0}##'.format(index),
                'type': 'label'
            },{
                'label': 'Type',
                'type': 'enumerator',
                'name': 'task_{0}_typeid'.format(index),
                'data': TASK_TYPE_ENUMERATOR_OPTIONS
            },{
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
        }, {
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
        }]
    )

    return {'items': items}


class ProjectCreate(ftrack.Action):

    label = 'Project Create'
    identifier = 'com.ftrack.projCreate'
    numberOfTasks = 0
    structureType = ''

    def register(self):
        '''Register discover actions on logged in user.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

    def discover(self, event):
        '''Return action config if triggered on a single selection.'''
        selection = event['data'].get('selection', [])
        entityType = None
        if len(selection)>0:
            entityType = selection[0]['entityType']
        if entityType == 'show':
            return {
                'items': [{
                    'label': self.label,
                    'actionIdentifier': self.identifier
                }]
            }
        else:
            return

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

    def launch(self, event):
        selection = event['data'].get('selection', [])
        project = ftrack.Project(selection[0]['entityId'])
        projectFolder = self.getProjectFolder(project)
        templateFolder = os.path.join(projectFolder, 'template_files')
        projectFolder = os.path.join(projectFolder, 'shots')

        if 'values' in event['data']:
            values = event['data']['values']
            if 'number_of_tasks' in values:
                self.numberOfTasks = int(values['number_of_tasks'])
                self.structureType = values['structure_type']
                form = get_form(
                    int(values['number_of_tasks']),
                    values['structure_type']
                )
                return form
            else:
                structure = generate_structure(values)
                logging.debug('Creating structure "{0}"'.format(str(structure)))
                create(project, structure, projectFolder, projectFolder, values['create_template'], templateFolder)
                if values['create_a_seq'] == 'Yes':
                    form = get_form(
                        self.numberOfTasks,
                        self.structureType
                    )
                    return form
                else:
                    return {
                        'success': True,
                        'message': 'Action completed successfully'
                    }

        return {
            'items': [{
                'label': 'Structure',
                'type': 'enumerator',
                'value': 'sequence',
                'name': 'structure_type',
                'data': [{
                    'label': 'Sequence, Shot',
                    'value': 'sequence'
                }]
            },{
                'label': 'Number of tasks',
                'type': 'number',
                'name': 'number_of_tasks',
                'value': 2
            }]
        }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.projCreate'
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

    action = ProjectCreate()
    action.register()
