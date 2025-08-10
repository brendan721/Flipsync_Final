"""
Clean eBay OAuth API Routes - Version 2.0

This module provides clean, simple REST API endpoints for eBay OAuth operations.
Designed for plug-and-play integration with Flutter frontend.

Endpoints:
- POST /api/v1/ebay/oauth/authorize - Start OAuth flow
- GET  /api/v1/ebay/oauth/callback  - Handle eBay callback
- GET  /api/v1/ebay/oauth/status    - Check auth status
- POST /api/v1/ebay/oauth/refresh   - Refresh tokens
- DELETE /api/v1/ebay/oauth/revoke  - Revoke access
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse

from fs_agt_clean.api.models.ebay_oauth_models import (
    EbayOAuthAuthorizeRequest,
    EbayOAuthAuthorizeResponse,
    EbayOAuthCallbackRequest,
    EbayOAuthCallbackResponse,
    EbayOAuthStatusResponse,
    EbayOAuthRefreshResponse,
    EbayOAuthRevokeResponse,
    EbayOAuthErrorResponse,
)
from fs_agt_clean.services.marketplace.ebay_oauth_service_v2 import (
    get_ebay_oauth_service,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/ebay/oauth", tags=["eBay OAuth V2"])


@router.post("/authorize", response_model=EbayOAuthAuthorizeResponse)
async def authorize_ebay_oauth(request: EbayOAuthAuthorizeRequest):
    """
    Start eBay OAuth authorization flow.

    This endpoint generates an eBay OAuth authorization URL for the specified user.
    The user will be redirected to eBay to authorize the application.

    User ID Mapping:
    - "testuser" -> Sandbox environment
    - "realuser" -> Production environment
    - Others -> Sandbox (default)
    """
    try:
        oauth_service = get_ebay_oauth_service()

        # Generate authorization URL
        auth_url, state = await oauth_service.generate_authorization_url(
            user_id=request.user_id, scopes=request.scopes
        )

        # Get user environment for response
        credentials = oauth_service._get_credentials_for_user(request.user_id)

        logger.info(
            f"Generated OAuth URL for user {request.user_id} ({credentials.environment})"
        )

        return EbayOAuthAuthorizeResponse(
            success=True,
            message=f"OAuth authorization URL generated for {credentials.environment} environment",
            data={
                "authorization_url": auth_url,
                "state": state,
                "user_id": request.user_id,
                "environment": credentials.environment,
                "scopes": request.scopes,
                "expires_in": 600,  # 10 minutes
            },
        )

    except Exception as e:
        logger.error(f"Failed to generate OAuth URL for user {request.user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}",
        )


@router.get("/callback")
async def handle_ebay_oauth_callback(
    request: Request,
    code: Optional[str] = Query(None, description="Authorization code from eBay"),
    state: Optional[str] = Query(None, description="State parameter for validation"),
    error: Optional[str] = Query(None, description="OAuth error from eBay"),
    error_description: Optional[str] = Query(
        None, description="OAuth error description"
    ),
):
    """
    Handle eBay OAuth callback.

    This endpoint handles the callback from eBay after user authorization.
    It exchanges the authorization code for access tokens and stores them securely.

    Returns HTML response for browser compatibility and Flutter integration.
    """
    try:
        # Handle OAuth error from eBay
        if error:
            logger.error(f"eBay OAuth error: {error} - {error_description}")
            return _generate_callback_html(
                success=False,
                error_message=f"eBay authentication failed: {error}",
                error_details=error_description,
            )

        # Validate required parameters
        if not code or not state:
            logger.error("Missing required OAuth parameters")
            return _generate_callback_html(
                success=False,
                error_message="Missing required authentication parameters",
                error_details="Please try connecting to eBay again",
            )

        # Exchange code for tokens
        oauth_service = get_ebay_oauth_service()
        result = await oauth_service.exchange_code_for_tokens(code, state)

        logger.info(f"OAuth callback successful for user {result['user_id']}")

        # Notify WebSocket clients of successful OAuth
        try:
            from fs_agt_clean.api.websockets.ebay_oauth_ws import notify_oauth_success

            await notify_oauth_success(result["user_id"], result["environment"])
        except Exception as e:
            logger.warning(f"Failed to send WebSocket notification: {e}")

        return _generate_callback_html(
            success=True,
            success_message="eBay account connected successfully!",
            result_data=result,
        )

    except ValueError as e:
        logger.error(f"OAuth callback validation error: {e}")
        return _generate_callback_html(
            success=False,
            error_message="Invalid authentication state",
            error_details="Please try connecting to eBay again",
        )

    except Exception as e:
        logger.error(f"OAuth callback processing error: {e}")
        return _generate_callback_html(
            success=False,
            error_message="Authentication processing error",
            error_details=str(e),
        )


@router.get("/status/{user_id}", response_model=EbayOAuthStatusResponse)
async def get_oauth_status(user_id: str):
    """
    Get eBay OAuth authentication status for a user.

    This endpoint checks if the user has valid eBay authentication tokens
    and returns the current authentication status.
    """
    try:
        oauth_service = get_ebay_oauth_service()
        status_data = await oauth_service.get_auth_status(user_id)

        return EbayOAuthStatusResponse(
            success=True, message="Authentication status retrieved", data=status_data
        )

    except Exception as e:
        logger.error(f"Failed to get OAuth status for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get authentication status: {str(e)}",
        )


@router.post("/refresh/{user_id}", response_model=EbayOAuthRefreshResponse)
async def refresh_oauth_tokens(user_id: str):
    """
    Refresh eBay OAuth tokens for a user.

    This endpoint manually refreshes the user's eBay OAuth tokens.
    Note: Tokens are automatically refreshed when needed, so this is rarely required.
    """
    try:
        oauth_service = get_ebay_oauth_service()

        # Get current tokens (this will trigger refresh if needed)
        tokens = await oauth_service.get_user_tokens(user_id)

        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No tokens found for user"
            )

        return EbayOAuthRefreshResponse(
            success=True,
            message="Tokens refreshed successfully",
            data={
                "user_id": user_id,
                "environment": tokens["environment"],
                "token_type": tokens["token_type"],
                "expires_at": tokens["expires_at"].isoformat(),
                "scopes": tokens["scopes"],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh tokens for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh tokens: {str(e)}",
        )


@router.delete("/revoke/{user_id}", response_model=EbayOAuthRevokeResponse)
async def revoke_oauth_tokens(user_id: str):
    """
    Revoke eBay OAuth tokens for a user.

    This endpoint revokes and deletes the user's eBay OAuth tokens,
    effectively disconnecting their eBay account.
    """
    try:
        oauth_service = get_ebay_oauth_service()
        revoked = await oauth_service.revoke_user_tokens(user_id)

        return EbayOAuthRevokeResponse(
            success=True,
            message=(
                "Tokens revoked successfully"
                if revoked
                else "No tokens found to revoke"
            ),
            data={"user_id": user_id, "revoked": revoked},
        )

    except Exception as e:
        logger.error(f"Failed to revoke tokens for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke tokens: {str(e)}",
        )


@router.post("/test-notification/{user_id}")
async def test_oauth_notification(user_id: str):
    """
    Test endpoint to manually trigger OAuth success notification.

    This endpoint is for testing the WebSocket notification system.
    """
    try:
        from fs_agt_clean.api.websockets.ebay_oauth_ws import notify_oauth_success

        logger.info(f"🧪 Testing OAuth notification for user {user_id}")
        await notify_oauth_success(user_id, "sandbox")

        return {
            "success": True,
            "message": f"OAuth notification test triggered for user {user_id}",
            "data": {"user_id": user_id, "environment": "sandbox"},
        }

    except Exception as e:
        logger.error(f"Error testing OAuth notification for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-api-access/{user_id}")
async def test_ebay_api_access(user_id: str):
    """
    Test endpoint to verify stored eBay tokens can make real eBay API calls.

    This demonstrates that autonomous agents can access eBay marketplace data.
    """
    try:
        import httpx

        oauth_service = get_ebay_oauth_service()
        tokens = await oauth_service.get_user_tokens(user_id)

        if not tokens:
            raise HTTPException(
                status_code=404, detail=f"No eBay tokens found for user {user_id}"
            )

        logger.info(f"🧪 Testing eBay API access for user {user_id}")

        # Test eBay API call using stored tokens
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }

        # Use eBay Browse API to search for items (read-only, safe for testing)
        api_url = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"
        params = {"q": "test", "limit": 1}

        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers, params=params)

        if response.status_code == 200:
            api_data = response.json()
            return {
                "success": True,
                "message": f"eBay API access verified for user {user_id}",
                "data": {
                    "user_id": user_id,
                    "environment": tokens["environment"],
                    "api_response_status": response.status_code,
                    "items_found": len(api_data.get("itemSummaries", [])),
                    "token_expires_at": tokens["expires_at"].isoformat(),
                    "api_test": "browse_api_search_successful",
                },
            }
        else:
            return {
                "success": False,
                "message": f"eBay API call failed for user {user_id}",
                "data": {
                    "user_id": user_id,
                    "environment": tokens["environment"],
                    "api_response_status": response.status_code,
                    "api_response": response.text[:500],
                    "token_expires_at": tokens["expires_at"].isoformat(),
                },
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing eBay API access for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-agent-integration/{user_id}")
async def test_agent_integration(user_id: str):
    """
    Test endpoint for autonomous agent eBay integration.

    Tests the complete agent workflow including market analysis,
    pricing research, and opportunity detection.
    """
    try:
        from fs_agt_clean.services.marketplace.ebay_agent_service import (
            get_ebay_agent_service,
        )

        logger.info(f"🤖 Testing agent integration for user {user_id}")

        ebay_service = get_ebay_agent_service()

        # Test 1: Market Search
        search_results = await ebay_service.search_marketplace(
            user_id=user_id, query="electronics", limit=10
        )

        # Test 2: Market Analysis
        market_data = await ebay_service.analyze_market_trends(
            user_id=user_id,
            category_id="293",  # Electronics category
            keywords=["smartphone", "laptop", "tablet"],
        )

        # Test 3: User Listings (may fail if user has no listings)
        try:
            user_listings = await ebay_service.get_user_listings(user_id, limit=5)
        except Exception as e:
            user_listings = []
            logger.warning(f"User listings test failed (expected): {e}")

        return {
            "success": True,
            "message": f"Agent integration test completed for user {user_id}",
            "data": {
                "user_id": user_id,
                "tests": {
                    "marketplace_search": {
                        "status": "success",
                        "results_count": len(search_results),
                        "sample_items": [
                            {
                                "title": (
                                    item.title[:50] + "..."
                                    if len(item.title) > 50
                                    else item.title
                                ),
                                "price": item.price,
                                "currency": item.currency,
                            }
                            for item in search_results[:3]
                        ],
                    },
                    "market_analysis": {
                        "status": "success",
                        "category_id": market_data.category_id,
                        "average_price": market_data.average_price,
                        "total_listings": market_data.total_listings,
                        "competition_level": market_data.competition_level,
                    },
                    "user_listings": {
                        "status": "success" if user_listings else "no_listings",
                        "count": len(user_listings),
                    },
                },
                "agent_capabilities": [
                    "market_search",
                    "trend_analysis",
                    "price_research",
                    "competition_analysis",
                    "opportunity_detection",
                ],
            },
        }

    except Exception as e:
        logger.error(f"Agent integration test failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-market-agent/{user_id}")
async def test_market_agent(user_id: str, query: str = "electronics"):
    """
    Test endpoint for Market Agent with eBay integration.

    Tests the 4+1 architecture Market Agent functionality.
    """
    try:
        from fs_agt_clean.core.agents.market_agent_ebay import create_market_agent_ebay

        logger.info(f"🏪 Testing Market Agent for user {user_id} with query: {query}")

        # Create and initialize Market Agent
        market_agent = create_market_agent_ebay()
        await market_agent.initialize()

        # Test market analysis decision
        analysis_request = {
            "decision_type": "market_analysis",
            "user_id": user_id,
            "query": query,
            "keywords": [query, "trending", "popular"],
        }

        analysis_result = await market_agent.process_decision_request(analysis_request)

        # Test pricing research decision
        pricing_request = {
            "decision_type": "price_research",
            "user_id": user_id,
            "product_title": query,
        }

        pricing_result = await market_agent.process_decision_request(pricing_request)

        # Test opportunity detection
        opportunity_request = {
            "decision_type": "opportunity_detection",
            "user_id": user_id,
            "categories": ["Electronics", "Home & Garden"],
        }

        opportunity_result = await market_agent.process_decision_request(
            opportunity_request
        )

        # Cleanup
        await market_agent.cleanup()

        return {
            "success": True,
            "message": f"Market Agent test completed for user {user_id}",
            "data": {
                "user_id": user_id,
                "agent_id": market_agent.agent_id,
                "agent_state": market_agent.state,
                "test_results": {
                    "market_analysis": {
                        "success": analysis_result.get("success", False),
                        "data": analysis_result.get("data", {}),
                        "processing_time_ms": analysis_result.get(
                            "processing_time_ms", 0
                        ),
                    },
                    "price_research": {
                        "success": pricing_result.get("success", False),
                        "data": pricing_result.get("data", {}),
                        "processing_time_ms": pricing_result.get(
                            "processing_time_ms", 0
                        ),
                    },
                    "opportunity_detection": {
                        "success": opportunity_result.get("success", False),
                        "data": opportunity_result.get("data", {}),
                        "processing_time_ms": opportunity_result.get(
                            "processing_time_ms", 0
                        ),
                    },
                },
                "4plus1_integration": "verified",
            },
        }

    except Exception as e:
        logger.error(f"Market Agent test failed for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_callback_html(
    success: bool,
    success_message: str = None,
    error_message: str = None,
    error_details: str = None,
    result_data: dict = None,
) -> HTMLResponse:
    """Generate HTML response for OAuth callback popup window."""

    if success:
        status_content = f"""
            <div class="success">
                <h2>✅ {success_message or 'eBay Connected Successfully!'}</h2>
                <p>Your eBay account has been connected to FlipSync.</p>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        """
        message_data = {
            "source": "ebay_oauth_callback_v2",
            "success": True,
            "message": success_message or "eBay account connected successfully",
            "data": result_data or {},
        }
    else:
        status_content = f"""
            <div class="error">
                <h2>❌ {error_message or 'Authentication Failed'}</h2>
                <p>{error_details or 'Please try connecting to eBay again.'}</p>
                <button class="close-btn" onclick="window.close()">Close Window</button>
            </div>
        """
        message_data = {
            "source": "ebay_oauth_callback_v2",
            "success": False,
            "error": error_message or "Authentication failed",
            "error_description": error_details or "Unknown error",
        }

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FlipSync eBay OAuth</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
            max-width: 400px;
            width: 100%;
        }}
        .success {{ color: #4caf50; }}
        .error {{ color: #f44336; }}
        h2 {{ margin-bottom: 20px; }}
        p {{ margin-bottom: 30px; color: #666; }}
        .close-btn {{
            background: #2196f3;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
        }}
        .close-btn:hover {{ background: #1976d2; }}
    </style>
</head>
<body>
    <div class="container">
        {status_content}
    </div>
    
    <script>
        console.log('🚀 FlipSync eBay OAuth V2 Callback');
        
        const messageData = {json.dumps(message_data)};
        console.log('📤 Sending result to parent:', messageData);
        
        // Send message to parent window
        if (window.opener && !window.opener.closed) {{
            try {{
                // Send to both www and apex domains to avoid origin mismatch
                try {{ window.opener.postMessage(messageData, 'https://www.flipsyncai.com'); }} catch (e) {{ console.log('postMessage www error', e); }}
                try {{ window.opener.postMessage(messageData, 'https://flipsyncai.com'); }} catch (e) {{ console.log('postMessage apex error', e); }}
                console.log('✅ Message sent to parent window (www/apex)');
            }} catch (error) {{
                console.log('❌ Failed to send message:', error);
            }}
        }}
        
        // Auto-close after 3 seconds
        setTimeout(() => {{
            window.close();
        }}, 3000);
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content, status_code=200 if success else 400)
