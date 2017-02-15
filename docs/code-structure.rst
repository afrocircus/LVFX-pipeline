Code Structure
==============

This is a quick overview of the structure of pipeline code.

Where is the pipeline code located?
-----------------------------------

The live pipeline code is located at ``/data/production/pipeline/linux/``
When doing development work, always work locally in your own sandbox. Never work directly in this
folder. Once you are sure of your script, copy it over to the right folder in this location.

How is it structured?
---------------------
List of directories::

    # Top level code directory
    /data/production/pipeline/linux/
    # The directory 'common' includes fonts, environment variables, common coding modules etc.
    /data/production/pipeline/linux/common
    # Contains common fonts to be used by everyone
    /data/production/pipeline/linux/common/fonts
    # Contains config files used by the shot_submit plugin, slack etc.
    /data/production/pipeline/linux/common/config
    # Contains common icons
    /data/production/pipeline/linux/common/icons
    # Contains common code. This includes the ftrack API and common python modules used by plugins
    eg. coverting media using ffmpeg, submitting to the farm, common GUI modules etc.
    /data/production/pipeline/linux/common/packages
    # Template files for various tasks
    /data/production/pipeline/linux/common/template
    # Envionment variables and aliases
    /data/production/pipeline/linux/common/var
    /data/production/pipeline/linux/common/sourceimages
    /data/production/pipeline/linux/common/lighting_assets
    # Documentation files
    /data/production/pipeline/linux/common/docs
    # All maya pluging and scripts
    /data/production/pipeline/linux/maya
    # Yeti module
    /data/production/pipeline/linux/maya/yeti
    # Common Maya shelves
    /data/production/pipeline/linux/maya/shelves
    # Common maya icons
    /data/production/pipeline/linux/maya/icons
    # Common maya modules like MTOA and OpenVDB MAYA_MODULE_PATH
    /data/production/pipeline/linux/maya/modules
    # Maya plugins directory MAYA_PLUG_IN_PATH
    /data/production/pipeline/linux/maya/plug-ins
    # Maya scripts MAYA_SCRIPT_PATH
    /data/production/pipeline/linux/maya/scripts
    /data/production/pipeline/linux/maya/scripts/mel
    /data/production/pipeline/linux/maya/scripts/python
    # Ftrack connect application lives here, along with associated files.
    # You shouldn't have to touch this folder.
    /data/production/pipeline/linux/ftrack-connect-package
    # Ftrack connect user plugins. All ftrack plugins developed by us live here.
    /data/production/pipeline/linux/ftrack-connect-plugins
    /data/production/pipeline/linux/ftrack-connect-plugins/custom_hook
    # All custom ftrack events and actions that are monitored by the ftrack event server.
    /data/production/pipeline/linux/ftrack-events
    /data/production/pipeline/linux/ftrack-events/plugins
    # Custom hiero plugins
    /data/production/pipeline/linux/hiero
    /data/production/pipeline/linux/hiero/Python
    /data/production/pipeline/linux/hiero/Python/Startup
    # Common nuke plugins and gizmos
    /data/production/pipeline/linux/nuke
    # For common nuke gizmos
    /data/production/pipeline/linux/nuke/gizmos
    /data/production/pipeline/linux/nuke/icons
    # For nuke plugins only
    /data/production/pipeline/linux/nuke/plugins
    # Nuke Python scripts
    /data/production/pipeline/linux/nuke/scripts
    # Pyblish scripts, organized as per department.
    /data/production/pipeline/linux/pyblish-plugins
    /data/production/pipeline/linux/pyblish-plugins/animation
    /data/production/pipeline/linux/pyblish-plugins/layout
    /data/production/pipeline/linux/pyblish-plugins/modeling
    /data/production/pipeline/linux/pyblish-plugins/rigging
    # Commonly used python scripts, independent of a 3D application.
    /data/production/pipeline/linux/scripts
    # Standalone Tools
    /data/production/pipeline/linux/tools
    # Linux service scripts
    /data/production/pipeline/linux/init.d

What are the global variables?
------------------------------
All the global environment variables are defined in a single env file.
For JHB::

    /data/production/pipeline/linux/common/var/env

For CPT::
    /data/production/pipeline/linux/common/var/env_cpt

These files are sourced in each computers local ~/.bashrc. These variables tell various application
where to find the plugins and scripts. Also sets up the ftrack environment variables.

