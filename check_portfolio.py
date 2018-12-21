#!/usr/bin/python3
from constants import CONFIG_FILE, AUTH_FILE, HOOK_DIR
from tabulate import tabulate
from collections import OrderedDict
from datetime import datetime
from robinhood.RobinhoodClient import RobinhoodClient

import pandas as pd

import utils
import sys
import json
import os

DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

# Reclaim STDIN when used in git hook
# see https://stackoverflow.com/questions/3417896/how-do-i-prompt-the-user-from-within-a-commit-msg-hook
try:
    sys.stdin = open('/dev/tty', 'r')
except OSError:
    pass

# Attempt to read config file
config_data = {}
if os.path.exists(CONFIG_FILE) and os.stat(CONFIG_FILE).st_size != 0:
    with open(CONFIG_FILE, 'r') as config_file:
        try:
            config_data = json.load(config_file)
        except:
            sys.exit('Failed to read config file.')
# Delete the authorization file if we will not store the token
if not config_data.get('save_token', False):
    if os.path.exists(AUTH_FILE):
        os.remove(AUTH_FILE)
# Attempt to read authorization file
auth_data = {}
if os.path.exists(AUTH_FILE) and os.stat(AUTH_FILE).st_size != 0:
    with open(AUTH_FILE, 'r') as auth_file:
        try:
            auth_data = json.load(auth_file)
        except:
            sys.exit('Failed to read auth file.')

# Authenticate user
is_logged_in = False
rh = RobinhoodClient()
if auth_data:
    # Login from token
    rh.set_oauth2_token(
        auth_data['token_type'],
        auth_data['access_token'],
        datetime.strptime(auth_data['expires_at'], "%Y-%m-%d %H:%M:%S.%f"),
        auth_data['refresh_token']
    )
    is_logged_in = True

if not is_logged_in:
    # Prompt user login
    save_token = config_data.get('save_token', False)
    utils.account.prompt_user_login(rh, save_token)

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
for index, row in options_df.iterrows():
    # Fetch additional instrument data
    option_id = row['option'].split('/')[-2]
    option_data = rh.get_options_instrument(option_id)
    option_quote = rh.get_options_marketdata(option_id)
    option_chain = rh.get_options_chains([row['chain_id']])[0]
    # Assume only one underlying instrument
    option_underlying_instr = option_chain['underlying_instruments'][0]
    option_instrument_id = option_underlying_instr['instrument'].split('/')[-2]
    option_underlying_quote = rh.get_quote(option_instrument_id)
    # Determine symbols
    options_data['symbols'].append(option_data['chain_symbol'])
    # Determine strike price
    options_data['strike_prices'].append(option_data['strike_price'])
    # Determine underlying price
    options_data['underlying_prices'].append(option_underlying_quote['last_trade_price'])
    # Determine contract value
    option_contract_value = option_quote['adjusted_mark_price']
    options_data['contract_value'].append(option_contract_value)
    # Determine quantity
    option_contracts = row['quantity']
    options_data['contracts'].append(option_contracts)
    # Determine position amounts
    option_underlying_amt = option_underlying_instr['quantity']
    position_amount = float(option_contracts)*float(option_contract_value)*option_underlying_amt
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
total_positions = (
    sum(equities_data['position_amounts']) +
    sum(options_data['position_amounts']) +
    sum(cryptos_data['position_amounts'])
)
portfolio_value = total_positions + unused_margin - margin_limit

# Print individual tables
if equities_data['position_amounts']:
    print('Equity Positions:\n\n', tabulate(equities_data, headers='keys', floatfmt='.2f'), '\n\n')
if options_data['position_amounts']:
    print('Option Positions:\n\n', tabulate(options_data, headers='keys', floatfmt='.2f'), '\n\n')
if cryptos_data['position_amounts']:
    print('Crypto Positions:\n\n', tabulate(cryptos_data, headers='keys', floatfmt='.2f'), '\n')

# Print account balances
print('Margin: {:.2f}'.format(margin_limit))
print('Unused Margin: {:.2f}'.format(unused_margin))
print('Portfolio Value: {:.2f}\n'.format(portfolio_value))
