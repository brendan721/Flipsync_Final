import asyncio
from typing import Dict, Optional

# Optional dependencies
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

    # Create mock aiohttp for graceful fallback
    class MockClientSession:
        async def request(self, *args, **kwargs):
            raise RuntimeError("aiohttp not available")

        async def close(self):
            pass

    class MockAiohttp:
        ClientSession = MockClientSession
        ClientError = Exception
        ClientConnectorError = Exception
        ClientSSLError = Exception

    aiohttp = MockAiohttp()

try:
    from tenacity import retry, stop_after_attempt, wait_exponential

    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

    # Create mock retry decorator
    def retry(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def stop_after_attempt(*args):
        return None

    def wait_exponential(*args, **kwargs):
        return None


"\nBase API client class providing common HTTP functionality.\n"


class APIClient:
    """Base class for API clients with common HTTP functionality."""

    def __init__(self, base_url: str = ""):
        """Initialize the API client.

        Args:
            base_url: Base URL for API requests
        """
        self.base_url = base_url.rstrip("/")
        self.session = None
        self.retry_count = 0
        self.connection_errors = 0
        self.ssl_errors = 0
        self.last_error = None
        self.retry_after = 0

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint.

        Args:
            endpoint: API endpoint path

        Returns:
            Complete URL
        """
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/{endpoint}"

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional request arguments

        Returns:
            Response data
        """
        if self.session is None:
            await self._ensure_session()
            if self.session is None:
                raise RuntimeError("Failed to create session")

        url = self._build_url(endpoint)
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 429:
                    retry_after = response.headers.get("Retry-After", "5")
                    self.retry_after = int(retry_after)
                    return {
                        "status_code": 429,
                        "data": {"message": "Rate limit exceeded"},
                        "headers": {"Retry-After": retry_after},
                    }
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError as e:
            self.retry_count += 1
            self.last_error = str(e)
            raise
        except aiohttp.ClientSSLError as e:
            self.ssl_errors += 1
            self.last_error = str(e)
            raise
        except aiohttp.ClientConnectorError as e:
            self.connection_errors += 1
            self.last_error = str(e)
            if "DNS" in str(e):
                raise Exception("DNS resolution failed") from e
            raise
        except aiohttp.ClientError as e:
            self.connection_errors += 1
            self.last_error = str(e)
            raise
        except Exception as e:
            error_msg = str(e)
            self.last_error = error_msg
            if "SSL certificate" in error_msg:
                self.ssl_errors += 1
            elif "DNS" in error_msg:
                self.connection_errors += 1
            elif isinstance(e, ConnectionError):
                self.connection_errors += 1
            elif isinstance(e, TimeoutError):
                self.retry_count += 1
            raise

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict:
        """Send GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Request headers

        Returns:
            Response data
        """
        return await self.make_request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict:
        """Send POST request.

        Args:
            endpoint: API endpoint
            json: JSON payload
            data: Form data
            headers: Request headers

        Returns:
            Response data
        """
        return await self.make_request(
            "POST", endpoint, json=json, data=data, headers=headers
        )

    async def put(
        self, endpoint: str, json: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Dict:
        """Send PUT request.

        Args:
            endpoint: API endpoint
            json: JSON payload
            headers: Request headers

        Returns:
            Response data
        """
        return await self.make_request("PUT", endpoint, json=json, headers=headers)

    async def delete(self, endpoint: str, headers: Optional[Dict] = None) -> Dict:
        """Send DELETE request.

        Args:
            endpoint: API endpoint
            headers: Request headers

        Returns:
            Response data
        """
        return await self.make_request("DELETE", endpoint, headers=headers)

    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            self.session = None


# Alias for backward compatibility
ApiClient = APIClient
BaseAPIClient = APIClient  # Add BaseAPIClient alias for the Priority 1 test
