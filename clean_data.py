import pandas as pd
import numpy as np
import re

print("جاري قراءة الملف...")
df = pd.read_json('raw_places.json')
initial_count = len(df)

# 1. مسح الأماكن اللي إحداثياتها أو أسماءها فارغة
df = df.dropna(subset=['latitude', 'longitude'])
df['name'] = df['name'].astype(str).str.strip()
df['name'] = df['name'].replace(r'^\s*$', np.nan, regex=True)
df = df.dropna(subset=['name'])

# 2. توحيد الأسماء العربية (أ،إ،آ -> ا | ة -> ه) حتى يصيد التكرار بالأسماء
df['name_clean'] = df['name'].apply(lambda x: re.sub(r'[أإآ]', 'ا', re.sub(r'ة', 'ه', str(x).lower())))

# 3. تقريب الإحداثيات لـ 4 مراتب (حوالي 11 متر) لصيد الدبوس المكرر
df['lat_clean'] = df['latitude'].round(4)
df['lng_clean'] = df['longitude'].round(4)

# 4. الحذف الذكي
df = df.drop_duplicates(subset=['name_clean', 'lat_clean', 'lng_clean'], keep='first')

# تنظيف وترتيب الملف للناتج
df = df.drop(columns=['name_clean', 'lat_clean', 'lng_clean'])

final_count = len(df)
print(f"العدد الأصلي: {initial_count}")
print(f"العدد بعد التنظيف: {final_count}")
print(f"تم حذف {initial_count - final_count} مكان مكرر أو غير صالح!")

df.to_json('cleaned_places.json', orient='records', force_ascii=False, indent=2)
