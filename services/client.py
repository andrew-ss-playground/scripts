import requests
from typing import Any
import logging

LOG_LEVEL = logging.INFO

logger = logging.getLogger(name=__name__)

class StorageScholarsClient:
    def __init__(self, api_key: str) -> None:
        """Initialize the client

        Args:
            api_key (str): Bearer token for authorization
        """

        self.BASE_URL: str = "https://api.storagescholars.com"
        self.TIMEOUT_DURATION: int = 10
        self.session: requests.Session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Referer': 'https://signup.storagescholars.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Brave";v="139", "Chromium";v="139"',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-mobile': '?0',
        })

    def get_request(self, url: str, params: dict[str, Any] = {}) -> list[dict[str, Any]] | None:
        """Sends a get request with the client

        Args:
            url (str): URL to send the request to
            params (dict[str, Any], optional): Dictionary of parameters. Defaults to {}.

        Returns:
            Any: JSON dictionary of request response. None if errors.
        """
        try:
            url = f"{self.BASE_URL}{url}"
            response: requests.Response = self.session.get(url=url, params=params, timeout=self.TIMEOUT_DURATION)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error_message:
            logger.exception(msg=f"Get request failed: {error_message}")
        except Exception as error_message:
            logger.exception(msg=f"Unexpected error: {error_message}")
