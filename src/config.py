import os

# Configuration
MODEL_SIZE = "base"  # Options: tiny, base, small, medium, large
DEVICE = "cpu"       # "cpu" or "cuda"
COMPUTE_TYPE = "int8" # "int8" or "float16" (if GPU)

APP_NAME = "uWhisper"
SOCKET_PATH = "/tmp/uwhisper.sock"
DEFAULT_LANGUAGE = "en"  # "en" or "pl"
SHORTCUT_TRIGGER_DELAY = 0.5 # Seconds to wait before simulating keys (if applicable)

# Notification settings
ICON_PATH = "" # Add path to an icon if available
