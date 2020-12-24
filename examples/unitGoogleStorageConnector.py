#!/usr/bin/python
#encoding=utf8
import baseWorkflowUnit
import os
import unicodeCSV

##OLD
import httplib2
import googleapiclient.discovery
import oauth2client.client
from googleapiclient.errors import HttpError as googleHttpError

##NEW doesnt work with py2exe
# import google.cloud.storage
# from google.cloud import storage
# from google.cloud.storage import Blob

from workFlowConstants import *


def create_service(ca_certs):
    # Get the application default credentials. When running locally, these are
    # available after running `gcloud init`. When running on compute
    # engine, these are available from the environment.
    credentials = oauth2client.client.GoogleCredentials.get_application_default()
    
    # Construct the service object for interacting with the Cloud Storage API -
    # the 'storage' service, at version 'v1'.
    # You can browse other available api services and versions here:
    #     http://g.co/dv/api-client-library/python/apis/
    
    http = httplib2.Http(ca_certs=ca_certs)
    return googleapiclient.discovery.build('storage', 'v1', http=http, credentials=credentials)

def writeListToCSV(csvFilePath, listData, header=None):
    fileObject = open(csvFilePath, "wb")
    
    writer = unicodeCSV.UnicodeWriter(fileObject)
    
    if header:
        listData.insert(0, header)
    
    writer.writerows(listData)
    
    fileObject.close()

