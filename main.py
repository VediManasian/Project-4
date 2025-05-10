import csv
string = []
xytechPaths = []
consecutive = []
d = {}
comparisonD = {}
correctD = {}
#Opens both files
with open("Baselight_export_spring2025.txt", "r") as baselight, open("Xytech_spring2025.txt", "r") as xytech:
    # Puts baselight.txt each line as an element in baselightLines
    baselightLines = baselight.read().splitlines()
    # Makes string as a list of lists, and puts every word as part of the second list
    for i in range(len(baselightLines)):
        string.append(baselightLines[i].split())
    # Makes a disctionary where the locations are the keys and the values are the list of values associated with the location(key).
    for i in range(len(string)):
        for word in range(len(string[i]) - 1):
            #Checks if location is not already a key in the list, if it isnt, adds it as a key with the first value
            if string[i][0] not in d:
                d[string[i][0]] = [string[i][word + 1]]
               #adds the value to the key when it exists
            else:
                d[string[i][0]].append(string[i][word + 1])
    #-------------------------------------------------------------------
    #Gets all the paths from the xytech text file.
    xytechLines = xytech.read().splitlines()
    for i in xytechLines:
        if i.startswith("/"):
            xytechPaths.append(i)

#Takes the paths(keys) from the baselight dictionary and prepares them for comparison with the correct path of xytechPaths
            for key, value in d.items():
                #Takes the path, removes the first part of the directory and rejoins them to make 
                newPath = "/" + "/".join(key.split("/")[2:])
                comparisonD[newPath] = value

#Creates a dictionary that associated all the frames with the correct path.
for key in comparisonD:
    for i in xytechPaths:
        newpath = "/" + "/".join(i.split("/")[3:])
        if key == newpath:
            correctD[i] = comparisonD[key]
with open("output", "w", newline='') as file:
    writer = csv.writer(file)

    for key, value in correctD.items():
        
        for i in range(len(value)):
            if i + 1 < len(value) and int(value[i]) == int(value[i + 1]) - 1:
                consecutive.append(value[i])
            else:
                consecutive.append(value[i])
                consecutive_str = ",".join(consecutive)
                writer.writerow([key, consecutive_str])
                consecutive = []
print("CSV created")
