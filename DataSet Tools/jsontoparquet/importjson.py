import json
import pandas as pd 
import pyarrow as pa
import pyarrow.parquet as pq

from os import listdir
from os.path import isfile, join

mypath = '.'
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f)) and f.endswith('.json') ]
print('List of files in current folder')
print(onlyfiles)

# loop through the files
#for f in onlyfiles:
with open(onlyfiles[0]) as json_data:
    data = json.load(json_data)
        #df = pd.DataFrame(data['sessions'])

    # print the head
    #print(df.head())

#    outputFile = f + '.parquet'
#    pqtable = pa.Table.from_pandas(df)

    # Write Arrow Table to Parquet file
#    pq.write_table(pqtable, outputFile)
