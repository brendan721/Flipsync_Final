#!/usr/bin/env python3
"""
Test script for shipping arbitrage calculations.
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fs_agt_clean'))

from services.shipping_arbitrage import ShippingArbitrageService

async def test_shipping_arbitrage():
    """Test shipping arbitrage calculations."""
    print("🚚 Testing Shipping Arbitrage Calculations...")
    
    # Initialize the service
    service = ShippingArbitrageService()
    
    # Test Case 1: Basic arbitrage calculation
    print("\n📦 Test Case 1: Basic Arbitrage Calculation")
    result1 = await service.calculate_arbitrage(
        origin_zip="90210",
        destination_zip="10001", 
        weight=2.5,
        package_type="standard",
        current_rate=12.50
    )
    
    print(f"Origin: {result1['arbitrage_analysis']['origin_zip']}")
    print(f"Destination: {result1['arbitrage_analysis']['destination_zip']}")
    print(f"Weight: {result1['arbitrage_analysis']['package_weight']} lbs")
    print(f"Shipping Zone: {result1['arbitrage_analysis']['shipping_zone']}")
    
    print("\n💰 Carrier Rates:")
    for carrier, data in result1['carrier_rates'].items():
        print(f"  {data['carrier']}: ${data['rate']} ({data['estimated_delivery']})")
    
    print(f"\n🎯 Optimal Carrier: {result1['optimal_carrier']['name']} - ${result1['optimal_carrier']['rate']}")
    
    if result1['savings']:
        print(f"💵 Savings: ${result1['savings']['savings_amount']} ({result1['savings']['savings_percentage']:.1f}%)")
    
    # Test Case 2: Express shipping
    print("\n📦 Test Case 2: Express Shipping")
    result2 = await service.calculate_arbitrage(
        origin_zip="30301",
        destination_zip="94102",
        weight=1.0,
        package_type="express",
        current_rate=25.00
    )
    
    print(f"Express shipping from Atlanta to San Francisco:")
    print(f"Optimal: {result2['optimal_carrier']['name']} - ${result2['optimal_carrier']['rate']}")
    if result2['savings']:
        print(f"Savings: ${result2['savings']['savings_amount']} ({result2['savings']['savings_percentage']:.1f}%)")
    
    # Test Case 3: Multiple shipment optimization
    print("\n📦 Test Case 3: Multiple Shipment Optimization")
    shipments = [
        {"origin_zip": "90210", "destination_zip": "10001", "weight": 2.0, "current_rate": 10.00},
        {"origin_zip": "30301", "destination_zip": "94102", "weight": 1.5, "current_rate": 15.00},
        {"origin_zip": "60601", "destination_zip": "33101", "weight": 3.0, "current_rate": 12.00}
    ]
    
    result3 = await service.optimize_shipping(shipments, "cost")
    
    print(f"Total shipments: {result3['summary']['total_shipments']}")
    print(f"Total original cost: ${result3['summary']['total_original_cost']:.2f}")
    print(f"Total optimized cost: ${result3['summary']['total_optimized_cost']:.2f}")
    print(f"Total savings: ${result3['summary']['total_savings']:.2f} ({result3['summary']['savings_percentage']:.1f}%)")
    
    print("\n✅ Shipping arbitrage calculations completed successfully!")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_shipping_arbitrage())
        if result:
            print("\n🎉 All shipping arbitrage tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
