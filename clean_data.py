import pandas as pd
import numpy as np
import re
from thefuzz import fuzz
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

logging.info("جاري قراءة الملف...")
df = pd.read_json('raw_places.json')
initial_count = len(df)

# 1. مسح الأماكن التي إحداثياتها أو أسماؤها فارغة
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df = df.dropna(subset=['latitude', 'longitude'])

df['name'] = df['name'].astype(str).str.strip()
df = df[df['name'] != 'nan']
df = df[df['name'].str.len() > 1]

# 2. تطبيع الأسماء بشكل أعمق وأسرع
logging.info("جاري تطبيع الأسماء...")
name_col = df['name'].str.lower()
name_col = name_col.str.replace(r'[أإآ]', 'ا', regex=True)
name_col = name_col.str.replace('ة', 'ه', regex=True)
name_col = name_col.str.replace('ى', 'ي', regex=True)
name_col = name_col.str.replace(r'[\u064B-\u0652]', '', regex=True) 
name_col = name_col.str.replace(r'[^\w\s]', '', regex=True)
name_col = name_col.str.replace(r'\s+', ' ', regex=True).str.strip()

df['name_clean'] = name_col

# 3. تقريب الإحداثيات لـ 5 مراتب
df['lat_clean'] = df['latitude'].round(5)
df['lng_clean'] = df['longitude'].round(5)

# 4. الحذف الذكي للتكرار
logging.info("جاري البحث عن التكرارات المتطابقة والتقريبية...")

# الخطوة أ: حذف التكرار التام 100% مع تضمين عمود type
if 'type' in df.columns:
    df = df.drop_duplicates(subset=['name_clean', 'lat_clean', 'lng_clean', 'type'], keep='first')
else:
    df = df.drop_duplicates(subset=['name_clean', 'lat_clean', 'lng_clean'], keep='first')

# الخطوة ب: الحذف التقريبي (Fuzzy)
def fuzzy_dedup(group):
    if len(group) == 1:
        return group
    
    keep_indices = [group.index[0]]
    base_name = group.iloc[0]['name_clean']
    
    for i in range(1, len(group)):
        current_name = group.iloc[i]['name_clean']
        ratio = fuzz.token_sort_ratio(base_name, current_name)
        
        # إذا التشابه أقل من 85% نعتبره مكان جديد
        if ratio < 85: 
            keep_indices.append(group.index[i])
            
    return group.loc[keep_indices]

if 'type' in df.columns:
    df = df.groupby(['lat_clean', 'lng_clean', 'type'], group_keys=False).apply(fuzzy_dedup)
else:
    df = df.groupby(['lat_clean', 'lng_clean'], group_keys=False).apply(fuzzy_dedup)

# تنظيف الأعمدة المؤقتة
df = df.drop(columns=['name_clean', 'lat_clean', 'lng_clean'])

final_count = len(df)
logging.info(f"العدد الأصلي: {initial_count}")
logging.info(f"العدد بعد التنظيف: {final_count}")
logging.info(f"تم حذف {initial_count - final_count} مكان مكرر أو غير صالح!")

df.to_json('cleaned_places.json', orient='records', force_ascii=False, indent=2)
logging.info("تم حفظ الملف بنجاح!")
