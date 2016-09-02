Shot Ingestion
==============

Creating an Ftrack Project
~~~~~~~~~~~~~~~~~~~~~~~~~~
Before you start with the shot ingestion process, make sure the corresponding project exists on Ftrack.
To create an ftrack project, simply go to the ftrack page, click on 'Projects' in the top left corner and
click on the "Create new project" button.

.. image:: /img/proj_create.png

Now a UI will pop up on your screen.

.. image:: /img/proj_create_gui.png

Type in the project name, select the workflow schema and click on 'Create'.

.. note:: 1. Make sure there are no spaces in your project name. Ideally, your project name should be all
          lower case. Use an underscore ('_') to add a space between words.
          2. Please select "VFX Scheme" as the workflow schema.

When a project is created on ftrack, the corresponding folder structure in automatically created on disk.

The template folder structure is:

``Project Drive: /data/production/<project_name>``
``<project_drive>/assets``
``<project_drive>/assets/3d``
``<project_drive>/assets/artwork``
``<project_drive>/assets/hdri``
``<project_drive>/production``
``<project_drive>/production/approvals``
``<project_drive>/production/editorial``
``<project_drive>/production/io``
``<project_drive>/production/meetings``
``<project_drive>/production/schedule``
``<project_drive>/reference``
``<project_drive>/shots``
``<project_drive>/template_files``


Hiero Workflow
~~~~~~~~~~~~~~


