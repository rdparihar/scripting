"""
   This script extraxts Snapshot deployemnt status from UC for a given release

   - Data extracted for each release (fixversion) from Urbancode
   - The status of latest snapshot in each application is written in two output files
   - Package file has all the  latest snapshots
   - Deployment file has the status of depoyment in SDLC & PROD environments
   - This script can be used to extract data for any report gtoup (Engineering, Salesforce etc.)

   - **********************************************************************************
   - Modification History
   - Date        Developer    Purpose
   - ----------------------------------------------------------------------------------
   - 01/15/2020  Rajdeep  New script created 
   - 02/10/2020  Seth     Modified for multiple report groups

"""
 
# --- Import Python modules
import os
import sys
import json
import getpass
import re
import datetime

from time import gmtime, strftime
from requests.auth import HTTPBasicAuth
from collections import defaultdict

# --- Import release engineering modules
import reCommon
import ucCommon
import reMessage
import reProperty

gTaskID = "EXTRACT_SNAPSHOT"
gOutputPrefix = "Extract_UC_deployment"       # Output file name prefix
gFailMsg = "***Release calender data conversion failed with errors***"
gSuccessMsg = "***Release calender data exported to JSON successfully***"

# --- Declearation of the keys for dict 
gReportGroup = "report_group"
gRelFixVer = "fix_version"
gAppName = "aplication_name"
gPackageName = "package_name"
gEnvironmentName = "environment_name"
gEnvironmentType = "environment_type"
gDeploymentTime = "deployment_time"
gDeploymentStatus = "deployment_status"

# Report group names
gReportGroupENG = "ENG"          # Engineering Report
gReportGroupSFDC = "SFDC"        # Salesforece Report

# Valid Report groups Engineering / Sales Force 
gReportGroups = [gReportGroupENG, gReportGroupSFDC]

gKeyApplication = "application"
gKeyEnvironment = "environment"

gGroupProperty = {
  gReportGroupENG: {
    gKeyApplication: ["PassPort", "Micro Services"],
    gKeyEnvironment: {"val01br": "VAL", "stg01br": "STAGER", "prd01au" : "PROD"}   # env name: env type

  },
  gReportGroupSFDC: {  # Not ready
  }
}

# Output file names
gFilePackage = "jira_package.json"
gFileDeployment = "jira_deployment.json"

# Output data
gPackageData = []
gDeploymentData = []

# UC Urls
gUCUrlApp = "cli/application/environmentsInApplication?application={0}&maxResults=1000"
gUCUrlSnapshot = "cli/application/snapshotsInApplication?application={0}&maxResults=1000"
gUCUrlSnapshotID = "cli/snapshot/getSnapshot?application={0}&snapshot={1}"
gUCUrlDeployment1 = "rest/deploy/applicationProcessRequest/table?orderField=calendarEntry.scheduledDate"
gUCUrlDeployment2 = "&sortType=desc&filterFields=environment.id&filterFields=snapshot.id&filterValue_environment.id={0}"
gUCUrlDeployment3 = "&filterType_environment.id=eq&filterClass_environment.id=UUID&filterValue_snapshot.id={1}"
gUCUrlDeployment4 = "&filterType_snapshot.id=eq&filterClass_snapshot.id=UUID&outputType=BASIC&outputType=LINKED"

def validateCmdParam(argv, webEnv, logFp):
   """
   Collect input param and validate

   Arguments:
      argv   - Command line param
      webEnv -  True: UI, False: command line
      logFp  -  Log file handler
   """

   global gCmdParam

   allParam, gCmdParam = reCommon.getCmdParam(argv, gTaskID, logFp, webEnv)

   # Default report group is Engineering
   if gCmdParam.get('reportGroup') is None:   
      gCmdParam["reportGroup"] = gReportGroupENG
   
   if gCmdParam["reportGroup"] not in gReportGroups:
      msg = "Report group not in " + str(gReportGroups)
      raise(reMessage.ReException(logFp, "E108", msg))

   reCommon.writeCmdParamLog(allParam, gCmdParam, logFp)

