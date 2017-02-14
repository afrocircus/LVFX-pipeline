Frequently Asked Questions
==========================

* **How do I change permissions of my directory or file?**
    Changing directory permissions::

        # Open a terminal, sudo as root.
        su
        Password: locor00t
        # chmod a+w <path of directory>
        chmod a+w /data/production/rnd_pipeline/shots/001/001_0010/

    Changing file permissions::

        # Open a terminal, sudo as root.
        su
        Password: locor00t
        # chmod a+w <path of file>
        chmod a+w /data/production/rnd_pipeline/shots/001/001_0010/scene/layout/001_0010_v01.mb

* **Why do I not see any ftrack actions?**

    First check to see if your ftrack-connect application is running on your computer.
    You can check that `here`_.

    .. _here: ftrack-connect.html

    If ftrack-connect is running on your computer, then check to see the event server workstation is
    running and connected to the network.

    If the computer is running, then check to see if the supervisor daemon is running on the machine.
    You can check this by running::

        # Open a terminal and type
        ssh root@192.168.0.153
        Password: locor00t
        # restart the supervisord service
        service supervisord restart

