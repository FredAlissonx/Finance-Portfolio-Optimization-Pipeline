from sec_edgar_downloader import Downloader
from utils.config import bronze_logger
from email_validator import validate_email, EmailNotValidError
import os

class SecEdgarData:
    """
    A class to handle downloading SEC filings using the sec_edgar_downloader library.

    This class validates company credentials (name and email), ensures the download directory
    exists, and provides methods to download SEC filings for a list of ticker symbols and filing types.
    
    Attributes:
        DOWNLOAD_PATH (str): The local directory path where SEC filings will be stored.
    """
    DOWNLOAD_PATH: str = "sec-fillings"

    @classmethod
    def _validate_company_name(self, name: str) -> str:
        """
        Validate and normalize the company name from the environment variable.

        Args:
            name (str): The raw company name obtained from the environment variable.

        Returns:
            str: The validated and stripped company name.

        Raises:
            ValueError: If the company name is not set or is empty.
        """
        if not name:
            bronze_logger.error("Company name environment variable (SEC_EDGAR_NAME) not set")
            raise ValueError("SEC_EDGAR_NAME environment variable required")
            
        stripped_name = name.strip()
        if not stripped_name:
            bronze_logger.error("Company name cannot be empty")
            raise ValueError("Company name cannot be empty")
            
        return stripped_name

    @classmethod
    def _validate_company_email_address(self, email: str) -> str:
        """
        Validate and normalize the company email address from the environment variable.

        Args:
            email (str): The raw email address obtained from the environment variable.

        Returns:
            str: The validated email address.

        Raises:
            ValueError: If the email environment variable is not set or the email is invalid.
        """
        if not email:
            bronze_logger.error("Email environment variable (SEC_EDGAR_EMAIL) not set")
            raise ValueError("SEC_EDGAR_EMAIL environment variable required")

        try:
            validated = validate_email(email, check_deliverability=False)
            return validated.email
        except EmailNotValidError as e:
            bronze_logger.error(f"Invalid email format: {e}")
            raise ValueError(f"Invalid email address: {email}") from e

    @classmethod
    def _get_download_path(self) -> str:
        """
        Ensure that the download directory exists, creating it if necessary.

        Returns:
            str: The download path where SEC filings will be stored.
        """
        if not os.path.exists(self.DOWNLOAD_PATH):
            os.makedirs(self.DOWNLOAD_PATH)
        return self.DOWNLOAD_PATH

    @classmethod
    def get_downloader(self) -> Downloader:
        """
        Create and return a SEC Downloader instance using validated credentials.

        This method retrieves and validates the company name and email from the environment,
        ensures the download directory exists, and then creates an instance of Downloader.

        Returns:
            Downloader: A configured Downloader instance ready to fetch SEC filings.

        Raises:
            ValueError: If any required configuration (company name or email) is missing or invalid.
        """
        try:
            company_name = self._validate_company_name(os.getenv("SEC_EDGAR_NAME"))
            email = self._validate_company_email_address(os.getenv("SEC_EDGAR_EMAIL"))
            
            bronze_logger.info("Creating SEC Downloader with valid credentials")
            return Downloader(
                company_name=company_name,
                email_address=email,
                download_folder=self._get_download_path()
            )
        except ValueError as e:
            bronze_logger.critical(f"Configuration error: {e}")
            raise
    
    @classmethod
    def download_filings(self, tickers: list[str], filing_types: dict, filings_per_ticker: int) -> None:
        """
        Download a specified number of filings for each filing type for each ticker in the given list.

        Args:
            tickers (list[str]): A list of ticker symbols (e.g., ["AAPL", "MSFT"]).
            filing_types (dict): A dictionary mapping a descriptive filing name to its SEC form code.
                                 For example: {"10-K": "10-K", "10-Q": "10-Q", "8-K": "8-K", ...}
            filings_per_ticker (int): The number of filings to download per filing type for each ticker.

        Returns:
            None

        Side Effects:
            Downloads SEC filings and logs messages indicating success or errors.
        """
        dl = self.get_downloader()
        for ticker in tickers:
            bronze_logger.info(f"Processing ticker: {ticker}")
            for description, form_code in filing_types.items():
                bronze_logger.info(f"Downloading {description} filings for {ticker} (limit: {filings_per_ticker})...")
                try:
                    dl.get(form_code, ticker, limit=filings_per_ticker)
                    bronze_logger.info(f"Successfully downloaded {filings_per_ticker} {description} filings for {ticker}.")
                except Exception as e:
                    bronze_logger.error(f"Error downloading {description} filings for {ticker}: {e}")

if __name__ == "__main__":
    sec_data = SecEdgarData()

    filing_types = {
        "10-K": "10-K",
        "10-Q": "10-Q",
        "8-K": "8-K",
        "Form 4 (Insider Trading)": "4",
        "Proxy Statements (DEF 14A)": "DEF 14A"
    }
    
    tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "FB"]

    filings_per_ticker = 5

    sec_data.download_filings(tickers, filing_types, filings_per_ticker)
    print("Download complete")
