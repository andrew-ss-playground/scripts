from services.client import StorageScholarsClient
from utils.openai import ask_openai

import os
from dotenv import load_dotenv
import logging
from typing import Any
import csv
import time
from alive_progress import alive_bar

LOG_LEVEL = logging.INFO
ORDER_IDS_FILE_NAME = "data\\order_ids_8-21-25.csv"
REQUEST_DELAY = 0.6

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(name=__name__)

def get_client() -> StorageScholarsClient:
    load_dotenv()
    api_key: str | None = os.getenv(key="SS_API_KEY")
    if api_key is None:
        raise Exception("Missing api key")
    return StorageScholarsClient(api_key=api_key)

def get_rows_and_fieldnames(file_name: str) -> tuple[list[dict[str, Any]], list[str]]:
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

def fetch_pronunciation(first_name: str) -> str | None:
    try:
        return ask_openai(f"In one word, no fluff, give me the pronunciation of the first name {first_name}")
    except Exception as error_message:
        logger.warning(f"Could not fetch pronunciation of {first_name}: {error_message}")
        return None

def write_to_csv(file_name: str, rows: list[dict], fieldnames: list[str]) -> str:
    for key in rows[0].keys():
        if key not in fieldnames:
            fieldnames.append(key)
    
    attempt = 1
    while True:
        try:
            with open(file_name, mode="w", newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            break
        except PermissionError:
            logger.warning(f"Permission Error: Could not write to {file_name}, retrying...")
            base = file_name.split(".")[0]
            file_name = f"{base} ({attempt}).csv"
    return file_name

def main() -> None:
    logger.info(msg="Starting...")
    try:
        client: StorageScholarsClient = get_client()
        rows, fieldnames = get_rows_and_fieldnames(ORDER_IDS_FILE_NAME)
        logger.info(msg=f"Getting details for {len(rows)} order(s)")

        with alive_bar(len(rows), title="Fetching orders") as bar:
            for key, row in enumerate(rows):
                try:
                    order_id = get_order_id(row)
                    first_name = row["FullName"].split(" ")[0]
                    row['Items'] = fetch_item_description(client=client, order_id=order_id)
                    row['Pronunciation'] = fetch_pronunciation(first_name=first_name) or ""
                    # row['Phone'] = get_formatted_phone(row['StudentPhone'])
                    # row['Parent Phone'] = get_formatted_phone(row['ParentPhone'])
                    # row['Storage Unit'] = fetch_storage_unit(client=client, order_id=order_id)
                    # row['Dropoff Location Full'] = get_formatted_location(row)
                    # row['Comments'] = get_comments(row) # proxy name, proxy phone, is first hour, is last hour, has pending balance
                    # download images
                except Exception as error_message:
                    logger.warning(f"Failed to fetch details for row #{key}: {error_message}")
                bar()
                time.sleep(REQUEST_DELAY)

        file_name = write_to_csv(ORDER_IDS_FILE_NAME, rows, fieldnames)
        logger.info(msg=f"Updated details of {len(rows)} order(s) in {file_name}.")
    except Exception as error_message:
        logger.exception(msg=error_message)
    logger.info(msg="Finished")

if __name__ == '__main__':
    main()
