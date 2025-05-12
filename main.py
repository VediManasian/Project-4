import csv
import argparse
import pymongo
import pandas as pd


baselight_Frames = []
baselight_LinesSplit = []
baselight_Locations = []
baselight_dict = {}
xytech_Locations = []
xytech_comparisonLocation = []
final_dict = {}
soloFrames = []
Location_Frames = []
xytech_location_dict = {}
xytech_location_listTuple = []

#Initilize argparse
parser = argparse.ArgumentParser()
parser.add_argument("--baselight", nargs="+", required=True)
parser.add_argument("--xytech", nargs="+", required=True)
args = parser.parse_args()


#Initilize Database
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]

baselightCol = mydb["baselight"]
xytechCol = mydb["xytech"]
baselightCol.drop()
xytechCol.drop()



def loadBaselight(data):
    data_dict = {}
    tempData = data
    dataLines = tempData.read().splitlines()
    for i in dataLines:
        frames = i.split()
        if frames:
            directory = frames.pop(0)
            if directory in data_dict:
                data_dict[directory].extend(frames)
            else:
                data_dict[directory] = frames
    return data_dict

def loadXytech(data):
    directory = []
    data_dict = {}
    tempData = data
    dataLines = tempData.read().splitlines()
    for i in dataLines:
        if "workorder" in i.lower():
            workorderNumber = i.lower().split("workorder")[1].strip()
        elif i.startswith("/"):
            directory.append(i)
    if workorderNumber in data_dict:
        data_dict[workorderNumber].extend(directory)
    else:
        data_dict[workorderNumber] = directory
    return data_dict

def comparisonAlgorithm(baselight, xytech):
    Dict = {}
    for location, frames in baselight.items():
        modifiedLocation = location.split("/", 2)[2:]
        for workorder, directories in xytech.items():
            for i in directories:
                if i.endswith(modifiedLocation[0]):
                    if i in Dict:
                        Dict[i].extend(frames)
                    else:
                        Dict[i] = frames
    return Dict

def frameRanges(data):
    for location, frames in data.items():
        current = [frames[0]]
        for i in range(1, len(frames)):
            if (int(frames[i]) - 1) == int(frames[i - 1]):
                current.append(frames[i])
            else:
                if len(current) == 1:
                    frameBlock = current[0]
                    soloFrames.append((location, frameBlock))
                else:
                    frameBlock = f"{current[0]}-{current[-1]}"
                current = [frames[i]]
                Location_Frames.append((location, frameBlock))
    return (Location_Frames, soloFrames)
#Main-------------------------------------------------------------------------------

    #Loads baselight into DB
for baselight_file in args.baselight:
    with open(baselight_file, "r") as baselight:
        tempBaselightDict = loadBaselight(baselight)
        document = [{"shot": s, "frames": f} for s, f in tempBaselightDict.items()]
        baselightCol.insert_many(document)
    #Loads xytech into DB
for xytech_file in args.xytech:
    with open(xytech_file, "r") as xytech:
        tempXytechDict = loadXytech(xytech)
        document = [{"workorder": w, "directories": d} for w, d in tempXytechDict.items()]
        xytechCol.insert_many(document)

# Extracts the Data from baselight collection
baselightDict = {doc["shot"]: doc["frames"] for doc in baselightCol.find()}
# Extracts the Data from xytech collection
xytechDict = {doc["workorder"]: doc["directories"] for doc in xytechCol.find()}

frameDirectory = comparisonAlgorithm(baselight=baselightDict, xytech=xytechDict)

frameRanges = frameRanges(frameDirectory)
frameRangesWithLocation = frameRanges[0]
soloFrames = frameRanges[1]

Sorted_frameRanges = sorted(frameRangesWithLocation, key=lambda x: int(x[1].split("-")[0]))

with open('output.csv', "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(Sorted_frameRanges)

