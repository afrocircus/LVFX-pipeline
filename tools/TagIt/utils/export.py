import csv


class Export(object):
    def __init__(self, tagDict=None, exportFile=None):
        dataList = self.formatData(tagDict)
        self.writeCSVFile(exportFile, dataList)

    def formatData(self, tagDict):
        """
        Formats the tag dictionary into csv format
        :param tagDict: tag dictionary
        :return: dataList: CSV readable data
        """

        titles = ['Sequence No', 'Sequence Description', 'Sequence Page No', 'Task Type']
        dataList = [titles]
        print tagDict
        for seq in sorted(tagDict.iterkeys()):
            descriptionAdded = False
            for task in tagDict[seq]['tasks']:
                if not descriptionAdded:
                    row = [seq, tagDict[seq]['desc'], tagDict[seq]['page']]
                    descriptionAdded = True
                else:
                    row = ['', '', '']
                row.append(task)
                dataList.append(row)
        return dataList

    def writeCSVFile(self, exportFile, dataList):
        """
        Writes the csv file to disk
        :param exportFile: Output file
        :param dataList: csv data
        :return: None
        """
        with open(exportFile, 'wb') as fp:
            a = csv.writer(fp)
            a.writerows(dataList)