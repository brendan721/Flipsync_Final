#!/usr/bin/env python3
"""
FlipSync Agent Database Cleanup Script (SQL Direct)
==================================================
Removes test agents using direct SQL commands to ensure 4+1 architecture compliance.
"""

import subprocess
import sys
from datetime import datetime
from typing import List

def run_sql_command(sql: str) -> tuple[bool, str]:
    """Execute SQL command using psql."""
    try:
        cmd = [
            'psql',
            '-h', '174.138.77.110',
            '-U', 'postgres',
            '-d', 'flipsync_agentic_test',
            '-c', sql
        ]
        
        env = {'PGPASSWORD': 'FlipSync_DB_Prod_2024_Secure_Key_9x7z'}
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "SQL command timed out"
    except Exception as e:
        return False, f"Error executing SQL: {e}"

def get_current_agents() -> tuple[bool, List[dict]]:
    """Get current agents from database."""
    sql = """
    SELECT agent_id, agent_type, status, created_at 
    FROM autonomous_agents 
    ORDER BY created_at;
    """
    
    success, output = run_sql_command(sql)
    if not success:
        return False, []
    
    agents = []
    lines = output.strip().split('\n')
    
    # Skip header lines and parse data
    data_started = False
    for line in lines:
        line = line.strip()
        if not line or line.startswith('-') or line.startswith('agent_id'):
            if line.startswith('agent_id'):
                data_started = True
            continue
        if not data_started:
            continue
        if line.startswith('(') and 'row' in line:
            break
            
        # Parse the line
        parts = line.split('|')
        if len(parts) >= 4:
            agent_id = parts[0].strip()
            agent_type = parts[1].strip()
            status = parts[2].strip()
            created_at = parts[3].strip()
            
            agents.append({
                'agent_id': agent_id,
                'agent_type': agent_type,
                'status': status,
                'created_at': created_at
            })
    
    return True, agents

def cleanup_test_agents():
    """Main cleanup function."""
    print("🧹 FlipSync Agent Database Cleanup Script (SQL Direct)")
    print("=" * 60)
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Define production agents that should remain
    production_agents = {
        'market_autonomous_agent',
        'content_autonomous_agent', 
        'executive_autonomous_agent',
        'logistics_autonomous_agent'
    }
    
    print("✅ Expected production agents:")
    for agent_id in sorted(production_agents):
        print(f"   - {agent_id}")
    print()
    
    # Get current agents
    print("🔍 Scanning database for agents...")
    success, agents = get_current_agents()
    
    if not success:
        print("❌ Failed to retrieve agents from database")
        return False
    
    print(f"📊 Found {len(agents)} total agents in database")
    
    # Categorize agents
    production_found = []
    test_agents = []
    
    for agent in agents:
        if agent['agent_id'] in production_agents:
            production_found.append(agent)
        else:
            test_agents.append(agent)
    
    print(f"\n📈 Analysis Results:")
    print(f"   Production agents found: {len(production_found)}")
    print(f"   Test agents found: {len(test_agents)}")
    
    # Show production agents
    if production_found:
        print(f"\n✅ Production agents (keeping these):")
        for agent in production_found:
            print(f"   - {agent['agent_id']} (status: {agent['status']})")
    
    # Show test agents to be removed
    if test_agents:
        print(f"\n🗑️  Test agents to remove:")
        for agent in test_agents:
            print(f"   - {agent['agent_id']}")
            print(f"     Type: {agent['agent_type']}")
            print(f"     Status: {agent['status']}")
            print(f"     Created: {agent['created_at']}")
            print()
        
        # Confirm removal
        print(f"⚠️  WARNING: This will permanently delete {len(test_agents)} test agents!")
        confirm = input(f"Remove {len(test_agents)} test agents? (y/N): ").strip().lower()
        
        if confirm == 'y':
            print(f"\n🗑️  Removing {len(test_agents)} test agents...")
            
            removed_count = 0
            for agent in test_agents:
                agent_id = agent['agent_id']
                
                # Delete agent from database
                sql = f"DELETE FROM autonomous_agents WHERE agent_id = '{agent_id}';"
                success, output = run_sql_command(sql)
                
                if success:
                    removed_count += 1
                    print(f"   ✅ Removed: {agent_id}")
                else:
                    print(f"   ❌ Failed to remove {agent_id}: {output}")
            
            print(f"\n✅ Successfully removed {removed_count} test agents")
            
        else:
            print("❌ Cleanup cancelled by user")
            return False
    else:
        print("\n✅ No test agents found - database is already clean!")
    
    # Verify final state
    print(f"\n🔍 Verifying final database state...")
    success, final_agents = get_current_agents()
    
    if not success:
        print("❌ Failed to verify final state")
        return False
    
    print(f"📊 Final state: {len(final_agents)} agents remaining")
    
    if len(final_agents) == 4:
        print("✅ Perfect! Exactly 4 autonomous agents remain")
        
        # Verify they are the correct production agents
        remaining_ids = {agent['agent_id'] for agent in final_agents}
        if remaining_ids == production_agents:
            print("✅ All remaining agents are correct production agents")
            
            print(f"\n📋 Final agent list:")
            for agent in sorted(final_agents, key=lambda x: x['agent_id']):
                print(f"   - {agent['agent_id']} ({agent['agent_type']})")
            
            print(f"\n🎉 Database cleanup completed successfully!")
            print(f"   - 4+1 Architecture compliance: READY")
            print(f"   - Production agents: {len(final_agents)}")
            print(f"   - Test agents: 0")
            print(f"   - Conversational interface: 1 (strategic_chat_service)")
            
            return True
        else:
            print("❌ ERROR: Remaining agents don't match expected production agents")
            missing = production_agents - remaining_ids
            extra = remaining_ids - production_agents
            if missing:
                print(f"   Missing: {missing}")
            if extra:
                print(f"   Extra: {extra}")
            return False
    else:
        print(f"❌ ERROR: Expected 4 agents, but {len(final_agents)} remain")
        return False

def main():
    """Main execution function."""
    print(f"🚀 Starting FlipSync Agent Database Cleanup")
    print()
    
    success = cleanup_test_agents()
    
    if success:
        print(f"\n✅ CLEANUP SUCCESSFUL - 4+1 Architecture Ready!")
        return 0
    else:
        print(f"\n❌ CLEANUP FAILED - Manual intervention required")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
