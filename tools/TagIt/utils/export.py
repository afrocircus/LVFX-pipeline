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

        titles = ['Sequence Name', 'Sequence Description', 'Sequence Page No',
                  'Shot Name', 'Shot Description', 'Shot Page No', 'Task Type',
                  'Task Name', 'Assignee', 'Bid']
        dataList = [titles]
        for seq in sorted(tagDict.iterkeys()):
            descriptionAdded = False
            shots = tagDict[seq]['shots']
            if len(shots) > 0:
                for shot in sorted(shots.iterkeys()):
                    shotDescription = False
                    tasks = shots[shot]['task']
                    if len(tasks) > 0:
                        for task in tasks:
                            row, descriptionAdded = self.formatSeqShot(seq, tagDict, descriptionAdded)
                            shotRow, shotDescription = self.formatSeqShot(shot, shots, shotDescription)
                            row.extend(shotRow)
                            row.append(task)
                            dataList.append(row)
                    else:
                        row, descriptionAdded = self.formatSeqShot(seq, tagDict, descriptionAdded)
                        shotRow, shotDescription = self.formatSeqShot(shot, shots, shotDescription)
                        row.extend(shotRow)
                        dataList.append(row)
            else:
                row, descriptionAdded = self.formatSeqShot(seq, tagDict, descriptionAdded)
                dataList.append(row)
        return dataList

    def formatSeqShot(self, key, tagDict, descriptionFlag):
        row = [key]
        if not descriptionFlag:
            row.append(tagDict[key]['description'])
            descriptionFlag = True
        else:
            row.append('')
        row.append(tagDict[key]['page'])
        return row, descriptionFlag

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