##encoding=utf8
import baseWorkflowUnit
import PIL.Image as Image

import os
import subprocess
import json
from workFlowConstants import *

class WorkflowUnit(baseWorkflowUnit.BaseWorkflowUnit):
    """Using imagemagick application to convert most image types as well as frontpages of pdf to online access versions
    
    dependencies:
    pillow
    """
    
    def __init__(self, GUI, unitID):
        baseWorkflowUnit.BaseWorkflowUnit.__init__(self, GUI, unitID)
        
        self.convertionTypes = {"tif" : ["SMALL", "MEDIUM", "LARGE"],
                                "jpg" : ["SMALL", "MEDIUM", "LARGE"],
                                "jpeg" : ["SMALL", "MEDIUM", "LARGE"],
                                "bmp" : ["SMALL", "MEDIUM", "LARGE"],
                                "pdf" : ["SMALL", "MEDIUM"]}
    
    ##################
    ### UNIT SPECS ###
    ##################
    def getContract(self):
        ins = [("loadedCSVs", list)]
        outs = []
        
        return {"ins": ins, "outs":outs}
    
    ###########
    ### RUN ###
    ###########
    def run(self, unitWorkFlowVarScope):
        loadedCsvSrc = unitWorkFlowVarScope.get("loadedCSVs")
        header, data = loadedCsvSrc
        nrOfRows = len(data)
        
        overwriteBoolean = self.getSetupValue("overwrite")
        
        convertType = self.getSetupValue("convert_type", isRequired=True)
        takeFromAccess = self.getSetupValue("take_from_access", isRequired=True)
        
        includeWatermark = self.getSetupValue("include_watermark")
        self.icon_white = self.getSetupValue("watermark_white")
        self.icon_black = self.getSetupValue("watermark_black")
        
        ##Convertion Standards
        self.webFormat = self.getSetupValue("webFormat", isRequired=True)
        self.largeThreshold = self.getSetupValue("largeThreshold", isRequired=True)
        self.mediumThreshold = self.getSetupValue("mediumThreshold", isRequired=True)
        self.smallThreshold = self.getSetupValue("smallThreshold", isRequired=True)
        
        ##Folders and directories
        archiveFolder = self.getSetupValue("archive_folder", isRequired=True)
        accessFolder = self.getSetupValue("access_folder", isRequired=True)
        self.largePathDir = self.getSetupValue("largePathDir", isRequired=True)
        self.mediumPathDir = self.getSetupValue("mediumPathDir", isRequired=True)
        self.smallPathDir = self.getSetupValue("smallPathDir", isRequired=True)
        
        self.imageMagickFolder = self.getSetupValue("imageMagick_folder", isRequired=True)
        self.imageMagickBinary = self.getSetupValue("imageMagick_binary", isRequired=True)
        
        programPath = os.path.join(self.imageMagickFolder, self.imageMagickBinary)
        if not os.path.isfile(programPath):
            self.logMessage("Missing imagemagick binary used for convertion!, %s not found..." % (programPath), CRITICAL_MSG)
        
        if convertType == "PDF":
            self.ghostScriptFolder = self.getSetupValue("ghostScript_folder", isRequired=True)
            self.ghostScriptBinary = self.getSetupValue("ghostScript_binary", isRequired=True)
            
            programPath = os.path.join(self.ghostScriptFolder, self.ghostScriptBinary)
            if not os.path.isfile(programPath):
                self.logMessage("Missing ghostscript binary used for convertion!, %s not found..." % (programPath), CRITICAL_MSG)
        
        oasIDCol = self.getSetupValue("oasid_col", isRequired=True)
        colDictColName = self.getSetupValue("oas_dict_col", isRequired=True)
        filenameKey = self.getSetupValue("filename_key", isRequired=True)
        
        try:
            oasIDIndex = header.index(oasIDCol)
        except ValueError:
            self.logMessage('CSV header: "%s", does not contain the YAML specified column "%s" used in key:oasid_col' % (header, oasIDCol), CRITICAL_MSG)
        
        try:
            colDictIndex = header.index(colDictColName)
        except ValueError:
            self.logMessage('CSV header: "%s", does not contain the YAML specified column "%s" used in key:oas_dict_key_filename' % (header, colDictColName), CRITICAL_MSG)
        
        ## CONVERT PICTURES
        self.logMessage("Starting Process", STATUS_MSG)
        
        for i, row in enumerate(data):
            oasID = row[oasIDIndex]
            self.logMessage("%s-%s: %s" % (i + 1,nrOfRows, oasID), STATUS_MSG)
            
            rowDict = json.loads(row[colDictIndex])

            # Added by CJK on 2020-06-15. Skip image-generation if restricted by GDPR 
            legal_restrictions = rowDict.get("other_legal_restrictions")
            if legal_restrictions and int(legal_restrictions["id"]) > 1:
                self.logMessage("-Skipped: file restricted by privacy-settings", STATUS_MSG)
                continue
 
            if not takeFromAccess:
                filename = rowDict.get(filenameKey)
                if not filename:
                     self.logMessage("-Done Skipped no filename", STATUS_MSG) 
                     continue
                
                fullFileName = os.path.join(archiveFolder, filename)
            else:
                if convertType == "PDF":
                    accessFileName = oasID + "_c.pdf"
                    fullFileName = os.path.join(accessFolder, accessFileName)
                    if not os.path.isfile(fullFileName):
                        self.logMessage("-Done Skipped no access PDF", STATUS_MSG)
                        continue
                else: # convertType == "IMAGE"
                    accessFileName = oasID + "_c.jpg"
                    fullFileName = os.path.join(accessFolder, accessFileName)
                    if not os.path.isfile(fullFileName):
                        self.logMessage("-Done Skipped no access JPG", STATUS_MSG)
                        continue
            
            fileType = fullFileName.rsplit(".")[-1].lower()
            if not os.path.isfile(fullFileName):
                self.logMessage("%s - No binary file pressent with path: %s" % (oasID, fullFileName), WARNING_MSG)
                continue
            
            convertionList = self.convertionTypes.get(fileType)
            if len(convertionList) == 0:
                self.logMessage("-Skipped: file type is not handled by this module", STATUS_MSG)
                continue
            
            distFilenameLarge = os.path.join(self.largePathDir, ".".join(("%s_l" % oasID, self.webFormat)))
            distFilenameMedium = os.path.join(self.mediumPathDir, ".".join(("%s_m" % oasID, self.webFormat)))
            distFilenameSmall = os.path.join(self.smallPathDir, ".".join(("%s_s" % oasID, self.webFormat)))
            
            allowToSkip = True
            if overwriteBoolean:
                allowToSkip = False
            elif "LARGE" in convertionList and not os.path.isfile(distFilenameLarge):
                allowToSkip = False
            elif "MEDIUM" in convertionList and not os.path.isfile(distFilenameMedium):
                allowToSkip = False
            elif "SMALL" in convertionList and not os.path.isfile(distFilenameSmall):
                allowToSkip = False
            
            if allowToSkip:
                self.logMessage("-Skipped: file already has binary access versions", STATUS_MSG)
                continue
            
            if convertType == "IMAGE":
                self.logMessage("-Image", STATUS_MSG)
                
                pixelSize = self.getImagePixelSize(fullFileName)
                self.logMessage("-size: " + unicode(pixelSize), STATUS_MSG)
                
                if fileType == "tif":
                    fullFileName = fullFileName + "[0]" ##fix to not make multi images out of multi layered tif
            else: #convertType == "PDF"
                self.logMessage("-Pdf", STATUS_MSG)
                formatConvert = "tif"
                
                tempFilePath = self.GUI.WORKFLOW_PATH + os.path.sep + "temp." + formatConvert
                
                ### extract the first page of the pdf and save to a temperary file
                self.pdfBaseConvert(fullFileName, tempFilePath)
                
                pixelSize = self.getImagePixelSize(tempFilePath)
                self.logMessage("-size: " + unicode(pixelSize), STATUS_MSG)
                fullFileName = tempFilePath
            
            ##Convertion flow
            if "LARGE" in convertionList:
                self.imgtjpg(fullFileName, distFilenameLarge, pixelSize, self.largeThreshold)
                self.logMessage("-Large Done!", STATUS_MSG)
                
                if includeWatermark:
                    self.addWaterMark(distFilenameLarge, distFilenameLarge)
                
            if "MEDIUM" in convertionList:
                self.imgtjpg(fullFileName, distFilenameMedium, pixelSize, self.mediumThreshold)
                self.logMessage("-Medium Done!", STATUS_MSG)
                
                if includeWatermark:
                    self.addWaterMark(distFilenameMedium, distFilenameMedium)
                
            if "SMALL" in convertionList:
                self.imgtjpg(fullFileName, distFilenameSmall, pixelSize, self.smallThreshold)
                self.logMessage("-Small Done!", STATUS_MSG)
            
            if convertType == "PDF":
                os.remove(tempFilePath)
    
    def addWaterMark(self, fp, tp):
        im = Image.open(fp)
        bw = im.convert('L')
        
        defaultIcon = Image.open(self.icon_white)
        
        iconXSize, iconYSize = defaultIcon.size
        
        del defaultIcon
        
        width, height = im.size
        if width > 640:
            rotate = False
        elif width >= iconXSize:
            rotate = False
        elif width >= iconYSize:
            if height >= iconXSize:
                temp = iconXSize
                
                iconXSize = iconYSize
                iconYSize = temp
                rotate = True
            else:
                self.logMessage("too small to add a watermark", STATUS_MSG)
                return
        else:
            self.logMessage("too small to add a watermark", STATUS_MSG)
            return
        
        anchorX = width - iconXSize
        anchorY = height - iconYSize
    
        nrOfPixels = iconXSize * iconYSize
        sumPixel = 0
        for x in xrange(anchorX, anchorX + iconXSize):
            for y in xrange(anchorY, anchorY + iconYSize):
                sumPixel = sumPixel + bw.getpixel((x,y))
        
        averagePixel = sumPixel / nrOfPixels
    
        if averagePixel < 128:
            #its more blackish
            waterIcon = Image.open(self.icon_white)
        else:
            #its more whitish
            waterIcon = Image.open(self.icon_black)
        
        waterIcon = waterIcon.convert("RGBA")
            
        if rotate:
            waterIcon = waterIcon.rotate(90, expand=True)
            
        im.paste(waterIcon, (anchorX, anchorY), waterIcon)        
        im.save(tp)
    
    def getImagePixelSize(self, srcFileName):
        try:
            programPath = os.path.join(self.imageMagickFolder, self.imageMagickBinary)
            
            argList = [programPath, srcFileName]
            argList.extend(["-ping", "-format", '%w#%h', "info:"])
            
            
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            p = subprocess.Popen(argList, startupinfo=startupinfo, stdout=subprocess.PIPE)
            stdOut = p.communicate()[0]
            
            return map(lambda e: int(e), stdOut.split("#"))
        except ValueError as err:
            return [4000, 4000]
    
    def pdfBaseConvert(self, srcFileName, distFilename):
        programPath = os.path.join(self.ghostScriptFolder, self.ghostScriptBinary)
        
        ghostScriptArgs = ["-sDEVICE=tiff48nc",
                           "-dNOPAUSE",
                           "-dBATCH",
                           "-dQUIET",
                           "-sOutputFile=%s" % distFilename,
                           "-dFirstPage=1",
                           "-dLastPage=1",
                           "-dTextAlphaBits=4",
                           "-r300x300"]
        
        argList = [programPath]
        argList.extend(ghostScriptArgs)
        argList.append(srcFileName)
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        p = subprocess.Popen(argList, startupinfo=startupinfo)
        
        #Wait for finish
        self.logMessage("-Extracting Page", STATUS_MSG)
        p.communicate()
    
    def imgtjpg(self, srcFile, distFile, curSize, wantedSize):
        programPath = os.path.join(self.imageMagickFolder, self.imageMagickBinary)
        
        maxSize = max(curSize)
        if maxSize > wantedSize:
            imgSize = "%sx%s" % (wantedSize, wantedSize)
        else:
            imgSize = "%sx%s" % (maxSize, maxSize)
        
        argList = [programPath, srcFile]
        
        argList.extend(["-resize", imgSize])
        argList.append(distFile)
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        p = subprocess.Popen(argList, startupinfo=startupinfo)
        p.communicate()