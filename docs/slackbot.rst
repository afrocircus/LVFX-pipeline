Slack Messaging Setup
=====================

When are slack messages sent?
-----------------------------

renderbot sends messages to groups or users on slack when
    * There is a new publish
    * If a task status is changed to "Update to Comp" or "Update to Lighting" in ftrack.


How can I ensure my channel receives messages?
----------------------------------------------

In order for the messaging to work, we need to make sure
    * renderbot is part of the slack group
        type ``/invite @renderbot`` in the slack channel to make renderbot part of that group

    * Add the slack channel or user to the config file.
      The config file is located at ``/data/production/pipeline/linux/common/config/slack_ftrack_users.json``
      The file contains a one to one correspondence between the ftrack project name or ftrack username
      and the slack channel or username.

      Example::

        {
        #Ftrack username : Slack username
        "Natasha":"@natasha",
        "Derik":"@derik",
        "Jeanelize":"@jeaneliz",
        "JC":"@jc",
        "Will":"@will",
        "David": "@davetheron",
        "Gina":"@gina_gibson",
        "Dominique":"@dominique",
        "George":"@gwebster",
        "Jason":"@jason",
        "Bradlee":"@hyro-chan",
        "vf_alone":"#alone",
        "sep_dsl":"#dsl",
        #Ftrack Project: Slack channel name
        "osg_szm":"#sizematters",
        "rnd_pipeline":"#test",
        "tutorials":"tutorials"
        }

