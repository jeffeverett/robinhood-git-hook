from constants import CONFIG_FILE

def is_logged_in():
    with open(CONFIG_FILE, 'r') as config_file:
        if