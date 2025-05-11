import csv

baselightFrames = []
baselightLinesSplit = []

with open("Baselight_export_spring2025.txt", "r") as baselight, open("Xytech_spring2025.txt", "r") as xytech:
    #Imported the Files and and parsed them to seperate lines
    baselightLines = baselight.read().splitlines()
    xytechLines = xytech.read().splitlines()

    #Get all Frames from baselight
    for i in baselightLines:
        frames = i.split()
        if frames:
            frames.pop(0)
            baselightFrames.append(frames)
    print(f"{baselightFrames}")

