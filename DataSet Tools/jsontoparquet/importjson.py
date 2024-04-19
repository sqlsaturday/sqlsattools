import json
import pandas as pd 

file = 'SQLSat1043.json'
with open(file) as json_data:
    data = json.load(json_data)
    df = pd.DataFrame(data['sessions'])

print(df.head())
