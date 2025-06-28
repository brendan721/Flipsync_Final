#!/usr/bin/env python3
"""
Quick test server to verify mobile integration endpoints
"""

import json
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="FlipSync Mobile Test Server")

# Add CORS middleware for mobile app connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/v1/auth/login")
async def auth_login_get():
    # Mobile test expects this to respond (even with error for GET)
    return {"error": "Method not allowed", "message": "Use POST for login"}

@app.post("/api/v1/auth/login")
async def auth_login_post():
    return {"error": "Invalid credentials", "message": "Test endpoint"}

@app.get("/api/v1/agents")
async def get_agents():
    return {
        "total_agents": 4,
        "agents": [
            {"agent_id": "market_agent", "status": "active", "type": "market"},
            {"agent_id": "executive_agent", "status": "active", "type": "executive"},
            {"agent_id": "content_agent", "status": "active", "type": "content"},
            {"agent_id": "logistics_agent", "status": "active", "type": "logistics"}
        ]
    }

@app.get("/api/v1/agents/communication/status")
async def get_agent_communication_status():
    return {
        "status": "operational",
        "active_connections": 4,
        "last_update": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/analytics/dashboard")
async def get_analytics_dashboard():
    return {
        "status": "success",
        "data": {
            "total_products": 150,
            "active_listings": 45,
            "revenue": 12500.00,
            "profit_margin": 0.25
        }
    }

@app.get("/api/v1/marketplace")
async def get_marketplace():
    return {
        "status": "success",
        "marketplaces": ["ebay", "amazon"],
        "active_listings": 45
    }

@app.get("/api/v1/marketplace/products")
async def get_marketplace_products():
    return {
        "status": "success",
        "products": [
            {"id": 1, "title": "Test Product 1", "price": 29.99},
            {"id": 2, "title": "Test Product 2", "price": 49.99}
        ]
    }

@app.post("/api/v1/notifications/push/register")
async def register_push_notifications():
    return {"status": "success", "message": "Push notifications registered"}

@app.get("/api/v1/notifications")
async def get_notifications():
    return {
        "status": "success",
        "notifications": [
            {"id": 1, "message": "Test notification", "timestamp": datetime.now(timezone.utc).isoformat()}
        ]
    }

@app.post("/api/v1/ai/analysis/analyze")
async def analyze_product():
    return {
        "status": "success",
        "analysis": {
            "profit_potential": "high",
            "competition_level": "medium",
            "recommendation": "proceed"
        }
    }

@app.get("/api/v1/mobile/dashboard")
async def get_mobile_dashboard():
    return {
        "status": "success",
        "data": {
            "total_products": 150,
            "active_listings": 45,
            "revenue": 12500.00,
            "notifications": 3
        }
    }

@app.get("/api/v1/mobile/agents/status")
async def get_mobile_agent_status():
    return {
        "status": "success",
        "agents": {
            "market": {"status": "active", "last_update": datetime.now(timezone.utc).isoformat()},
            "executive": {"status": "active", "last_update": datetime.now(timezone.utc).isoformat()},
            "content": {"status": "active", "last_update": datetime.now(timezone.utc).isoformat()},
            "logistics": {"status": "active", "last_update": datetime.now(timezone.utc).isoformat()}
        }
    }

@app.get("/api/v1/mobile/notifications")
async def get_mobile_notifications():
    return {
        "status": "success",
        "notifications": [
            {"id": 1, "message": "Mobile test notification", "timestamp": datetime.now(timezone.utc).isoformat()}
        ]
    }

@app.get("/api/v1/mobile/settings")
async def get_mobile_settings():
    return {
        "status": "success",
        "settings": {
            "notifications_enabled": True,
            "sync_frequency": "hourly",
            "theme": "auto"
        }
    }

@app.post("/api/v1/mobile/sync")
async def mobile_sync():
    return {
        "sync_status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "synced_items": {
            "products": 150,
            "listings": 45,
            "notifications": 3
        },
        "next_sync": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting FlipSync Mobile Test Server...")
    print("📱 Testing mobile integration endpoints on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
