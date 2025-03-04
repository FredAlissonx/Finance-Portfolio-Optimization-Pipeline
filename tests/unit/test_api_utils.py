import pytest
from unittest.mock import MagicMock
from utils.api_utils import APIUtils, session
from fake_response_api import fake_requests_get_exception

@pytest.fixture(autouse=True)
def set_base_url():
    APIUtils.BASE_URL = "https://example.com/api"

class TestAPIUtils:
    def test_get_api_key_success(self, monkeypatch):
        """Test successful retrieval of API key from environment variables."""
        monkeypatch.setenv("SOME_API", "testkey")
        key = APIUtils._get_api_key("SOME_API")
        assert key == "testkey"

    def test_get_api_key_missing(self, monkeypatch):
        """Test that a missing API key raises a ValueError."""
        monkeypatch.delenv("SOME_API", raising=False)
        with pytest.raises(ValueError, match="API Key missing."):
            APIUtils._get_api_key("SOME_API")

    def test_fetch_data_success(self, monkeypatch):
        """Test successful API request returning valid JSON."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": [{"id": 1, "value": 100}]}
    
        monkeypatch.setattr(session, "get", lambda url, params, timeout: mock_response)
        result = APIUtils._fetch_data({"query": "test"})
        assert result == {"data": [{"id": 1, "value": 100}]}

    def test_fetch_data_failure(self, monkeypatch):
        """Test that a request exception results in a None return value."""
        monkeypatch.setattr(session, "get", fake_requests_get_exception)
        result = APIUtils._fetch_data({"query": "test"})
        assert result is None

    @pytest.mark.parametrize(
        "response_data, expected",
        [
            ({"data": [{"id": 1, "value": 100}]}, {"data": [{"id": 1, "value": 100}]}),
            ({"Error Message": "Invalid request"}, None),
            ({"Note": "Rate limit exceeded"}, None)
        ],
    )
    def test_validate_response(self, response_data, expected):
        """
        Test _validate_response with different response structures:
         - Valid response
         - Empty data
         - API error messages
         - Rate limit warnings
        """
        result = APIUtils._validate_response(response_data, symbol="AAPL")
        assert result == expected
