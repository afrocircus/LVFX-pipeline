import logging
from pymongo import MongoClient


def getDatabase():
    """
    Initialize database
    """
    client = MongoClient('localhost:27017')
    db = client.MediaData
    return db


def insert(db, folder, name, tags):
    # Insert new document in the database
    try:
        db.Media.insert_one(
            {
                'name': name,
                'tags': tags,
                'refDir': folder
            }
        )
    except Exception, e:
        logging.error(e)


def read(db):
    # Read all entries in the database
    mediaList = []
    try:
        mediaCol = db.Media.find()
        for media in mediaCol:
            mediaList.append(media)

    except Exception, e:
        logging.error(e)
    return mediaList


def find(db, key, value):
    # Find document matching key, value pair in the database
    results = []
    try:
        for result in db.Media.find({key: value}):
            results.append(result)
    except Exception, e:
        logging.error(e)
    return results


def update(db, name, tags, folder):
    # update the database document
    try:
        db.Media.update_one(
            {'refDir': folder},
            {
                "$set": {
                    'name': name,
                    'tags': tags
                }
            }
        )
        logging.info('Records updated successfully')

    except Exception, e:
        logging.error(e)
