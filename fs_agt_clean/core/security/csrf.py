import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import List, Optional

from fastapi import Cookie, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.status import HTTP_403_FORBIDDEN

# Constants
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"
DEFAULT_SECRET_LENGTH = 32
DEFAULT_TOKEN_EXPIRY = 86400  # 24 hours in seconds

# Set up logging
logger = logging.getLogger(__name__)


class CSRFConfig(BaseModel):
    """Configuration for CSRF protection."""

    secret: str = Field(
        default_factory=lambda: secrets.token_hex(DEFAULT_SECRET_LENGTH)
    )
    cookie_name: str = CSRF_COOKIE_NAME
    header_name: str = CSRF_HEADER_NAME
    form_field: str = CSRF_FORM_FIELD
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"  # Lowercase to match Literal type
    cookie_path: str = "/"
    cookie_domain: Optional[str] = None
    token_expiry: int = DEFAULT_TOKEN_EXPIRY
    exempt_paths: List[str] = Field(default_factory=list)
    exempt_methods: List[str] = Field(default_factory=list)
    debug: bool = False  # Add debug mode flag


async def extract_token_from_form(request: Request, field_name: str) -> Optional[str]:
    """Extract CSRF token from form data if present."""
    try:
        form_data = await request.form()
        return form_data.get(field_name)
    except Exception as e:
        logger.debug(f"Could not extract token from form data: {str(e)}")
        return None


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection."""

    def __init__(
        self,
        app: FastAPI,
        config: Optional[CSRFConfig] = None,
    ):
        super().__init__(app)
        self.config = config or CSRFConfig()

        # Default exempt methods
        if not self.config.exempt_methods:
            self.config.exempt_methods = ["GET", "HEAD", "OPTIONS"]

        logger.info(
            f"CSRF Middleware initialized with config: exempt_paths={self.config.exempt_paths}, exempt_methods={self.config.exempt_methods}"
        )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and apply CSRF protection."""
        # Log the incoming request
        logger.debug(f"CSRF middleware processing: {request.method} {request.url.path}")

        # Step 1: Check if the path is exempt
        path = request.url.path
        if self._is_path_exempt(path):
            logger.debug(f"CSRF check skipped for exempt path: {path}")
            return await call_next(request)

        # Step 2: Check if the method is exempt (GET, HEAD, OPTIONS)
        if request.method in self.config.exempt_methods:
            logger.debug(f"CSRF check skipped for exempt method: {request.method}")
            response = await call_next(request)

            # For GET requests, set a CSRF token cookie if it doesn't exist
            if request.method == "GET":
                csrf_cookie = request.cookies.get(self.config.cookie_name)
                if not csrf_cookie:
                    token = await generate_csrf_token(self.config.secret)
                    logger.debug(f"Setting CSRF token cookie for GET request: {path}")
                    response = self._set_csrf_cookie(response, token)

            return response

        # Step 3: For non-exempt methods, validate the CSRF token
        logger.info(f"Validating CSRF token for: {request.method} {path}")

        # Extract token from request - try multiple sources
        token = await self._extract_csrf_token(request)

        if not token:
            # No token found, block request
            logger.warning(f"No CSRF token found for: {request.method} {path}")
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing"},
            )

        # Step 4: Validate the token
        is_valid = await validate_csrf_token(token, self.config.secret)
        if not is_valid:
            logger.warning(f"Invalid CSRF token for: {request.method} {path}")
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"},
            )

        # Step 5: Token is valid, proceed with the request
        logger.debug(f"Valid CSRF token for: {request.method} {path}")
        return await call_next(request)

    def _is_path_exempt(self, path: str) -> bool:
        """Check if a path is exempt from CSRF protection."""
        for exempt_path in self.config.exempt_paths:
            if path.startswith(exempt_path):
                return True
        return False

    async def _extract_csrf_token(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request (header, cookie, or form)."""
        # 1. Try getting token from header (preferred)
        token = request.headers.get(self.config.header_name)
        if token:
            logger.debug(f"Found CSRF token in header: {self.config.header_name}")
            return token

        # 2. Try getting token from cookie
        token = request.cookies.get(self.config.cookie_name)
        if token:
            logger.debug(f"Found CSRF token in cookie: {self.config.cookie_name}")
            return token

        # 3. Try getting token from form data
        token = await extract_token_from_form(request, self.config.form_field)
        if token:
            logger.debug(f"Found CSRF token in form field: {self.config.form_field}")
            return token

        # No token found
        logger.warning("No CSRF token found in header, cookie, or form data")
        return None

    def _set_csrf_cookie(self, response: Response, token: str) -> Response:
        """Set the CSRF token as a cookie in the response."""
        # Handle samesite parameter safely
        samesite = self.config.cookie_samesite
        if samesite and isinstance(samesite, str):
            samesite = samesite.lower()

        response.set_cookie(
            key=self.config.cookie_name,
            value=token,
            max_age=self.config.token_expiry,
            path=self.config.cookie_path,
            domain=self.config.cookie_domain,
            secure=self.config.cookie_secure,
            httponly=self.config.cookie_httponly,
            samesite=samesite,
        )
        logger.debug(f"Set CSRF cookie: {self.config.cookie_name}=<token>")
        return response


async def generate_csrf_token(secret: str) -> str:
    """Generate a new CSRF token."""
    # Create a random token
    random_bytes = os.urandom(16)
    random_token = base64.urlsafe_b64encode(random_bytes).decode("utf-8").rstrip("=")

    # Add timestamp for expiration checking
    timestamp = int(time.time())

    # Create the payload
    payload = {"token": random_token, "ts": timestamp}

    # Serialize and sign the payload
    payload_str = json.dumps(payload)
    payload_bytes = payload_str.encode("utf-8")

    # Create signature
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()

    # Encode signature
    signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

    # Encode payload
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")

    # Combine payload and signature
    token = f"{payload_b64}.{signature_b64}"
    logger.debug(f"Generated new CSRF token")
    return token


async def validate_csrf_token(token: str, secret: str) -> bool:
    """Validate a CSRF token."""
    try:
        # Split token into payload and signature
        parts = token.split(".")
        if len(parts) != 2:
            logger.warning("Invalid CSRF token format: not two parts")
            return False

        payload_b64, signature_b64 = parts

        # Add padding if needed
        payload_b64 = payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)
        signature_b64 = signature_b64 + "=" * ((4 - len(signature_b64) % 4) % 4)

        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64)

        # Verify signature
        expected_signature = hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).digest()

        actual_signature = base64.urlsafe_b64decode(signature_b64)

        if not hmac.compare_digest(expected_signature, actual_signature):
            logger.warning("CSRF token signature verification failed")
            return False

        # Check timestamp if valid
        payload_dict = json.loads(payload_bytes.decode("utf-8"))
        timestamp = payload_dict.get("ts", 0)
        current_time = int(time.time())

        # Token is valid if it's not expired (24 hours)
        is_valid = current_time - timestamp <= DEFAULT_TOKEN_EXPIRY
        if not is_valid:
            logger.warning(
                f"CSRF token expired: token_age={current_time - timestamp}s, max_age={DEFAULT_TOKEN_EXPIRY}s"
            )
        return is_valid

    except Exception as e:
        logger.error(f"Error validating CSRF token: {str(e)}")
        return False


async def get_csrf_token(
    request: Request,
    csrf_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    config: CSRFConfig = CSRFConfig(),
) -> str:
    """
    Dependency to get or generate a CSRF token.

    If a token exists in the cookie, it is returned.
    Otherwise, a new token is generated.
    """
    if csrf_cookie:
        logger.debug("Using existing CSRF token from cookie")
        return csrf_cookie

    # Generate a new token if none exists
    logger.debug("Generating new CSRF token in dependency")
    token = await generate_csrf_token(config.secret)

    # For response cookies to work with FastAPI dependencies, we need to set it
    # in the response object that is stored in request.state
    response = getattr(request.state, "response", None)
    if response:
        logger.debug("Setting CSRF token in response (from dependency)")
        response.set_cookie(
            key=config.cookie_name,
            value=token,
            max_age=config.token_expiry,
            path=config.cookie_path,
            domain=config.cookie_domain,
            secure=config.cookie_secure,
            httponly=config.cookie_httponly,
            samesite=config.cookie_samesite,
        )
    else:
        logger.warning(
            "Could not set CSRF cookie: response object not available in request.state"
        )

    return token


def csrf_protect(app: FastAPI, config: Optional[CSRFConfig] = None) -> None:
    """
    Add CSRF protection to a FastAPI application.

    This is a convenience function to add the CSRFMiddleware to the app.
    """
    logger.info("Adding CSRF protection middleware to application")
    app.add_middleware(CSRFMiddleware, config=config)


def csrf_meta_tag(token: str) -> str:
    """Generate an HTML meta tag for a CSRF token."""
    return f'<meta name="csrf-token" content="{token}">'


def csrf_input_field(token: str) -> str:
    """Generate an HTML input field for a CSRF token."""
    return f'<input type="hidden" name="csrf_token" value="{token}">'


def validate_csrf_token_sync(token: str, secret: str) -> bool:
    """Synchronous version of validate_csrf_token for use in sync contexts."""
    try:
        # Split token into payload and signature
        parts = token.split(".")
        if len(parts) != 2:
            logger.warning("Invalid CSRF token format: not two parts")
            return False

        payload_b64, signature_b64 = parts

        # Add padding if needed
        payload_b64 = payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)
        signature_b64 = signature_b64 + "=" * ((4 - len(signature_b64) % 4) % 4)

        # Decode payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64)

        # Verify signature
        expected_signature = hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).digest()

        actual_signature = base64.urlsafe_b64decode(signature_b64)

        if not hmac.compare_digest(expected_signature, actual_signature):
            logger.warning("CSRF token signature verification failed (sync)")
            return False

        # Check timestamp if valid
        payload_dict = json.loads(payload_bytes.decode("utf-8"))
        timestamp = payload_dict.get("ts", 0)
        current_time = int(time.time())

        # Token is valid if it's not expired (24 hours)
        is_valid = current_time - timestamp <= DEFAULT_TOKEN_EXPIRY
        if not is_valid:
            logger.warning(
                f"CSRF token expired: token_age={current_time - timestamp}s, max_age={DEFAULT_TOKEN_EXPIRY}s"
            )
        return is_valid

    except Exception as e:
        logger.error(f"Error validating CSRF token (sync): {str(e)}")
        return False


async def verify_csrf_token(token: str, secret: str) -> bool:
    """Alias for validate_csrf_token for backward compatibility."""
    return await validate_csrf_token(token, secret)
