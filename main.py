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

#Initilize argparse
parser = argparse.ArgumentParser()
parser.add_argument("--baselight", required=True)
parser.add_argument("--xytech", required=True)
args = parser.parse_args()


#Initilize Database
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]
baselightCol = mydb["baselight"]
xytechCol = mydb["xytech"]

with open(args.baselight, "r") as baselight, open(args.xytech, "r") as xytech:
    #Imported the Files and and parsed them to seperate lines
    baselight_Lines = baselight.read().splitlines()
    xytech_Lines = xytech.read().splitlines()

    #Get all Frames from baselight
    for i in baselight_Lines:
        frames = i.split()
        if frames:
            baselight_Locations = frames.pop(0)
            if baselight_Locations in baselight_dict:
                baselight_dict[baselight_Locations].extend(frames)
            else:
                baselight_dict[baselight_Locations] = frames
            baselight_Frames.append(frames) #Frames from baselight acquired as baselight_Frames
    
    #Get all the locations from Xytech
    for i in xytech_Lines:
        if i.startswith("/"):
            xytech_Locations.append(i)

            modified_location = i
            modified_location = modified_location.split("/", 3)[3:] #possible optimization needed to remove bugs
            xytech_comparisonLocation.append((modified_location))
    
    #Compare the locations and create a dict with the correct location associated with the appropriate frames
    for location, frames in baselight_dict.items():
        for i in range(len(xytech_comparisonLocation)): #possible optimization needed
            if location.endswith(xytech_comparisonLocation[i][0]):
                if xytech_Locations[i] in final_dict:
                    final_dict[xytech_Locations[i]].extend(frames)
                else:
                    final_dict[xytech_Locations[i]] = frames #result final_dict
    
    #Create Frame Ranges and add them to a tupe associated with their location in a list, Location_Frames
    #Also create a soloFrames list aswell for singular frames (Location_Frames contains singular frames aswell)
    for location, frames in final_dict.items():
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

    #Sorting Algorithm Based On Frames for Location_Frames
    
    Sorted_Location_Frames = sorted(Location_Frames, key=lambda x: int(x[1].split("-")[0]))
    print(Sorted_Location_Frames)

    #Output Data to CSV
    with open('output.csv', "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(Sorted_Location_Frames)

