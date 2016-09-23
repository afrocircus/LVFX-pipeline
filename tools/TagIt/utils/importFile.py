import csv
from collections import defaultdict


class ImportFile(object):
    def __init__(self, filename=None):
        self.filename = filename

    def readCSV(self):
        rows = []
        with open(self.filename, 'rb') as fp:
            reader = csv.reader(fp)
            for row in reader:
                rows.append(row)
        tagDict = self.convertToTagDict(rows[1:])
        return tagDict

    def convertToTagDict(self, dataList):
        tagDict = defaultdict(dict)
        sceneLine = ''
        for tagList in dataList:
            if tagList[0] is not '':
                sceneLine = int(tagList[0])
                d = tagDict[sceneLine]
                d['desc'] = tagList[1],
                d['page'] = int(tagList[2])
                d['tasks'] = [(tagList[3], int(tagList[4]))]
            else:
                tagDict[sceneLine]['tasks'].append((tagList[3], int(tagList[4])))
        return tagDict


