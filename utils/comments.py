
"""
Comment generation utilities for order processing.
"""

import logging
from typing import Any
from services.client import StorageScholarsClient
from utils.parsing import parse_phone, parse_int
from config import IS_FETCH_INTERNAL_NOTES

logger = logging.getLogger(__name__)

def generate_comments(client: StorageScholarsClient, old_data, new_data: dict[str, Any]) -> str:
    """
    Generate a summary comment string for an order row.

    Args:
        client (StorageScholarsClient): The API client.
        old_data (dict[str, Any]): The order row from the old .csv.
        new_data (dict[str, Any]): The order row from the fetched dropoff data.

    Returns:
        str: The generated comments string.
    """
    comments = []
    
    if str(new_data.get("Cancelled", "0")) == "1":
        comments.append("Order was canceled.")
        logger.info(f"Added custom comment for order {new_data.get("OrderID")}: Order was canceled.")
    if str(new_data.get("Deleted", "0")) == "1":
        comments.append("Order was deleted.")
        logger.info(f"Added custom comment for order {new_data.get("OrderID")}: Order was deleted.")
    
    dropoff_name = new_data.get("DropoffPersonName")
    dropoff_phone = new_data.get("DropoffPersonPhone")
    if dropoff_name and dropoff_phone:
        formatted_phone = parse_phone(dropoff_phone)
        comments.append(f"Call proxy {dropoff_name} at {formatted_phone}.")
        logger.info(f"Added custom comment for order {new_data.get("OrderID")}: Call proxy {dropoff_name} at {formatted_phone}.")
    
    balance = parse_int(old_data.get("Balance"))
    if balance is not None and balance > 0:
        comments.append("Call customer to pay pending balance.")
        logger.info(f"Added custom comment for order {new_data.get("OrderID")}: Call customer to pay pending balance.")
    
    order_id = new_data.get("OrderID")
    if order_id is not None:
        try:
            internal_notes = client.fetch_internal_notes(order_id) if IS_FETCH_INTERNAL_NOTES else []
            comments.extend(internal_notes)
        except Exception as e:
            logger.warning(f"Failed to fetch internal notes for order {order_id}: {e}")
    
    return " ".join(comments)
