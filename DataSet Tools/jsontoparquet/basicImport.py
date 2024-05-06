# Basic import of a JSON file
import json
import chardet
import pandas as pd
import os

mypath = '.\\raw'
onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f)) and f.endswith('.json') ]

# loop through the files
for f in onlyfiles:
    currentfile = os.path.join(mypath,f)
    enc=chardet.detect(open(currentfile,'rb').read())['encoding']
    with open(currentfile,'r', encoding=enc) as json_data:
        data = json.load(json_data)

    # get session data from json
    df = pd.DataFrame(data['sessions'])

    # print the head
    print(df.head())
