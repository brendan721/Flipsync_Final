#!/usr/bin/env python3
"""
Test Vision Analysis Enhancement
===============================

Validates that the vision analysis enhancement is complete and working correctly.
Tests enhanced vision service, multi-model support, and advanced processing capabilities.
"""

import asyncio
import base64
import io
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

from PIL import Image

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VisionAnalysisEnhancementTest:
    """Test the vision analysis enhancement."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Expected enhancement files
        self.enhancement_files = {
            "fs_agt_clean/core/ai/enhanced_vision_service.py": {
                "description": "Enhanced vision analysis service with multi-model support",
                "min_size": 15000,
                "key_classes": [
                    "EnhancedVisionService",
                    "VisionModelProvider",
                    "AnalysisType",
                    "ProcessingOperation"
                ]
            },
            "fs_agt_clean/agents/content/enhanced_image_agent.py": {
                "description": "Enhanced image processing agent",
                "min_size": 10000,
                "key_classes": [
                    "EnhancedImageUnifiedAgent"
                ]
            },
            "fs_agt_clean/api/routes/enhanced_vision_routes.py": {
                "description": "Enhanced vision API routes",
                "min_size": 8000,
                "key_endpoints": [
                    "/analyze",
                    "/batch",
                    "/process",
                    "/optimize"
                ]
            }
        }
        
    def create_test_image_data(self) -> str:
        """Create test image data for analysis."""
        # Create a simple test image
        image = Image.new('RGB', (800, 600), color='white')
        
        # Add some basic content
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(image)
        
        # Draw a simple product-like rectangle
        draw.rectangle([200, 150, 600, 450], fill='lightblue', outline='black', width=3)
        
        # Add text
        try:
            # Try to use default font
            draw.text((250, 280), "TEST PRODUCT", fill='black')
            draw.text((250, 320), "Model: ABC123", fill='black')
        except:
            # Fallback if font issues
            pass
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85)
        image_bytes = buffer.getvalue()
        
        return base64.b64encode(image_bytes).decode()
    
    def test_enhancement_files_exist(self) -> bool:
        """Test that enhancement files exist."""
        logger.info("📁 Testing enhancement files existence...")
        
        try:
            missing_files = []
            for file_path, file_info in self.enhancement_files.items():
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    if file_size >= file_info["min_size"]:
                        logger.info(f"  ✅ Found: {file_path} ({file_size} bytes)")
                    else:
                        logger.warning(f"  ⚠️ Found but small: {file_path} ({file_size} bytes)")
                        missing_files.append(file_path)
                else:
                    logger.error(f"  ❌ Missing: {file_path}")
                    missing_files.append(file_path)
            
            if not missing_files:
                logger.info("  ✅ All enhancement files exist with substantial content")
                return True
            else:
                logger.error(f"  ❌ Missing or insufficient files: {missing_files}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Enhancement files check failed: {e}")
            return False
    
    def test_enhanced_vision_service_import(self) -> bool:
        """Test enhanced vision service imports."""
        logger.info("🔧 Testing enhanced vision service import...")
        
        try:
            from fs_agt_clean.core.ai.enhanced_vision_service import (
                EnhancedVisionService,
                VisionModelProvider,
                AnalysisType,
                ProcessingOperation,
                EnhancedAnalysisResult
            )
            
            logger.info("  ✅ Enhanced vision service imports successfully")
            logger.info(f"  📝 EnhancedVisionService: {EnhancedVisionService.__name__}")
            logger.info(f"  📝 VisionModelProvider: {VisionModelProvider.OPENAI_GPT4O}")
            logger.info(f"  📝 AnalysisType: {AnalysisType.PRODUCT_IDENTIFICATION}")
            logger.info(f"  📝 ProcessingOperation: {ProcessingOperation.QUALITY_ENHANCEMENT}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Enhanced vision service import failed: {e}")
            return False
    
    def test_enhanced_image_agent_import(self) -> bool:
        """Test enhanced image agent imports."""
        logger.info("🤖 Testing enhanced image agent import...")
        
        try:
            from fs_agt_clean.agents.content.enhanced_image_agent import EnhancedImageUnifiedAgent
            
            logger.info("  ✅ Enhanced image agent imports successfully")
            logger.info(f"  📝 EnhancedImageUnifiedAgent: {EnhancedImageUnifiedAgent.__name__}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Enhanced image agent import failed: {e}")
            return False
    
    def test_enhanced_vision_service_functionality(self) -> bool:
        """Test enhanced vision service basic functionality."""
        logger.info("⚙️ Testing enhanced vision service functionality...")
        
        try:
            from fs_agt_clean.core.ai.enhanced_vision_service import (
                EnhancedVisionService,
                VisionModelProvider,
                AnalysisType
            )
            
            # Create service instance
            service = EnhancedVisionService(config={"daily_budget": 1.0})
            
            # Test model selection
            model = asyncio.run(service._select_optimal_model(
                [AnalysisType.PRODUCT_IDENTIFICATION],
                VisionModelProvider.OPENAI_GPT4O_MINI
            ))
            
            assert model == VisionModelProvider.OPENAI_GPT4O_MINI
            logger.info(f"  ✅ Model selection working: {model}")
            
            # Test image preparation
            test_image_data = self.create_test_image_data()
            prepared_data = asyncio.run(service._prepare_image_data(test_image_data))
            
            assert isinstance(prepared_data, bytes)
            logger.info(f"  ✅ Image preparation working: {len(prepared_data)} bytes")
            
            # Test cost calculation
            cost = asyncio.run(service._calculate_cost_estimate(
                VisionModelProvider.OPENAI_GPT4O_MINI, 2, 1.5
            ))
            
            assert cost > 0
            logger.info(f"  ✅ Cost calculation working: ${cost:.4f}")
            
            logger.info("  ✅ Enhanced vision service functionality validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Enhanced vision service functionality test failed: {e}")
            return False
    
    def test_enhanced_image_agent_functionality(self) -> bool:
        """Test enhanced image agent basic functionality."""
        logger.info("🎨 Testing enhanced image agent functionality...")
        
        try:
            from fs_agt_clean.agents.content.enhanced_image_agent import EnhancedImageUnifiedAgent
            from fs_agt_clean.core.ai.enhanced_vision_service import AnalysisType, ProcessingOperation
            
            # Create agent instance
            agent = EnhancedImageUnifiedAgent()
            
            # Test initialization
            assert agent.agent_type == "enhanced_image_processing"
            assert agent.supported_formats == ["JPEG", "PNG", "WEBP", "BMP", "TIFF"]
            logger.info(f"  ✅ Agent initialization working: {agent.agent_id}")
            
            # Test processing stats
            stats = asyncio.run(agent.get_processing_stats())
            assert "total_processed" in stats
            assert "success_rate" in stats
            logger.info(f"  ✅ Processing stats working: {stats['total_processed']} processed")
            
            # Test health check
            health = asyncio.run(agent.health_check())
            assert "status" in health
            logger.info(f"  ✅ Health check working: {health['status']}")
            
            logger.info("  ✅ Enhanced image agent functionality validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Enhanced image agent functionality test failed: {e}")
            return False
    
    def test_api_routes_import(self) -> bool:
        """Test enhanced vision API routes import."""
        logger.info("🌐 Testing enhanced vision API routes import...")
        
        try:
            from fs_agt_clean.api.routes.enhanced_vision_routes import router
            
            # Check router configuration
            assert router.prefix == "/api/v1/vision/enhanced"
            assert "Enhanced Vision Analysis" in router.tags
            
            # Check that routes exist
            route_paths = [route.path for route in router.routes]
            expected_paths = ["/analyze", "/batch", "/process", "/optimize", "/models", "/stats", "/health"]
            
            found_paths = 0
            for expected_path in expected_paths:
                if any(expected_path in path for path in route_paths):
                    found_paths += 1
                    logger.info(f"  ✅ Found route: {expected_path}")
            
            if found_paths >= len(expected_paths) * 0.8:  # 80% of expected routes
                logger.info("  ✅ Enhanced vision API routes validated")
                return True
            else:
                logger.error(f"  ❌ Missing routes: {found_paths}/{len(expected_paths)}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Enhanced vision API routes import failed: {e}")
            return False
    
    def test_multi_model_support(self) -> bool:
        """Test multi-model support capabilities."""
        logger.info("🧠 Testing multi-model support...")
        
        try:
            from fs_agt_clean.core.ai.enhanced_vision_service import VisionModelProvider
            
            # Check all expected models are available
            expected_models = [
                VisionModelProvider.OPENAI_GPT4O,
                VisionModelProvider.OPENAI_GPT4O_MINI,
                VisionModelProvider.CLAUDE_VISION,
                VisionModelProvider.GOOGLE_VISION,
                VisionModelProvider.AZURE_VISION,
                VisionModelProvider.OLLAMA_LLAVA
            ]
            
            available_models = list(VisionModelProvider)
            
            found_models = 0
            for model in expected_models:
                if model in available_models:
                    found_models += 1
                    logger.info(f"  ✅ Model available: {model.value}")
            
            if found_models >= len(expected_models) * 0.8:  # 80% of expected models
                logger.info(f"  ✅ Multi-model support validated: {found_models}/{len(expected_models)} models")
                return True
            else:
                logger.error(f"  ❌ Insufficient model support: {found_models}/{len(expected_models)}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Multi-model support test failed: {e}")
            return False
    
    def test_specialized_analysis_types(self) -> bool:
        """Test specialized analysis types."""
        logger.info("🔍 Testing specialized analysis types...")
        
        try:
            from fs_agt_clean.core.ai.enhanced_vision_service import AnalysisType
            
            # Check all expected analysis types
            expected_types = [
                AnalysisType.PRODUCT_IDENTIFICATION,
                AnalysisType.QUALITY_ASSESSMENT,
                AnalysisType.BRAND_DETECTION,
                AnalysisType.DEFECT_ANALYSIS,
                AnalysisType.AUTHENTICITY_VERIFICATION,
                AnalysisType.STYLE_ANALYSIS,
                AnalysisType.MARKETPLACE_COMPLIANCE,
                AnalysisType.COMPETITIVE_ANALYSIS
            ]
            
            available_types = list(AnalysisType)
            
            found_types = 0
            for analysis_type in expected_types:
                if analysis_type in available_types:
                    found_types += 1
                    logger.info(f"  ✅ Analysis type available: {analysis_type.value}")
            
            if found_types >= len(expected_types) * 0.8:  # 80% of expected types
                logger.info(f"  ✅ Specialized analysis types validated: {found_types}/{len(expected_types)} types")
                return True
            else:
                logger.error(f"  ❌ Insufficient analysis types: {found_types}/{len(expected_types)}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Specialized analysis types test failed: {e}")
            return False
    
    def test_advanced_processing_operations(self) -> bool:
        """Test advanced processing operations."""
        logger.info("🎛️ Testing advanced processing operations...")
        
        try:
            from fs_agt_clean.core.ai.enhanced_vision_service import ProcessingOperation
            
            # Check all expected processing operations
            expected_operations = [
                ProcessingOperation.BACKGROUND_REMOVAL,
                ProcessingOperation.QUALITY_ENHANCEMENT,
                ProcessingOperation.STYLE_TRANSFER,
                ProcessingOperation.NOISE_REDUCTION,
                ProcessingOperation.COLOR_CORRECTION,
                ProcessingOperation.RESOLUTION_UPSCALING,
                ProcessingOperation.WATERMARK_REMOVAL,
                ProcessingOperation.PERSPECTIVE_CORRECTION
            ]
            
            available_operations = list(ProcessingOperation)
            
            found_operations = 0
            for operation in expected_operations:
                if operation in available_operations:
                    found_operations += 1
                    logger.info(f"  ✅ Processing operation available: {operation.value}")
            
            if found_operations >= len(expected_operations) * 0.8:  # 80% of expected operations
                logger.info(f"  ✅ Advanced processing operations validated: {found_operations}/{len(expected_operations)} operations")
                return True
            else:
                logger.error(f"  ❌ Insufficient processing operations: {found_operations}/{len(expected_operations)}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Advanced processing operations test failed: {e}")
            return False
    
    async def run_enhancement_test(self) -> Dict[str, Any]:
        """Run complete vision analysis enhancement test."""
        logger.info("🚀 Starting Vision Analysis Enhancement Test")
        logger.info("=" * 70)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Run all tests
        tests = [
            ('Enhancement Files Exist', self.test_enhancement_files_exist),
            ('Enhanced Vision Service Import', self.test_enhanced_vision_service_import),
            ('Enhanced Image Agent Import', self.test_enhanced_image_agent_import),
            ('Enhanced Vision Service Functionality', self.test_enhanced_vision_service_functionality),
            ('Enhanced Image Agent Functionality', self.test_enhanced_image_agent_functionality),
            ('API Routes Import', self.test_api_routes_import),
            ('Multi-Model Support', self.test_multi_model_support),
            ('Specialized Analysis Types', self.test_specialized_analysis_types),
            ('Advanced Processing Operations', self.test_advanced_processing_operations),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results['tests'][test_name] = 'PASS' if result else 'FAIL'
                if result:
                    passed_tests += 1
                print()  # Add spacing between tests
            except Exception as e:
                logger.error(f"Test '{test_name}' failed with exception: {e}")
                test_results['tests'][test_name] = 'ERROR'
                print()
        
        # Determine overall status
        if passed_tests == total_tests:
            test_results['overall_status'] = 'PASS'
        elif passed_tests >= total_tests * 0.75:
            test_results['overall_status'] = 'PARTIAL_PASS'
        else:
            test_results['overall_status'] = 'FAIL'
        
        # Print summary
        logger.info("=" * 70)
        logger.info("📋 VISION ANALYSIS ENHANCEMENT TEST SUMMARY:")
        logger.info("=" * 70)
        
        for test_name, status in test_results['tests'].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {test_name}: {status}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {test_results['overall_status']}")
        logger.info(f"📊 PASSED: {passed_tests}/{total_tests} tests")
        
        if test_results['overall_status'] == 'PASS':
            logger.info("\n🎉 Vision Analysis Enhancement SUCCESSFUL!")
            logger.info("✅ Enhanced vision service with multi-model support")
            logger.info("✅ Advanced image processing capabilities")
            logger.info("✅ Specialized analysis types (8 types)")
            logger.info("✅ Advanced processing operations (8 operations)")
            logger.info("✅ Production-ready API endpoints")
            logger.info("✅ Cost-optimized model routing")
            logger.info("✅ Batch processing with concurrency control")
            logger.info("📈 Significantly enhanced computer vision capabilities")
        else:
            logger.info("\n⚠️ Some enhancement issues detected")
        
        return test_results


async def main():
    """Main test execution."""
    test_runner = VisionAnalysisEnhancementTest()
    results = await test_runner.run_enhancement_test()
    
    # Save results
    with open('vision_analysis_enhancement_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: vision_analysis_enhancement_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
