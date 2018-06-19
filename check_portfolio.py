#!/usr/local/bin/python3
from constants import CONFIG_FILE, AUTH_FILE, HOOK_DIR
from tabulate import tabulate
from collections import OrderedDict
from getpass import getpass
from datetime import datetime
from robinhood.RobinhoodClient import RobinhoodClient

import pandas as pd

import sys
import json
import os

DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

# First, read user files
config_data = {}
auth_data = {}
if os.path.exists(CONFIG_FILE) and os.stat(CONFIG_FILE).st_size != 0:
    with open(CONFIG_FILE, 'r') as config_file:
        try:
            config_data = json.load(config_file)
        except:
            sys.exit('Failed to read config file.')
if os.path.exists(AUTH_FILE) and os.stat(AUTH_FILE).st_size != 0:
    with open(AUTH_FILE, 'r') as auth_file:
        try:
            auth_data = json.load(auth_file)
        except:
            sys.exit('Failed to read auth file.')

# Next, authenticate user
rh = RobinhoodClient()
if 'token' in auth_data:
    # Login from token
    rh.set_auth_token(auth_data['token'])
else:
    # Prompt user login
    username = input('Username: ')
    password = getpass('Password: ')
    rh.set_auth_token_with_credentials(username, password)
    # Store authentication data if necessary
    auth_header = rh._authorization_headers['Authorization']
    auth_data = {
        'token': auth_header.split(' ')[1]
    }
    if 'save_token' not in config_data or config_data['save_token'] == True:
        if not os.path.exists(HOOK_DIR):
            os.makedirs(HOOK_DIR)
        with open(AUTH_FILE, 'w') as auth_file:
            json.dump(auth_data, auth_file, default=str)
# Migrate simple token to OAuth2
rh.migrate_token()

# Obtain equity, options, and crypto positions
equities = rh.get_positions()
options = rh.get_options_positions()
cryptos = rh.get_crypto_holdings()

# Create curated data table for equities
equities_data = OrderedDict({
    'symbols': [],
    'stock_prices': [],
    'shares_owned': [],
    'position_amounts': []
})
equities_df = pd.DataFrame(equities)
for index, row in equities_df.iterrows():
    # Fetch additional instrument data
    equity_id = row['instrument'].split('/')[-2]
    equity_data = rh.get_instrument_by_id(equity_id)
    equity_quote = rh.get_quote(equity_id)
    # Determine symbols
    equities_data['symbols'].append(equity_data['symbol'])
    # Determine stock prices
    equity_value = equity_quote['last_extended_hours_trade_price']
    equities_data['stock_prices'].append(equity_value)
    # Determine shares owned
    equity_quantity = row['quantity']
    equities_data['shares_owned'].append(equity_quantity)
    # Determine position amounts
    position_amount = float(equity_quantity)*float(equity_value)
    equities_data['position_amounts'].append(position_amount)

# Create curated data table for options
options_data = OrderedDict({
    'symbols': [],
    'strike_prices': [],
    'underlying_prices': [],
    'contract_value': [],
    'contracts': [],
    'position_amounts': []
})
options_df = pd.DataFrame(options)
options_per_contract = 100
for index, row in options_df.iterrows():
    # Fetch additional instrument data
    option_id = row['option'].split('/')[-2]
    option_data = rh.get_options_instrument(option_id)
    option_quote = rh.get_options_marketdata(option_id)
    # Determine symbols
    options_data['symbols'].append(option_data['chain_symbol'])
    # Determine strike price
    options_data['strike_prices'].append(option_data['strike_price'])
    # Determine contract value
    option_contract_value = option_quote['adjusted_mark_price']
    options_data['contract_value'].append(option_contract_value)
    # Determine quantity
    option_contracts = row['quantity']
    options_data['contracts'].append(option_contracts)
    # Determine position amounts
    position_amount = float(option_contracts)*float(option_contract_value)*options_per_contract
    options_data['position_amounts'].append(position_amount)

# Create curated data table for cryptos
cryptos_data = OrderedDict({
    'symbols': [],
    'usd_values': [],
    'quantities': [],
    'position_amounts': []
})
cryptos_df = pd.DataFrame(cryptos)
currency_pairs = rh.get_crypto_currency_pairs()
for index, row in cryptos_df.iterrows():
    # Do not consider currencies with 0 quantity
    if row['quantity'] == 0:
        continue
    # Find additional instrument data
    crypto_symbol = row['currency']['code']
    crypto_pair = next((cp for cp in currency_pairs if cp['symbol'] == (crypto_symbol + '-USD')), None)
    if not crypto_pair:
        continue
    crypto_pair_data = rh.get_crypto_quote(crypto_pair['id'])
    # Determine symbol
    cryptos_data['symbols'].append(crypto_symbol)
    # Determine USD value
    crypto_usd_value = crypto_pair_data['mark_price']
    cryptos_data['usd_values'].append(crypto_usd_value)
    # Determine quantities
    crypto_quantity = row['quantity']
    cryptos_data['quantities'].append(crypto_quantity)
    # Determine position amounts
    position_amount = float(crypto_quantity)*float(crypto_usd_value)
    cryptos_data['position_amounts'].append(position_amount)

# Compute balances for account
account_data = rh.get_account()
margin_limit = float(account_data['margin_balances']['margin_limit'])
unused_margin = float(account_data['margin_balances']['unallocated_margin_cash'])
total_positions = (sum(equities_data['position_amounts']) +
                  sum(options_data['position_amounts']) +
                  sum(cryptos_data['position_amounts']))
portfolio_value = total_positions + unused_margin - margin_limit


# Print individual tables
print('Equities\n', tabulate(equities_data, floatfmt='.2f'), '\n')
print('Options\n', tabulate(options_data, floatfmt='.2f'), '\n')
print('Cryptos\n', tabulate(cryptos_data, floatfmt='.2f'), '\n')

# Print account balances
print('Margin: {:.2f}'.format(margin_limit))
print('Unused Margin: {:.2f}'.format(unused_margin))
print('Portfolio Value: {:.2f}'.format(portfolio_value))