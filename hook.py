#!/usr/local/bin/python3
from constants import CONFIG_FILE
from tabulate import tabulate
from Robinhood import Robinhood

import sys
import json
import os

# First, read current configurations
data = {}
if os.stat(CONFIG_FILE).st_size:
    with open(CONFIG_FILE, 'r') as config_file:
        try:
            data = json.load(config_file)
        except:
            sys.exit('Failed to read config file.')

# Next, check if user is currently logged in
robinhood = Robinhood()
robinhood.login_prompt()
positions = robinhood.positions()

# Finally, print positions
print(positions)