
"""
Script to fetch and update order details, saving results to a new CSV file.
"""

import logging
import os
from services.client import StorageScholarsClient
from services.order_details import get_updated_rows
from utils.csv import get_rows, write_to_csv, add_suffix_to_file_name

ORDER_IDS_FILE_NAME = "data\\order_ids_8-21-25.csv"

def main() -> None:
    """
    Main entry point for fetching and updating order details.
    Reads order IDs from a CSV, fetches details, and writes results to a new CSV.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)

    ss_api_key = os.getenv("SS_API_KEY")
    if not ss_api_key:
        logger.error("SS_API_KEY environment variable not set.")
        raise EnvironmentError("SS_API_KEY environment variable not set.")

    client = StorageScholarsClient(api_key=ss_api_key)
    old_rows = get_rows(ORDER_IDS_FILE_NAME)
    new_rows = get_updated_rows(client, old_rows)
    output_file_name = add_suffix_to_file_name(ORDER_IDS_FILE_NAME, "_output")
    write_to_csv(output_file_name, new_rows)
    logger.info(f"Order details written to {output_file_name}")

if __name__ == "__main__":
    main()
