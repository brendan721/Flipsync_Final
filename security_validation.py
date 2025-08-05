#!/usr/bin/env python3
"""
FlipSync Security Validation Script
Scans for hardcoded secrets and sensitive information before git commit
"""

import os
import re
import subprocess
from pathlib import Path

# Patterns to detect secrets
SECRET_PATTERNS = [
    (r'sk-proj-[A-Za-z0-9_-]{100,}', 'OpenAI API Key'),
    (r'AIza[0-9A-Za-z_-]{35}', 'Google API Key'),
    (r'postgresql://[^:]+:[^@]+@[^/]+/[^"\']+', 'Database URL with credentials'),
    (r'redis://:[^@]+@[^/]+', 'Redis URL with password'),
    (r'FlipSync[_A-Za-z0-9]*[Pp]assword[_A-Za-z0-9]*', 'FlipSync password pattern'),
    (r'FlipSync[_A-Za-z0-9]*[Kk]ey[_A-Za-z0-9]*', 'FlipSync key pattern'),
    (r'BrendanB-[A-Za-z0-9-]+', 'eBay App ID'),
    (r'SBX-[A-Za-z0-9-]+', 'eBay Sandbox credentials'),
    (r'PRD-[A-Za-z0-9-]+', 'eBay Production credentials'),
    (r'["\']password["\']\s*:\s*["\'][^"\']+["\']', 'Password in JSON/dict'),
    (r'["\']secret["\']\s*:\s*["\'][^"\']+["\']', 'Secret in JSON/dict'),
    (r'["\']key["\']\s*:\s*["\'][^"\']+["\']', 'Key in JSON/dict'),
]

# File extensions to scan
SCAN_EXTENSIONS = {'.py', '.js', '.ts', '.json', '.yaml', '.yml', '.md', '.txt', '.sh'}

# Files and directories to exclude from scanning
EXCLUDE_PATTERNS = {
    '.git',
    '__pycache__',
    'node_modules',
    '.env.example',
    'security_validation.py',
    'validate_integration_examples.js',
    'validate_framework_examples.md',
    'FLIPSYNC_BACKEND_AUDIT_SUMMARY.md'
}

def should_scan_file(file_path):
    """Check if file should be scanned for secrets"""
    path = Path(file_path)
    
    # Skip if extension not in scan list
    if path.suffix not in SCAN_EXTENSIONS:
        return False
    
    # Skip if matches exclude patterns
    for exclude in EXCLUDE_PATTERNS:
        if exclude in str(path):
            return False
    
    return True

def scan_file_for_secrets(file_path):
    """Scan a single file for secret patterns"""
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for line_num, line in enumerate(content.split('\n'), 1):
            for pattern, description in SECRET_PATTERNS:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        'file': file_path,
                        'line': line_num,
                        'pattern': description,
                        'match': match.group()[:50] + '...' if len(match.group()) > 50 else match.group(),
                        'full_line': line.strip()
                    })
    
    except Exception as e:
        print(f"Error scanning {file_path}: {e}")
    
    return findings

def get_git_tracked_files():
    """Get list of files tracked by git"""
    try:
        result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
        else:
            print("Warning: Could not get git tracked files, scanning all files")
            return []
    except Exception as e:
        print(f"Error getting git files: {e}")
        return []

def scan_directory():
    """Scan all relevant files for secrets"""
    print("🔍 FlipSync Security Validation")
    print("=" * 50)
    
    # Get files to scan
    git_files = get_git_tracked_files()
    if git_files:
        files_to_scan = [f for f in git_files if should_scan_file(f) and os.path.exists(f)]
        print(f"Scanning {len(files_to_scan)} git-tracked files...")
    else:
        # Fallback: scan all files in directory
        files_to_scan = []
        for root, dirs, files in os.walk('.'):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_PATTERNS]
            
            for file in files:
                file_path = os.path.join(root, file)
                if should_scan_file(file_path):
                    files_to_scan.append(file_path)
        
        print(f"Scanning {len(files_to_scan)} files in directory...")
    
    # Scan files
    all_findings = []
    for file_path in files_to_scan:
        findings = scan_file_for_secrets(file_path)
        all_findings.extend(findings)
    
    # Report results
    if all_findings:
        print(f"\n🚨 SECURITY VIOLATIONS FOUND: {len(all_findings)}")
        print("=" * 50)
        
        for finding in all_findings:
            print(f"File: {finding['file']}")
            print(f"Line: {finding['line']}")
            print(f"Type: {finding['pattern']}")
            print(f"Match: {finding['match']}")
            print(f"Context: {finding['full_line']}")
            print("-" * 30)
        
        print("\n❌ COMMIT BLOCKED - Secrets detected!")
        print("Please remove all hardcoded secrets before committing.")
        return False
    else:
        print("\n✅ SECURITY VALIDATION PASSED")
        print("No hardcoded secrets detected in tracked files.")
        return True

if __name__ == "__main__":
    success = scan_directory()
    exit(0 if success else 1)
