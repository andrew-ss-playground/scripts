from services.client import StorageScholarsClient
import os
from dotenv import load_dotenv
import logging

LOG_LEVEL = logging.INFO

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(name=__name__)

def get_client() -> StorageScholarsClient:
    load_dotenv()
    api_key: str | None = os.getenv(key="SS_API_KEY")
    if api_key is None:
        raise Exception("Missing api key")

    return StorageScholarsClient(api_key=api_key)

def main():
    try:
        client = get_client()
        order_id = 95003
        items = client.get_request(url=f"/order/items/{order_id}")
        if items is None or len(items) == 0:
            raise Exception("Items is None")
        
        print(items)
    except Exception as error_message:
        logger.exception(msg=error_message)

if __name__ == '__main__':
    main()
