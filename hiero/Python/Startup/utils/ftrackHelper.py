'''
Re-using ftrack foundry asm plugin code. This function is taken from
ftrack-connect-package/resource/legacy_plugins/theFoundry/assetmng_hiero/ui/commands.py
'''

import hiero.ui
import FnAssetAPI
import assetmgr_hiero.utils as cmdUtils
import hiero.core

from assetmgr_hiero import utils
from FnAssetAPI.core.decorators import debugStaticCall
from FnAssetAPI.decorators import ensureManager
import thumbnail

def createShotsFromTrackItemsUI(trackItems, options, context=None, parent=None):
  """

  @param trackItems list(hiero.core.TrackItem) Should be sorted in time order.

  @param options UI options dictionary

  @localeUsage hiero.specifications.HieroTimelineLocale

  """
  if not trackItems:
    return []

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()
  if not manager:
    hiero.core.log.error("No Asset Manager has been chosen.")
    return []

  duplicates = cmdUtils.object.checkForDuplicateItemNames(trackItems,
      allowConsecutive=True)
  if duplicates:
    hiero.core.log.error(("There are duplicate Shot names in your selection, "
      + "please make sure any identically named Shots are adjacent or "
      + "overlapping so they can be combined.  - %s.")
        % ", ".join(duplicates))
    return []

  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple

  ## @todo There is probably a better place for this
  #context.locale = specifications.HieroTimelineLocale()
  #context.locale.objects = trackItems

  sequence = None
  if hasattr(trackItems[0], 'sequence'):
    sequence = trackItems[0].sequence()

  # Prepare some to store as persistent options
  timingOpts = cmdUtils.track.filterToTimingOptions(options)
  timingOpts['setShotTimings'] = options.get('setShotTimings', True)

  targetEntityRef = options['targetEntityRef']
  targetEntity = session.getEntity(targetEntityRef, mustExist=True)

  context.managerOptions = options.get('managerOptionsShot', {})

  shotItems = createShotsFromTrackItems(trackItems,
      targetEntity, adoptExistingShots=False,
      updateConflictingShots=False, context=context,
      trackItemOptions=timingOpts, linkToEntities=True,
      coalesseByName=True)

  return shotItems

