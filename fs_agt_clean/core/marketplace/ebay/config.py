from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EbayConfig:
    """Configuration for eBay API access."""

    # Authentication
    client_id: str
    client_secret: str

    # API endpoints
    api_base_url: str = "https://api.ebay.com"
    auth_url: str = "https://api.ebay.com/identity/v1/oauth2/token"

    # API scopes for OAuth
    scopes: Optional[List[str]] = None

    def __post_init__(self):
        """Set default scopes if none provided."""
        if self.scopes is None:
            self.scopes = [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/buy.item.feed",
                "https://api.ebay.com/oauth/api_scope/buy.marketing",
                "https://api.ebay.com/oauth/api_scope/buy.item.bulk",
                "https://api.ebay.com/oauth/api_scope/buy.item.bulk.feed",
                "https://api.ebay.com/oauth/api_scope/sell.inventory",
                "https://api.ebay.com/oauth/api_scope/sell.marketing",
                "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
            ]

    @property
    def client_credentials(self) -> str:
        """Get base64 encoded client credentials for OAuth.

        Returns:
            Encoded credentials string
        """
        import base64

        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    @property
    def scopes_string(self) -> str:
        """Get space-separated string of scopes for OAuth.

        Returns:
            Space-separated scopes
        """
        return " ".join(self.scopes) if self.scopes else ""
