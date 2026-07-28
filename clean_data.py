import pandas as pd
import numpy as np

df = pd.read_json('raw_places.json')
df = df.dropna(subset=['latitude', 'longitude'])
df['name'] = df['name'].replace(r'^\s*$', np.nan, regex=True)
df = df.dropna(subset=['name'])
df = df.drop_duplicates(subset=['name', 'latitude', 'longitude'], keep='first')
df.to_json('cleaned_places.json', orient='records', force_ascii=False, indent=2)

