"""
Billing Cycle Management for FlipSync Payment Processing.

This module provides billing cycle definitions and management for subscription
and payment processing services.
"""

from enum import Enum
from typing import Dict, List


class BillingCycle(Enum):
    """Billing cycle enumeration for subscription management."""
    
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    YEARLY = "yearly"  # Alias for ANNUAL
    WEEKLY = "weekly"
    DAILY = "daily"


class BillingCycleManager:
    """Manager for billing cycle operations and conversions."""
    
    @staticmethod
    def get_paypal_frequency(billing_cycle: BillingCycle) -> str:
        """
        Convert BillingCycle to PayPal frequency string.
        
        Args:
            billing_cycle: The billing cycle to convert
            
        Returns:
            PayPal frequency string
        """
        frequency_mapping = {
            BillingCycle.MONTHLY: "MONTH",
            BillingCycle.QUARTERLY: "QUARTER", 
            BillingCycle.ANNUAL: "YEAR",
            BillingCycle.YEARLY: "YEAR",
            BillingCycle.WEEKLY: "WEEK",
            BillingCycle.DAILY: "DAY"
        }
        
        if billing_cycle not in frequency_mapping:
            raise ValueError(f"Unsupported billing cycle: {billing_cycle}")
            
        return frequency_mapping[billing_cycle]
    
    @staticmethod
    def from_paypal_frequency(frequency: str) -> BillingCycle:
        """
        Convert PayPal frequency string to BillingCycle.
        
        Args:
            frequency: PayPal frequency string
            
        Returns:
            BillingCycle enum value
        """
        frequency_mapping = {
            "MONTH": BillingCycle.MONTHLY,
            "QUARTER": BillingCycle.QUARTERLY,
            "YEAR": BillingCycle.ANNUAL,
            "WEEK": BillingCycle.WEEKLY,
            "DAY": BillingCycle.DAILY
        }
        
        if frequency not in frequency_mapping:
            raise ValueError(f"Unsupported PayPal frequency: {frequency}")
            
        return frequency_mapping[frequency]
    
    @staticmethod
    def get_cycle_days(billing_cycle: BillingCycle) -> int:
        """
        Get the number of days in a billing cycle.
        
        Args:
            billing_cycle: The billing cycle
            
        Returns:
            Number of days in the cycle
        """
        days_mapping = {
            BillingCycle.DAILY: 1,
            BillingCycle.WEEKLY: 7,
            BillingCycle.MONTHLY: 30,  # Approximate
            BillingCycle.QUARTERLY: 90,  # Approximate
            BillingCycle.ANNUAL: 365,  # Approximate
            BillingCycle.YEARLY: 365   # Alias for ANNUAL
        }
        
        return days_mapping.get(billing_cycle, 30)
    
    @staticmethod
    def get_all_cycles() -> List[BillingCycle]:
        """
        Get all available billing cycles.
        
        Returns:
            List of all BillingCycle enum values
        """
        return list(BillingCycle)
    
    @staticmethod
    def get_cycle_display_name(billing_cycle: BillingCycle) -> str:
        """
        Get human-readable display name for billing cycle.
        
        Args:
            billing_cycle: The billing cycle
            
        Returns:
            Human-readable display name
        """
        display_names = {
            BillingCycle.DAILY: "Daily",
            BillingCycle.WEEKLY: "Weekly", 
            BillingCycle.MONTHLY: "Monthly",
            BillingCycle.QUARTERLY: "Quarterly",
            BillingCycle.ANNUAL: "Annual",
            BillingCycle.YEARLY: "Yearly"
        }
        
        return display_names.get(billing_cycle, billing_cycle.value.title())
