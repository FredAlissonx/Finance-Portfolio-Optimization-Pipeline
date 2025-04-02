from utils.config import bronze_logger
from utils.api_utils import APIUtils

class FredAPIFetch(APIUtils):
    """
    A class to fetch economic data series observations from the Federal Reserve Economic Data (FRED) API.

    This class inherits from APIUtils and provides methods to prepare query parameters,
    fetch data for a single series, and batch fetch data for multiple series.
    """
    BASE_URL: str = "https://api.stlouisfed.org/fred/series/observations"
    
    @classmethod
    def _setup_params(
        cls,
        series_id: str,
        observation_start: str = None,
        observation_end: str = None,
        frequency = None
        ) -> dict[str, str]:
        """
        Prepare the query parameters for the FRED API request.

        Constructs a dictionary of parameters required by the FRED API, including the series
        identifier and optional parameters such as observation start/end dates and frequency.

        Args:
            series_id (str): The unique identifier for the economic data series.
            observation_start (Optional[str]): The start date for the observations (YYYY-MM-DD). Defaults to None.
            observation_end (Optional[str]): The end date for the observations (YYYY-MM-DD). Defaults to None.
            frequency (Optional[str]): The data frequency (e.g., 'daily', 'monthly'). Defaults to None.

        Returns:
            dict[str]: A dictionary of parameters to be sent with the API request.
        """
        params =  {
            "series_id": series_id,
            "api_key": cls._get_api_key("API_FREDAPI_KEY"),
            "file_type": "json"
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        if frequency:
            params["frequency"] = frequency
            
        return params

    @classmethod
    def fetch_data(cls, series_id: str) -> list:
        """
        Fetch observations data for a specified FRED series.

        This method prepares the request parameters for a given series ID, calls the API using
        the parent class method, and validates the response. It returns the list of observations
        for the series.

        Args:
            series_id (str): The unique identifier for the economic data series.

        Returns:
            list[dict[str]]: A list of observations from the FRED API. If no observations
            are found or an error occurs, an empty list is returned.
        """
        params = cls._setup_params(series_id=series_id)
        data =  cls._fetch_data(params=params).get("observations", [])
        super()._validate_response(data = data, symbol = series_id)
        return data
    
    @classmethod
    def fetch_batch_series(cls, series_ids: list[str]) -> dict:
        """
        Fetch observations data for multiple FRED series.

        Iterates over a list of series IDs, fetches the data for each series, and compiles the results
        into a dictionary mapping each series ID to its respective list of observations.

        Args:
            series_ids (list[str]): A list of unique identifiers for economic data series.

        Returns:
            dict[str, list[dict[str]]]: A dictionary where keys are series IDs and values are lists
            of observations for each series.
        """
        result = {}
        for series_id in series_ids:
            bronze_logger.info(f"Fetching data for series id: {series_id}")
            data = cls.fetch_data(series_id=series_id)
            result[series_id] = data
        return result