@ensureManager
@debugStaticCall
def createShotsFromTrackItems(trackItems, targetEntity,
    adoptExistingShots=False, updateConflictingShots=False, context=None,
    trackItemOptions=None, linkToEntities=False, replaceTrackItemMeta=False,
    coalesseByName=True, batch=True):
  """

  This will create new Shots (via. a HieroShotTrackItem) in the current Asset
  Management System, under the supplied targetEntity.

  @param trackItems list, A list of hiero.core.TrackItems to create shots from.

  @param targetEnity Entity, An FnAssetAPI.Entity to create shots under

  @adoptExistingShots bool [False], If true, then any existing shots that match
  by name will be set in the HieroShotTrackItems returned by this call, for
  subsequent use. If false, then the only items associated with an Entity in
  the asset manager will be those used for newly created shots.

  @param updateConflictingShots bool [False], If True, then for shots
  in the asset system that match by name, but have different metadata, the
  properties of the corresponding TrackItem will be used to update the asset
  managed Entity.

  @param trackItemOptions dict {}, Options used when analysing the Hiero Track items
  (for example what timing method to use, etc...) \see
  utils.object.trackitemsToShotItems

  @param linkToEntities bool [False] If True, then each TrackItem will be
  linked to the resulting entity (new, or matched if adopeExistingShots is
  True).

  @param replaceTrackItemMeta bool [False] If True, and linkToEntities is also
  True, then when TrackItems are associated with Entites in the asset system,
  their metadata and timings will be updated to match too.

  @param coalesseByName bool [True] When enabled, TrackItems with identical names
  will be coalesced into a single shot in the asset system, with the union of
  the source TrackItem's timings. If False, multiple shots with the same name
  will be registered.

  @param batch bool [True] When set, will determine whether or not Hiero will
  use the batch version of FnAssetAPI calls to register assets when supported
  by the Manager.

  @return a list HieroShotTrackItems that were used to create the shots.

  """

  ## @todo Ensure only track items passed in?

  l = FnAssetAPI.l

  session = FnAssetAPI.SessionManager.currentSession()
  manager = session.currentManager()
  if not manager:
    raise RuntimeError("No Asset Manager available")

  if not context:
    context = session.createContext()
  context.access = context.kWriteMultiple

  # First check for duplicates
  duplicates = utils.object.checkForDuplicateItemNames(trackItems,
      allowConsecutive=True)
  if duplicates:
    raise RuntimeError("Some supplied TrackItems have duplicate names (%s)" %
        ", ".join(duplicates))

  shotItems = utils.object.trackItemsToShotItems(trackItems, trackItemOptions,
      coalesseByName)

  new, existing, conflicting = analyzeHieroShotItems(shotItems,
      targetEntity, context=context, adopt=adoptExistingShots,
      checkForConflicts=updateConflictingShots)
  # See if we need to make thumbnails (but only for new shots)
  thumbnail.setupThumbnails(new, context)

  if new:
    policy = manager.managementPolicy(new[0].toSpecification(), context)
    batch = batch and policy & FnAssetAPI.constants.kSupportsBatchOperations
    registration = utils.publishing.ItemRegistration(targetEntity, context, items=new)
    if batch:
      #FnAssetAPI.logging.progress(0.5, l("Batch-{publishing} %d {shots}, please"
       #   +" wait...") % len(new))
      utils.publishing.registerBatch(registration, context)

      #FnAssetAPI.logging.progress(1.0, "")
    else:
      utils.publishing.register(registration, session)

  if existing:
    updateEntitiesFromShotItems(existing, context)

  # shotItems will now have an entity in so this is a nice way of returning
  # that data in relation to the orig track items.
  return shotItems

def analyzeHieroShotItems(hieroShotItems, parentEntity, context=None,
    adopt=False, checkForConflicts=True):
  """
  @param adopt bool [False] if True, then any existing, matching shots will be
  set as the entity in the corresponding ShotItem.
  """

  # We're looking for:
  #   - new shots
  newShots = []
  #   - existing shots
  existingShots = []
  #   - existing shots with different timings
  conflictingShots = []

  if not parentEntity:
    return hieroShotItems, [], []

  session = FnAssetAPI.SessionManager.currentSession()
  if not session:
    raise RuntimeError("No Asset Management session is available")

  manager = session.currentManager()
  if not manager:
    raise RuntimeError("No Asset Management system is available")

  if not context:
    context = session.createContext()

  # Set the context to read
  context.access = context.kRead

  # Ensure the target parent entity exists, if it doesn't, this might not be an
  # issue, ans the parent entity ref may be speculative in some systems and
  # it'll be happy creating it on the fly....
  if not parentEntity.exists(context):
    hiero.core.log.debug("analyzeHieroShotItems: Skipping check for "+
        "existing shots under %s as it doesn't exist (yet)." % parentEntity)
    return hieroShotItems, [], []

  existingEntities = utils.shot.checkForExistingShotEntities(hieroShotItems, parentEntity, context)
  # Warn the manager we're about to do a bunch of lookups
  entities = [e for e in existingEntities if e]
  if entities:
    manager.prefetch(entities, context)

  if not existingEntities:
    return hieroShotItems, [], []

  for s,e in zip(hieroShotItems, existingEntities):
    if not e:
      newShots.append(s)
    else:
      existingShots.append(s)

  return newShots, existingShots, conflictingShots


def updateEntitiesFromShotItems(shotItems, context):

  oldLocale = context.locale
  context.access = context.kWriteMultiple

  with FnAssetAPI.SessionManager.currentSession().scopedActionGroup(context):
    for s in shotItems:
      if s.getEntity():
        s.updateEntity(context)

  context.locale = oldLocale
