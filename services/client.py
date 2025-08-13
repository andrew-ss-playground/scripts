import requests
from typing import Any, Optional
import logging
import os
import time
from utils.parsing import parse_file_type, parse_date

logger = logging.getLogger(__name__)

BASE_URL = "https://api.storagescholars.com"
IMAGES_DIR = os.path.join("data", "images")
TIMEOUT_DURATION = 10
REQUEST_DELAY = 0.3

class StorageScholarsClientError(Exception):
    """Custom exception for StorageScholarsClient errors."""

class StorageScholarsClient:
    def __init__(self, api_key: str) -> None:
        """
        Initialize the StorageScholarsClient.

        Args:
            api_key (str): Bearer token for authorization.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Referer': 'https://signup.storagescholars.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-mobile': '?0',
        })

    def _get_request(self, url: str, params: Optional[dict[str, Any]] = None) -> Any:
        """
        Send a GET request.

        Args:
            url (str): Endpoint URL (relative to BASE_URL).
            params (Optional[dict[str, Any]]): Query parameters.

        Returns:
            Any: JSON response.

        Raises:
            StorageScholarsClientError: On request failure.
        """
        full_url = f"{BASE_URL}{url}"
        try:
            logger.debug(f"GET {full_url} params={params}")
            response = self.session.get(full_url, params=params, timeout=TIMEOUT_DURATION)
            response.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise StorageScholarsClientError(f"Get request failed: {e}")

    def _download_image(self, image_url: str, file_name: str) -> str:
        """
        Download an image from a URL and save it locally.

        Args:
            image_url (str): The image URL.
            file_name (str): The local file path.

        Returns:
            str: The saved file path.

        Raises:
            StorageScholarsClientError: On download failure.
        """
        try:
            response = requests.get(image_url, timeout=TIMEOUT_DURATION)
            response.raise_for_status()
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, "wb") as f:
                f.write(response.content)
            logger.debug(f"Downloaded image to {file_name}")
            return file_name
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            raise StorageScholarsClientError(f"Failed to download image: {e}")

    def fetch_dropoff_info(self, order_id: int) -> dict[str, Any]:
        """
        Fetch dropoff info for an order.

        Args:
            order_id (int): The order ID.

        Returns:
            dict[str, Any]: Dropoff info.

        Raises:
            StorageScholarsClientError: If info is missing.
        """
        dropoff_info = self._get_request("/worklist/dropoff", params={'OrderID': order_id})
        if not dropoff_info or not dropoff_info.get('StorageUnitName') or not dropoff_info.get('Quadrant'):
            logger.warning(f"Could not get storage unit info for order {order_id}")
            raise StorageScholarsClientError(f"Could not get storage unit info for order {order_id}")
        return dropoff_info

    def fetch_items(self, order_id: int) -> list[dict[str, Any]]:
        """
        Fetch items for an order, aggregating identical items by ItemTitle.

        Args:
            order_id (int): The order ID.

        Returns:
            list[dict[str, Any]]: List of aggregated items.

        Raises:
            StorageScholarsClientError: If items are missing.
        """
        items = self._get_request(f"/order/items/{order_id}")
        if not items:
            logger.warning(f"No items found for order {order_id}")
            raise StorageScholarsClientError(f"Could not get items for order {order_id}")

        # Aggregate items by ItemTitle
        aggregated = {}
        for item in items:
            title = item.get("ItemTitle", "Unknown")
            qty = int(item.get("Quantity", 1))
            if title in aggregated:
                aggregated[title]["Quantity"] += qty
            else:
                aggregated[title] = {"ItemTitle": title, "Quantity": qty}
            
        return list(aggregated.values())

    def fetch_images(self, order_id: int) -> list[str]:
        """
        Fetch and download images for an order.

        Args:
            order_id (int): The order ID.

        Returns:
            list[str]: List of local image file paths.

        Raises:
            StorageScholarsClientError: If images are missing.
        """
        image_file_names = []
        image_datas = self._get_request("/order/images", params={"orderID": order_id})
        if not image_datas:
            logger.warning(f"No images found for order {order_id}")
            raise StorageScholarsClientError(f"No images found for order {order_id}")

        os.makedirs(IMAGES_DIR, exist_ok=True)
        for image_index, image_dict in enumerate(image_datas, start=1):
            image_url = image_dict.get("ImageURL")
            file_ext = parse_file_type(image_dict.get("Filepath", ""))
            file_name = os.path.join(IMAGES_DIR, f"{order_id}_{image_index}.{file_ext}")
            file_name = self._download_image(image_url, file_name)
            image_file_names.append(file_name)

        return image_file_names

    def fetch_internal_notes(self, order_id: int) -> list[str]:
        """
        Fetch internal notes for an order.

        Args:
            order_id (int): The order ID.

        Returns:
            list[str]: List of formatted internal notes.
        """
        internal_notes = []
        internal_notes_data = self._get_request(f"/order/internalNote/{order_id}")
        if internal_notes_data:
            for note in internal_notes_data:
                comment = note.get('Comment', '')
                username = note.get('AddedByUserName', 'Unknown')
                created_date = parse_date(note.get('CreatedDate'))
                is_deleted = note.get('Deleted') == '1'
                note_str = f"{'DELETED ' if is_deleted else ''}Internal note by {username} on {created_date}: {comment}{'' if comment.endswith('.') else '.'}"
                internal_notes.append(note_str)
        return internal_notes
