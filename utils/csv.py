
"""
CSV utility functions for reading and writing order data.
"""

import csv
import logging
from typing import Any, List, Dict

logger = logging.getLogger(__name__)

def get_rows(file_name: str) -> List[Dict[str, Any]]:
    """
    Read rows from a CSV file into a list of dictionaries.

    Args:
        file_name (str): The path to the CSV file.

    Returns:
        List[Dict[str, Any]]: List of row dictionaries.

    Raises:
        Exception: If no data or headers are found in the CSV.
    """
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    if not rows:
        raise Exception("No data or headers found in input CSV.")
    logger.info(f"Getting details for {len(rows)} order(s)")
    return rows

def write_to_csv(file_name: str, rows: List[Dict[str, Any]]) -> str:
    """
    Write a list of dictionaries to a CSV file. If the file is locked, try a new filename.

    Args:
        file_name (str): The path to the CSV file.
        rows (List[Dict[str, Any]]): The rows to write.

    Returns:
        str: The filename used for writing.

    Raises:
        Exception: If writing fails for reasons other than file lock.
    """
    if not rows:
        raise ValueError("No rows to write to CSV.")
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
            logger.error(f"Failed to write to CSV: {error_message}")
            raise
    logger.info(f"Saved rows to {file_name}.")
    return file_name

def add_suffix_to_file_name(file_name: str, suffix: str) -> str:
    """
    Add a suffix to a filename before the extension.

    Args:
        file_name (str): The original filename.
        suffix (str): The suffix to add.

    Returns:
        str: The new filename with the suffix.
    """
    parts = file_name.rsplit(".", 1)
    if len(parts) == 2:
        return f"{parts[0]}{suffix}.{parts[1]}"
    else:
        return f"{file_name}{suffix}"
