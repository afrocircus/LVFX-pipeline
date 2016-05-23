import math

import FnAssetAPI

from assetmgr_hiero.utils import object as objectUtils


__all__ = [
  'setupThumbnails',
  'getThumbnailOptionsForItem',
  'writeThumbnailForObject',
  'processAndWriteThumbnailQImage',
  'getTmpThumbnailPath',
  'getThumbnailFrameForTrackItem'
]


## @name Thumbnails
## These functions relate to the creation of thumbnails from Hiero objects or
## items.
## @{

def setupThumbnails(items, context):
  """
  Iterates the supplied items and calls 'item.prepareThumbnail(options)' if the
  current asset manager returns True for manager.thumbnailSpecification() when
  called with the item's specification.
  """

  if not items:
    return

  manager = FnAssetAPI.SessionManager.currentManager()
  if not manager:
    return
  thumbOpts= {}
  for i in items:
    options = {}
    if not hasattr(i, 'prepareThumbnail'):
      continue
    if getThumbnailOptionsForItem(i, context, options, cache=thumbOpts):
      i.prepareThumbnail(options)


def getThumbnailOptionsForItem(item, context, options, manager=None, cache=None):
  """

  A cached wrapper around Manager.thumbnailSpecification that takes items, and
  an optional cache (dict).

  @param manager [optional] an FnAssetAPI.Manager to use instead the current
  one.

  @param cache dict [optional] a cache of results to use if desired.

  @return bool, As per Manager.thumbnailSpecification

  """

  options.clear()
  ret = False

  spec = item.toSpecification()
  key = spec.getSchema()

  if cache is not None and key in cache:
    ret, opts = cache.get(key)
    options.update(opts)
    return ret

  if not manager:
    manager = FnAssetAPI.SessionManager.currentManager()

  if manager:
    ret = manager.thumbnailSpecification(spec, context, options)

  if cache is not None:
    cache[key] = (ret, options)

  return ret


def writeThumbnailForObject(obj, options, frame=0):
  """

  Takes a hiero.core object and writes its thumbnail to a file based on the
  supplied options dict (from Manager.thumbnailSpecification)path.

  @return the path the thumbnail was written to or '' if it was unsuccessful
  (messages are logged using the asset API).

  """

  try:
    qImage = obj.thumbnail(frame)

    return processAndWriteThumbnailQImage(qImage, options)

  except Exception as e:
    FnAssetAPI.logging.debug("Failed to create thumbnail for %s: %s"
      % (obj, e))

  return ''


def processAndWriteThumbnailQImage(qImage, options):
  """

  Takes a Qimage processes it, and writes it to a file based on the supplied
  options (from Manager.thumbnailSpecification), returns the path or an empty
  string if the write failed.

  """

  ## @todo This isn't a good method as it won't work in batch (when we have it)

  from PySide import QtCore, QtGui

  path = getTmpThumbnailPath(options)

  width = options.get(FnAssetAPI.constants.kField_PixelWidth,
      FnAssetAPI.constants.kThumbnail_DefaultPixelWidth)

  height = options.get(FnAssetAPI.constants.kField_PixelHeight,
      FnAssetAPI.constants.kThumbnail_DefaultPixelHeight)

  qImage = qImage.scaled(width, height,
      QtCore.Qt.KeepAspectRatioByExpanding,
      QtCore.Qt.SmoothTransformation)

  writer = QtGui.QImageWriter()
  writer.setFormat("jpeg")
  writer.setFileName(path)

  if writer.write(qImage):
    return path

  return ''


def getTmpThumbnailPath(options):
  """
  Returns a unique, temporary path that can be used. Its very naive.
  """

  ## @todo This is most likely questionable.

  import os
  import tempfile
  from time import time

  dir = tempfile.gettempdir()
  filename = "thumbnail.%.8f.jpg" % time()

  return os.path.join(dir, filename)

## @}


def getThumbnailFrameForTrackItem(trackItem):
  """

  Returns the souce media 'in' frame from the supplied hiero.core.TrackItem.
  or 0 if one can't be determined.

  """

  frame = 0

  if not trackItem:
    return frame

  clip = objectUtils.clipFromTrackItem(trackItem)
  if not clip:
    return frame

  # For thumbnails, its 0 based, regardless of the actual starting frame number
  # of the media.
  frame = trackItem.sourceIn()

  # The floor is to account for re-times
  frame = math.floor(frame)

  return frame


def getThumbnailFrameForClip(clip):
  """

  Returns the in frame for the clip, or 0 if none was set.

  """

  frame = 0

  if not clip:
    return frame

  # This raises if its not been set
  try:
    frame = clip.posterFrame()
  except RuntimeError:
    pass

  return frame


