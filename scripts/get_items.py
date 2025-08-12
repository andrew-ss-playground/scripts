from threading import TIMEOUT_MAX
from services.client import StorageScholarsClient
import os
from dotenv import load_dotenv
import logging
from typing import Any
import csv
import time
from alive_progress import alive_bar

LOG_LEVEL = logging.INFO
ORDER_ID_FILE_NAME = "data\\order_ids_8-21-25.csv"
REQUEST_DELAY = 0.3
DELAY_MIN_REQUESTS = 50

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(name=__name__)

def add_suffix_to_file_name(file_name, suffix):
    parts = ORDER_ID_FILE_NAME.split(".")
    return f"{parts[0]}{suffix}.{parts[1]}"

def get_client() -> StorageScholarsClient:
    load_dotenv()
    api_key: str | None = os.getenv(key="SS_API_KEY")
    if api_key is None:
        raise Exception("Missing api key")

    return StorageScholarsClient(api_key=api_key)

def get_order_ids_from_csv(file_name: str) -> list[int]:
    order_ids: list[int] = []
    try:
        with open(file=file_name, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                order_id_str = row.get("OrderID") or row.get(next(iter(row)))  # fallback to first column if no header
                if order_id_str and order_id_str.isdigit():
                    order_ids.append(int(order_id_str))
    except FileNotFoundError:
        raise Exception(f"Order ID list file not found: {file_name}")
    except Exception as error_message:
        raise Exception(f"Could not get order ids from {file_name}: {error_message}")

    if len(order_ids) == 0:
        raise Exception("No order IDs found.")

    return order_ids

def fetch_item_description(client: StorageScholarsClient, order_id: int) -> str:
    items: list[dict[str, Any]] = client.get_request(url=f"/order/items/{order_id}")
    if len(items) == 0:
        raise Exception("Items is None")
    return ", ".join([f"{item['Quantity']}x {item['ItemTitle']}" for item in items])

def save_items_to_csv(file_name: str, rows: list[dict[str, int | str]]) -> None:
    attempt = 0
    while True:
        try:
            with open(file=file_name, mode="w", newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            return
        except PermissionError:
            logger.warning(f"Could not write to {file_name}, trying again...")
            attempt += 1
            file_name = add_suffix_to_file_name(file_name=file_name, suffix=f" ({attempt})")
        except Exception as error_message:
            raise(error_message)

def main() -> None:
    logger.info(msg="Starting...")
    try:
        client: StorageScholarsClient = get_client()

        order_ids: list[int] = get_order_ids_from_csv(file_name=ORDER_ID_FILE_NAME)
        logger.info(msg=f"Getting items for {len(order_ids)} order(s)")

        rows: list[dict[str, int | str]] = []
        with alive_bar(len(order_ids), title="Fetching orders") as bar:
            for order_id in order_ids:
                item_description = fetch_item_description(client=client, order_id=order_id)
                rows.append({"order_id": order_id, "items": item_description})
                bar()
                time.sleep(REQUEST_DELAY if len(order_ids) >= DELAY_MIN_REQUESTS else 0)

        output_file_name = add_suffix_to_file_name(file_name=ORDER_ID_FILE_NAME, suffix="_output")
        save_items_to_csv(file_name=output_file_name, rows=rows)
        logger.info(msg=f"Saved items of {len(order_ids)} order(s) to {output_file_name}")
    except Exception as error_message:
        logger.exception(msg=error_message)
    logger.info(msg="Finished")

if __name__ == '__main__':
    main()
