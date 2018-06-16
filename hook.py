#!/usr/local/bin/python3
from constants import CONFIG_FILE
from tabulate import tabulate
from collections import OrderedDict
from robinhood.RobinhoodClient import RobinhoodClient

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
rh = RobinhoodClient()
if config_data['username'] and config_data['password']:
    rh.set_auth_token_with_credentials(config_data['username'], config_data['password'])
else:
    username = input('Username: ')
    password = input('Password: ')
    rh.set_auth_token_with_credentials(username, password)

# Obtain equity, options, and crypto positions
equities = rh.get_positions()
options = rh.get_options_positions()
#cryptos = rh.get_crypto_holdings()

# Create curated data table for equities
equities_data = OrderedDict({
    'symbols': [],
    'stock_prices': [],
    'shares_owned': [],
    'position_amounts': []
})
equities_df = pd.DataFrame(equities)
for equity_url in equities_df['instrument']:
    # Fetch additional instrument data
    equity_id = equity_url.split('/')[-2]
    equity_data = rh.get_instrument_by_id(equity_id)
    # Determine symbols
    equities_data['symbols'].append(equity_data['symbol'])
for index, row in equities_df.iterrows():
    # Determine stock prices
    equities_data['stock_prices'].append(row['average_buy_price'])
    # Determine shares owned
    equities_data['shares_owned'].append(row['quantity'])
    # Determine position amounts
    position_amount = float(row['quantity'])*float(row['average_buy_price'])
    equities_data['position_amounts'].append(position_amount)

# Create curated data table for options
options_data = OrderedDict({
    'symbols': [],
    'strike_prices': [],
    'underlying_prices': [],
    'contracts': [],
    'position_amounts': []
})
options_df = pd.DataFrame(options)
for option_url in options_df['option']:
    # Fetch additional instrument data
    option_id = option_url.split('/')[-2]
    option_data = rh.get_options_instrument(option_id)
    # Determine symbols
    options_data['symbols'].append(option_data['chain_symbol'])
    # Determine strike price
    options_data['strike_prices'].append(option_data['strike_price'])
for index, row in options_df.iterrows():
    position_amount = float(row['quantity'])*float(row['average_price'])
    options_data['position_amounts'].append(position_amount)

# Create curated data table for cryptos
cryptos_data = OrderedDict({
    'symbols': [],
    'position_amounts': []
})

# Print individual tables
print('Equities\n', tabulate(equities_data, floatfmt='.2f'), '\n')
print('Options\n', tabulate(options_data, floatfmt='.2f'), '\n')
print('Cryptos\n', tabulate(cryptos_data, floatfmt='.2f'), '\n')

# Summary diagnostics
total_positions = (sum(equities_data['position_amounts']) +
                  sum(options_data['position_amounts']) +
                  sum(cryptos_data['position_amounts']))
print('Total account value: {:.2f}'.format(total_positions))