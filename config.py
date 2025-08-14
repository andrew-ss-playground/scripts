import os
from dotenv import load_dotenv

load_dotenv()

# get_details.py
SS_API_KEY = os.getenv("SS_API_KEY")
DEFAULT_ORDER_IDS_FILE_NAME = "data\\order_ids_8-19-25.csv"

# client.py
BASE_URL = "https://api.storagescholars.com"
IMAGES_DIR = os.path.join("data", "images")
TIMEOUT_DURATION = 10
REQUEST_DELAY = 0.3

# order_details.py
IS_FETCH_OPENAI = False
IS_FETCH_IMAGES = False
IS_FETCH_ITEMS = False
IS_FETCH_INTERNAL_NOTES = False

# openai.py
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
