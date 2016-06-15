import ftrack
import logging
import collections
import threading
import os
import sys


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

class AssetCreate(ftrack.Action):

    label = 'Asset Create'
    identifier = 'com.ftrack.assetCreate'

    def getForm(self, number_of_tasks):
        items = []

        items.extend([
            {
                'type': 'label',
                'value': '___'
            }
        ])

        items.extend(
            [
                {
                    'value': '##{0}##'.format('Asset'.capitalize()),
                    'type': 'label'
                }, {
                    'label': 'Asset Names',
                    'type': 'text',
                    'value': '',
                    'name': 'asset_name'
                }, {
                    'label': 'Asset Type',
                    'type': 'enumerator',
                    'value': 'Characters',
                    'name': 'asset_type',
                    'data': [{
                            'label': 'Characters',
                            'value': 'Characters'
                        }, {
                            'label': 'Props',
                            'value': 'Props'
                        }, {
                            'label': 'Sets',
                            'value': 'Sets'
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
        return {'items': items }

    def generate_structure(self, values):
        structure = []
        if 'asset_name' in values:
            structure.append({
                'object_type': 'asset',
                'data': [name.strip() for name in values['asset_name'].split(',')],
                'type': values['asset_type']
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

    @async
    def create(self, parent, structure, projectFolder, assetFolder, createFolders):
        """Create *structure* under *parent*."""
        return self.create_from_structure(parent, structure, projectFolder, assetFolder, createFolders)

    def create_from_structure(self, parent, structure, projectFolder, assetFolder, createFolders):
        """Create *structure* under *parent*."""
        level = structure[0]
        children = structure[1:]
        object_type = level['object_type']

        if object_type == 'asset':
            try:
                asset_object = parent.create('Folder', 'Assets')
            except Exception:
                asset_object = ftrack.getFromPath([parent.getName(), 'Assets'])
            try:
                type_object = asset_object.create('Folder', level['type'])
            except Exception:
                type_object = ftrack.getFromPath([parent.getName(), 'Assets', level['type']])
            projectFolder = os.path.join(projectFolder, 'assets', level['type'].lower())
            self.createFoldersOnDisk(projectFolder, createFolders)

        for data in level['data']:
            if object_type == 'asset':
                try:
                    new_object = type_object.create('Asset Build', data)
                except Exception:
                    new_object = ftrack.getFromPath([parent.getName(), 'Assets', level['type'], data])
                assetFolder = os.path.join(projectFolder, data.lower())
                self.createFoldersOnDisk(assetFolder, createFolders)

            if object_type == 'task':
                taskType = ftrack.TaskType(id=data['typeid'])
                try:
                    new_object = parent.createTask(
                        TASK_TYPE_LOOKUP[data['typeid']],
                        taskType
                    )
                    new_object.set(data)
                    taskFolder = os.path.join(assetFolder, str(taskType.getName()).lower())
                except Exception:
                    logging.info('Task {0} already exists. Doing nothing'.format(
                        TASK_TYPE_LOOKUP[data['typeid']]))
                    new_object = ''
                self.createFoldersOnDisk(taskFolder, createFolders)

            logging.debug(
                'Created {new_object} on parent {parent}'.format(
                    parent=parent, new_object=new_object
                )
            )

            if children:
                self.create_from_structure(new_object, children, projectFolder, assetFolder, createFolders)

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

        if selection[0]['entityType'] == 'show':
            return {
                'items': [{
                    'label': self.label,
                    'actionIdentifier': self.identifier
                }]
            }
        else:
            return

    def launch(self, event):
        selection = event['data'].get('selection', [])
        entityType = selection[0]['entityType']

        if 'values' in event['data']:
            values = event['data']['values']
            if 'number_of_tasks' in values and int(values['number_of_tasks']) >= 0:
                form = self.getForm(int(values['number_of_tasks']))
                return form
            else:
                structure = self.generate_structure(values)
                project = ftrack.Project(selection[0]['entityId'])
                projectFolder = self.getProjectFolder(project)
                self.create(project, structure, projectFolder, projectFolder, values['create_template'])
            return {
                'success': True,
                'message': 'Action completed successfully'
            }

        return {
            'items': [{
                'label': 'Number of tasks',
                'type': 'number',
                'name': 'number_of_tasks',
                'value': 2
            }]
        }

def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.assetCreate'
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

    action = AssetCreate()
    action.register()


logging.basicConfig(level=logging.INFO)
ftrack.setup()
action = AssetCreate()
action.register()

# Wait for events
ftrack.EVENT_HUB.wait()