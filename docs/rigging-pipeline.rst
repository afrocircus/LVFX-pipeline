Rigging Pipeline
================

.. note:: Before you start anything, make sure that `ftrack-connect`_ is running.

.. _ftrack-connect: ftrack-connect.html

Artist Workflow
~~~~~~~~~~~~~~~

Open a scene file
-----------------

Once an artist is assigned a modeling task, the artist must navigate to the Ftrack task
and open the Maya scene file from the actions menu.

.. image:: /img/comp.gif

When the application launches, the artist timer will start in Ftrack. This tracks the time the
artist spends on the task.

.. image:: /img/ftrack-timer.png

The timer stops when the application is closed.


Rigging File Location
----------------------

When the artist starts maya from ftrack, the corresponding asset's model file will be launched.
The file should be called <assetName_version>.mb and will be located at::

    /data/production/<show>/assets/<assetType>/<assetName>/rigging/

For example the location of a rig file for asset 'boy' of type 'character for project 'test' will be::

    /data/production/test/assets/character/boy/rigging/boy_v01.mb


File Setup
----------

A rigging artist must import the publish modeling reference file into their scene.
The latest published modeling reference is located at::

    /data/production/<show>/assets/<assetType>/<assetName>/modeling/publish/assetName_ref.mb


Naming Conventions
------------------

The rig must be grouped under a parent group. The parent group must have '_grp' in it's name.
This group must have 2 child groups: one with '_geo' in it's name and another with '_rig' in its name.
The 'geo' group contains the reference model. The 'rig' group contains the asset rig.

.. image:: /img/rig_outliner.png

It is important to name the model and it's parts correctly as these names will travel through the pipeline.


Publishing
----------

When a rig has to be made available to other departments, the artist must run a 'Publish'
This can be done by selecting 'Publish' under the File menu in Maya.

.. image:: /img/publish.png

The publish involves running validation tests that check if the scene was opened via Ftrack,
if the file and rig naming conventions are correct and so on.
If a scene passes the validation checks, then the publish is run.

.. image:: /img/pyblish-rig-gui.png
.. image:: /img/pyblish-buttons.png

Press the 'Play' button shown above to run the validation and publish. If the validation fails,
check the log and fix the scene. Then press the 'refresh' button and re-run the validation and publish.

The model in the scene is exported to a publish folder and renamed::

    /data/production/<show>/assets/<assetType>/<assetName>/rigging/publish/assetName_rig.mb

This scene is now available to the downstream departments to use in their scenes.
The corresponding ftrack task is updated with the publish data.