def extractUCData(webEnv, logFp, fpPackage, fpDeployment):

  reportGroup = gCmdParam["reportGroup"] 
  allApplications = gGroupProperty[reportGroup][gKeyApplication]   # Valid applications for current group
  allEnvironments = gGroupProperty[reportGroup][gKeyEnvironment]   # Valid env name: env type

  for app in allApplications:
    appEnvironments = getEnvironmentsInApp(logFp, app, allEnvironments)
    latestSnapshots = getLatestSnapshots(logFp, app)

    for snapshot in latestSnapshots:
      getDeploymentStatus(appEnvironments, app, snapshot, logFp)

  writeOutput(logFp, fpPackage, fpDeployment)

def writeOutput(logFp, fpPackage, fpDeployment):

  output = {}
  output['data'] = gPackageData
  json.dump(output, fpPackage, indent=2)
  fpPackage.close()

  output = {}
  output['data'] = gDeploymentData
  json.dump(output, fpDeployment, indent=2)
  fpDeployment.close()

def getDeploymentStatus(appEnvironments, app, snapshot, logFp):

  reportGroup = gCmdParam["reportGroup"]
  fixVersion = gCmdParam["fixVersion"]
  snapshotID = getSnapshotId(logFp,snapshot,app)
  urlDeployment = gUCUrlDeployment1  + gUCUrlDeployment2 + gUCUrlDeployment3 + gUCUrlDeployment4

  # Write package output
  output = {}
  output[gReportGroup] = reportGroup
  output[gRelFixVer] = fixVersion
  output[gAppName] = app
  output[gPackageName] = snapshot
  gPackageData.append(output)

  # Collect deployment status in each SDLC & PROD environments
  for envName, envID in appEnvironments.items():
    output = {}
    output[gReportGroup] = reportGroup
    output[gRelFixVer] = fixVersion
    output[gAppName] = app
    output[gPackageName] = snapshot
    output[gEnvironmentName] = envName
    output[gEnvironmentType] = gGroupProperty[reportGroup][gKeyEnvironment][envName]
    output[gDeploymentStatus] = "Not Deployed"
    output[gDeploymentTime] = ""

    urlData = urlDeployment.format(envID, snapshotID)
    status, data, msg = ucCommon.getSnapshotData(gCmdParam["user"], gCmdParam["password"], urlData, logFp)
    if status == 200:   
      for statusData in data:
        s = statusData["endTime"] / 1000.0
        output[gDeploymentTime] = datetime.datetime.fromtimestamp(s).strftime('%Y/%m/%d %H:%M')
        output[gDeploymentStatus] = statusData["result"]
        break

    # Write deployment output
    gDeploymentData.append(output)  

def getEnvironmentsInApp(logFp, appName, allEnvironments): 

  envDict = {}  # Env name: Env ID
  urlData = gUCUrlApp.format(appName)
  status, data, msg = ucCommon.getSnapshotData(gCmdParam["user"], gCmdParam["password"], urlData, logFp)

  if status != 200:   # Status will alway be HTTP:200 it should be even of 0:[] records returned 
    return envDict

  for ucEnv in data:
    for env in allEnvironments:
      if env == ucEnv["name"]:
         envDict[ucEnv["name"]] = ucEnv["id"]   # {"prd01au": 'acf7b558-d9a6-4d79-bd4c-1f0e6d16848f'} 
         break

  return envDict

