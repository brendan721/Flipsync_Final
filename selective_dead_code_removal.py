#!/usr/bin/env python3
"""
Selective Dead Code Removal for FlipSync
Only removes code with 95%+ confidence to preserve legitimate complexity
"""

import re
import os
from pathlib import Path

# High-confidence dead code items (95%+ confidence only)
HIGH_CONFIDENCE_REMOVALS = [
    # 100% confidence unused variables
    ("fs_agt_clean/agents/content/__init__.py", 53, "unused variable 'content_format'"),
    ("fs_agt_clean/agents/market/amazon_client.py", 109, "unused variable 'exc_tb'"),
    ("fs_agt_clean/agents/market/ebay_client.py", 102, "unused variable 'exc_tb'"),
    ("fs_agt_clean/api/routes/agents.py", 848, "redundant if-condition"),
    ("fs_agt_clean/api/routes/agents.py", 856, "unreachable code after 'return'"),
    ("fs_agt_clean/api/routes/agents.py", 939, "unreachable code after 'if'"),
    ("fs_agt_clean/api/routes/auth.py", 51, "unused variable 'ex'"),
    ("fs_agt_clean/api/routes/users/payment_methods.py", 41, "unused variable 'payment_data'"),
    ("fs_agt_clean/core/ai/llm_adapter.py", 76, "unused variable 'base_system_prompt'"),
    ("fs_agt_clean/core/db/database_adapter.py", 202, "unused variable 'exc_tb'"),
    ("fs_agt_clean/core/events/bus/secure_event_bus.py", 200, "unused variable 'original_event'"),
    ("fs_agt_clean/core/learning/learning_module.py", 1041, "unused variable 'learning_points'"),
    ("fs_agt_clean/core/monitoring/protocols/metrics_protocol.py", 99, "unused variable 'default_labels'"),
    ("fs_agt_clean/core/monitoring/protocols/metrics_protocol.py", 189, "unused variable 'label_key'"),
    ("fs_agt_clean/core/monitoring/protocols/monitoring_protocol.py", 235, "unused variable 'monitoring_system'"),
    ("fs_agt_clean/core/state_management/state_manager.py", 611, "unused variable 'success_only'"),
    ("fs_agt_clean/database/error_handling.py", 329, "unused variable 'exc_tb'"),
    ("fs_agt_clean/database/repositories/chat_repository.py", 168, "unused variable 'include_reactions'"),
    ("fs_agt_clean/services/advanced_features/ai_integration/brain/decision.py", 31, "unused variable 'possible_actions'"),
    ("fs_agt_clean/services/data_pipeline/acquisition_agent.py", 22, "unused variable 'range_name'"),
    ("fs_agt_clean/services/infrastructure/monitoring/health.py", 204, "unused variable 'metric_category'"),
    ("fs_agt_clean/services/infrastructure/monitoring/manager.py", 284, "unused variable 'default_labels'"),
    ("fs_agt_clean/services/infrastructure/monitoring/manager.py", 390, "unused variable 'label_key'"),
    ("fs_agt_clean/services/logistics/shippo/shippo_service.py", 642, "unused variable 'original_transaction_id'"),
    ("fs_agt_clean/services/market_analysis/service.py", 310, "unused variable 'sort_order'"),
    ("fs_agt_clean/services/monitoring/alert_service.py", 68, "unused variable 'auto_resolve_minutes'"),
    ("fs_agt_clean/services/search/service.py", 367, "unused variable 'sort_order'"),
]

def remove_unused_variable(file_path: str, line_num: int, description: str):
    """Remove unused variable from specific line"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if line_num <= len(lines):
            original_line = lines[line_num - 1]
            
            # Extract variable name from description
            if "unused variable" in description:
                var_match = re.search(r"'([^']+)'", description)
                if var_match:
                    var_name = var_match.group(1)
                    
                    # Remove variable assignment or declaration
                    if f"{var_name} =" in original_line:
                        # Comment out the line instead of removing to preserve line numbers
                        lines[line_num - 1] = f"# REMOVED: {original_line}"
                        print(f"✅ Commented out unused variable '{var_name}' in {file_path}:{line_num}")
                    elif f", {var_name}" in original_line:
                        # Remove from tuple unpacking
                        lines[line_num - 1] = original_line.replace(f", {var_name}", "")
                        print(f"✅ Removed '{var_name}' from tuple in {file_path}:{line_num}")
                    elif f"{var_name}," in original_line:
                        # Remove from tuple unpacking (first position)
                        lines[line_num - 1] = original_line.replace(f"{var_name}, ", "")
                        print(f"✅ Removed '{var_name}' from tuple in {file_path}:{line_num}")
            
            elif "redundant if-condition" in description or "unreachable code" in description:
                # Comment out redundant/unreachable code
                lines[line_num - 1] = f"# REMOVED: {original_line}"
                print(f"✅ Commented out redundant/unreachable code in {file_path}:{line_num}")
            
            # Write back the modified file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
    except Exception as e:
        print(f"❌ Error processing {file_path}:{line_num} - {e}")

def main():
    """Main function to perform selective dead code removal"""
    print("=== FlipSync Selective Dead Code Removal ===")
    print("Only removing code with 95%+ confidence to preserve architecture")
    print()
    
    removed_count = 0
    
    for file_path, line_num, description in HIGH_CONFIDENCE_REMOVALS:
        if os.path.exists(file_path):
            remove_unused_variable(file_path, line_num, description)
            removed_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print()
    print(f"=== Selective Dead Code Removal Complete ===")
    print(f"Processed {removed_count} high-confidence dead code items")
    print("Preserved all 90% confidence items to maintain architecture integrity")
    print()
    print("Note: Lines were commented out rather than deleted to preserve")
    print("line numbers for debugging and maintain code structure.")

if __name__ == "__main__":
    main()
