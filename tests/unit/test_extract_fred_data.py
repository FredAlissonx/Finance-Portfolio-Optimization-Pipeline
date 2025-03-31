import pytest
from src.bronze.extract_fred_data import FredAPIFetch

@pytest.fixture(autouse=True)
def set_fred_api_key(monkeypatch):
    monkeypatch.setenv("API_FREDAPI_KEY", "fredkey")

class TestFredAPIFetch:
    def test_setup_params_required(self):
        """Test _setup_params with only the required parameter."""
        params = FredAPIFetch._setup_params("GDP")
        expected = {
            "series_id": "GDP",
            "api_key": "fredkey",
            "file_type": "json"
        }
        assert params == expected

    @pytest.mark.parametrize(
        "start, end, frequency, expected_extra",
        [
            ("2020-01-01", None, None, {"observation_start": "2020-01-01"}),
            (None, "2020-12-31", None, {"observation_end": "2020-12-31"}),
            (None, None, "monthly", {"frequency": "monthly"}),
            (
                "2020-01-01", "2020-12-31", "daily", 
                    {    
                    "observation_start": "2020-01-01",
                    "observation_end": "2020-12-31",
                    "frequency": "daily"
                    }
                ),
            ]
        )
    def test_setup_params_optional(self, start, end, frequency, expected_extra):
        """Test _setup_params with optional parameters."""
        params = FredAPIFetch._setup_params("GDP", observation_start=start, observation_end=end, frequency=frequency)
        expected = {
            "series_id": "GDP",
            "api_key": "fredkey",
            "file_type": "json"
        }
        expected.update(expected_extra)
        assert params == expected

    def test_fetch_data_returns_observations(self, monkeypatch):
        """
        Test that fetch_data returns the list of observations when _fetch_data returns valid data.
        We simulate _fetch_data to return a dict containing 'observations'.
        """
        fake_obs = [{"date": "2020-01-01", "value": "100"}]
        monkeypatch.setattr(FredAPIFetch, "_fetch_data", lambda params: {"observations": fake_obs})
        result = FredAPIFetch.fetch_data("GDP")
        assert result == fake_obs

    def test_fetch_data_returns_empty_list(self, monkeypatch):
        """
        Test that fetch_data returns an empty list when _fetch_data returns a dict
        without an 'observations' key.
        """
        monkeypatch.setattr(FredAPIFetch, "_fetch_data", lambda params: {})
        result = FredAPIFetch.fetch_data("GDP")
        assert result == []

    def test_fetch_batch_series(self, monkeypatch):
        """
        Test that fetch_batch_series aggregates the observations for multiple series correctly.
        We simulate fetch_data to return different results based on the series id.
        """
        def fake_fetch_data(series_id):
            if series_id == "GDP":
                return [{"date": "2020-01-01", "value": "100"}]
            elif series_id == "CPI":
                return [{"date": "2020-01-01", "value": "200"}]
            else:
                return []
        monkeypatch.setattr(FredAPIFetch, "fetch_data", fake_fetch_data)
        series_ids = ["GDP", "CPI", "UNEMPLOYMENT"]
        result = FredAPIFetch.fetch_batch_series(series_ids)
        expected = {
            "GDP": [{"date": "2020-01-01", "value": "100"}],
            "CPI": [{"date": "2020-01-01", "value": "200"}],
            "UNEMPLOYMENT": []
        }
        assert result == expected
