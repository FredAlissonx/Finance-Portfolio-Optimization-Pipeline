import pytest
from unittest.mock import Mock
from src.bronze.extract_finnhub_news_data import FinnhubNewsAPIFetcher
from utils.api_utils import APIUtils

@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("API_FINNHUB_NEWS_KEY_TEST", "dummy_key")

class TestFinnhubNewsFetcher:
    @pytest.fixture
    def mock_finnhub_client(self, monkeypatch):
        mock_client = Mock()
        mock_client.market_holiday.return_value = [{"name": "Test Holiday"}]
        monkeypatch.setattr(FinnhubNewsAPIFetcher, "finnhub_client", mock_client)
        return mock_client

    @pytest.mark.parametrize("exchange_symbol", ["USD", "EUR", "JPY"])
    def test_fetch_market_holiday_success(self, mock_finnhub_client, exchange_symbol):
        result = FinnhubNewsAPIFetcher.fetch_market_holiday(exchange_symbol=exchange_symbol)
        assert isinstance(result, list)
        assert len(result) > 0
        mock_finnhub_client.market_holiday.assert_called_once_with(exchange=exchange_symbol)

    def test_market_holiday_api_failure(self, mock_finnhub_client):
        mock_finnhub_client.market_holiday.side_effect = Exception("API Error")
        with pytest.raises(Exception):
            FinnhubNewsAPIFetcher.fetch_market_holiday("USD")

    def test_client_initialization_without_key(self, monkeypatch):
        monkeypatch.delenv("API_FINNHUB_NEWS_KEY_TEST")
        with pytest.raises(ValueError):
            APIUtils._get_api_key("API_FINNHUB_NEWS_KEY_TEST")
    
    