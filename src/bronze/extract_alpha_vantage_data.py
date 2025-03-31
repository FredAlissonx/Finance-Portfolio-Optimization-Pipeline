from typing import Optional, Dict, List
from utils.config import bronze_logger
from utils.api_utils import APIUtils
import time

class AlphaVantageAPIFetcher(APIUtils):
    """
    A class to fetch historical options and overview data from the Alpha Vantage API.

    This class inherits from APIUtils and provides methods to prepare query parameters,
    fetch data for a single symbol, and batch fetch data for multiple symbols.
    """

    BASE_URL: str = "https://www.alphavantage.co/query"
    RATE_LIMIT_DELAY: int = 15
    SUPPORTED_FUNCTIONS: List[str] = ["HISTORICAL_OPTIONS", "OVERVIEW"]
    
    @classmethod
    def _setup_params(cls, symbol: str, function: str) -> Dict:
        """
        Prepare the parameters required for the Alpha Vantage API request.

        Constructs a dictionary of parameters needed by the Alpha Vantage API, including the function type,
        symbol, API key, and output size if the function is HISTORICAL_OPTION.

        Args:
            symbol (str): The stock symbol for which to fetch data.
            function (str): Function to get data, can be HISTORICAL_OPTION or OVERVIEW.

        Returns:
            Dict[str, str]: A dictionary of parameters to be sent with the API request.
        """
        if function not in cls.SUPPORTED_FUNCTIONS:
            raise ValueError(
                f"Unsupported function: {function}. Valid option: {cls.SUPPORTED_FUNCTIONS}"
            )
        api_key = cls._get_api_key(name_key="API_ALPHA_VANTAGE_KEY")
        params: dict = {
            "function": function,
            "symbol": symbol,
            "apikey": api_key,
        }
        
        if function == "HISTORICAL_OPTIONS":
            params["outputsize"] = "full"
        
        return params

    @classmethod
    def fetch_data(cls, symbol: str, function: str) -> Optional[Dict]:
        """
        Fetch historical options data for the given symbol from the Alpha Vantage API.

        This method prepares the request parameters for a given symbol, calls the API using
        the parent class method, and validates the response.

        Args:
            symbol (str): The stock symbol for which to fetch data.
            function (str): Function to get data, can be HISTORICAL_OPTION or OVERVIEW.

        Returns:
            Optional[Dict]: A dictionary containing the API data if successful; otherwise, None.
        """
        params = cls._setup_params(symbol, function)
        raw_data = cls._fetch_data(params = params)
        validate_data = super()._validate_response(data = raw_data, symbol = symbol)
        
        return validate_data
        
    @classmethod
    def fetch_batch_data(cls, symbols: List[str], function: str) -> Dict[str, Optional[Dict]]:
        """
        Fetch historical options data for multiple symbols from the Alpha Vantage API.

        Iterates over a list of symbols, fetches the data for each symbol based on the function, and compiles the results
        into a dictionary mapping each symbol to its respective data and their index for rate limit.

        Args:
            symbols (List[str]): A list of stock symbols for which to fetch data.
            function (str): Function to get data, can be HISTORICAL_OPTION or OVERVIEW.
        Returns:
            Dict[str, Optional[Dict]]: A dictionary where keys are symbols and values are the corresponding
            data dictionaries. If data retrieval fails for a symbol, its value will be None.
        """
        results: dict = {}
        for idx, symbol in enumerate(symbols):
            bronze_logger.info(f"Processing {symbol} ({idx+1}/{len(symbols)})")
            results[symbol] = cls.fetch_data(symbol, function)
            
            if (idx + 1) % 5 == 0:
                bronze_logger.debug(f"Rate limit throttle: Waiting {cls.RATE_LIMIT_DELAY}s")
                time.sleep(cls.RATE_LIMIT_DELAY)
            
        return results

if __name__ == "__main__":
    import pandas as pd
    try:
        data = AlphaVantageAPIFetcher.fetch_data(
            symbol="AAPL",
            function="OVERVIEW"  # Corrected function name
        )
        if data:
            # Adjust key access based on the actual response structure.
            print(f"Successfully retrieved {data['data'][0]['symbol']} options data")
        else:
            print("Failed to retrieve data")
            
        # Batch processing example
        batch_data = AlphaVantageAPIFetcher.fetch_batch_data(
            symbols=["MSFT", "GOOGL", "AMZN"],
            function="OVERVIEW"
        )
        print(f"Processed {len(batch_data)} symbols")
        df = pd.DataFrame(data["data"])
        print(df)
    except Exception as e:
        bronze_logger.critical(f"Application error: {str(e)}")

    