class WorkflowUnit(baseWorkflowUnit.BaseWorkflowUnit):
    """This module is used for establishing a connection to the googledatastore
       and through this connections upload / remove binary files from the datastore

       operation <str>: options: "UPLOAD", "REMOVE\""""
    
    def __init__(self, GUI, unitID):
        baseWorkflowUnit.BaseWorkflowUnit.__init__(self, GUI, unitID)
        self.resourceDir = os.path.join(GUI.WORKFLOW_PATH, "resources", "googleUpload")
    
    ##################
    ### UNIT SPECS ###
    ##################
    def getContract(self):
        ins = [("uploadData", list)]
        outs = []
        
        return {"ins": ins, "outs":outs}
    
    ###########
    ### RUN ###
    ###########
    # def newUploadFile(self, client, bucket, filePath, unique_name, license, content_type):
    #     storageBucket = client.get_bucket(bucket)
    #     fileBlob = google.cloud.storage.Blob(unique_name, storageBucket)
    #     
    #     with open(filePath, 'rb') as aFile:
    #         fileBlob.upload_from_file(aFile, content_type=content_type, predefined_acl="publicRead")
    #     
    #     fileBlob.metadata = {"license" : license}
    #     fileBlob.cache_control = "public, max-age=3600"
    #     fileBlob.content_language = 'en'
    #     fileBlob.update()
    
    def uploadFile(self, service, bucket, filePath, filename, license):
        retries = 3
        
        while retries > 0:
            try:
                # This is the request body as specified:
                # http://g.co/cloud/storage/docs/json_api/v1/objects/insert#request
                body = {
                    'name': filename,
                    'metadata': {"license" : license},
                    'contentLanguage': "en",
                    'cacheControl': "public, max-age=3600"
                }
                # Now insert them into the specified bucket as a media insertion.
                # http://g.co/dv/resources/api-libraries/documentation/storage/v1/python/latest/storage_v1.objects.html#insert
                req = service.objects().insert(bucket=bucket, body=body, predefinedAcl="publicRead", media_body=filePath)
                resp = req.execute()
                
                return
            except googleHttpError as err:
                retries = retries - 1
                
                if retries == 0:
                    self.logMessage(unicode(err), CRITICAL_MSG)
                else:
                    self.logMessage(unicode(err), STATUS_MSG)
            except oauth2client.client.ApplicationDefaultCredentialsError as err:
                self.logMessage(unicode(err), CRITICAL_MSG)
                return
    
    def run(self, unitWorkFlowVarScope):
        destFile = self.getSetupValue("csvDest")
        
        operation = self.getSetupValue("operation", isRequired=True)
        googleCredentials = self.getSetupValue("google_credentials", isRequired=True)
        
        googleCredentialsPath = os.path.join(self.resourceDir, googleCredentials)
        if not os.path.isfile(googleCredentialsPath):
            self.logMessage("missing google service account json file %s" % googleCredentialsPath, CRITICAL_MSG)
        else:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = googleCredentialsPath
        
        isABatchJob = self.getSetupValue("is_a_batch_job")
        
        if not isABatchJob:
            if operation == "UPLOAD":
                if not destFile:
                    self.logMessage("no valid csv save file have been choosen", CRITICAL_MSG)
                
                uploadData = unitWorkFlowVarScope.get("uploadData")
                nrOfRecords, data = uploadData
                 
                skipUpload = -1 ## used for crashed big uploads
                progress = 0
                uploaded = {}
                activeItem = []
                
                service = create_service(os.path.join(self.resourceDir, "cacerts.txt"))
                # storageClient = google.cloud.storage.Client()
                for item in data:
                    if len(item) == 2:
                        activeItem = item
                        if progress != 0:
                            self.logMessage("DONE %s-%s" % (progress, nrOfRecords), STATUS_MSG)
                            self.logMessage("%s" % (activeItem[0]), STATUS_MSG)
                        
                        progress = progress + 1
                    else:
                        bucket, unique_name, license, filePath = item
                        
                        if os.path.isfile(filePath):
                            identifier = activeItem[0]
                            recordType = activeItem[1]
                            
                            fileSig = unique_name[10]
                            curDict = uploaded.get(identifier, {"oasid":identifier, "record_type": recordType})
                            
                            if recordType == "image":
                                if skipUpload < progress:
                                    contentType = 'image/jpeg'
                                    # self.newUploadFile(storageClient, bucket, filePath, unique_name, license, contentType)
                                    
                                    self.uploadFile(service, bucket, filePath, unique_name, license)
                                    self.logMessage("uploaded: %s" % unique_name, STATUS_MSG)
                                
                                if fileSig == "s":
                                    curDict["thumbnail"] = 'https://storage.googleapis.com/%s/%s' % (bucket, unique_name)
                                elif fileSig == "m":
                                    curDict["record_image"] = 'https://storage.googleapis.com/%s/%s' % (bucket, unique_name)
                                elif fileSig == "l":
                                    curDict["large_image"] = 'https://storage.googleapis.com/%s/%s' % (bucket, unique_name)
                                
                                uploaded[identifier] = curDict    
                            elif recordType == "web_document":
                                if skipUpload < progress:
                                    if filePath.rsplit(".", 1)[-1] == "jpg":
                                        contentType = 'image/jpeg'
                                    else:
                                        contentType = 'application/pdf'
                                    
                                    # self.newUploadFile(storageClient, bucket, filePath, unique_name, license, contentType)
                                    
                                    self.uploadFile(service, bucket, filePath,unique_name, license)
                                    self.logMessage("uploaded: %s" % unique_name, STATUS_MSG)
                                
                                if fileSig == "s":
                                    curDict["thumbnail"] = 'https://storage.googleapis.com/%s/%s' % (bucket, unique_name)
                                elif fileSig == "m":
                                    curDict["record_image"] = 'https://storage.googleapis.com/%s/%s' % (bucket, unique_name)
                                elif fileSig == "l":
                                    curDict["large_image"] = 'https://storage.googleapis.com/%s/%s' % (bucket, unique_name)
                                elif fileSig == "c":
                                    curDict["web_document_url"] = 'https://storage.googleapis.com/%s/%s' % (bucket, unique_name)
                                
                                uploaded[identifier] = curDict
                            else:
                                self.logMessage("record %s with record_type %s is not supported" % (identifier, recordType), WARNING_MSG)
                
                if activeItem:
                    self.logMessage("DONE %s-%s" % (progress, nrOfRecords), STATUS_MSG)
                
                #write csv file
                newData = []
                writeHeader = ["oasid","thumbnail","record_image","record_type","large_image","web_document_url"]
                for key, valueDict in sorted(uploaded.items(), key=lambda e: e[0]):
                    newRow = []  
                    for hCol in writeHeader:
                        hVal = valueDict.get(hCol, "")
                        newRow.append(hVal)
                    
                    newData.append(newRow)
                    
                writeListToCSV(destFile, newData, writeHeader)
        else:
            pass
    #     if isABatchJob:
    #         globalMetaConfig = self.configGetAndValidate(config, "global_meta_config", 1)
    #         fileFolderPath = self.configGetAndValidate(config, "file_folder_path", 1)
    #         googleBucket = self.configGetAndValidate(config, "google_bucket", 1)
    #         
    #         progress = 0
    #         nrOfRecords = 0
    #         for f in os.listdir(fileFolderPath):
    #             if f == "Thumbs.db":
    #                 continue
    #             
    #             nrOfRecords = nrOfRecords + 1
    #         
    #         for f in os.listdir(fileFolderPath):
    #             if f == "Thumbs.db":
    #                 continue
    #             
    #             filePath = os.path.join(fileFolderPath, f)
    #             unique_name = f
    #             license = globalMetaConfig.get("license")
    #             if not license:
    #                 self.logMessage("no license specified update config yaml!", CRITICAL_MSG)
    #                 
    #             self.uploadFile(googleBucket, filePath, unique_name, license)
    #             
    #             progress = progress + 1
    #             self.logMessage("%s, DONE %s-%s" % (f, progress, nrOfRecords), STATUS_MSG)
        

        
    # #     # elif operation == "REMOVE":
    # #     #     header, data = self.uploadData
    # #     #     
    # #     #     allowedFormat = ["bucket", "unique_name"]
    # #     #     
    # #     #     if header == allowedFormat:
    # #     #         for row in data:
    # #     #             bucket, unique_name = row
    # #     #             
    # #     #             bucketPath = '%s/%s' % (bucket, unique_name)
    # #     #             self.removeFile(bucketPath)
    # #     #             self.logMessage("%s, DONE" % bucketPath, STATUS_MSG)
    # #     #     else:
    # #     #         self.logMessage("CSV file does not have the correct header must have the %s" % allowedFormat, CRITICAL_MSG)
    # #     # else:
    # #     #     self.logMessage("ERROR: operation is not a valid option - %s" % operation, CRITICAL_MSG)
    # 
    
    
    # def removeFile(self, bucketPath):
    #     raise ValueError("NOT SUPPORTED")
    #     