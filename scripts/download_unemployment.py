import eurostat
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data_raw')
os.makedirs(DATA_DIR, exist_ok=True)

print("İşsizlik verisi indiriliyor...")

data = eurostat.get_data_df('une_rt_m', flags=False)

# SADECE yüzde işsizlik
data = data[
    (data['age'] == 'TOTAL') &
    (data['sex'] == 'T') &
    (data['unit'] == 'PC_ACT')
]

countries = ['DE','FR','IT','ES','NL','BE','AT','PT','GR']
data = data[data['geo\\TIME_PERIOD'].isin(countries)]

# sadece gerekli kolonları bırak
data = data[['geo\\TIME_PERIOD'] + [c for c in data.columns if c[:4].isdigit()]]

print("Dönüştürülüyor...")

data = data.melt(
    id_vars=['geo\\TIME_PERIOD'],
    var_name='date',
    value_name='unemployment'
)

data = data.rename(columns={'geo\\TIME_PERIOD':'country'})
data = data.dropna()

print("Kaydediliyor...")

save_path = os.path.join(DATA_DIR, 'unemployment.csv')
data.to_csv(save_path, index=False)

print("Kaydedildi:", save_path)
print("Bitti.")
