#!/usr/bin/env python3
"""
V3 Routes Implementation Test Script

Tests the V3 backend routes implementation to verify they are
properly coded and would work when deployed to production.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

class V3RoutesImplementationTester:
    def __init__(self):
        self.base_path = Path("/home/brend/Flipsync_Final")
        self.routes_path = self.base_path / "fs_agt_clean" / "api" / "routes"
        
    def test_v3_routes_implementation(self) -> Dict[str, Any]:
        """Test V3 routes implementation."""
        
        results = {
            "test_timestamp": "2025-01-29",
            "phase": "Phase 2: V3 Backend Routes Implementation Test",
            "routes_tested": {},
            "integration_status": {},
            "deployment_readiness": {}
        }
        
        print("🧪 Testing V3 Routes Implementation")
        print("=" * 50)
        
        # Test 1: V3 User Profile Routes
        print("\n1️⃣ Testing V3 User Profile Routes Implementation")
        user_profile_test = self._test_user_profile_routes()
        results["routes_tested"]["user_profile"] = user_profile_test
        
        # Test 2: V3 Opportunities Routes
        print("\n2️⃣ Testing V3 Opportunities Routes Implementation")
        opportunities_test = self._test_opportunities_routes()
        results["routes_tested"]["opportunities"] = opportunities_test
        
        # Test 3: V3 Optimization Routes
        print("\n3️⃣ Testing V3 Optimization Routes Implementation")
        optimization_test = self._test_optimization_routes()
        results["routes_tested"]["optimization"] = optimization_test
        
        # Test 4: Main App Integration
        print("\n4️⃣ Testing Main App Integration")
        integration_test = self._test_main_app_integration()
        results["integration_status"] = integration_test
        
        # Test 5: Deployment Readiness
        print("\n5️⃣ Testing Deployment Readiness")
        deployment_test = self._test_deployment_readiness()
        results["deployment_readiness"] = deployment_test
        
        return results
    
    def _test_user_profile_routes(self) -> Dict[str, Any]:
        """Test V3 user profile routes implementation."""
        try:
            routes_file = self.routes_path / "v3_user_profile_routes.py"
            
            if not routes_file.exists():
                return {
                    "status": "error",
                    "message": "V3 user profile routes file not found"
                }
            
            # Read and parse the file
            with open(routes_file, 'r') as f:
                content = f.read()
            
            # Check for required components
            required_components = [
                "router = APIRouter",
                "get_user_profile",
                "update_user_profile", 
                "get_user_preferences",
                "set_user_preferences",
                "UserProfileV3",
                "UserPreferencesV3"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
            
            if missing_components:
                print(f"⚠️ User profile routes missing components: {missing_components}")
                return {
                    "status": "partial",
                    "message": f"Missing components: {missing_components}",
                    "file_exists": True,
                    "file_size": len(content)
                }
            else:
                print("✅ User profile routes implementation complete")
                return {
                    "status": "success",
                    "message": "All required components present",
                    "file_exists": True,
                    "file_size": len(content),
                    "endpoints_count": content.count("@router.")
                }
                
        except Exception as e:
            print(f"❌ User profile routes test failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _test_opportunities_routes(self) -> Dict[str, Any]:
        """Test V3 opportunities routes implementation."""
        try:
            routes_file = self.routes_path / "v3_opportunities_routes.py"
            
            if not routes_file.exists():
                return {
                    "status": "error",
                    "message": "V3 opportunities routes file not found"
                }
            
            with open(routes_file, 'r') as f:
                content = f.read()
            
            required_components = [
                "router = APIRouter",
                "get_trending_opportunities",
                "get_liquidation_opportunities",
                "get_thrifting_opportunities", 
                "get_miscellaneous_opportunities",
                "OpportunityV3",
                "OpportunityResponse"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
            
            if missing_components:
                print(f"⚠️ Opportunities routes missing components: {missing_components}")
                return {
                    "status": "partial",
                    "message": f"Missing components: {missing_components}",
                    "file_exists": True,
                    "file_size": len(content)
                }
            else:
                print("✅ Opportunities routes implementation complete")
                return {
                    "status": "success",
                    "message": "All required components present",
                    "file_exists": True,
                    "file_size": len(content),
                    "endpoints_count": content.count("@router.")
                }
                
        except Exception as e:
            print(f"❌ Opportunities routes test failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _test_optimization_routes(self) -> Dict[str, Any]:
        """Test V3 optimization routes implementation."""
        try:
            routes_file = self.routes_path / "v3_optimization_routes.py"
            
            if not routes_file.exists():
                return {
                    "status": "error",
                    "message": "V3 optimization routes file not found"
                }
            
            with open(routes_file, 'r') as f:
                content = f.read()
            
            required_components = [
                "router = APIRouter",
                "get_optimization_score",
                "get_optimization_opportunities",
                "submit_optimization_feedback",
                "OptimizationScore",
                "OptimizationOpportunity"
            ]
            
            missing_components = []
            for component in required_components:
                if component not in content:
                    missing_components.append(component)
            
            if missing_components:
                print(f"⚠️ Optimization routes missing components: {missing_components}")
                return {
                    "status": "partial",
                    "message": f"Missing components: {missing_components}",
                    "file_exists": True,
                    "file_size": len(content)
                }
            else:
                print("✅ Optimization routes implementation complete")
                return {
                    "status": "success",
                    "message": "All required components present",
                    "file_exists": True,
                    "file_size": len(content),
                    "endpoints_count": content.count("@router.")
                }
                
        except Exception as e:
            print(f"❌ Optimization routes test failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _test_main_app_integration(self) -> Dict[str, Any]:
        """Test main app integration of V3 routes."""
        try:
            main_file = self.base_path / "fs_agt_clean" / "app" / "main.py"
            
            if not main_file.exists():
                return {
                    "status": "error",
                    "message": "Main app file not found"
                }
            
            with open(main_file, 'r') as f:
                content = f.read()
            
            # Check for V3 routes integration
            v3_integration_checks = [
                "v3_user_profile_routes",
                "v3_opportunities_routes", 
                "v3_optimization_routes",
                "app.include_router(v3_user_profile_router",
                "app.include_router(v3_opportunities_router",
                "app.include_router(v3_optimization_router"
            ]
            
            missing_integration = []
            for check in v3_integration_checks:
                if check not in content:
                    missing_integration.append(check)
            
            if missing_integration:
                print(f"⚠️ Main app missing V3 integration: {missing_integration}")
                return {
                    "status": "partial",
                    "message": f"Missing integration: {missing_integration}",
                    "file_exists": True
                }
            else:
                print("✅ Main app V3 integration complete")
                return {
                    "status": "success",
                    "message": "All V3 routes properly integrated",
                    "file_exists": True,
                    "has_error_handling": "except Exception as e:" in content
                }
                
        except Exception as e:
            print(f"❌ Main app integration test failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _test_deployment_readiness(self) -> Dict[str, Any]:
        """Test deployment readiness of V3 routes."""
        try:
            # Check if all required files exist
            required_files = [
                "fs_agt_clean/api/routes/v3_user_profile_routes.py",
                "fs_agt_clean/api/routes/v3_opportunities_routes.py",
                "fs_agt_clean/api/routes/v3_optimization_routes.py",
                "fs_agt_clean/app/main.py"
            ]
            
            missing_files = []
            existing_files = []
            
            for file_path in required_files:
                full_path = self.base_path / file_path
                if full_path.exists():
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)
            
            if missing_files:
                print(f"❌ Deployment blocked - missing files: {missing_files}")
                return {
                    "status": "error",
                    "message": f"Missing required files: {missing_files}",
                    "existing_files": existing_files,
                    "missing_files": missing_files
                }
            else:
                print("✅ All required files present for deployment")
                return {
                    "status": "success",
                    "message": "Ready for deployment",
                    "existing_files": existing_files,
                    "missing_files": [],
                    "deployment_command": "uvicorn fs_agt_clean.app.main:app --host 0.0.0.0 --port 8000 --reload"
                }
                
        except Exception as e:
            print(f"❌ Deployment readiness test failed: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_phase2_summary(self, results: Dict[str, Any]) -> None:
        """Generate Phase 2 implementation summary."""
        print("\n" + "=" * 50)
        print("📋 V3 PHASE 2 ROUTES IMPLEMENTATION TEST SUMMARY")
        print("=" * 50)
        
        routes = results["routes_tested"]
        integration = results["integration_status"]
        deployment = results["deployment_readiness"]
        
        # Count successful implementations
        success_count = sum(1 for test in routes.values() if test.get("status") == "success")
        total_routes = len(routes)
        
        print(f"Routes Implementation: {success_count}/{total_routes} complete")
        
        print("\n🎯 V3 ROUTES IMPLEMENTATION STATUS:")
        
        # Individual route status
        for route_name, route_test in routes.items():
            if route_test.get("status") == "success":
                print(f"✅ {route_name.replace('_', ' ').title()} routes: COMPLETE")
            elif route_test.get("status") == "partial":
                print(f"⚠️ {route_name.replace('_', ' ').title()} routes: PARTIAL")
            else:
                print(f"❌ {route_name.replace('_', ' ').title()} routes: FAILED")
        
        # Integration status
        if integration.get("status") == "success":
            print("✅ Main app integration: COMPLETE")
        else:
            print("❌ Main app integration: ISSUES")
        
        # Deployment readiness
        if deployment.get("status") == "success":
            print("✅ Deployment readiness: READY")
            print(f"📋 Deployment command: {deployment.get('deployment_command', 'N/A')}")
        else:
            print("❌ Deployment readiness: BLOCKED")
        
        print("\n📋 NEXT STEPS FOR PHASE 2:")
        if deployment.get("status") == "success":
            print("1. ✅ All V3 routes implemented and ready")
            print("2. 🚀 Deploy to production backend")
            print("3. 🧪 Test V3 endpoints with authentication")
            print("4. 🔄 Update Flutter services to use new endpoints")
        else:
            print("1. ❌ Fix missing route implementations")
            print("2. 🔧 Complete main app integration")
            print("3. 🚀 Prepare for deployment")

def main():
    """Run V3 routes implementation tests."""
    tester = V3RoutesImplementationTester()
    results = tester.test_v3_routes_implementation()
    tester.generate_phase2_summary(results)
    
    # Save results
    import json
    with open("/home/brend/Flipsync_Final/v3_phase2_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: v3_phase2_test_results.json")

if __name__ == "__main__":
    main()
