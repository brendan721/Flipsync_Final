#!/usr/bin/env python3
import sys
import asyncio
sys.path.append('/app')

async def test_ebay_simple():
    try:
        from fs_agt_clean.agents.market.ebay_client import eBayClient
        
        print('🛒 eBay Integration Validation')
        print('=' * 40)
        
        client = eBayClient()
        print('✅ eBay Client created successfully')
        
        async with client:
            print('✅ eBay authentication successful')
            
            # Test credential validation
            print('\n🔑 Testing Credential Validation...')
            try:
                is_valid = await client.validate_credentials()
                print(f'  Credentials valid: {is_valid}')
                cred_test = True
            except Exception as e:
                print(f'  Credential validation error: {e}')
                cred_test = False
            
            # Test product search
            print('\n🔍 Testing Product Search...')
            try:
                products = await client.search_products('test', limit=1)
                print(f'  Search method working: {products is not None}')
                print(f'  Products found: {len(products) if products else 0}')
                search_test = True
            except Exception as e:
                print(f'  Product search error: {e}')
                search_test = False
            
            # Test competitive pricing
            print('\n💰 Testing Competitive Pricing...')
            try:
                prices = await client.get_competitive_prices('test')
                print(f'  Pricing method working: {prices is not None}')
                print(f'  Prices found: {len(prices) if prices else 0}')
                pricing_test = True
            except Exception as e:
                print(f'  Competitive pricing error: {e}')
                pricing_test = False
        
        print('\n📊 eBay Integration Summary:')
        print(f'  Client Creation: ✅ Success')
        print(f'  Authentication: ✅ Success')
        print(f'  Credential Validation: {"✅" if cred_test else "❌"} {"Success" if cred_test else "Failed"}')
        print(f'  Product Search: {"✅" if search_test else "❌"} {"Success" if search_test else "Failed"}')
        print(f'  Competitive Pricing: {"✅" if pricing_test else "❌"} {"Success" if pricing_test else "Failed"}')
        
        overall_success = cred_test and search_test and pricing_test
        print(f'  Overall Status: {"✅ PASS" if overall_success else "❌ FAIL"}')
        
        return overall_success
        
    except Exception as e:
        print(f'❌ eBay integration failed: {e}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    result = await test_ebay_simple()
    print(f'\nFinal Result: {"SUCCESS" if result else "FAILURE"}')
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
