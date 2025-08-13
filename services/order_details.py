
"""
Business logic for fetching and transforming order details.
"""

from typing import Any, List, Dict
from alive_progress import alive_bar
import logging
import time

from utils.comments import generate_comments
from utils.parsing import parse_phone, parse_full_location
from utils.openai import ask_openai
from services.client import StorageScholarsClient

REQUEST_DELAY = 0.3

logger = logging.getLogger(__name__)

def get_order_id(row: Dict[str, Any]) -> int:
    """
    Extracts the order ID from a row dictionary.

    Args:
        row (Dict[str, Any]): The row containing order data.

    Returns:
        int: The order ID.

    Raises:
        ValueError: If the order ID is missing or invalid.
    """
    order_id_str = row.get("OrderID") or row.get(next(iter(row)))
    if order_id_str is not None and str(order_id_str).isdigit():
        return int(order_id_str)
    raise ValueError("Row does not have a valid order ID.")

def build_row(client: StorageScholarsClient, old_row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a new row with enriched order details.

    Args:
        client (StorageScholarsClient): The API client.
        old_row (Dict[str, Any]): The original row.

    Returns:
        Dict[str, Any]: The enriched row.
    """
    order_id = get_order_id(old_row)
    first_name = (old_row.get("FullName") or "").split(" ")[0]
    pronunciation = ask_openai(
        f"In one word, no fluff, give me the pronunciation of the first name {first_name}"
    ) or ""

    items = client.fetch_items(order_id=order_id)
    items_text = ", ".join(
        f"{item['Quantity']}x {item['ItemTitle']}" for item in items
    ) if items else ""

    dropoff_info = client.fetch_dropoff_info(order_id)
    storage_unit = (
        f"{dropoff_info.get('StorageUnitName', '')} {dropoff_info.get('Quadrant', '')}".strip()
        if dropoff_info else ""
    )

    image_file_names = client.fetch_images(order_id)

    return {
        "ID": old_row.get("OrderID"),
        "Name": old_row.get("FullName"),
        "Pronunciation": pronunciation,
        "Phone": parse_phone(old_row.get("StudentPhone")),
        "Location": parse_full_location(old_row),
        "Ct.": old_row.get("ItemCount"),
        "Items": items_text,
        "Time Loaded": "",
        "Time Arrived": "",
        "Time Delivered": "",
        "Storage Unit": storage_unit,
        "Parent Phone": parse_phone(old_row.get("ParentPhone")),
        "Image Ct.": len(image_file_names),
        "Comments": generate_comments(client=client, data=old_row),
    }

def get_updated_rows(client: StorageScholarsClient, old_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes a list of order rows and returns enriched rows.

    Args:
        client (StorageScholarsClient): The API client.
        old_rows (List[Dict[str, Any]]): The original rows.

    Returns:
        List[Dict[str, Any]]: The enriched rows.
    """
    new_rows: List[Dict[str, Any]] = []
    with alive_bar(len(old_rows), title="Fetching orders") as bar:
        for idx, old_row in enumerate(old_rows):
            try:
                new_row = build_row(client, old_row)
                new_rows.append(new_row)
            except Exception as error:
                logger.warning(f"Failed to fetch details for row #{idx}: {error}")
            bar()
            time.sleep(REQUEST_DELAY)
    logger.info(f"Updated details of {len(new_rows)} order(s).")
    return new_rows
