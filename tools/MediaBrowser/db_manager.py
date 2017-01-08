from pymongo import MongoClient


def getDatabase():
    client = MongoClient('localhost:27017')
    db = client.MediaData
    return db


def insert(db, folder, name, tags):
    try:
        db.Media.insert_one(
            {
                'name': name,
                'tags': tags,
                'refDir': folder
            }
        )
    except Exception, e:
        print str(e)


def read(db):
    mediaList = []
    try:
        mediaCol = db.Media.find()
        for media in mediaCol:
            mediaList.append(media)

    except Exception, e:
        print str(e)
    return mediaList


def find(db, key, value):
    results = []
    try:
        for result in db.Media.find({key: value}):
            results.append(result)
    except Exception, e:
        print str(e)
    return results


def update(db, name, tags, folder):
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
        print "\nRecords updated successfully\n"

    except Exception, e:
        print str(e)


'''def delete(db):
    try:
        criteria = raw_input('\nEnter employee id to delete\n')
        db.Employees.delete_many({"id": criteria})
        print '\nDeletion successful\n'
    except Exception, e:
        print str(e)'''
