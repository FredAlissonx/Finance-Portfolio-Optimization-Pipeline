import requests
import os
from typing import Dict, Optional, Any
from utils.config import bronze_logger, session

class APIUtils:
    """
    A utility class for handling API interactions.

    This class provides methods to retrieve API keys from environment variables,
    perform GET requests to specified APIs, and validate API responses.
    """

    BASE_URL = ""
    DEFAULT_TIMEOUT: tuple = (5, 25)

    @classmethod
    def _get_api_key(cls, name_key: str) -> str:
        """
        Retrieve the API key from environment variables.

        Args:
            name_key (str): The name of the environment variable containing the API key.

        Returns:
            str: The API key retrieved from the environment variable.

        Raises:
            ValueError: If the API key is not found in the environment variables.
        """
        _API_KEY = os.getenv(name_key)
        if _API_KEY is None:
            bronze_logger.error(f"{name_key} API key is missing. Please check your environment variables.")
            raise ValueError("API Key missing.")
        return _API_KEY

    @classmethod
    def _fetch_data(cls, params: Dict[str, Any]) -> Optional[Dict]:
        """
        Perform a GET request to the API with the given parameters.

        Args:
            params (Dict[str, Any]): The query parameters to include in the API request.

        Returns:
            Optional[Dict]: The JSON response from the API as a dictionary if successful; otherwise, None.

        Raises:
            requests.exceptions.RequestException: If the request fails due to network issues or invalid responses.
            ValueError: If the response cannot be parsed as JSON.
        """
        try:
            bronze_logger.info(f"Fetching data from {cls.BASE_URL}.")
            response = session.get(cls.BASE_URL, params=params, timeout=cls.DEFAULT_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            bronze_logger.info("Data fetched successfully.")
            return data
        except (requests.exceptions.RequestException, ValueError) as e:
            bronze_logger.error(f"Request failed: {e}")
            return None

    @classmethod
    def _validate_response(cls, data: Optional[Dict[str, Any]], symbol: str) -> Optional[Dict[str, Any]]:
        """
        Validate the API response data for errors or warnings.

        Args:
            data (Optional[Dict[str, Any]]): The API response data to validate.
            symbol (str): The symbol associated with the API request (e.g., stock ticker or series ID).

        Returns:
            Optional[Dict[str, Any]]: The validated data if no errors or warnings are found; otherwise, None.
        """
        if data is None:
            bronze_logger.error(f"No data returned for {symbol}.")
            return None
        if "Error Message" in data:
            bronze_logger.error(f"Error fetching data for {symbol}: {data['Error Message']}")
            return None
        if "Note" in data:
            bronze_logger.warning(f"Rate limit hit for {symbol}: {data['Note']}")
            return None
        return data
