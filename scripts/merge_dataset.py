import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data_raw')
CLEAN_DIR = os.path.join(BASE_DIR, '..', 'data_clean')

os.makedirs(CLEAN_DIR, exist_ok=True)

print("Veriler okunuyor...")

inflation = pd.read_csv(os.path.join(DATA_DIR, 'inflation.csv'))
unemployment = pd.read_csv(os.path.join(DATA_DIR, 'unemployment.csv'))

# tarih formatını düzelt
inflation = inflation[inflation['date'].str.contains(r'^\d{4}-\d{2}$')]
inflation['date'] = pd.to_datetime(inflation['date']).dt.to_period('M')

unemployment = unemployment[unemployment['date'].str.contains(r'^\d{4}-\d{2}$')]
unemployment['date'] = pd.to_datetime(unemployment['date']).dt.to_period('M')


print("Birleştiriliyor...")

df = pd.merge(inflation, unemployment, on=['country','date'], how='inner')

df['date'] = df['date'].dt.to_timestamp()
df = df.sort_values(['country','date'])

print("Kaydediliyor...")

df.to_csv(os.path.join(CLEAN_DIR, 'macro_dataset.csv'), index=False)

print("Bitti → data_clean/macro_dataset.csv oluştu")
