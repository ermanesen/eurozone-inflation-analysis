import eurostat
import pandas as pd
import os

# script'in bulunduğu klasör
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data_raw')

os.makedirs(DATA_DIR, exist_ok=True)

print("Veri indiriliyor...")

data = eurostat.get_data_df('prc_hicp_manr', flags=False)
data = data[data['coicop'] == 'CP00']

countries = ['DE','FR','IT','ES','NL','BE','AT','PT','GR']
data = data[data['geo\\TIME_PERIOD'].isin(countries)]

print("Dönüştürülüyor...")

data = data.melt(
    id_vars=['geo\\TIME_PERIOD'],
    var_name='date',
    value_name='inflation'
)

data = data.rename(columns={'geo\\TIME_PERIOD':'country'})
data = data.dropna()

print("Kaydediliyor...")

save_path = os.path.join(DATA_DIR, 'inflation.csv')
data.to_csv(save_path, index=False)

print("Kaydedildi:", save_path)
print("Bitti.")
