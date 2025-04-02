import requests

class FakeResponse:
    """A fake response object to simulate requests.Response."""
    def __init__(
        self,
        json_data: dict[str] = None,
        status_code: int = 200,
        json_callable = None
    ):
        self._json_data = json_data
        self.status_code = status_code
        self._json_callable = json_callable

    def raise_for_status(self) -> None:
        """Raise an HTTPError if the status code indicates an error."""
        if self.status_code >= 400:
            raise requests.HTTPError(
                f"HTTP error: status code {self.status_code}", response=self
            )

    def json(self):
        """Return JSON data or invoke the callable if provided."""
        if self._json_callable:
            return self._json_callable()
        return self._json_data

def fake_requests_get_success(url: str, params: dict, timeout: int) -> FakeResponse:
    """Simulate a successful API call returning valid data."""
    return FakeResponse(json_data={"data": "some_data"}, status_code=200)

def fake_requests_get_api_error(url: str, params: dict, timeout: int) -> FakeResponse:
    """Simulate a response with an error message from the API."""
    return FakeResponse(json_data={"Error Message": "invalid symbol"}, status_code=200)

def fake_requests_get_rate_limit(url: str, params: dict, timeout: int) -> FakeResponse:
    """
    Simulate a response where the rate limit has been hit.
    It's more appropriate to use HTTP status code 429 for rate limit scenarios.
    """
    return FakeResponse(json_data={"note": "rate limit hit"}, status_code=429)

def fake_requests_get_http_error(url: str, params: dict, timeout: int) -> FakeResponse:
    """Simulate an HTTP error (e.g., 404 Not Found)."""
    return FakeResponse(json_data={}, status_code=404)

def fake_requests_get_exception(url: str, params: dict, timeout: int) -> FakeResponse:
    """Simulate a network exception during the API call."""
    raise requests.RequestException("Network error occurred")

def fake_json() -> None:
    """A fake JSON callable that always raises a ValueError to simulate invalid JSON."""
    raise ValueError("Invalid JSON")

def fake_requests_get_invalid_json(url: str, params: dict, timeout: int) -> FakeResponse:
    """Simulate a response with invalid JSON."""
    return FakeResponse(json_callable=fake_json, status_code=200)

def fake_request_data(url: str, params: dict, timeout: int) -> FakeResponse:
    """Simulate a response with JSON with data"""
    mock_json: dict = {
        "data": "some_data"
    }
    return FakeResponse(json_data=mock_json, status_code=200)
