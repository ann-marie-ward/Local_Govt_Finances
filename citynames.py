import pandas as pd
import pathlib
import pickle

import data_utilities as du

pd.set_option("display.max_rows", 100)
pd.set_option("display.max_columns", 12)

PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("./data").resolve()
DATA_PREP_PATH = PATH.joinpath("./data_prep_city").resolve()


df = pd.read_excel(
        DATA_PREP_PATH.joinpath('city_names.xlsx'))

# Make a DF of cities and states where the city name ends in "City"
df = df[['City', 'State short']]
df = df.astype(str)

df['STCity'] = df['State short'] + df['City']
df = df[df['STCIty'].str.endswith('City')]
df = df.drop_duplicates(subset=['STCity'])

df_city_city = df['City','State short']




