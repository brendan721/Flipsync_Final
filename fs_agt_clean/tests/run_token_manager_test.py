#!/usr/bin/env python3
"""
Run tests for the token_manager.py file.
"""

import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the test
from fs_agt_clean.tests.core.auth.test_token_manager import TestTokenManager

# Run the tests
if __name__ == "__main__":
    # Create a test suite with just the TokenManager tests
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestTokenManager)

    # Run the tests
    unittest.TextTestRunner().run(test_suite)
