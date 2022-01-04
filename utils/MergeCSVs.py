# merge all columns of the csv file in current directory into a single 'merge.csv' file. 
# requires pandas library to be installed.
# you can customize the merge in many ways: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.concat.html

import pandas as pd
import glob

dfs = glob.glob('*.csv')
result = pd.concat([pd.read_csv(df, sep=';') for df in dfs], ignore_index=True)
result.to_csv('merge.csv')
