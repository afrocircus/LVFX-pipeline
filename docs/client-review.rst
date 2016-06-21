Client Review System
====================

Loco VFX uses a local installation of ftrack. As a result, clients do not have access to
the media uploaded by the artists. This makes client reviews tedious and gathering notes and
feedback difficult. A solution such as CineSync is ideal, but comes at a price.

The Ftrack cloud server (a remote ftrack installation) supports client reviews natively. It allows clients
to view media and give notes in an easy and secure environment.

Our client review system tries to leverage the benefits of the ftrack cloud server while keeping costs at a
minimum.


Setup
-----

* A single user ftrack cloud account
* An action running locally that syncs the local client review session with the remote cloud account
* An action running locally that syncs the feedback from the remote cloud account to the local ftrack session.


Syncing the Client Review Session
---------------------------------

You can watch `this video`_ to learn about how create a client review session in Ftrack.

.. _this video: https://www.ftrack.com/portfolio/internal-client-review-ftrack


Once you have created your client review session, click on the session and select 'Actions' from the
drop down menu.

.. image:: /img/client-review-selection.png

When you click on Actions, these actions should pop up on your screen.

.. image:: /img/client-review-actions.png

Select the 'Review Sync' action.