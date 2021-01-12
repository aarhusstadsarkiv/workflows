#!/usr/bin/python
# encoding=utf8
import baseWorkflowUnit
import unicodeCSV

from workFlowConstants import *


def loadCSVtoListTuple(csvFilePath):
    fileObject = open(csvFilePath, "rb")

    reader = unicodeCSV.UnicodeReader(fileObject)

    csvHeader = reader.next()

    return csvHeader, reader


class WorkflowUnit(baseWorkflowUnit.BaseWorkflowUnit):
    """Loads CSV(s) file into a tuple with the [header, data] format if used with more files the csv files must have identical headers"""

    def __init__(self, GUI, unitID):
        baseWorkflowUnit.BaseWorkflowUnit.__init__(self, GUI, unitID)

    ##################
    ### UNIT SPECS ###
    ##################
    def getContract(self):
        ins = []
        outs = [("csvDataTuple", list)]

        return {"ins": ins, "outs": outs}

    ###########
    ### RUN ###
    ###########
    def run(self, unitWorkFlowVarScope):
        csvSrc = self.getSetupValue("csvSrc", isRequired=True)

        if not csvSrc:
            self.logMessage("No csv files was choosen", CRITICAL_MSG)

        filesToLoad = []
        if type(csvSrc) == tuple:
            for f in csvSrc:
                if "csv" == f.split(".")[-1].lower():
                    filesToLoad.append(f)
        else:
            filesToLoad.append(csvSrc)

        loadedCSV = []
        currentHeader = None
        for f in filesToLoad:
            header, data = loadCSVtoListTuple(f)

            if not currentHeader:
                currentHeader = header
            elif currentHeader != header:
                self.logMessage(
                    "Different headers in the CSV files cannot merge!",
                    CRITICAL_MSG,
                )

            for row in data:
                loadedCSV.append(row)

        ### OUTPUT
        self.logMessage(
            "Loaded %s csv rows to memory." % str(len(loadedCSV)), STATUS_MSG
        )

        # Loaded CSV is returned as a list inside a list
        returnScope = {}
        returnScope["csvDataTuple"] = [currentHeader, loadedCSV]

        return returnScope
