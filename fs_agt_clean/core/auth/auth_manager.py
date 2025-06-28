import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from jose import JWTError, jwt

# JWT configuration
JWT_ALGORITHM = "HS256"


@dataclass
class TokenInfo:
    """Information about an authentication token."""

    token: str
    refresh_token: str
    expiry: datetime


@dataclass
class UnifiedUserCredentials:
    """UnifiedUser authentication credentials."""

    username: str
    password: str
    roles: List[str]


class AuthManager:
    def __init__(self, secret_key: str):
        """Initialize the auth manager."""
        self.secret_key = secret_key
        self.reset()

    def reset(self) -> None:
        """Reset the auth manager to its initial state."""
        self.active_tokens = {}
        self.token_expiry = 3600  # 1 hour default expiry
        self.refresh_token_expiry = 86400  # 24 hours default expiry
        self.users = {}

    async def validate_token(self, token: str) -> bool:
        """Validate an access token."""
        try:
            # First check if token is in active tokens
            if token not in self.active_tokens:
                return False

            # Check if token has expired in our active tokens list
            now = datetime.now(timezone.utc)
            token_expiry = self.active_tokens[token].replace(tzinfo=timezone.utc)
            if now > token_expiry:
                del self.active_tokens[token]
                return False

            # Then validate JWT claims
            payload = jwt.decode(token, self.secret_key, algorithms=[JWT_ALGORITHM])
            username = payload.get("sub")
            exp_timestamp = payload.get("exp")

            if not username or not exp_timestamp:
                if token in self.active_tokens:
                    del self.active_tokens[token]
                return False

            exp = datetime.fromtimestamp(float(exp_timestamp), timezone.utc)

            if now > exp:
                if token in self.active_tokens:
                    del self.active_tokens[token]
                return False

            return True
        except JWTError:
            if token in self.active_tokens:
                del self.active_tokens[token]
            return False

    async def generate_tokens(self, username: str, roles: List[str]) -> TokenInfo:
        """Generate access and refresh tokens for a user."""
        now = datetime.now(timezone.utc)
        expiry = now + timedelta(seconds=self.token_expiry)
        refresh_expiry = now + timedelta(seconds=self.refresh_token_expiry)

        # Add random nonce to ensure unique tokens
        nonce = secrets.token_hex(8)

        token = jwt.encode(
            {
                "sub": username,
                "roles": roles,
                "exp": int(expiry.timestamp()),
                "iat": int(now.timestamp()),
                "nonce": nonce,
            },
            self.secret_key,
            algorithm=JWT_ALGORITHM,
        )

        refresh_token = jwt.encode(
            {
                "sub": username,
                "type": "refresh",
                "exp": int(refresh_expiry.timestamp()),
                "iat": int(now.timestamp()),
                "nonce": secrets.token_hex(8),  # Different nonce for refresh token
            },
            self.secret_key,
            algorithm=JWT_ALGORITHM,
        )

        token_info = TokenInfo(token=token, refresh_token=refresh_token, expiry=expiry)
        self.active_tokens[token] = expiry
        return token_info

    async def refresh_token(self, refresh_token: str) -> Optional[TokenInfo]:
        """Refresh an access token using a refresh token."""
        try:
            payload = jwt.decode(
                refresh_token, self.secret_key, algorithms=[JWT_ALGORITHM]
            )
            if payload.get("type") != "refresh":
                return None

            username = payload.get("sub")
            if not username or username not in self.users:
                return None

            return await self.generate_tokens(username, self.users[username].roles)
        except JWTError:
            return None

    async def register_user(
        self, username: str, password: str, roles: List[str]
    ) -> bool:
        """Register a new user."""
        if username in self.users:
            raise ValueError(f"UnifiedUser {username} already exists")

        self.users[username] = UnifiedUserCredentials(
            username=username, password=password, roles=roles
        )
        return True

    async def authenticate(self, username: str, password: str) -> Optional[TokenInfo]:
        """Authenticate a user and generate tokens."""
        if username not in self.users:
            raise ValueError(f"UnifiedUser {username} not found")

        if self.users[username].password != password:
            raise ValueError("Invalid password")

        return await self.generate_tokens(username, self.users[username].roles)
