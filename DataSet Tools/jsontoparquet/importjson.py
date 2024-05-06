import json
import pandas as pd 
import pyarrow as pa
import pyarrow.parquet as pq
import chardet

from os import listdir
from os.path import isfile, join

mypath = '.\\raw'
outPath = '.\\bronze'
onlyJsonFiles = [f for f in listdir(mypath) if isfile(join(mypath, f)) and f.endswith('.json') ]
print('List of files in current folder')
print(onlyJsonFiles)

# loop through the files
for f in onlyJsonFiles:
    currentfile = join(mypath,f)
    enc=chardet.detect(open(currentfile,'rb').read())['encoding']
    with open(currentfile,'r', encoding=enc) as json_data:
        data = json.load(json_data)

    df = pd.DataFrame(data['sessions'])

    # print the head
    print(df.head())

    outputFilename = f + '.parquet'
    outputFile = join(outPath, outputFilename)
    pqtable = pa.Table.from_pandas(df)

    # Write Arrow Table to Parquet file
    pq.write_table(pqtable, outputFile)
