Cron Jobs
=========


What is a cron?
---------------

A cron is a scheduled task. It is linux utility which schedules a command or a script to run
automatically at a specified time and date.


What are the scheduled cron jobs at Loco?
-----------------------------------------

**Crons running on the CPT server**

The cape town server runs sync crons run every evening. To access the cron file, first ssh onto the
server with::

    ssh root@192.168.2.5
    password: server

Then access the cron file with the command::

    crontab -e

The file opens up in the terminal::

    # Minute   Hour   Day of Month       Month          Day of Week        Command
    # (0-59)  (0-23)     (1-31)    (1-12 or Jan-Dec)  (0-6 or Sun-Sat)

    # This cron runs everyday at 5pm in CPT
    # Sync all shots for osg_szm. Exclude img, playblasts, playblast and movies dirs
    0 17 * * * rsync -auvzrh --exclude=io --exclude=playblasts --exclude=playblast --exclude=img --exclude=movies --progress /data/production/osg_szm/shots/E1 --exclude=plates root@192.168.0.210:/mnt/production/osg_szm/shots/ > /tmp/rsync_sm_shots_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # Sync all shots for osg_szm. Exclude img, playblasts, playblast and movies dirs
    0 17 * * * rsync -auvzrh --exclude=io --exclude=playblasts --exclude=playblast --exclude=img --exclude=movies --progress /data/production/osg_szm/shots/E2 --exclude=plates root@192.168.0.210:/mnt/production/osg_szm/shots/ > /tmp/rsync_sm_e2_shots_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    40 17 * * * rsync -auvzrh --exclude=incrementalSave --exclude=io --exclude=playblasts --exclude=playblast --exclude=img --exclude=movies --exclude=plates --progress /data/production/vf_alone/shots root@192.168.0.210:/mnt/production/vf_alone/ > /tmp/rsync_alone_shots_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # Sync assets of osg_szm. Exclude movies, vrscenes, incrementalSave and tmp dirs.
    30 17 * * * rsync -auvzrh --exclude=incrementalSave --exclude=io --exclude=playblasts --exclude=playblast --exclude=img --exclude=movies --exclude=tmp --exclude=photogrammetry_data --exclude=render_images --exclude=*.vrscene --exclude=*.mov --exclude=*.tmp  --progress /data/production/osg_szm/assets root@192.168.0.210:/mnt/production/osg_szm/ > /tmp/rsync_osg_szm_assets_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # Change permissions of dirs and files for osg_szm
    0 16 * * * find /data/production/osg_szm/ -exec chmod a+w {} \; > /tmp/osg_szm_chmod_log_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # Change permissions of dirs and files in vf_alone
    15 16 * * * find /data/production/vf_alone/ -exec chmod a+w {} \; > /tmp/vf_alone_chmod_log_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # Start the rsync queue. Run through all files in /data/production/tmp_files
    0 18 * * * /opt/scripts/rsync_queue > /tmp/rsync_queue_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # */1 * * * * echo "This is a cron" > /tmp/test_cron-$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1


**Crons running on the JHB server**

ssh onto the file server in JHB with::

    ssh root@192.168.0.210
    password: server

Then access the cron file with::

    crontab -e

The following file opens in the terminal::

    # Minute   Hour   Day of Month       Month          Day of Week        Command
    # (0-59)  (0-23)     (1-31)    (1-12 or Jan-Dec)  (0-6 or Sun-Sat)

    # This is a hack, changing file permission of all files at 8pm everyday so we do not run
    # into file permission issues.
    # Change file permission for osg_szm
    0 20 * * * find /mnt/production/osg_szm/ -exec chmod a+w {} \; > /tmp/osg_szm_chmod_log_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # Start the rsync queue. Run through all files in /mnt/production/tmp_files
    30 18 * * * /opt/scripts/rsync_queue > /tmp/rsync_queue_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

    # Kill all running rsync jobs at 9am everyday so that we do not slow down CPT network
    0 9 * * * kill -9 `ps -ef | grep 'rsync' | grep -v grep | grep -v $$ | awk '{ print $2 }' | xargs` > /tmp/rsync_jobs_killed_$(date +\%Y\%m\%d\%H\%M\%S).log 2>&1

