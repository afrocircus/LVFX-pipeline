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

