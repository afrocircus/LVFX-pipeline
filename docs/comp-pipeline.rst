Compositing Pipeline
====================

.. note:: Before you start anything, make sure that `ftrack-connect`_ is running.

.. _ftrack-connect: ftrack-connect.html

Artist Workflow
~~~~~~~~~~~~~~~

Open a scene file
-----------------

Once an artist is assigned a compositing task, the artist must navigate to the Ftrack task
and open the Nuke scene file from the actions menu.

.. image:: /img/comp.gif


Nuke File Location
-------------------

When the artist starts nuke from ftrack, the corresponding shot's nuke script will be launched.
The file should be called <shotname_version>.nk and will be located at::

    $ /data/production/<show>/shots/<sq>/<shot>/scene/compositing/

For example the location of a nuke file for shot '001_0010' in sequence '001' for project 'test' will be::

    $ /data/production/test/shots/001/001_0010/scene/compositing/001_0010_v01.nk


Nuke File Structure
-------------------

A nuke file for a brand new shot must have the following nodes.

.. image:: /img/nuke-template.png