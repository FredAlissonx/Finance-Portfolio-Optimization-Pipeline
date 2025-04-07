import pytest
from src.bronze.extract_alpha_vantage_data import AlphaVantageAPIFetcher
from fake_response_api import FakeResponse, fake_request_data
from utils.api_utils import session

@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("API_ALPHA_VANTAGE_KEY", "alphakey")

class TestAlphaVantageAPIFetcher:
    def test_historical_options_setup_params(self):
        """Test that _setup_params for HISTORICAL_OPTIONS function correctly constructs parameters."""
        expected = {
            "function": "HISTORICAL_OPTIONS",
            "symbol": "TEST",
            "apikey": "alphakey",
            "outputsize": "full"
        }
        assert AlphaVantageAPIFetcher._setup_params(symbol="TEST", function="HISTORICAL_OPTIONS") == expected
    
    def test_overview_setup_params(self):
        """Test that _setup_params for OVERVIEW function correctly constructs parameters."""
        expected = {
            "function": "OVERVIEW",
            "symbol": "TEST",
            "apikey": "alphakey"
        }
        assert AlphaVantageAPIFetcher._setup_params(symbol = "TEST", function = "OVERVIEW") == expected

    def test_fetch_data_success_historical_options(self, monkeypatch):
        """
        Test that fetch_data returns valid data when the underlying GET call succeeds.
        (Lower-level behavior is assumed to be covered in APIUtils tests.)
        """
        monkeypatch.setattr(
            session, "get",
            lambda url, params, timeout: FakeResponse(json_data={"data": "some_data"}, status_code=200)
        )
        expected_data: dict = {"data": "some_data"}
        assert AlphaVantageAPIFetcher.get_data("TEST", "HISTORICAL_OPTIONS") == expected_data
        assert AlphaVantageAPIFetcher.get_data("TEST", "OVERVIEW") == expected_data

    @pytest.mark.parametrize(
        "symbols, patch_method, expected",
        [
            (
                ["AAPL", "GOOG"],
                "session",
                {"AAPL": {"data": "some_data"}, "GOOG": {"data": "some_data"}}
            ),
            (
                ["AAPL", "INVALID"],
                "get_data",
                {"AAPL": {"data": "ok"}, "INVALID": None}
            )
        ]
    )
    def test_fetch_batch_data(self, monkeypatch, mocker, symbols, patch_method, expected):
        """
        Parameterized test for batch processing:
         - When 'patch_method' is "session", we patch session.get to return a successful fake response.
         - When 'patch_method' is "fetch_data", we patch fetch_data to simulate partial failures.
        """
        if patch_method == "session":
            monkeypatch.setattr(session, "get", fake_request_data)
        elif patch_method == "get_data":
            mocker.patch.object(
                AlphaVantageAPIFetcher,
                "get_data",
                side_effect=lambda symbol, _: {"data": "ok"} if symbol == "AAPL" else None
            )
        
        assert AlphaVantageAPIFetcher.get_data_in_batch(symbols = symbols, function = "HISTORICAL_OPTIONS") == expected
        
