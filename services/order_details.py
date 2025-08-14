
"""
Business logic for fetching and transforming order details.
"""

from typing import Any, List, Dict
from alive_progress import alive_bar
import logging

from utils.comments import generate_comments
from utils.parsing import parse_phone, parse_full_location, parse_date
from utils.openai import ask_openai
from services.client import StorageScholarsClient
from config import IS_FETCH_IMAGES, IS_FETCH_OPENAI, IS_FETCH_ITEMS

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
    dropoff_info = client.fetch_dropoff_info(order_id)
    storage_unit = (
        f"{dropoff_info.get('StorageUnitName', '')} {dropoff_info.get('Quadrant', '')}".strip()
        if dropoff_info else ""
    ) or ""
    pronunciation = ask_openai(
        f"In one word, no fluff, give me the pronunciation of the first name {dropoff_info.get("FirstName")}"
    ) or "" if IS_FETCH_OPENAI else ""

    items = client.fetch_items(order_id=order_id) if IS_FETCH_ITEMS else []
    items_text = ", ".join(
        f"{item['Quantity']}x {item['ItemTitle']}" for item in items
    ) if items else ""

    image_file_names = client.fetch_images(order_id) if IS_FETCH_IMAGES else []

    return {
        "ID": dropoff_info.get("OrderID"),
        "Name": f"{dropoff_info.get("FirstName")} {dropoff_info.get("LastName")}",
        "Pronunciation": pronunciation,
        "Phone": parse_phone(dropoff_info["StudentPhone"]) if dropoff_info.get("StudentPhone") else "",
        "Location": parse_full_location(dropoff_info),
        "Ct.": len(items),
        "Items": items_text,
        "Dropoff Date": parse_date(dropoff_info["DropoffDate"]) if dropoff_info.get("DropoffDate") else "",
        "Time Loaded": "",
        "Time Arrived": "",
        "Time Delivered": "",
        "Storage Unit": storage_unit,
        "Parent Phone": parse_phone(dropoff_info["ParentPhone"]) if dropoff_info.get("ParentPhone") else "",
        "Image Ct.": len(image_file_names),
        "Comments": generate_comments(client=client, old_data=old_row, new_data=dropoff_info),
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
    logger.info(f"Updated details of {len(new_rows)} order(s).")
    return new_rows
