import os
import pandas as pd
import argparse

# parse command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("FILENAME", help="Filename to process")
parser.add_argument("COLUMNS", help='Comma separated list of columns to pass for drop duplicates')
args = parser.parse_args()

FILENAME = args.FILENAME
COLUMNS = args.COLUMNS.split(',')

read_csv_kwargs = {}
read_csv_kwargs['low_memory'] = False
read_csv_kwargs['dtype'] = str
read_csv_kwargs['index_col'] = False
read_csv_kwargs['quotechar'] = '"'
read_csv_kwargs['error_bad_lines'] = True

# read csv
csv = pd.read_csv(FILENAME, **read_csv_kwargs)

# drop duplicates
#csv.drop_duplicates(subset = COLUMNS, keep = 'first', inplace = True, ignore_index = False)
csv.drop_duplicates(subset = COLUMNS, keep = 'first', inplace = True)

# write back to same FILENAME
csv.to_csv(FILENAME,index=False)