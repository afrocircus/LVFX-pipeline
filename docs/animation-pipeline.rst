Animation Pipeline
==================

.. note:: Before you start anything, make sure that `ftrack-connect`_ is running.

.. _ftrack-connect: ftrack-connect.html

Artist Workflow
~~~~~~~~~~~~~~~

Open a scene file
-----------------

Once an artist is assigned an animation task, the artist must navigate to the Ftrack task
and open the Maya scene file from the actions menu.

.. image:: /img/comp.gif

When the application launches, the artist timer will start in Ftrack. This tracks the time the
artist spends on the task.

.. image:: /img/ftrack-timer.png

The timer stops when the application is closed.


Animation File Location
----------------------

When the artist starts maya from ftrack, the corresponding task's scene file will be launched.
The file will be located at::

    /data/production/<show>/shots/<sq>/<shot>/scene/animation/<shot>_<version>.mb

For example the location of a animation file for shot '001_0010' in sequence '001' for project 'test' will be::

    /data/production/test/shots/001/001_0010/scene/animation/001_0010_v01.mb


Scene Setup
-----------

If a version 01 of the animation file does not exist, the artist can create one by running the "Get Latest
Publish" action. This action can be found by clicking on the animation/previz task and selecting the Actions
menu

.. image:: /img/get-latest-publish.png

This action creates an animation file based on the latest layout publish. It copies the character file
imported by layout, references in the master environment file and also references in the camera alembic file
published by layout.


Scene Update
------------

When artist opens the file associated with the task from Ftrack, it opens the file that is mentioned in the
task's metadata. This information can be found under the 'Info' tab of the task.

.. image:: /img/task-meta.png

If this filename does not correspond to your latest working version, simply click on the action menu and
select "Update to latest". This action will update the metadata to the latest version of the file. You can
then proceed to open the application via Ftrack.

.. image:: /img/update-to-latest.png


Animation Publish
-----------------

When the animation has to be made available to other departments, the artist must run a 'Publish'
This can be done by selecting 'Publish' under the File menu in Maya.

.. image:: /img/publish.png

The publish involves running validation tests that check if the scene was opened via Ftrack,
if the file naming conventions are correct, if the character hierarchies are correct and so on.
If a scene passes the validation checks, then the publish is run.

.. image:: /img/animation-publish.png
.. image:: /img/pyblish-buttons.png

Press the 'Play' button shown above to run the validation and publish. If the validation fails,
check the log and fix the scene. Then press the 'refresh' button and re-run the validation and publish.

The animation publish

* Exports an alembic file for each character in the scene. The alembic file is exported to::

    /data/production/<show>/shots/<sq>/<shot>/shotAsset/<assetName>/<version>/<assetName>.abc

* Creates a playblast. The playblast is saved to::

    /data/production/<show>/shots/<sq>/<shot>/scene/animation/playblast/<shot>_<version>.mov

The playblast is uploaded to ftrack for review. The task metadata is also updated with the publish
information.