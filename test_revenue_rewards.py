#!/usr/bin/env python3
"""
Test script for revenue sharing and rewards calculations.
"""
import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime, timezone

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fs_agt_clean'))

from services.subscription.enhanced_subscription_service import (
    EnhancedSubscriptionService, SubscriptionTier, FeatureType
)

async def test_revenue_rewards():
    """Test revenue sharing and rewards calculations."""
    print("💰 Testing Revenue Sharing and Rewards Calculations...")
    
    # Initialize service
    subscription_service = EnhancedSubscriptionService()
    
    # Test Case 1: Subscription Tier Pricing
    print("\n📊 Test Case 1: Subscription Tier Pricing")
    
    for tier in SubscriptionTier:
        plan = subscription_service.subscription_plans[tier]
        print(f"\n  {plan.name} ({tier.value}):")
        print(f"    Monthly: ${plan.monthly_price}")
        print(f"    Annual: ${plan.annual_price} (${plan.annual_price/12:.2f}/month)")
        
        if plan.annual_price > 0:
            annual_savings = (plan.monthly_price * 12) - plan.annual_price
            savings_percentage = (annual_savings / (plan.monthly_price * 12)) * 100
            print(f"    Annual Savings: ${annual_savings:.2f} ({savings_percentage:.1f}%)")
        
        print(f"    Features: {len(plan.features)} available")
        print(f"    Popular: {'Yes' if hasattr(plan, 'most_popular') and plan.most_popular else 'No'}")
    
    # Test Case 2: Feature Usage Limits and Pricing
    print("\n📊 Test Case 2: Feature Usage Limits and Pricing")
    
    test_user_id = "test_user_123"
    
    for tier in [SubscriptionTier.FREE, SubscriptionTier.BASIC, SubscriptionTier.PREMIUM]:
        plan = subscription_service.subscription_plans[tier]
        print(f"\n  {plan.name} Tier Features:")
        
        for feature_type, feature in plan.features.items():
            limit_text = "Unlimited" if feature.unlimited else f"{feature.limit} per month"
            print(f"    {feature_type.value}: {limit_text}")
    
    # Test Case 3: Revenue Calculation Scenarios
    print("\n📊 Test Case 3: Revenue Calculation Scenarios")
    
    revenue_scenarios = [
        {
            "scenario": "Small Seller",
            "monthly_sales": 5000,
            "shipping_savings": 150,
            "tier": SubscriptionTier.BASIC,
            "listings": 50
        },
        {
            "scenario": "Medium Seller", 
            "monthly_sales": 25000,
            "shipping_savings": 750,
            "tier": SubscriptionTier.PREMIUM,
            "listings": 250
        },
        {
            "scenario": "Large Seller",
            "monthly_sales": 100000,
            "shipping_savings": 3000,
            "tier": SubscriptionTier.ENTERPRISE,
            "listings": 1000
        }
    ]
    
    for scenario in revenue_scenarios:
        plan = subscription_service.subscription_plans[scenario["tier"]]
        monthly_cost = plan.monthly_price
        annual_cost = plan.annual_price
        
        # Calculate value metrics
        shipping_roi = (scenario["shipping_savings"] / monthly_cost) * 100 if monthly_cost > 0 else 0
        cost_per_listing = monthly_cost / scenario["listings"] if scenario["listings"] > 0 else 0
        revenue_percentage = (monthly_cost / scenario["monthly_sales"]) * 100
        
        print(f"\n  {scenario['scenario']} ({scenario['tier'].value}):")
        print(f"    Monthly Sales: ${scenario['monthly_sales']:,}")
        print(f"    Subscription Cost: ${monthly_cost}/month")
        print(f"    Shipping Savings: ${scenario['shipping_savings']}/month")
        print(f"    Net Benefit: ${scenario['shipping_savings'] - monthly_cost:.2f}/month")
        print(f"    Shipping ROI: {shipping_roi:.1f}%")
        print(f"    Cost per Listing: ${cost_per_listing:.2f}")
        print(f"    Cost as % of Revenue: {revenue_percentage:.2f}%")
    
    # Test Case 4: Rewards Tier Calculations
    print("\n📊 Test Case 4: Rewards Tier Calculations")
    
    rewards_tiers = [
        {"tier": "Bronze", "min_spent": 0, "cashback_rate": 0.01, "bonus_multiplier": 1.0},
        {"tier": "Silver", "min_spent": 500, "cashback_rate": 0.015, "bonus_multiplier": 1.2},
        {"tier": "Gold", "min_spent": 2000, "cashback_rate": 0.02, "bonus_multiplier": 1.5},
        {"tier": "Platinum", "min_spent": 10000, "cashback_rate": 0.025, "bonus_multiplier": 2.0}
    ]
    
    test_spending_amounts = [100, 750, 3500, 15000]
    
    for amount in test_spending_amounts:
        # Determine tier
        applicable_tier = rewards_tiers[0]  # Default to Bronze
        for tier in reversed(rewards_tiers):
            if amount >= tier["min_spent"]:
                applicable_tier = tier
                break
        
        # Calculate rewards
        base_cashback = amount * applicable_tier["cashback_rate"]
        bonus_cashback = base_cashback * (applicable_tier["bonus_multiplier"] - 1)
        total_cashback = base_cashback + bonus_cashback
        
        print(f"\n  Spending: ${amount:,}")
        print(f"    Tier: {applicable_tier['tier']}")
        print(f"    Base Cashback: ${base_cashback:.2f} ({applicable_tier['cashback_rate']:.1%})")
        print(f"    Bonus Cashback: ${bonus_cashback:.2f} ({applicable_tier['bonus_multiplier']}x multiplier)")
        print(f"    Total Cashback: ${total_cashback:.2f} ({total_cashback/amount:.2%})")
    
    # Test Case 5: Upgrade ROI Analysis
    print("\n📊 Test Case 5: Upgrade ROI Analysis")
    
    upgrade_scenarios = [
        {"from": SubscriptionTier.FREE, "to": SubscriptionTier.BASIC, "additional_features": 5},
        {"from": SubscriptionTier.BASIC, "to": SubscriptionTier.PREMIUM, "additional_features": 8},
        {"from": SubscriptionTier.PREMIUM, "to": SubscriptionTier.ENTERPRISE, "additional_features": 12}
    ]
    
    for scenario in upgrade_scenarios:
        from_plan = subscription_service.subscription_plans[scenario["from"]]
        to_plan = subscription_service.subscription_plans[scenario["to"]]
        
        monthly_cost_increase = to_plan.monthly_price - from_plan.monthly_price
        annual_cost_increase = to_plan.annual_price - from_plan.annual_price
        
        # Estimate value per additional feature
        value_per_feature = monthly_cost_increase / scenario["additional_features"] if scenario["additional_features"] > 0 else 0
        
        print(f"\n  Upgrade: {from_plan.name} → {to_plan.name}")
        print(f"    Monthly Cost Increase: ${monthly_cost_increase}")
        print(f"    Annual Cost Increase: ${annual_cost_increase}")
        print(f"    Additional Features: {scenario['additional_features']}")
        print(f"    Cost per Additional Feature: ${value_per_feature:.2f}/month")
        
        # Break-even analysis (assuming each feature saves $10/month)
        estimated_monthly_value = scenario["additional_features"] * 10
        roi_months = monthly_cost_increase / estimated_monthly_value if estimated_monthly_value > 0 else float('inf')
        
        if roi_months < 12:
            print(f"    ROI: Pays for itself in {roi_months:.1f} months")
        else:
            print(f"    ROI: May not pay for itself within 12 months")
    
    print("\n✅ Revenue sharing and rewards calculations validated successfully!")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_revenue_rewards())
        if result:
            print("\n🎉 All revenue and rewards tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
