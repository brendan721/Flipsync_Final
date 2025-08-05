#!/usr/bin/env python3
"""
FlipSync Database Schema Validation Test
=======================================

This script validates the database connectivity and schema against documentation claims.
"""

import asyncio
import sys
import os
from pathlib import Path
import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add the fs_agt_clean directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "fs_agt_clean"))

async def test_database_connectivity():
    """Test database connectivity and schema validation."""
    print("🔍 Testing FlipSync Database Connectivity & Schema")
    print("=" * 55)
    
    results = {
        "connectivity": False,
        "tables": {},
        "schema_validation": {},
        "production_data": {}
    }
    
    # Database connection details from .env.production.test
    DATABASE_URL = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
    
    try:
        print("\n1️⃣ Testing Database Connectivity...")
        
        # Create async engine
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Test basic connectivity
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Database connected: {version}")
            results["connectivity"] = True
            
            # Test 2: Check for autonomous_agents table
            print("\n2️⃣ Validating Autonomous Agents Table...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'autonomous_agents'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                if columns:
                    print("✅ autonomous_agents table exists")
                    results["tables"]["autonomous_agents"] = {
                        "exists": True,
                        "columns": [{"name": col[0], "type": col[1], "nullable": col[2]} for col in columns]
                    }
                    
                    # Check for expected columns
                    column_names = [col[0] for col in columns]
                    expected_columns = ["id", "agent_id", "agent_type", "status", "health_score", "last_decision_time_ms"]
                    
                    missing_columns = [col for col in expected_columns if col not in column_names]
                    if missing_columns:
                        print(f"⚠️ Missing expected columns: {missing_columns}")
                    else:
                        print("✅ All expected columns present")
                        
                else:
                    print("❌ autonomous_agents table not found")
                    results["tables"]["autonomous_agents"] = {"exists": False}
                    
            except Exception as e:
                print(f"❌ Error checking autonomous_agents table: {e}")
                results["tables"]["autonomous_agents"] = {"exists": False, "error": str(e)}
            
            # Test 3: Check for unified_users table
            print("\n3️⃣ Validating Users Table...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'unified_users'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                if columns:
                    print("✅ unified_users table exists")
                    results["tables"]["unified_users"] = {
                        "exists": True,
                        "columns": [{"name": col[0], "type": col[1], "nullable": col[2]} for col in columns]
                    }
                else:
                    print("❌ unified_users table not found")
                    results["tables"]["unified_users"] = {"exists": False}
                    
            except Exception as e:
                print(f"❌ Error checking unified_users table: {e}")
                results["tables"]["unified_users"] = {"exists": False, "error": str(e)}
            
            # Test 4: Check for eBay OAuth table
            print("\n4️⃣ Validating eBay OAuth Table...")
            try:
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'ebay_oauth_tokens'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                if columns:
                    print("✅ ebay_oauth_tokens table exists")
                    results["tables"]["ebay_oauth_tokens"] = {
                        "exists": True,
                        "columns": [{"name": col[0], "type": col[1], "nullable": col[2]} for col in columns]
                    }
                else:
                    print("❌ ebay_oauth_tokens table not found")
                    results["tables"]["ebay_oauth_tokens"] = {"exists": False}
                    
            except Exception as e:
                print(f"❌ Error checking ebay_oauth_tokens table: {e}")
                results["tables"]["ebay_oauth_tokens"] = {"exists": False, "error": str(e)}
            
            # Test 5: Check for decision tracking tables
            print("\n5️⃣ Validating Decision Tracking...")
            try:
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE '%decision%'
                """))
                decision_tables = [row[0] for row in result.fetchall()]
                
                if decision_tables:
                    print(f"✅ Decision tracking tables found: {decision_tables}")
                    results["tables"]["decision_tables"] = decision_tables
                else:
                    print("❌ No decision tracking tables found")
                    results["tables"]["decision_tables"] = []
                    
            except Exception as e:
                print(f"❌ Error checking decision tables: {e}")
                results["tables"]["decision_tables"] = {"error": str(e)}
            
            # Test 6: Check production data
            print("\n6️⃣ Checking Production Data...")
            try:
                # Check for existing agent records
                result = await conn.execute(text("SELECT COUNT(*) FROM autonomous_agents"))
                agent_count = result.fetchone()[0] if result else 0
                
                result = await conn.execute(text("SELECT COUNT(*) FROM unified_users"))
                user_count = result.fetchone()[0] if result else 0
                
                print(f"✅ Production data - Agents: {agent_count}, Users: {user_count}")
                results["production_data"] = {
                    "agent_count": agent_count,
                    "user_count": user_count
                }
                
            except Exception as e:
                print(f"❌ Error checking production data: {e}")
                results["production_data"] = {"error": str(e)}
        
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        results["connectivity"] = False
        results["error"] = str(e)
    
    return results

def print_database_summary(results):
    """Print database validation summary."""
    print("\n" + "=" * 55)
    print("🎯 DATABASE VALIDATION SUMMARY")
    print("=" * 55)
    
    if results.get("connectivity"):
        print("📊 Database Connectivity: ✅ SUCCESS")
    else:
        print("📊 Database Connectivity: ❌ FAILED")
        return
    
    # Table validation summary
    tables = results.get("tables", {})
    table_count = sum(1 for table_data in tables.values() 
                     if isinstance(table_data, dict) and table_data.get("exists", False))
    
    print(f"📊 Database Tables: {table_count} validated")
    
    for table_name, table_data in tables.items():
        if isinstance(table_data, dict):
            if table_data.get("exists"):
                column_count = len(table_data.get("columns", []))
                print(f"  ✅ {table_name}: {column_count} columns")
            else:
                print(f"  ❌ {table_name}: Not found")
        elif isinstance(table_data, list):
            print(f"  ✅ {table_name}: {len(table_data)} tables")
    
    # Production data summary
    prod_data = results.get("production_data", {})
    if "agent_count" in prod_data:
        print(f"📊 Production Data: {prod_data['agent_count']} agents, {prod_data['user_count']} users")
    
    print(f"\n📋 DETAILED RESULTS: {results}")

if __name__ == "__main__":
    results = asyncio.run(test_database_connectivity())
    print_database_summary(results)
