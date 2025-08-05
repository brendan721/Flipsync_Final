"""
Centralized SSL/TLS Configuration for FlipSync
Consolidates all SSL settings to eliminate redundancy and confusion.
"""

import os
from typing import Dict, Optional


class SSLConfig:
    """Centralized SSL configuration for FlipSync."""
    
    def __init__(self):
        self.ssl_enabled = os.getenv("SSL_ENABLED", "false").lower() == "true"
        self.cert_file = os.getenv("SSL_CERT_FILE", "/etc/ssl/certs/server.crt")
        self.key_file = os.getenv("SSL_KEY_FILE", "/etc/ssl/private/server.key")
        self.ca_file = os.getenv("SSL_CA_FILE", "/etc/ssl/certs/ca.crt")
        
    def get_ssl_context(self) -> Optional[Dict[str, str]]:
        """
        Returns SSL context configuration if SSL is enabled.
        """
        if not self.ssl_enabled:
            return None
            
        return {
            "ssl_certfile": self.cert_file,
            "ssl_keyfile": self.key_file,
            "ssl_ca_certs": self.ca_file,
        }
    
    def get_nginx_ssl_config(self) -> Dict[str, str]:
        """
        Returns SSL configuration for nginx.
        """
        return {
            "ssl_certificate": self.cert_file,
            "ssl_certificate_key": self.key_file,
            "ssl_trusted_certificate": self.ca_file,
        }
    
    def is_ssl_enabled(self) -> bool:
        """Returns whether SSL is enabled."""
        return self.ssl_enabled


# Global SSL configuration instance
ssl_config = SSLConfig()


def get_ssl_config() -> SSLConfig:
    """Returns the global SSL configuration instance."""
    return ssl_config


def get_ssl_context() -> Optional[Dict[str, str]]:
    """Returns SSL context if SSL is enabled."""
    return ssl_config.get_ssl_context()


def is_ssl_enabled() -> bool:
    """Returns whether SSL is enabled."""
    return ssl_config.is_ssl_enabled()
