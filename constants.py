from pathlib import Path
import os

HOME = str(Path.home())
CONFIG_FILE=os.path.join(HOME, ".robinhood-hook-config.json")