Contents of this file::

    # Set the STUDIO variable to JHB (It's set to CPT in the env_cpt file)
    export STUDIO=JHB

    # FOUNDRY_ASSET_PLUGIN_PATH and HIERO_PLUGIN_PATH are used by hiero, these allow us to use the
    ftrack plugins in hiero.
    export FOUNDRY_ASSET_PLUGIN_PATH=/data/production/pipeline/linux/ftrack-connect-package/resource/legacy_plugins/ftrackProvider
    export HIERO_PLUGIN_PATH=/data/production/pipeline/linux/ftrack-connect-package/resource/legacy_plugins/ftrackHieroPlugin:/data/production/pipeline/linux/hiero

    # Sets the python path to include all the scripts we have written. Also includes the ftrack-api.
    export PYTHONPATH=/usr/local/lib/python2.7/site-packages/:/data/production/pipeline/linux/common/packages/loco-api/:/data/production/pipeline/linux/common/packages/ftrack-api-3.3/:/data/production/pipeline/linux/maya/scripts/python:/data/production/pipeline/linux/ftrack-connect-package/resource/legacy_plugins/theFoundry:/data/production/pipeline/linux/ftrack-connect-package/resource/legacy_plugins/theFoundry/assetmgr_hiero:/usr/local/lib/python2.7/site-packages/pyblish/:/usr/local/lib/python2.7/site-packages/pyblish_maya/

    # Setting TEMP variable, used by many scripts to write tmp files.
    export TEMP=/tmp

    # Setting the icons path
    export ICONS_PATH=/data/production/pipeline/linux/common/icons/

    # Setting the maya module path
    export MAYA_MODULE_PATH=/data/production/pipeline/linux/maya/modules

    # Setting the maya plug-in path
    export MAYA_PLUG_IN_PATH=/data/production/pipeline/linux/maya/plug-ins

    # Setting the maya shelf path
    export MAYA_SHELF_PATH=/data/production/pipeline/linux/maya/shelves

    # Setting the maya scripts path
    export MAYA_SCRIPT_PATH=/data/production/pipeline/linux/maya/scripts/mel

    # Setting the nuke path
    export NUKE_PATH=/data/production/pipeline/linux/nuke:/data/production/pipeline/linux/nuke/StarPro

    # Setting the maya icons path
    export XBMLANGPATH=/data/production/pipeline/linux/maya/icons

    # Used by the shot-submit plugin in nuke and maya
    export SHOT_SUBMIT_CONFIG=/data/production/pipeline/linux/common/config/shot_submit_config.json

    # Used by ftrack-connect to find the custom actions written by us.
    export FTRACK_EVENT_PLUGIN_PATH=/data/production/pipeline/linux/ftrack-connect-plugins/custom_hook

    # Used by the optical flares nuke plugin
    export OPTICAL_FLARES_PRESET_PATH=/data/share01/install/2d/Nuke/plugs/OpticalFlaresForNuke.1/OpticalFlares2016/OpticalFlaresForNuke9_1.0.8/Textures-And-Presets
    export OFX_PLUGIN_PATH=/data/production/pipeline/linux/nuke/plugins/Lenscare_OFX_v1.44/

    # Used by Pyblish during publishing in Maya.
    export PYBLISHPLUGINPATH=/data/production/pipeline/linux/pyblish-plugins/
    export MAYA_PYTHON_PATH=/usr/autodesk/maya2016/lib/python2.7/site-packages/
    export PYBLISH_LAYOUT_PATH=/data/production/pipeline/linux/pyblish-plugins/layout
    export PYBLISH_MODELING_PATH=/data/production/pipeline/linux/pyblish-plugins/modeling
    export PYBLISH_RIGGING_PATH=/data/production/pipeline/linux/pyblish-plugins/rigging
    export PYBLISH_ANIMATION_PATH=/data/production/pipeline/linux/pyblish-plugins/animation

What are the global aliases?
----------------------------

The ``/data/production/pipeline/linux/common/var/vars`` file contains a list of variables
and aliases common to all.

The file contains::

    # Variables for directories. Just so it's easy to get to these directories via the commandline.
    export PIPE_DIR=/data/production/pipeline
    export VAR_DIR=$PIPE_DIR/common/var
    export PACKAGES_DIR=$PIPE_DIR/common/packages
    export PIPE_DEV_DIR=$PIPE_DIR/dev
    export PIPE_LIVE_DIR=$PIPE_DIR/live
    export FTRACK_DEV_DIR=$PIPE_DEV_DIR/ftrack-connect-package/resource
    export FTRACK_LIVE_DIR=$PIPE_LIVE_DIR/ftrack-connect-package/resource
    export SHOT_SUBMIT_CONFIG=/data/production/pipeline/linux/common/config/shot_submit_config.json
    export CONFIG_DIR=/data/production/pipeline/linux/common/config/

    # Slack bot token. Used by renderbox and slack API
    export SLACK_BOT_TOKEN=xoxb-72401566256-txDVSBf3peXtMnhdpDBnJ1iM

    # Defining aliases. Aliases are like short cuts, so instead of typing
    "python2.7 <path to script> the user would simply type prores_create or whatever the alias
    name is. It helps create a quick short command in place of a long one.
    alias prores_create='python2.7 /data/production/pipeline/linux/scripts/prores_create.py'
    alias vrscene_submit='python2.7 /data/production/pipeline/linux/scripts/vrscene_submit.py'
    alias vray_export='python2.7 /data/production/pipeline/linux/scripts/vray_export.py'
    alias copy_to_delivery='python2.7 /data/production/pipeline/linux/scripts/copy_to_delivery.py'
    alias make_symlink='python2.7 /data/production/pipeline/linux/scripts/make_symlink.py'
    alias extract_exr_rgb='/data/production/pipeline/linux/scripts/exrExtractRGB/exrExtractRGB'
    alias file_sync='python2.7 /data/production/pipeline/linux/scripts/sync_file.py'


What is the best way to do development work?
--------------------------------------------

First create a local sandbox for your code. You only need to do this once. Get the latest code from
the github repository. Always work locally, and version your code by checking it in to the github
repository.

Set up you own local workspace env by including the ``/data/production/pipeline/linux/common/var/env_dev``
environment variable file in your ~/.bashrc instead of the "env" file. This will ensure that all your
paths point to your local sandbox and not to the live code repository. As a result, when you test your
code, you will be running code in your local sandbox. When you are confident to roll it out to the
studio, copy this code over to the corresponding folder in the live code directory.

The contents of what a local ~/.bashrc should look like can be found in ``/data/production/pipeline/linux/common/docs/workstation_setup.pdf``
