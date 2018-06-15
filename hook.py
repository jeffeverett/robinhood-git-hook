#!/usr/local/bin/python3
from constants import CONFIG_FILE
from tabulate import tabulate
from collections import OrderedDict
from Robinhood import Robinhood

import pandas as pd

import sys
import json
import os

# First, read current configurations
config_data = {}
if os.stat(CONFIG_FILE).st_size:
    with open(CONFIG_FILE, 'r') as config_file:
        try:
            config_data = json.load(config_file)
        except:
            sys.exit('Failed to read config file.')

# Next, authenticate user
robinhood = Robinhood()
if config_data['username'] and config_data['password']:
    robinhood.login(config_data['username'], config_data['password'])
else:
    robinhood.login_prompt()
positions = robinhood.securities_owned()

# Create curated data table
curated_data = OrderedDict({
    'symbols': [],
    'position_amounts': []
})
df = pd.DataFrame(positions['results'])
for instrument_url in df['instrument']:
    instrument_id = instrument_url.split('/')[-2]
    instrument_data = robinhood.instrument(instrument_id)
    curated_data['symbols'].append(instrument_data['symbol'])
for index, row in df.iterrows():
    position_amount = float(row['quantity'])*float(row['average_buy_price'])
    curated_data['position_amounts'].append(position_amount)

print(tabulate(curated_data))

# Summary diagnostics
total_positions = sum(curated_data['position_amounts'])
print('Total account value: {:.2f}'.format(total_positions))