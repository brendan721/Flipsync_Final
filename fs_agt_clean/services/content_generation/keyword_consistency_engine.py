#!/usr/bin/env python3
"""
Enhanced Keyword Consistency Engine for FlipSync eBay Listing Optimization.

This service validates and optimizes keyword alignment across title, item specifics, 
and description components to maximize SEO impact and organic visibility. It provides
comprehensive consistency scoring, actionable improvement suggestions, and cross-component
keyword sharing optimization.

Key Features:
- Advanced keyword consistency scoring algorithm (target: 80+ consistency score)
- Semantic keyword analysis and grouping
- Cross-component keyword sharing optimization
- Actionable improvement suggestions with priority ranking
- Integration with ItemSpecificsMaximizer for comprehensive optimization
- Production-grade performance and reliability
"""

import asyncio
import logging
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class KeywordConsistencyEngine:
    """
    Enhanced keyword consistency engine that validates and optimizes keyword alignment
    across all eBay listing components for maximum SEO impact.
    """

    def __init__(self):
        """Initialize the keyword consistency engine."""
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'new', 'used', 'free', 'fast', 'best',
            'top', 'high', 'low', 'great', 'good', 'nice', 'this', 'that'
        }
        
        # Keyword importance weights for different components
        self.component_weights = {
            'title': 1.0,      # Highest weight - most important for SEO
            'specifics': 0.8,  # High weight - structured data
            'description': 0.6  # Medium weight - supporting content
        }
        
        # Semantic keyword groups for better matching
        self.semantic_groups = {
            'size': ['size', 'dimension', 'measurement', 'length', 'width', 'height'],
            'color': ['color', 'colour', 'shade', 'hue', 'tone'],
            'material': ['material', 'fabric', 'composition', 'made', 'construction'],
            'condition': ['condition', 'state', 'quality', 'grade'],
            'brand': ['brand', 'manufacturer', 'make', 'company'],
            'model': ['model', 'version', 'type', 'series', 'edition'],
            'feature': ['feature', 'function', 'capability', 'benefit', 'advantage'],
            'style': ['style', 'design', 'pattern', 'look', 'appearance']
        }

    async def analyze_keyword_consistency(
        self,
        title: str,
        item_specifics: Dict[str, str],
        description: str,
        target_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive keyword consistency analysis across all listing components.
        
        Args:
            title: eBay listing title
            item_specifics: Generated item specifics dictionary
            description: Product description
            target_keywords: Optional target keywords for optimization
            
        Returns:
            Comprehensive consistency analysis with scores and suggestions
        """
        start_time = time.perf_counter()
        
        try:
            # Extract and normalize keywords from each component
            title_keywords = self._extract_keywords(title, 'title')
            specifics_keywords = self._extract_keywords_from_specifics(item_specifics)
            description_keywords = self._extract_keywords(description, 'description')
            
            # Analyze keyword distribution and importance
            keyword_analysis = self._analyze_keyword_distribution(
                title_keywords, specifics_keywords, description_keywords
            )
            
            # Calculate comprehensive consistency scores
            consistency_scores = self._calculate_consistency_scores(
                title_keywords, specifics_keywords, description_keywords, keyword_analysis
            )
            
            # Generate semantic keyword mapping
            semantic_mapping = self._generate_semantic_mapping(
                title_keywords, specifics_keywords, description_keywords
            )
            
            # Create actionable improvement suggestions
            suggestions = self._generate_improvement_suggestions(
                title_keywords, specifics_keywords, description_keywords,
                consistency_scores, semantic_mapping, target_keywords
            )
            
            # Calculate keyword coverage metrics
            coverage_metrics = self._calculate_coverage_metrics(
                title_keywords, specifics_keywords, description_keywords, target_keywords
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return {
                'consistency_scores': consistency_scores,
                'keyword_analysis': keyword_analysis,
                'semantic_mapping': semantic_mapping,
                'coverage_metrics': coverage_metrics,
                'improvement_suggestions': suggestions,
                'execution_time_ms': round(execution_time, 2),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'production_ready': consistency_scores['overall_score'] >= 80
            }
            
        except Exception as e:
            logger.error(f"Error in keyword consistency analysis: {e}")
            raise

    def _extract_keywords(self, text: str, component_type: str) -> Dict[str, float]:
        """Extract and weight keywords from text content."""
        if not text:
            return {}
        
        # Normalize text
        text = text.lower().strip()
        
        # Extract words (alphanumeric + common punctuation)
        words = re.findall(r'\b[a-zA-Z0-9]+\b', text)
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 2 and word not in self.stop_words]
        
        # Count keyword frequency
        keyword_counts = Counter(keywords)
        
        # Calculate importance weights based on position and frequency
        weighted_keywords = {}
        total_words = len(keywords)
        
        for keyword, count in keyword_counts.items():
            # Base weight from frequency
            frequency_weight = count / total_words
            
            # Position weight (earlier words are more important)
            position_weight = 1.0
            if keyword in keywords[:5]:  # First 5 words get bonus
                position_weight = 1.5
            elif keyword in keywords[:10]:  # Next 5 words get smaller bonus
                position_weight = 1.2
            
            # Component-specific weight
            component_weight = self.component_weights.get(component_type, 0.5)
            
            # Final weighted score
            weighted_keywords[keyword] = frequency_weight * position_weight * component_weight
        
        return weighted_keywords

    def _extract_keywords_from_specifics(self, item_specifics: Dict[str, str]) -> Dict[str, float]:
        """Extract keywords from item specifics with aspect-based weighting."""
        if not item_specifics:
            return {}
        
        weighted_keywords = {}
        
        # Important aspects get higher weights
        aspect_weights = {
            'brand': 1.5, 'model': 1.4, 'color': 1.2, 'size': 1.2,
            'condition': 1.3, 'material': 1.1, 'style': 1.1, 'type': 1.1
        }
        
        for aspect_name, aspect_value in item_specifics.items():
            if not aspect_value:
                continue
            
            # Determine aspect weight
            aspect_weight = 1.0
            aspect_lower = aspect_name.lower()
            for key, weight in aspect_weights.items():
                if key in aspect_lower:
                    aspect_weight = weight
                    break
            
            # Extract keywords from aspect value
            value_keywords = self._extract_keywords(aspect_value, 'specifics')
            
            # Apply aspect weight to keywords
            for keyword, weight in value_keywords.items():
                if keyword in weighted_keywords:
                    weighted_keywords[keyword] = max(weighted_keywords[keyword], weight * aspect_weight)
                else:
                    weighted_keywords[keyword] = weight * aspect_weight
        
        return weighted_keywords

    def _analyze_keyword_distribution(
        self, title_kw: Dict[str, float], specifics_kw: Dict[str, float], desc_kw: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze keyword distribution across components."""
        all_keywords = set(title_kw.keys()) | set(specifics_kw.keys()) | set(desc_kw.keys())
        
        distribution_analysis = {
            'total_unique_keywords': len(all_keywords),
            'title_keywords': len(title_kw),
            'specifics_keywords': len(specifics_kw),
            'description_keywords': len(desc_kw),
            'cross_component_keywords': {},
            'component_exclusive_keywords': {
                'title_only': set(title_kw.keys()) - set(specifics_kw.keys()) - set(desc_kw.keys()),
                'specifics_only': set(specifics_kw.keys()) - set(title_kw.keys()) - set(desc_kw.keys()),
                'description_only': set(desc_kw.keys()) - set(title_kw.keys()) - set(specifics_kw.keys())
            }
        }
        
        # Analyze cross-component keyword sharing
        title_specifics_shared = set(title_kw.keys()) & set(specifics_kw.keys())
        title_desc_shared = set(title_kw.keys()) & set(desc_kw.keys())
        specifics_desc_shared = set(specifics_kw.keys()) & set(desc_kw.keys())
        all_shared = title_specifics_shared & set(desc_kw.keys())
        
        distribution_analysis['cross_component_keywords'] = {
            'title_specifics_shared': title_specifics_shared,
            'title_description_shared': title_desc_shared,
            'specifics_description_shared': specifics_desc_shared,
            'all_components_shared': all_shared
        }
        
        return distribution_analysis

    def _calculate_consistency_scores(
        self, title_kw: Dict[str, float], specifics_kw: Dict[str, float], 
        desc_kw: Dict[str, float], analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate comprehensive consistency scores."""
        # Base consistency scores
        title_specifics_overlap = len(analysis['cross_component_keywords']['title_specifics_shared'])
        title_desc_overlap = len(analysis['cross_component_keywords']['title_description_shared'])
        specifics_desc_overlap = len(analysis['cross_component_keywords']['specifics_description_shared'])
        all_shared = len(analysis['cross_component_keywords']['all_components_shared'])
        
        # Calculate component-pair consistency scores
        title_specifics_score = (title_specifics_overlap / max(len(title_kw), 1)) * 100
        title_description_score = (title_desc_overlap / max(len(title_kw), 1)) * 100
        specifics_description_score = (specifics_desc_overlap / max(len(specifics_kw), 1)) * 100
        
        # Calculate overall consistency with weighted average
        overall_score = (
            title_specifics_score * 0.4 +      # Title-specifics most important
            specifics_description_score * 0.35 + # Specifics-description important
            title_description_score * 0.25      # Title-description supporting
        )
        
        # Bonus for keywords shared across all components
        all_shared_bonus = (all_shared / max(analysis['total_unique_keywords'], 1)) * 10
        overall_score = min(100, overall_score + all_shared_bonus)
        
        return {
            'overall_score': round(overall_score, 2),
            'title_specifics_score': round(title_specifics_score, 2),
            'title_description_score': round(title_description_score, 2),
            'specifics_description_score': round(specifics_description_score, 2),
            'cross_component_bonus': round(all_shared_bonus, 2)
        }

    def _generate_semantic_mapping(
        self, title_kw: Dict[str, float], specifics_kw: Dict[str, float], desc_kw: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate semantic keyword mapping for better understanding."""
        semantic_mapping = {}
        all_keywords = set(title_kw.keys()) | set(specifics_kw.keys()) | set(desc_kw.keys())
        
        for group_name, group_keywords in self.semantic_groups.items():
            found_keywords = []
            for keyword in all_keywords:
                if any(group_kw in keyword.lower() for group_kw in group_keywords):
                    components = []
                    if keyword in title_kw:
                        components.append('title')
                    if keyword in specifics_kw:
                        components.append('specifics')
                    if keyword in desc_kw:
                        components.append('description')
                    
                    found_keywords.append({
                        'keyword': keyword,
                        'components': components,
                        'coverage': len(components)
                    })
            
            if found_keywords:
                semantic_mapping[group_name] = found_keywords
        
        return semantic_mapping

    def _generate_improvement_suggestions(
        self, title_kw: Dict[str, float], specifics_kw: Dict[str, float], desc_kw: Dict[str, float],
        scores: Dict[str, float], semantic_mapping: Dict[str, Any], target_keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Generate prioritized improvement suggestions."""
        suggestions = []
        
        # High-priority suggestions for low overall score
        if scores['overall_score'] < 80:
            # Title keywords missing from specifics
            title_only = set(title_kw.keys()) - set(specifics_kw.keys())
            if title_only:
                high_value_title_kw = [kw for kw in title_only if title_kw[kw] > 0.1][:3]
                if high_value_title_kw:
                    suggestions.append({
                        'priority': 'HIGH',
                        'type': 'keyword_alignment',
                        'suggestion': f"Add important title keywords to item specifics: {', '.join(high_value_title_kw)}",
                        'impact': 'Improves title-specifics consistency by 15-25 points',
                        'keywords': high_value_title_kw
                    })
            
            # Important specifics missing from description
            specifics_only = set(specifics_kw.keys()) - set(desc_kw.keys())
            if specifics_only:
                high_value_specifics = [kw for kw in specifics_only if specifics_kw[kw] > 0.1][:3]
                if high_value_specifics:
                    suggestions.append({
                        'priority': 'HIGH',
                        'type': 'content_enhancement',
                        'suggestion': f"Include key specifics in description: {', '.join(high_value_specifics)}",
                        'impact': 'Improves specifics-description consistency by 10-20 points',
                        'keywords': high_value_specifics
                    })
        
        # Medium-priority suggestions for semantic gaps
        for group_name, keywords in semantic_mapping.items():
            incomplete_coverage = [kw for kw in keywords if kw['coverage'] < 3]
            if incomplete_coverage:
                missing_components = []
                for kw_info in incomplete_coverage:
                    missing = set(['title', 'specifics', 'description']) - set(kw_info['components'])
                    missing_components.extend(missing)
                
                if missing_components:
                    most_missing = Counter(missing_components).most_common(1)[0][0]
                    suggestions.append({
                        'priority': 'MEDIUM',
                        'type': 'semantic_consistency',
                        'suggestion': f"Improve {group_name} keyword coverage in {most_missing}",
                        'impact': f'Enhances semantic consistency for {group_name} concepts',
                        'keywords': [kw['keyword'] for kw in incomplete_coverage[:2]]
                    })
        
        # Target keyword suggestions
        if target_keywords:
            missing_targets = []
            for target in target_keywords:
                target_lower = target.lower()
                if (target_lower not in title_kw and 
                    target_lower not in specifics_kw and 
                    target_lower not in desc_kw):
                    missing_targets.append(target)
            
            if missing_targets:
                suggestions.append({
                    'priority': 'HIGH',
                    'type': 'target_keyword_integration',
                    'suggestion': f"Integrate missing target keywords: {', '.join(missing_targets[:3])}",
                    'impact': 'Improves alignment with SEO targets',
                    'keywords': missing_targets[:3]
                })
        
        return suggestions

    def _calculate_coverage_metrics(
        self, title_kw: Dict[str, float], specifics_kw: Dict[str, float], 
        desc_kw: Dict[str, float], target_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate keyword coverage metrics."""
        all_keywords = set(title_kw.keys()) | set(specifics_kw.keys()) | set(desc_kw.keys())
        
        coverage_metrics = {
            'total_keyword_coverage': len(all_keywords),
            'component_coverage': {
                'title': len(title_kw),
                'specifics': len(specifics_kw),
                'description': len(desc_kw)
            },
            'keyword_density': {
                'title': sum(title_kw.values()) / max(len(title_kw), 1),
                'specifics': sum(specifics_kw.values()) / max(len(specifics_kw), 1),
                'description': sum(desc_kw.values()) / max(len(desc_kw), 1)
            }
        }
        
        if target_keywords:
            target_coverage = {
                'total_targets': len(target_keywords),
                'covered_targets': 0,
                'coverage_by_component': {'title': 0, 'specifics': 0, 'description': 0}
            }
            
            for target in target_keywords:
                target_lower = target.lower()
                covered = False
                
                if target_lower in title_kw:
                    target_coverage['coverage_by_component']['title'] += 1
                    covered = True
                if target_lower in specifics_kw:
                    target_coverage['coverage_by_component']['specifics'] += 1
                    covered = True
                if target_lower in desc_kw:
                    target_coverage['coverage_by_component']['description'] += 1
                    covered = True
                
                if covered:
                    target_coverage['covered_targets'] += 1
            
            target_coverage['coverage_percentage'] = (
                target_coverage['covered_targets'] / target_coverage['total_targets'] * 100
                if target_coverage['total_targets'] > 0 else 0
            )
            
            coverage_metrics['target_keyword_coverage'] = target_coverage
        
        return coverage_metrics

    async def optimize_keyword_distribution(
        self, analysis_result: Dict[str, Any], max_suggestions: int = 5
    ) -> Dict[str, Any]:
        """Generate optimized keyword distribution recommendations."""
        suggestions = analysis_result['improvement_suggestions']
        
        # Prioritize suggestions by impact and feasibility
        high_priority = [s for s in suggestions if s['priority'] == 'HIGH']
        medium_priority = [s for s in suggestions if s['priority'] == 'MEDIUM']
        
        optimized_suggestions = high_priority[:3] + medium_priority[:2]
        
        return {
            'optimization_plan': optimized_suggestions[:max_suggestions],
            'expected_improvement': self._calculate_expected_improvement(optimized_suggestions),
            'implementation_priority': [s['type'] for s in optimized_suggestions],
            'keyword_targets': self._extract_optimization_targets(optimized_suggestions)
        }

    def _calculate_expected_improvement(self, suggestions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate expected improvement from implementing suggestions."""
        high_impact_count = len([s for s in suggestions if s['priority'] == 'HIGH'])
        medium_impact_count = len([s for s in suggestions if s['priority'] == 'MEDIUM'])
        
        expected_improvement = {
            'consistency_score_increase': high_impact_count * 15 + medium_impact_count * 8,
            'keyword_coverage_increase': high_impact_count * 3 + medium_impact_count * 2,
            'seo_impact_score': high_impact_count * 20 + medium_impact_count * 10
        }
        
        return expected_improvement

    def _extract_optimization_targets(self, suggestions: List[Dict[str, Any]]) -> List[str]:
        """Extract target keywords from optimization suggestions."""
        targets = []
        for suggestion in suggestions:
            if 'keywords' in suggestion:
                targets.extend(suggestion['keywords'])
        
        return list(set(targets))  # Remove duplicates
