Layout Pipeline
===============

.. note:: Before you start anything, make sure that `ftrack-connect`_ is running.

.. _ftrack-connect: ftrack-connect.html

Artist Workflow
~~~~~~~~~~~~~~~

Open a scene file
-----------------

Once an artist is assigned a layout task, the artist must navigate to the Ftrack task
and open the Maya scene file from the actions menu.

.. image:: /img/comp.gif

When the application launches, the artist timer will start in Ftrack. This tracks the time the
artist spends on the task.

.. image:: /img/ftrack-timer.png

The timer stops when the application is closed.


Layout File Location
----------------------

When the artist starts maya from ftrack, the corresponding asset's model file will be launched.
The file should be called <assetName_version>.mb and will be located at::

    /data/production/<show>/shots/<sq>/<shot>/scene/layout/<shot>_<version>.mb

For example the location of a layout file for shot '001_0010' in sequence '001' for project 'test' will be::

    /data/production/test/shots/001/001_0010/scene/layout/001_0010_v01.mb


Scene Setup
-----------

Open the scene file from ftrack. Click on the LVFX layout shelf. There are 2 tools in LVFX_Layout shelf.

.. image:: /img/layout-shelf.png

* **The camera tool** - Creates a film camera in your scene called 'renderCam'. This camera has extra attributes
  to add an overlay to your viewport when you look through the renderCam. The overlay can be used for framing
  and scene composition.

  .. image:: /img/camera-attr.png
  .. image:: /img/viewport-layout.png

* **The reference tool** - The second tool in the layout shelf is the reference editor. The layout artist must
  refernence the enviroment and character elements through this GUI only.The assets are referenced in with
  the correct namespace which are used during the publish process.
  .. note:: All set dressing elements (those elements that will not be animated) must be referenced in as environment
  elements and all elements that will be animated must be referenced in as character.

  .. image:: /img/layout-ref.png


Scene Publish
-------------

When the layout scene has to be made available to other departments, the artist must run a 'Publish'
This can be done by selecting 'Publish' under the File menu in Maya.

.. image:: /img/publish.png

The publish involves running validation tests that check if the scene was opened via Ftrack,
if the file naming conventions are correct, if a valid renderCam exists and so on.
If a scene passes the validation checks, then the publish is run.

.. image:: /img/layout-publish.png
.. image:: /img/pyblish-buttons.png

Press the 'Play' button shown above to run the validation and publish. If the validation fails,
check the log and fix the scene. Then press the 'refresh' button and re-run the validation and publish.

The layout publish will result in 3 files:

* The renderCam is exported as an alembic file to::

    /data/production/<show>/shots/<sq>/<shot>/shotAsset/camera/renderCam.abc

* The environment elements in the scene are exported to a separate env master file located at::

    /data/production/<show>/shots/<sq>/<shot>/scene/layout/publish/env.mb

* The character elements in the scene are exported to a separate char file located at::

    /data/production/<show>/shots/<sq>/<shot>/scene/layout/publish/<version>/char.mb

In addition, the artist may choose to run a maya playblast for the scene.

The published files are now available to the downstream departments to use in their scenes.
The corresponding ftrack task is updated with the published data as well as the playblast movie, if one
was created.
