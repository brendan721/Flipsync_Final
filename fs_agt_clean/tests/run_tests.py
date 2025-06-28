#!/usr/bin/env python3
"""
Run tests for the fs_agt_clean package.
"""

import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Run the tests
if __name__ == "__main__":
    # Discover and run all tests
    test_suite = unittest.defaultTestLoader.discover(
        start_dir=os.path.dirname(__file__), pattern="test_*.py"
    )

    # Run the tests
    unittest.TextTestRunner().run(test_suite)
