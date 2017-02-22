#! /usr/bin/env python
# -*- coding: utf-8 -*
import pandas as pd
from os import listdir
from os.path import exists, isdir, isfile, join
from argparse import ArgumentParser
import shutil
import zipfile
import open_interest_plot as oip


# Constants
daily_folder = 'meff_daily_data'
tmp_folder = join(daily_folder, 'tmp')
inner_zip_filename = 'today_rv.zip'
daily_negotiations_file = 'TGENTRADES.M3'
contracts_file = 'CCONTRACTS.C2'
contracts_stats_file = 'CCONTRSTAT.C2'
contracts_columns = ['session_date', 'contract_code', 'contract_subgroup', 'contract_type', 'strike', 'expiration_date']
contracts_dtype = {'session_date': str, 'contract_code': str, 'contract_subgroup': str, 'contract_type': str, 'strike': float, 'expiration_date': str}
contracts_stats_columns = ['contract_code', 'volume', 'open_interest']
contracts_stats_dtype = {'contract_code': str, 'volume': int, 'open_interest': int}

if __name__ == '__main__':
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input_file', type=str,
                        help='Determines a single daily zip file')
    args = parser.parse_args()
    
    data = pd.DataFrame()
    daily_files = []
    if args.input_file:
        if exists(args.input_file):
            daily_files.append(args.input_file)
        else:
            print('ERROR: given input file does not exist')
    else:
        # Load all available daily files data
        daily_files = [join(daily_folder, f) for f in listdir(daily_folder) if isfile(join(daily_folder, f)) and f.lower().endswith('.zip')]
    
    for file in daily_files:
        # Delete tmp folder (if exists)
        if exists(tmp_folder) and isdir(tmp_folder):
            shutil.rmtree(tmp_folder)
        
        # First unzip (inside there is another zip file which also has to be unziped)
        outer_zip = zipfile.ZipFile(file, 'r')
        outer_zip.extractall(tmp_folder)
        outer_zip.close()
        inner_zip = zipfile.ZipFile(join(tmp_folder, inner_zip_filename), 'r')
        inner_zip.extractall(tmp_folder)
        inner_zip.close()
        
        # Load contracts file
        contracts_data = pd.read_csv(join(tmp_folder, contracts_file), sep=';', decimal=',',
                                     header=None, names=contracts_columns, dtype=contracts_dtype, parse_dates=[0, 5],
                                     usecols=[0, 2, 3, 4, 5, 6])
        
        # Now load contracts stats file
        contracts_stats_data = pd.read_csv(join(tmp_folder, contracts_stats_file), sep=';', decimal=',',
                                           header=None, names=contracts_stats_columns, dtype=contracts_stats_dtype, parse_dates=[0],
                                           usecols=[2, 13, 15])
        
        # Join dataframes on contract_code
        df = pd.merge(contracts_data, contracts_stats_data, how='inner', on='contract_code', sort=False)
        
        # Filter the dataframe to keep only mini-ibex contract subgroup
        df = df[(df.contract_subgroup == '20') & ((df.contract_type == '0210') | (df.contract_type == '0220'))]
        df['right'] = df['contract_type'].apply(lambda x: ('C' if (x == '0210') else 'P'))
        
        # Append dataframe into a single sataframe with the info from all files
        data = data.append(df)
            
        # Delete tmp folder
        shutil.rmtree(tmp_folder)
    
    # Delete unused columns
    del data['contract_code']
    del data['contract_subgroup']
    del data['contract_type']
    
    # Filter out options without open interest
    #data = data[data.open_interest > 0]
    print(data[data.expiration_date == '2017-03-17'])
    oip.plot_open_interest(data[data.expiration_date == '2017-03-17'])