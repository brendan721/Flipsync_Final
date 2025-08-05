#!/usr/bin/env python3
"""
Integrated eBay Listing Optimizer for FlipSync.

This service orchestrates the three critical components of eBay listing optimization:
1. ItemSpecificsMaximizer - Generates comprehensive item specifics
2. KeywordConsistencyEngine - Validates keyword alignment across components
3. FactualStorytellingGenerator - Creates buyer-focused descriptions
4. EbayTitleOptimizer - Optimizes titles for search visibility

The service ensures seamless integration and keyword consistency across all listing
components while maintaining production-grade performance and reliability.

Key Features:
- Complete listing optimization workflow
- Cross-component keyword consistency validation (target: 80+ consistency score)
- Production database integration (flipsync_agentic_test on 174.138.77.110)
- Real eBay API integration for accurate data
- Sub-1000ms performance for complete workflow
- Comprehensive optimization metrics and reporting
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .item_specifics_maximizer import ItemSpecificsMaximizer
from .keyword_consistency_engine import KeywordConsistencyEngine
from .factual_storytelling_generator import FactualStorytellingGenerator
from .ebay_title_optimizer import EbayTitleOptimizer

logger = logging.getLogger(__name__)


class IntegratedListingOptimizer:
    """
    Comprehensive eBay listing optimizer that orchestrates all optimization components
    to create fully optimized, SEO-ready eBay listings with maximum organic visibility.
    """

    def __init__(self, ebay_service=None):
        """Initialize the integrated listing optimizer.
        
        Args:
            ebay_service: Production eBay service for real API integration
        """
        self.ebay_service = ebay_service
        
        # Initialize optimization components
        self.item_specifics_maximizer = ItemSpecificsMaximizer(ebay_service)
        self.keyword_consistency_engine = KeywordConsistencyEngine()
        self.description_generator = FactualStorytellingGenerator()
        self.title_optimizer = EbayTitleOptimizer()
        
        # Performance targets
        self.performance_targets = {
            'total_execution_time': 1000,  # ms
            'consistency_score': 80,       # minimum
            'title_optimization_score': 80, # minimum
            'description_word_count_min': 200,
            'description_word_count_max': 700,
            'specifics_count_min': 20
        }

    async def optimize_complete_listing(
        self,
        product_data: Dict[str, Any],
        category_id: str,
        target_keywords: Optional[List[str]] = None,
        original_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform complete eBay listing optimization with all components.
        
        Args:
            product_data: Original product data
            category_id: eBay category ID
            target_keywords: Target keywords for SEO optimization
            original_title: Original title for comparison (optional)
            
        Returns:
            Complete optimized listing with all components and metrics
        """
        start_time = time.perf_counter()
        
        try:
            logger.info(f"Starting complete listing optimization for category {category_id}")
            
            # Step 1: Generate comprehensive item specifics
            specifics_result = await self._generate_item_specifics(
                product_data, category_id, target_keywords
            )
            
            # Step 2: Optimize eBay title
            title_result = await self._optimize_title(
                product_data, specifics_result['item_specifics'], 
                category_id, target_keywords, original_title
            )
            
            # Step 3: Generate factual storytelling description
            description_result = await self._generate_description(
                product_data, specifics_result['item_specifics'],
                title_result['optimized_title'], category_id, target_keywords
            )
            
            # Step 4: Validate keyword consistency across all components
            consistency_result = await self._validate_keyword_consistency(
                title_result['optimized_title'],
                specifics_result['item_specifics'],
                description_result['description'],
                target_keywords
            )
            
            # Step 5: Generate comprehensive optimization report
            optimization_report = self._generate_optimization_report(
                specifics_result, title_result, description_result, 
                consistency_result, product_data, category_id
            )
            
            # Step 6: Validate production readiness
            production_validation = self._validate_production_readiness(
                specifics_result, title_result, description_result, consistency_result
            )
            
            total_execution_time = (time.perf_counter() - start_time) * 1000
            
            # Compile complete optimized listing
            optimized_listing = {
                # Core optimized components
                'optimized_title': title_result['optimized_title'],
                'item_specifics': specifics_result['item_specifics'],
                'description': description_result['description'],
                
                # Component results
                'specifics_result': specifics_result,
                'title_result': title_result,
                'description_result': description_result,
                'consistency_result': consistency_result,
                
                # Optimization metrics
                'optimization_report': optimization_report,
                'production_validation': production_validation,
                
                # Performance metrics
                'total_execution_time_ms': round(total_execution_time, 2),
                'performance_targets_met': total_execution_time < self.performance_targets['total_execution_time'],
                
                # Metadata
                'category_id': category_id,
                'target_keywords': target_keywords or [],
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'production_ready': production_validation['overall_ready']
            }
            
            logger.info(f"Listing optimization completed in {total_execution_time:.2f}ms")
            return optimized_listing
            
        except Exception as e:
            logger.error(f"Error in complete listing optimization: {e}")
            raise

    async def _generate_item_specifics(
        self, product_data: Dict[str, Any], category_id: str, target_keywords: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate comprehensive item specifics using ItemSpecificsMaximizer."""
        try:
            result = await self.item_specifics_maximizer.maximize_item_specifics(
                product_data=product_data,
                category_id=category_id,
                target_keywords=target_keywords
            )
            
            logger.info(f"Generated {result['total_specifics']} item specifics with SEO score {result['seo_score']}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating item specifics: {e}")
            raise

    async def _optimize_title(
        self, product_data: Dict[str, Any], item_specifics: Dict[str, str],
        category_id: str, target_keywords: Optional[List[str]], original_title: Optional[str]
    ) -> Dict[str, Any]:
        """Optimize eBay title using EbayTitleOptimizer."""
        try:
            result = await self.title_optimizer.optimize_title(
                product_data=product_data,
                item_specifics=item_specifics,
                category_id=category_id,
                target_keywords=target_keywords,
                original_title=original_title
            )
            
            logger.info(f"Optimized title: '{result['optimized_title']}' ({result['character_count']} chars)")
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing title: {e}")
            raise

    async def _generate_description(
        self, product_data: Dict[str, Any], item_specifics: Dict[str, str],
        title: str, category_id: str, target_keywords: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate factual storytelling description using FactualStorytellingGenerator."""
        try:
            result = await self.description_generator.generate_description(
                product_data=product_data,
                item_specifics=item_specifics,
                title=title,
                category_id=category_id,
                target_keywords=target_keywords
            )
            
            logger.info(f"Generated description: {result['word_count']} words, {result['metadata']['specifics_utilization']}% specifics utilization")
            return result
            
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            raise

    async def _validate_keyword_consistency(
        self, title: str, item_specifics: Dict[str, str], 
        description: str, target_keywords: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Validate keyword consistency using KeywordConsistencyEngine."""
        try:
            result = await self.keyword_consistency_engine.analyze_keyword_consistency(
                title=title,
                item_specifics=item_specifics,
                description=description,
                target_keywords=target_keywords
            )
            
            logger.info(f"Keyword consistency score: {result['consistency_scores']['overall_score']}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating keyword consistency: {e}")
            raise

    def _generate_optimization_report(
        self, specifics_result: Dict[str, Any], title_result: Dict[str, Any],
        description_result: Dict[str, Any], consistency_result: Dict[str, Any],
        product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        report = {
            'optimization_summary': {
                'total_specifics_generated': specifics_result['total_specifics'],
                'specifics_seo_score': specifics_result['seo_score'],
                'title_character_count': title_result['character_count'],
                'title_optimization_score': title_result['optimization_metrics']['optimization_score'],
                'description_word_count': description_result['word_count'],
                'description_specifics_utilization': description_result['metadata']['specifics_utilization'],
                'overall_consistency_score': consistency_result['consistency_scores']['overall_score']
            },
            
            'performance_analysis': {
                'specifics_performance': {
                    'target_met': specifics_result['total_specifics'] >= self.performance_targets['specifics_count_min'],
                    'seo_target_met': specifics_result['seo_score'] >= 70,
                    'execution_time': specifics_result.get('execution_time_ms', 0)
                },
                'title_performance': {
                    'optimization_target_met': title_result['optimization_metrics']['optimization_score'] >= self.performance_targets['title_optimization_score'],
                    'length_target_met': title_result['character_count'] <= 80,
                    'sweet_spot_met': title_result['optimization_metrics']['sweet_spot_compliance'],
                    'execution_time': title_result.get('execution_time_ms', 0)
                },
                'description_performance': {
                    'word_count_target_met': (
                        self.performance_targets['description_word_count_min'] <= 
                        description_result['word_count'] <= 
                        self.performance_targets['description_word_count_max']
                    ),
                    'specifics_utilization_target_met': description_result['metadata']['specifics_utilization'] >= 90,
                    'execution_time': description_result.get('execution_time_ms', 0)
                },
                'consistency_performance': {
                    'consistency_target_met': consistency_result['consistency_scores']['overall_score'] >= self.performance_targets['consistency_score'],
                    'execution_time': consistency_result.get('execution_time_ms', 0)
                }
            },
            
            'seo_analysis': {
                'keyword_coverage': self._analyze_keyword_coverage(
                    title_result, description_result, consistency_result
                ),
                'search_optimization': {
                    'title_seo_score': title_result['seo_analysis']['search_algorithm_score'],
                    'description_seo_score': description_result['metadata']['seo_optimization_score'],
                    'overall_seo_readiness': self._calculate_overall_seo_score(
                        title_result, description_result, consistency_result
                    )
                }
            },
            
            'improvement_suggestions': self._generate_improvement_suggestions(
                specifics_result, title_result, description_result, consistency_result
            )
        }
        
        return report

    def _validate_production_readiness(
        self, specifics_result: Dict[str, Any], title_result: Dict[str, Any],
        description_result: Dict[str, Any], consistency_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate production readiness against all criteria."""
        validation = {
            'component_readiness': {
                'specifics_ready': specifics_result.get('production_ready', False),
                'title_ready': title_result.get('production_ready', False),
                'description_ready': description_result.get('production_ready', False),
                'consistency_ready': consistency_result.get('production_ready', False)
            },
            'performance_validation': {
                'specifics_count_met': specifics_result['total_specifics'] >= self.performance_targets['specifics_count_min'],
                'consistency_score_met': consistency_result['consistency_scores']['overall_score'] >= self.performance_targets['consistency_score'],
                'title_optimization_met': title_result['optimization_metrics']['optimization_score'] >= self.performance_targets['title_optimization_score'],
                'description_length_met': (
                    self.performance_targets['description_word_count_min'] <= 
                    description_result['word_count'] <= 
                    self.performance_targets['description_word_count_max']
                ),
                'specifics_utilization_met': description_result['metadata']['specifics_utilization'] >= 90
            },
            'quality_validation': {
                'seo_scores_adequate': (
                    specifics_result['seo_score'] >= 70 and
                    title_result['seo_analysis']['search_algorithm_score'] >= 70 and
                    description_result['metadata']['seo_optimization_score'] >= 70
                ),
                'keyword_consistency_adequate': consistency_result['consistency_scores']['overall_score'] >= 80,
                'content_quality_adequate': (
                    description_result['metadata']['readability_score'] >= 60 and
                    title_result['optimization_metrics']['components_included'] >= 5
                )
            }
        }
        
        # Calculate overall readiness
        component_ready = all(validation['component_readiness'].values())
        performance_ready = all(validation['performance_validation'].values())
        quality_ready = all(validation['quality_validation'].values())
        
        validation['overall_ready'] = component_ready and performance_ready and quality_ready
        validation['readiness_score'] = (
            (sum(validation['component_readiness'].values()) / len(validation['component_readiness'])) * 30 +
            (sum(validation['performance_validation'].values()) / len(validation['performance_validation'])) * 40 +
            (sum(validation['quality_validation'].values()) / len(validation['quality_validation'])) * 30
        )
        
        return validation

    def _analyze_keyword_coverage(
        self, title_result: Dict[str, Any], description_result: Dict[str, Any], 
        consistency_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze keyword coverage across all components."""
        return {
            'title_keyword_count': title_result['word_count'],
            'description_keyword_density': description_result['metadata']['keyword_density'],
            'cross_component_keywords': len(consistency_result['consistency_scores'].get('shared_keywords', [])),
            'keyword_distribution_score': consistency_result['consistency_scores']['overall_score']
        }

    def _calculate_overall_seo_score(
        self, title_result: Dict[str, Any], description_result: Dict[str, Any], 
        consistency_result: Dict[str, Any]
    ) -> float:
        """Calculate overall SEO readiness score."""
        title_seo = title_result['seo_analysis']['search_algorithm_score']
        description_seo = description_result['metadata']['seo_optimization_score']
        consistency_seo = consistency_result['consistency_scores']['overall_score']
        
        # Weighted average (title most important for eBay SEO)
        overall_seo = (title_seo * 0.4 + description_seo * 0.3 + consistency_seo * 0.3)
        return round(overall_seo, 1)

    def _generate_improvement_suggestions(
        self, specifics_result: Dict[str, Any], title_result: Dict[str, Any],
        description_result: Dict[str, Any], consistency_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized improvement suggestions."""
        suggestions = []
        
        # High priority suggestions
        if consistency_result['consistency_scores']['overall_score'] < 80:
            suggestions.extend(consistency_result['improvement_suggestions'])
        
        if title_result['optimization_metrics']['optimization_score'] < 80:
            suggestions.append({
                'priority': 'HIGH',
                'component': 'title',
                'suggestion': 'Optimize title structure and keyword positioning',
                'current_score': title_result['optimization_metrics']['optimization_score'],
                'target_score': 80
            })
        
        if description_result['metadata']['specifics_utilization'] < 90:
            suggestions.append({
                'priority': 'MEDIUM',
                'component': 'description',
                'suggestion': 'Increase utilization of item specifics in description',
                'current_utilization': description_result['metadata']['specifics_utilization'],
                'target_utilization': 90
            })
        
        # SEO improvement suggestions
        if title_result['seo_analysis']['search_algorithm_score'] < 70:
            suggestions.extend([{
                'priority': 'HIGH',
                'component': 'title',
                'suggestion': rec,
                'type': 'seo_optimization'
            } for rec in title_result['seo_analysis'].get('seo_recommendations', [])])
        
        return suggestions[:10]  # Limit to top 10 suggestions

    async def optimize_for_category(
        self, product_data: Dict[str, Any], category_id: str, 
        optimization_level: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """
        Optimize listing for specific eBay category with category-specific rules.
        
        Args:
            product_data: Product data
            category_id: eBay category ID
            optimization_level: 'basic', 'standard', or 'comprehensive'
            
        Returns:
            Category-optimized listing
        """
        # Category-specific target keywords
        category_keywords = {
            '9355': ['smartphone', 'unlocked', 'cell phone', 'mobile'],  # Cell Phones
            '95672': ['basketball shoes', 'sneakers', 'athletic', 'sports'],  # Basketball Shoes
            '31388': ['tablet', 'touchscreen', 'portable', 'WiFi'],  # Tablets
            'default': ['quality', 'premium', 'authentic']
        }
        
        target_keywords = category_keywords.get(category_id, category_keywords['default'])
        
        if optimization_level == 'comprehensive':
            return await self.optimize_complete_listing(
                product_data, category_id, target_keywords
            )
        else:
            # Simplified optimization for basic/standard levels
            specifics_result = await self._generate_item_specifics(
                product_data, category_id, target_keywords
            )
            
            title_result = await self._optimize_title(
                product_data, specifics_result['item_specifics'], 
                category_id, target_keywords, None
            )
            
            return {
                'optimized_title': title_result['optimized_title'],
                'item_specifics': specifics_result['item_specifics'],
                'optimization_level': optimization_level,
                'category_id': category_id
            }
