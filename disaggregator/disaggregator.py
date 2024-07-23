import pandas as pd
import numpy as np
import requests
import json
import random
import re
import os

print('Fetching PUMS data from API Census...')
url = 'https://api.census.gov/data/2018/acs/acs5/pums?get=PUMA,WGTP,SPORDER,HINCP,NP,SERIALNO,ADJINC,TEN,BLD&ucgid=0400000US06'

response = requests.get(url)
response.status_code
if (len(str(response.status_code)) == 3) & (str(response.status_code).startswith('2')):
    print('Successful.')
else:
    print('Error: check url.')


census = response.text
census = json.loads(census)

df = pd.DataFrame.from_dict(census)

new_header = df.iloc[0] #grab the first row for the header
df = df[1:] #take the data less the header row
df.columns = new_header

convert_dict = {
    'PUMA': int,
    'WGTP': int, 
    'SPORDER': int,
    'HINCP': int, 
    'NP': int,
    'SERIALNO': object, 
    'ADJINC': float,
    'TEN': int, 
    'BLD': int,
    'ST': int
    }
 
c = df.astype(convert_dict)

# filter & prepare pums data
ca_pums_18 = c[(c['SPORDER'] == 1) & (c['TEN'].isin([1, 2, 3, 4]))]

ca_pums_18['adjinc'] = ca_pums_18['ADJINC'] *ca_pums_18['HINCP'] / 1.06

ca_pums_18['inccat'] = (
    1 * (ca_pums_18['adjinc'] < 25000) +
    2 * ((ca_pums_18['adjinc'] >= 25000) & (ca_pums_18['adjinc'] < 50000)) +
    3 * ((ca_pums_18['adjinc'] >= 50000) & (ca_pums_18['adjinc'] < 75000)) +
    4 * ((ca_pums_18['adjinc'] >= 75000) & (ca_pums_18['adjinc'] < 100000)) +
    5 * ((ca_pums_18['adjinc'] >= 100000) & (ca_pums_18['adjinc'] < 150000)) +
    6 * ((ca_pums_18['adjinc'] >= 150000) & (ca_pums_18['adjinc'] < 200000)) +
    7 * (ca_pums_18['adjinc'] >= 200000)
)

ca_pums_18['is_sfh'] = ca_pums_18['BLD'].isin([2, 3]).astype(int)
ca_pums_18['is_mfh'] = ca_pums_18['BLD'].isin([4, 5, 6, 7, 8, 9]).astype(int)
ca_pums_18['is_oth'] = ca_pums_18['BLD'].isin([1, 10]).astype(int)

ca_pums_18['hhsize'] = ca_pums_18['NP']
ca_pums_18['sizcat'] = np.where(ca_pums_18['hhsize'] < 5, ca_pums_18['hhsize'], 5)
ca_pums_18['hh_cat'] = (ca_pums_18['inccat'] - 1) * 5 + ca_pums_18['sizcat']
ca_pums_18 = ca_pums_18.reset_index(drop=True)

# fetch & clean analysis units & location probability data
analysisunits = pd.read_csv('disagregator_test_data/AMBAG_Analysis_Units_ALLO.csv')
analysisunits.replace('-nan(ind)', np.nan, inplace=True)
locprob = pd.read_csv('disagregator_test_data/combined_locprob.csv', delimiter=';')
locprob[['H_Type[55]','cnty_fips']] = locprob['H_Type[55],cnty_fips'].str.split(',',expand=True)
locprob = locprob.drop(columns=['H_Type[55],cnty_fips'])
locprob = locprob[locprob.columns].astype(float)

# filter for only residential
nonres = locprob.columns[37:-1]
locprob = locprob.drop(nonres, axis=1)

# fill NAs
locprob = locprob.fillna(0)
analysisunits = analysisunits.fillna(0)

ex_cats = ["EX_SFR","EX_MFR","EX_ORES","EX_ADU"]
analysisunits[ex_cats] = analysisunits[ex_cats].apply(pd.to_numeric, errors='coerce')


results = []
h_type_cols = [col for col in locprob if col.startswith('H_Type')]
n_iter = 1

for i in range(n_iter): 
    for col in ex_cats:
        for row_index, row_value in analysisunits[col].items():
            if analysisunits[col].loc[row_index] > 0:
                # find locprob's row matching with analysis unit's TAZ and housing type
                fil_locprob = locprob[(locprob['Zone'] == analysisunits.loc[row_index]['TAZ_NUMBER']) & (locprob['Realestate'] == ex_cats.index(col) + 1)]

                if len(fil_locprob) > 0:
                    # random choice in locprob's row to find a housing category
                    locprob_choice = random.choices(h_type_cols, weights=pd.to_numeric(fil_locprob[h_type_cols].values[0]))
                    found_hh_cat = pd.to_numeric(re.search(r'\d+', locprob_choice[0])[0])

                    # filter pums for found random housing category, then sample (with replacement) for pums 
                    fil_pums = ca_pums_18[ca_pums_18['hh_cat'] == found_hh_cat]
                    row = random.choices(fil_pums.index, weights=fil_pums['WGTP'].values, k = int(float(row_value)))

                    res = fil_pums.loc[row]
                    res['analysis_unit'] = row_index
                    res['zone'] = analysisunits.loc[row_index]['TAZ_NUMBER']
                    res['realestate'] = fil_locprob['Realestate'].item()
                    results.extend(res.to_dict(orient='records'))
                    
                # to check progress, if needed
                if row_index%500 == 0:
                    print(f'Progress: {col}, {row_index/len(analysisunits[col]) * 100:.2f}%')
        print(col + ", done!")

fin = pd.DataFrame(results)

# change dtypes from float to int where appropriate
fl_to_int = ['zone', 'realestate']
fin[fl_to_int] = fin[fl_to_int].applymap(np.int64)

# save scv to output folder
directory = 'output'
file_path = os.path.join(directory, 'disaggregator_results.csv')

if not os.path.exists(directory):
    os.makedirs(directory)

fin.to_csv(file_path)

print(f"File saved to {file_path}")