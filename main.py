import csv
import argparse
import pymongo
import pandas as pd
import ffmpeg
import os
import sys
import openpyxl


baselight_Frames = []
baselight_LinesSplit = []
baselight_Locations = []
baselight_dict = {}
xytech_Locations = []
xytech_comparisonLocation = []
Location_Frames = []
xytech_location_dict = {}
xytech_location_listTuple = []

#Initilize argparse
parser = argparse.ArgumentParser()
parser.add_argument("--baselight", nargs="+", required=True)
parser.add_argument("--xytech", nargs="+", required=True)
parser.add_argument("--process", nargs="+")
parser.add_argument("--output", action="store_true")
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
                else:
                    frameBlock = f"{current[0]}-{current[-1]}"
                current = [frames[i]]
                Location_Frames.append((location, frameBlock))
    return Location_Frames

def seperateFrames(data):
    shots = []
    soloFrames = []
    for i in Sorted_frameRanges:
        if len(i[1].split("-")) == 1:
            soloFrames.append(i)
        else:
            shots.append(i)
    return (shots, soloFrames)


def time_conversion(frame):
    fps = 24
    frame = int(frame)
    hour = frame // (3600 * fps)
    frame %= (fps * 3600)
    minutes = frame // (fps * 60)
    frame %= (fps * 60)
    seconds = frame // fps
    frames = frame % fps
    result = f"{hour:02}:{minutes:02}:{seconds:02}:{frames:02}"
    return result

def getTimecode(targetVideo):
    info = ffmpeg.probe(targetVideo)
    duration = float(info['format']['duration'])
    return duration


def add_time(shotsList):
    result = []
    for i in range(len(shotsList)):
        targetRange = shots[i][1].split("-")
        result.append([shotsList[i][0], shotsList[i][1], f"{time_conversion(float(targetRange[0]))}-{time_conversion(float(targetRange[1]))}"])
    return result
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

#Compare Location and create the correct directory
frameDirectory = comparisonAlgorithm(baselight=baselightDict, xytech=xytechDict)
frameRanges = frameRanges(frameDirectory)

#Sort the data by Frames
Sorted_frameRanges = sorted(frameRanges, key=lambda x: int(x[1].split("-")[0]))

#Seperate solo-frames and frame-ranges
framesWithLocations = seperateFrames(Sorted_frameRanges)
shots = framesWithLocations[0] #Frame Ranges
soloShots = framesWithLocations[1] #Seperate Frames

if not args.output:
    with open('output.csv', "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(Sorted_frameRanges)

#Timecode/Main---------------------------------------------------------------------------
#to make sure the user has given process
if args.output and not args.process:
    print("ERROR: You must provice --process when giving --output")
    sys.exit(1)

elif args.output and args.process:
    videoTimecode = getTimecode(args.process[0])

    totalFrames = videoTimecode*24
    UNDESIRABLEandWORTHLESSshots = soloShots
    shotsInRange = []

    for i in range(len(shots)):
        targetRange = shots[i][1].split("-")
        if float(targetRange[0]) > totalFrames:
            UNDESIRABLEandWORTHLESSshots.append(shots[i])
        elif float(targetRange[0]) < totalFrames and float(targetRange[1]) > totalFrames:
            shotsInRange.append((shots[i][0], f"{targetRange[0]}-{round(totalFrames)}"))
        else:
            shotsInRange.append((shots[i]))

    shotsWithTime = add_time(shotsInRange)
    df = pd.DataFrame(shotsWithTime, columns=["Location", "Frame Ranges", "Timecode Ranges"])
    df.to_excel("output.xlsx", index=False)








#Create CSV file of the Solo-Frames
    with open('output.csv', "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(UNDESIRABLEandWORTHLESSshots)


    #TODO 1. Create TimeFrames for the code
    #TODO 2. Get the Thumbnails

