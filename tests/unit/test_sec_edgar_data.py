import pytest
import os
from src.bronze.sec_edgar_data import SecEdgarData
from sec_edgar_downloader import Downloader
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def set_credentials(monkeypatch):
    """
    Automatically set required environment variables for SEC credentials
    and ensure that any modifications to DOWNLOAD_PATH are reverted after the test.
    """
    monkeypatch.setenv("SEC_EDGAR_NAME", "name")
    monkeypatch.setenv("SEC_EDGAR_EMAIL", "address@domain.com")
    
    original_path = SecEdgarData.DOWNLOAD_PATH
    yield
    SecEdgarData.DOWNLOAD_PATH = original_path

@pytest.fixture
def fake_downloader(mocker):
    """
    Patch the Downloader class in the sec_edgar_data module and return a tuple
    of (patched_downloader_class, fake_downloader_instance) for use in tests.
    """
    patched = mocker.patch("src.bronze.sec_edgar_data.Downloader")
    fake_instance = patched.return_value
    return patched, fake_instance

class TestSecEdgarData:
    """
    Test suite for the SecEdgarData class, covering credential validation,
    download path creation, downloader instantiation, and download filings behavior.
    """
    def test_credentials_success(self):
        """
        Test that valid environment variables for SEC credentials are correctly validated.
        """
        company_name: str = SecEdgarData._validate_company_name(os.getenv("SEC_EDGAR_NAME"))
        email_address: str = SecEdgarData._validate_company_email_address(os.getenv("SEC_EDGAR_EMAIL"))
        assert company_name == "name"
        assert email_address == "address@domain.com"
    
    def test_company_name_missing(self, monkeypatch):
        """
        Test that missing SEC_EDGAR_NAME environment variable raises a ValueError.
        """
        monkeypatch.delenv("SEC_EDGAR_NAME")
        with pytest.raises(ValueError, match="SEC_EDGAR_NAME environment variable required"):
            SecEdgarData._validate_company_name(os.getenv("SEC_EDGAR_NAME"))
    
    def test_email_missing(self, monkeypatch):
        """
        Test that missing SEC_EDGAR_EMAIL environment variable raises a ValueError.
        """
        monkeypatch.delenv("SEC_EDGAR_EMAIL")
        with pytest.raises(ValueError, match="SEC_EDGAR_EMAIL environment variable required"):
            SecEdgarData._validate_company_email_address(os.getenv("SEC_EDGAR_EMAIL"))

    @pytest.mark.parametrize(
        "email, reason",
        [
            ("", "Empty email"),
            ("plainaddress", "Missing @ and domain"),
            ("@missingusername.com", "No username before @"),
            ("user@.com", "Domain missing"),
            ("user@company,com", "Invalid character ,"),
            ("user@company..com", "Double dots in domain"),
            ("user@com", "Missing valid TLD")
        ]
    )
    def test_validate_company_email_address(self, email, reason):
        """
        Test that invalid email formats raise a ValueError.
        The 'reason' parameter describes the expected error scenario.
        """
        with pytest.raises(ValueError):
            # print(reason)
            SecEdgarData._validate_company_email_address(email=email)
       
    def test_get_download_path_creates_dir(self, tmp_path):
        """
        Test that _get_download_path creates a directory if it does not exist.
        """
        test_download_dir = tmp_path / "downloads"
        assert not test_download_dir.exists()
        
        SecEdgarData.DOWNLOAD_PATH = str(test_download_dir)
        returned_path = SecEdgarData._get_download_path()
        
        assert test_download_dir.exists()
        assert returned_path == str(test_download_dir)
    
    def test_get_download_path_when_directory_exists(self, tmp_path):
        """
        Test that _get_download_path returns the directory path if it already exists.
        """
        test_download_dir = tmp_path / "downloads"
        test_download_dir.mkdir()
        SecEdgarData.DOWNLOAD_PATH = str(test_download_dir)
        returned_path = SecEdgarData._get_download_path()
        
        assert test_download_dir.exists()
        assert returned_path == str(test_download_dir)
    
    def test_get_downloader(self, tmp_path, mocker):
        """
        Test that get_downloader instantiates a Downloader with the correct credentials and download folder.
        Also, verify that the download directory is created if it does not exist.
        """
        test_download_path = tmp_path / "sec-filings"
        SecEdgarData.DOWNLOAD_PATH = str(test_download_path)
        mock_init = mocker.patch("src.bronze.sec_edgar_data.Downloader.__init__", return_value=None)
        downloader = SecEdgarData.get_downloader()
        mock_init.assert_called_once_with(
            company_name="name",
            email_address="address@domain.com",
            download_folder=str(test_download_path)
        )
        assert test_download_path.exists()
    
    def test_download_filings_success(self, mocker, fake_downloader):
        """
        Test that download_filings calls the Downloader's get method with the correct parameters
        for each combination of ticker and filing type.
        """
        mocker.patch("src.bronze.sec_edgar_data.os.path.exists", return_value=True)
        downloader_class, downloader_instance = fake_downloader
        
        tickers = ["AAPL", "MSFT"]
        filing_types = {"10-K": "10-K", "10-Q": "10-Q"}
        filings_per_ticker = 5
        
        SecEdgarData.download_filings(tickers, filing_types, filings_per_ticker)
        
        downloader_class.assert_called_once_with(
            company_name="name",
            email_address="address@domain.com",
            download_folder=SecEdgarData.DOWNLOAD_PATH
        )
        
        expected_calls = [
            mocker.call(form_type, ticker, limit=filings_per_ticker)
            for ticker in tickers
            for form_type in filing_types.values()
        ]
        assert downloader_instance.get.call_count == len(expected_calls)
        downloader_instance.get.assert_has_calls(expected_calls, any_order=True)
    
    def test_download_filings_handles_download_error(self, mocker, fake_downloader):
        """
        Test that download_filings logs an error if a download fails.
        The Downloader.get method is set to raise an Exception.
        """
        mocker.patch("src.bronze.sec_edgar_data.os.path.exists", return_value=True)
        _, downloader_instance = fake_downloader
        downloader_instance.get.side_effect = Exception("Download failed")
        mock_logger = mocker.patch("src.bronze.sec_edgar_data.bronze_logger")
        
        tickers = ["AAPL"]
        filing_types = {"10-K": "10-K"}
        filings_per_ticker = 5
        
        SecEdgarData.download_filings(tickers, filing_types, filings_per_ticker)
        
        mock_logger.error.assert_called_with("Error downloading 10-K filings for AAPL: Download failed")
        
    def test_download_filings_with_empty_inputs(self, mocker):
        """
        Test that download_filings does not call Downloader.get when there are no tickers or filing types.
        """
        downloader_patch = mocker.patch("src.bronze.sec_edgar_data.Downloader")
        tickers = []
        filing_types = {}
        filings_per_ticker = 5
        
        SecEdgarData.download_filings(tickers, filing_types, filings_per_ticker)
        
        downloader_patch.return_value.get.assert_not_called()           
        
        
    
        