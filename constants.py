from pathlib import Path
import os

HOME = str(Path.home())
HOOK_DIR = os.path.join(HOME, '.robinhood-git-hook')
CONFIG_FILE=os.path.join(HOOK_DIR, 'config.json')
AUTH_FILE=os.path.join(HOOK_DIR, 'authorization.json')