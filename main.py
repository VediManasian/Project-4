import csv
import argparse
import pymongo
import pandas as pd
import ffmpeg
import sys
import vimeo
import time



Location_Frames = []
allThumbnails = []
counter = 0

client = vimeo.VimeoClient(
    token='aeee7531eb1e85b514dc98d5fd9fdfd3',
    key='8d86ddad50b80b3cfb123f51a25584f345e47591',
    secret='HypJhnww9mRZ0TfBa8JzLLhdi12rI6fLtV8eSaatIq+UkMNchfFR42R83hpU5DmJIyS8yjLTWJAPFpmgk7u2WWDafctDX9lUGMvXWnrL690y7C8TSQHwFIph7rb2C0W9'
)

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

def timecode_to_seconds(timecode, fps=24):
    time = timecode.split(":")
    hours = int(time[0])
    minutes = int(time[1])
    seconds = int(time[2])
    frames = int(time[3])

    total_seconds = round(hours * 3600 + minutes * 60 + seconds + (frames / fps), 2)
    return total_seconds

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
    return [duration]

def add_time(shotsList):
    result = []
    for i in range(len(shotsList)):
        targetRange = shots[i][1].split("-")
        result.append([shotsList[i][0], shotsList[i][1], f"{time_conversion(float(targetRange[0]))}-{time_conversion(float(targetRange[1]))}"])
    return result

def render_timeFrames(video, startTime, endTime):
    output = f'{video[:-4]}_shot{counter}.mp4'

    #add 1 second blackscreen to ensure video is atleast 1 second long because FFMPEG VIMEO YOUTUBE are ASPUIFCGQ)*^&!@R^FG)RBASBNOPDFQWB&*RFYWB)Y and they dont transcode the videos unless they are 1 second long despite other students videos transcoding eventhough I TRIED EVERYTHINGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG
    # #CHAJACERTIFIED 
    probe = ffmpeg.probe(video)
    video_stream = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
    width = video_stream['width']
    height = video_stream['height']
    framerate = eval(video_stream['r_frame_rate'])
    main = ffmpeg.input(video, ss=startTime, to=endTime)
    black = ffmpeg.input(f'color=c=black:s={width}x{height}:d=1:r={framerate}', f='lavfi')
    silence = ffmpeg.input(f'anullsrc=channel_layout=stereo:sample_rate=48000', f='lavfi', t=1)
    #----------------------------------------------------------------------------------------

    (
        ffmpeg
        .concat(main.video, main.audio, black.video, silence.audio, v=1, a=1)
        .output(output, vcodec='libx264', acodec='aac', movflags="+faststart")
        .overwrite_output()
        .run()
    )
    return output

def thumbnail_creation(video):
    output = f"{video[:-4]}_thumbnail.jpg"
    duration = getTimecode(video)[0]
    time = duration / 2
    (
        ffmpeg
        .input(video, ss=0)
        .output(output, vframes=1, vf="scale=96:74")
        .overwrite_output()
        .run()
    )
    allThumbnails.append(output)
    return allThumbnails
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
    videoTimecode = getTimecode(args.process[0])[0]
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
    print(shotsWithTime)

 
    for i in range(len(shotsWithTime)):
        timerange = shotsWithTime[i][2].split("-")
        shotsWithTime[i].append('')
        counter += 1
        video = render_timeFrames(args.process[0], timecode_to_seconds(timerange[0]), timecode_to_seconds(timerange[1]))
        time.sleep(2)
        thumbnails = thumbnail_creation(video)
        uri = client.upload(video, data={'name': f"{video}", "description": ""})
        response = client.get(uri + '?fields=transcode.status').json()
        if response['transcode']['status'] == 'complete':
            print('Your video finished transcoding.')
        elif response['transcode']['status'] == 'in_progress':
            print('Your video is still transcoding.')
        else:
            print('Your video encountered an error during transcoding.')



    


    df = pd.DataFrame(shotsWithTime, columns=["Location", "Frame Ranges", "Timecode Ranges", "Thumbnails"])
    with pd.ExcelWriter('output.xlsx', engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="sheet1")
        book = writer.book
        sheet = writer.sheets["sheet1"]
        for i in range(len(thumbnails)):
            sheet.insert_image(f'D{i+2}', thumbnails[i])

        

    







#Create CSV file of the Solo-Frames
    with open('output.csv', "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(UNDESIRABLEandWORTHLESSshots)




