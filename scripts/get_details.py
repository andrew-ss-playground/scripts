from services.client import StorageScholarsClient
from utils.openai import ask_openai
from utils.parsing import parse_phone, parse_full_location

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

def add_suffix_to_file_name(file_name, suffix):
    parts = file_name.split(".")
    return f"{parts[0]}{suffix}.{parts[1]}"

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
    if items is None or len(items) == 0:
        logging.warning(f"Could not get items for order {order_id}")
        return ""
    
    return ", ".join([f"{item['Quantity']}x {item['ItemTitle']}" for item in items])

def fetch_storage_unit(client: StorageScholarsClient, order_id: int) -> str:
    url: str = "/worklist/dropoff"
    params: dict[str, int] = {'OrderID': order_id}
    dropoff_info: dict[str, Any] | None = client.get_request(url=url, params=params)
    if dropoff_info is None or dropoff_info.get('StorageUnitName') is None or dropoff_info.get('Quadrant') is None:
        logging.warning(f"Could not get storage unit info for order {order_id}")
        return ""

    return f"{dropoff_info['StorageUnitName']} {dropoff_info['Quadrant']}"

def fetch_pronunciation(first_name: str) -> str | None:
    try:
        return ask_openai(f"In one word, no fluff, give me the pronunciation of the first name {first_name}")
    except Exception as error_message:
        logger.warning(f"Could not fetch pronunciation of {first_name}: {error_message}")
        return None

def get_updated_rows(client: StorageScholarsClient, old_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    new_rows: list[dict[str, Any]] = []
    with alive_bar(len(old_rows), title="Fetching orders") as bar:
        for key, old_row in enumerate(old_rows):
            try:
                order_id = get_order_id(old_row)
                first_name = old_row["FullName"].split(" ")[0]
                
                new_rows.append({
                    "ID": old_row.get('OrderID'),
                    "Name": old_row.get('FullName'),
                    'Pronunciation': fetch_pronunciation(first_name=first_name) or "",
                    'Phone': parse_phone(old_row['StudentPhone']),
                    'Location': parse_full_location(old_row),
                    'Ct.': old_row.get('ItemCount'),
                    'Items': fetch_item_description(client=client, order_id=order_id),
                    'Time Loaded': '',
                    'Time Arrived': '',
                    'Time Delivered': '',

                    'Storage Unit': fetch_storage_unit(client=client, order_id=order_id),
                    'Parent Phone': parse_phone(old_row['ParentPhone']),
                    # 'Comments': get_comments(old_row), # proxy name, proxy phone, is first hour, is last hour, has pending balance
                })
                # download image
            except Exception as error_message:
                logger.warning(f"Failed to fetch details for row #{key}: {error_message}")
            
            bar()
            time.sleep(REQUEST_DELAY) 
    return new_rows

def write_to_csv(file_name: str, rows: list[dict]) -> str:
    attempt = 0
    while True:
        try:
            with open(file=file_name, mode="w", newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            break
        except PermissionError:
            logger.warning(f"Could not write to {file_name}, trying again...")
            attempt += 1
            file_name = add_suffix_to_file_name(file_name=file_name, suffix=f" ({attempt})")
        except Exception as error_message:
            raise(error_message)
    return file_name

def main() -> None:
    logger.info(msg="Starting...")
    try:
        client: StorageScholarsClient = get_client()
        logger.info(msg=f"Connected to Storage Scholars client")

        old_rows, fieldnames = get_rows_and_fieldnames(ORDER_IDS_FILE_NAME)
        logger.info(msg=f"Getting details for {len(old_rows)} order(s)")

        new_rows = get_updated_rows(client=client, old_rows=old_rows)
        logger.info(msg=f"Updated details of {len(new_rows)} order(s).")

        output_file_name = add_suffix_to_file_name(ORDER_IDS_FILE_NAME, "_output")
        file_name = write_to_csv(output_file_name, new_rows)
        logger.info(msg=f"Saved rows to {file_name}.")
    except Exception as error_message:
        logger.exception(msg=error_message)
    logger.info(msg="Finished")

if __name__ == '__main__':
    main()
