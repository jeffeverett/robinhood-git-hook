from getpass import getpass
from constants import AUTH_FILE, HOOK_DIR


import os
import json
import robinhood

def is_valid_token(rh):
    # Ensure valid token
    is_valid = True
    try:
        # Request is arbitrary -- just needs to be one that requires authentication
        rh.get_account()
    except robinhood.exceptions.NotLoggedIn:
        is_valid = False

    return is_valid

def prompt_user_login(rh, save_token):
    # Prompt user login
    username = input('Username: ')
    password = getpass('Password: ')
    rh.set_auth_token_with_credentials(username, password)
    # Store authentication data if necessary
    auth_header = rh._authorization_headers['Authorization']
    auth_data = {
        'token': auth_header.split(' ')[1]
    }

    if save_token:
        if not os.path.exists(HOOK_DIR):
            os.makedirs(HOOK_DIR)
        with open(AUTH_FILE, 'w') as auth_file:
            json.dump(auth_data, auth_file, default=str)