
import os
import sys

APP_NAME = "NOXIOUS NITRO"
APP_VERSION = "1.0.1"
DISCORD_URL = "https://discord.gg/CE8xPnpV6a"

                   
COLOR_BG = "#0d0d0d"                           
COLOR_BG_ALT = "#111511"                                  
COLOR_ACCENT = "#00FF00"                  
COLOR_ACCENT_DIM = "#0a3d0a"                            
COLOR_TEXT = "#d6ffd6"                         
COLOR_TEXT_DIM = "#6f8f6f"                      
COLOR_WARN = "#ffcc00"
COLOR_ERROR = "#ff4444"

                                      
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), APP_NAME)
LOG_DIR = os.path.join(DATA_DIR, "logs")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

for _d in (LOG_DIR, BACKUP_DIR):
    try:
        os.makedirs(_d, exist_ok=True)
    except OSError:
        pass


def resource_path(name):
    base = getattr(sys, "_MEIPASS",
                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, name)