def getLatestSnapshots(logFp, appName):

  allSnapshots = {}    # Key: snapshot name without version, value: all snapshot names with version
  snapshotsMapping = {}  # Key: zreo filled version name, value: original snapshot name
  latestSnapshots = [] # Unique snapshots with max version

  if gCmdParam["reportGroup"] == gReportGroupENG:          # Engineering 
    snapshotPattern = re.compile("Release-" + gCmdParam["fixVersion"])
  else:
    snapshotPattern = "Not Ready"

  urlData = gUCUrlSnapshot.format(appName)
  status, data, msg = ucCommon.getSnapshotData(gCmdParam["user"], gCmdParam["password"], urlData, logFp)

  if status != 200:   # Status will alway be HTTP:200 it should be even of 0:[] records returned 
    return latestSnapshots

  for snapshot in data:
    snapshotName = snapshot["name"]
    if not snapshotPattern.match(snapshotName):  # Skip snapshots not for current version
       continue

    snapshotWithoutVersion = ""
    snapshotZeroFilledVersion = ""

    snapshotParts = snapshotName.split(".")
    if snapshotParts[-1] < "1" or snapshotParts[-1] > "99":  # No version number in snapshot
      snapshotWithoutVersion = snapshotName
      snapshotZeroFilledVersion = snapshotName + "00"
    else:
      snapshotWithoutVersion = ".".join(snapshotParts[:-1])
      snapshotZeroFilledVersion = ".".join(snapshotParts[:-1]) + snapshotParts[-1].zfill(2)

    # Snapshot name without version is the dictionary key
    if snapshotWithoutVersion not in allSnapshots:
      allSnapshots[snapshotWithoutVersion] = []  # First time store in the dictionary

    # All snapshots with version number are stord as values in the dictionary
    allSnapshots[snapshotWithoutVersion].append(snapshotZeroFilledVersion)

    # Map snapshot name with zero filled version name
    snapshotsMapping[snapshotZeroFilledVersion] = snapshotName

  # Collect unique snapshots with max version number and replace with original name
  for key, snapshotZeroFilledName in allSnapshots.items():
    latestSnapshots.append(snapshotsMapping[max(snapshotZeroFilledName)])

  return latestSnapshots

def getSnapshotId(logFp,snapshot,app):
    snapshotID = ""
    urlData = gUCUrlSnapshotID.format(app, snapshot)
    status, ucSnpshotData, msg = ucCommon.getSnapshotData(gCmdParam["user"], gCmdParam["password"], urlData, logFp)
    if status == 200:                                    
       snapshotID = ucSnpshotData['id']

    return snapshotID

def main(argv, webEnv=False):
   """
   Main function to extract snapshot status from UrbanCode

   Arguments:
      argv   - Command lime param when the script runs from command line
             - Input from UI when called by Django

      webEnv - False when the script runs from command line
             - True  when called by Django
   """
   
   logFp = None
   context = {}

   try:
      curUser = getpass.getuser()
      context = reCommon.initContext()
      logFp, context["logFile"] = reCommon.createLogFile(webEnv, gOutputPrefix, curUser)
      validateCmdParam(argv, webEnv, logFp)	# Input param validation / default values

      # Create package file
      fileType = "Package"
      removeFile = True
      fpPackage, fileNameFull, output = reCommon.createOutFile(fileType, gFilePackage, removeFile, logFp)
      if webEnv:           # Return output file name if processing from UI
         context["output"].append(output)
      
      # Create deployment file
      fileType = "Deployment"
      removeFile = True
      fpDeployment, fileNameFull, output = reCommon.createOutFile(fileType, gFileDeployment, removeFile, logFp)
      if webEnv:           # Return output file name if processing from UI
         context["output"].append(output)
      
      extractUCData(webEnv, logFp, fpPackage, fpDeployment)
      return reCommon.processSuccess(gSuccessMsg, logFp, context, webEnv)   

   except reMessage.ReException as e:
      return reCommon.processFailure(e, webEnv, gFailMsg, logFp, context)   

   #except Exception as e:           # Unknown exceptions which are not captured 
   #   tmpMsg = str(type(e).__name__) + " : " + str(e.args)
   #   o = reMessage.ReException(logFp, "E199", tmpMsg)
   #   return reCommon.processFailure(o, webEnv, gFailMsg, logFp, context)   

# --- Call the main function only when run from the command line 
# --- Django will make a call with param collected from the UI
if __name__ == "__main__":
   main(sys.argv)
