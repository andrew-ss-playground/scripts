from services.client import StorageScholarsClient
import os
from dotenv import load_dotenv
import logging
from typing import Any
import csv
import time
from alive_progress import alive_bar

LOG_LEVEL = logging.INFO
ORDER_IDS_FILE_NAME = "data\\order_ids_8-21-25.csv"
REQUEST_DELAY = 0.3
DELAY_MIN_REQUESTS = 50

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(name=__name__)

def get_client() -> StorageScholarsClient:
    load_dotenv()
    api_key: str | None = os.getenv(key="SS_API_KEY")
    if api_key is None:
        raise Exception("Missing api key")
    return StorageScholarsClient(api_key=api_key)

def get_rows_and_fieldnames(file_name: str) -> tuple[list[dict], list[str]]:
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
    
    if not rows or not fieldnames:
        raise Exception("No data or headers found in input CSV.")
    
    return rows, fieldnames

def get_order_id(row: dict) -> int:
    order_id_str = row.get("OrderID") or row.get(next(iter(row)))
    if order_id_str and order_id_str.isdigit():
        return int(order_id_str)
    else:
        raise ValueError(f"Row does not have an order ID")

def fetch_item_description(client: StorageScholarsClient, order_id: int) -> str:
    items: list[dict[str, Any]] = client.get_request(url=f"/order/items/{order_id}")
    if items:
        return ", ".join([f"{item['Quantity']}x {item['ItemTitle']}" for item in items])
    return ""

def write_to_csv(file_name: str, rows: list[dict], fieldnames: list[str]) -> None:
    if 'items' not in fieldnames:
        fieldnames.append('items')
    
    with open(file_name, mode="w", newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main() -> None:
    logger.info(msg="Starting...")
    try:
        client: StorageScholarsClient = get_client()
        rows, fieldnames = get_rows_and_fieldnames(ORDER_IDS_FILE_NAME)
        logger.info(msg=f"Getting items for {len(rows)} order(s)")

        with alive_bar(len(rows), title="Fetching orders") as bar:
            for row in rows:
                order_id = get_order_id(row)
                try:
                    item_description = fetch_item_description(client=client, order_id=order_id)
                except Exception as error_message:
                    logger.warning(f"Failed to get items for order {order_id}: {error_message}")
                    item_description = ""
                row['Items'] = item_description
                bar()
                time.sleep(REQUEST_DELAY if len(rows) >= DELAY_MIN_REQUESTS else 0)

        write_to_csv(ORDER_IDS_FILE_NAME, rows, fieldnames)
        logger.info(msg=f"Updated items of {len(rows)} order(s) in {ORDER_IDS_FILE_NAME}.")
    except Exception as error_message:
        logger.exception(msg=error_message)
    logger.info(msg="Finished")

if __name__ == '__main__':
    main()
