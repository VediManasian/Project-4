import csv

baselight_Frames = []
baselight_LinesSplit = []
baselight_Locations = []
baselight_dict = {}
xytech_Locations = []
xytech_comparisonLocation = []
final_dict = {}

with open("baselight_export_spring2025.txt", "r") as baselight, open("xytech_spring2025.txt", "r") as xytech:
    #Imported the Files and and parsed them to seperate lines
    baselight_Lines = baselight.read().splitlines()
    xytech_Lines = xytech.read().splitlines()

    #Get all Frames from baselight
    for i in baselight_Lines:
        frames = i.split()
        if frames:
            baselight_Locations = frames.pop(0)
            baselight_dict[baselight_Locations].extend(frames)
            baselight_Frames.append(frames) #Frames from baselight acquired as baselight_Frames
    
    #Get all the locations from Xytech
    for i in xytech_Lines:
        if i.startswith("/"):
            xytech_Locations.append(i)

            modified_location = i
            modified_location = modified_location.split("/", 3)[3:]
            xytech_comparisonLocation.append((modified_location))
    
    for location, frames in baselight_dict.items():
        for i in range(len(xytech_comparisonLocation)):
            if location.endswith(xytech_comparisonLocation[i][0]):
                final_dict[xytech_Locations[i]] = frames
print(baselight_dict)
    
    
