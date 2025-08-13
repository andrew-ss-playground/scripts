from typing import Any, Optional
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

def parse_phone(raw_phone: Any) -> Optional[str]:
    """
    Parse a phone number into (XXX) XXX-XXXX format.

    Args:
        raw_phone (Any): The raw phone input.

    Returns:
        Optional[str]: Formatted phone number, or None if invalid.
    """
    digits = ''.join(filter(str.isdigit, str(raw_phone or "")))
    if digits.startswith('1') and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        logger.warning(f"Invalid phone number: {raw_phone}")
        return None
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

def parse_full_location(row: dict[str, Any]) -> str:
    """
    Concatenate location fields into a single string, omitting empty or irrelevant parts.

    Args:
        row (dict): Dictionary containing location fields.

    Returns:
        str: Concatenated location string.
    """
    dropoff_parts = [
        row.get("DropoffLocation"),
        row.get("DropoffDormRoomNumber"),
        row.get("DropoffDormRoomLetter"),
        row.get("DropoffAddressLine1"),
        row.get("DropoffAddressLine2"),
    ]
    return " ".join(
        str(part) for part in dropoff_parts
        if part not in (None, "", "None", "Off-Campus")
    ).strip()

def parse_file_type(filepath: str) -> str:
    """
    Extract the file extension from a filepath.

    Args:
        filepath (str): The file path.

    Returns:
        str: The file extension.

    Raises:
        ValueError: If the file type is missing.
    """
    if "." in filepath:
        return filepath.split(".")[-1]
    else:
        logger.error(f"Filepath missing file type: {filepath}")
        raise ValueError(f"{filepath} is missing a file type")

def parse_date(val: Any) -> Optional[date]:
    """
    Parse a value into a date object.

    Args:
        val (Any): The value to parse.

    Returns:
        Optional[date]: The parsed date, or None if parsing fails.
    """
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(val, fmt).date()
            except Exception:
                continue
        logger.warning(f"Could not parse date from value: {val}")
    return None

def parse_int(val: Any) -> Optional[int]:
    """
    Parse a value into an integer, returning None if zero or invalid.

    Args:
        val (Any): The value to parse.

    Returns:
        Optional[int]: The parsed integer, or None if invalid or zero.
    """
    try:
        i = int(val)
        return i if i != 0 else None
    except (TypeError, ValueError):
        logger.warning(f"Could not parse int from value: {val}")
        return None
