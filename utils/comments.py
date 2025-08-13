
"""
Comment generation utilities for order processing.
"""

import logging
from typing import Any
from services.client import StorageScholarsClient
from utils.parsing import parse_phone, parse_int

logger = logging.getLogger(__name__)

def generate_comments(client: StorageScholarsClient, data: dict[str, Any]) -> str:
    """
    Generate a summary comment string for an order row.

    Args:
        client (StorageScholarsClient): The API client.
        data (dict[str, Any]): The order row data.

    Returns:
        str: The generated comments string.
    """
    comments = []
    
    if str(data.get("Cancelled", "0")) == "1":
        comments.append("Order was canceled.")
    if str(data.get("Deleted", "0")) == "1":
        comments.append("Order was deleted.")
    
    dropoff_name = data.get("DropoffPersonName")
    dropoff_phone = data.get("DropoffPersonPhone")
    if dropoff_name and dropoff_phone:
        formatted_phone = parse_phone(dropoff_phone)
        comments.append(f"Call proxy {dropoff_name} at {formatted_phone}")
    
    balance = parse_int(data.get("Balance"))
    if balance is not None and balance > 0:
        comments.append("Call customer to pay pending balance.")
    
    order_id = data.get("OrderID")
    if order_id is not None:
        try:
            internal_notes = client.fetch_internal_notes(order_id)
            comments.extend(internal_notes)
        except Exception as e:
            logger.warning(f"Failed to fetch internal notes for order {order_id}: {e}")
    
    return " ".join(comments)
