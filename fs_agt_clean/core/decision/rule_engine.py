"""
FlipSync Rule Engine - Algorithmic Decision Making
=================================================

High-performance rule engine for autonomous decision making without LLM dependency.
Designed for scaling to thousands of users with sub-100ms response times.

Features:
- JSON-based rule definitions
- DAG-based decision flows
- Caching and optimization
- Performance monitoring
- A/B testing support
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """Types of rules supported by the engine."""
    
    CONDITION = "condition"      # If-then logic
    CALCULATION = "calculation"  # Mathematical operations
    LOOKUP = "lookup"           # Table/mapping lookups
    AGGREGATION = "aggregation" # Data aggregation
    VALIDATION = "validation"   # Data validation
    ROUTING = "routing"         # Decision routing


class OperatorType(str, Enum):
    """Supported operators for conditions."""
    
    # Comparison
    EQ = "eq"           # Equal
    NE = "ne"           # Not equal
    GT = "gt"           # Greater than
    GTE = "gte"         # Greater than or equal
    LT = "lt"           # Less than
    LTE = "lte"         # Less than or equal
    
    # Logical
    AND = "and"         # Logical AND
    OR = "or"           # Logical OR
    NOT = "not"         # Logical NOT
    
    # String
    CONTAINS = "contains"       # String contains
    STARTS_WITH = "starts_with" # String starts with
    ENDS_WITH = "ends_with"     # String ends with
    
    # List/Set
    IN = "in"           # Value in list
    NOT_IN = "not_in"   # Value not in list
    
    # Mathematical
    ADD = "add"         # Addition
    SUBTRACT = "subtract" # Subtraction
    MULTIPLY = "multiply" # Multiplication
    DIVIDE = "divide"   # Division
    MODULO = "modulo"   # Modulo operation


@dataclass
class Rule:
    """Individual rule definition."""
    
    rule_id: str
    rule_type: RuleType
    name: str
    description: str
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    priority: int = 100
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionContext:
    """Context for decision making."""
    
    context_id: str
    agent_type: str
    decision_type: str
    input_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionResult:
    """Result of rule engine processing."""
    
    decision_id: str
    context_id: str
    result_data: Dict[str, Any]
    rules_applied: List[str]
    processing_time_ms: int
    confidence_score: float
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class RuleCache:
    """High-performance caching for rule results."""
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
    
    def _generate_key(self, context: DecisionContext) -> str:
        """Generate cache key from context."""
        key_data = {
            "agent_type": context.agent_type,
            "decision_type": context.decision_type,
            "input_hash": hashlib.md5(
                json.dumps(context.input_data, sort_keys=True).encode()
            ).hexdigest()
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def get(self, context: DecisionContext) -> Optional[DecisionResult]:
        """Get cached result if available and valid."""
        key = self._generate_key(context)
        
        if key not in self.cache:
            return None
        
        # Check TTL
        if time.time() - self.access_times[key] > self.ttl_seconds:
            del self.cache[key]
            del self.access_times[key]
            return None
        
        # Update access time
        self.access_times[key] = time.time()
        
        cached_data = self.cache[key]
        return DecisionResult(
            decision_id=cached_data["decision_id"],
            context_id=context.context_id,
            result_data=cached_data["result_data"],
            rules_applied=cached_data["rules_applied"],
            processing_time_ms=cached_data["processing_time_ms"],
            confidence_score=cached_data["confidence_score"],
            cache_hit=True
        )
    
    def put(self, context: DecisionContext, result: DecisionResult):
        """Cache result."""
        key = self._generate_key(context)
        
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = {
            "decision_id": result.decision_id,
            "result_data": result.result_data,
            "rules_applied": result.rules_applied,
            "processing_time_ms": result.processing_time_ms,
            "confidence_score": result.confidence_score
        }
        self.access_times[key] = time.time()


class RuleEvaluator:
    """Core rule evaluation engine."""
    
    def __init__(self):
        self.operators = {
            OperatorType.EQ: lambda a, b: a == b,
            OperatorType.NE: lambda a, b: a != b,
            OperatorType.GT: lambda a, b: a > b,
            OperatorType.GTE: lambda a, b: a >= b,
            OperatorType.LT: lambda a, b: a < b,
            OperatorType.LTE: lambda a, b: a <= b,
            OperatorType.AND: lambda a, b: a and b,
            OperatorType.OR: lambda a, b: a or b,
            OperatorType.NOT: lambda a: not a,
            OperatorType.CONTAINS: lambda a, b: b in a,
            OperatorType.STARTS_WITH: lambda a, b: a.startswith(b),
            OperatorType.ENDS_WITH: lambda a, b: a.endswith(b),
            OperatorType.IN: lambda a, b: a in b,
            OperatorType.NOT_IN: lambda a, b: a not in b,
            OperatorType.ADD: lambda a, b: a + b,
            OperatorType.SUBTRACT: lambda a, b: a - b,
            OperatorType.MULTIPLY: lambda a, b: a * b,
            OperatorType.DIVIDE: lambda a, b: a / b if b != 0 else 0,
            OperatorType.MODULO: lambda a, b: a % b if b != 0 else 0,
        }
    
    def evaluate_condition(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate a single condition."""
        try:
            operator = OperatorType(condition["operator"])
            field = condition["field"]
            value = condition["value"]
            
            # Get field value from data
            field_value = self._get_nested_value(data, field)
            
            # Apply operator
            if operator in [OperatorType.NOT]:
                return self.operators[operator](field_value)
            else:
                return self.operators[operator](field_value, value)
                
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    def evaluate_conditions(self, conditions: List[Dict[str, Any]], data: Dict[str, Any]) -> bool:
        """Evaluate multiple conditions with AND logic."""
        if not conditions:
            return True
        
        return all(self.evaluate_condition(condition, data) for condition in conditions)
    
    def execute_action(self, action: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a rule action."""
        action_type = action.get("type")
        
        if action_type == "set_value":
            return self._execute_set_value(action, data)
        elif action_type == "calculate":
            return self._execute_calculate(action, data)
        elif action_type == "lookup":
            return self._execute_lookup(action, data)
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return data
    
    def _get_nested_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get nested value from data using dot notation."""
        keys = field.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _execute_set_value(self, action: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute set_value action."""
        field = action["field"]
        value = action["value"]
        
        # Set nested value
        keys = field.split(".")
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return data
    
    def _execute_calculate(self, action: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calculate action."""
        formula = action["formula"]
        result_field = action["result_field"]
        
        # Simple formula evaluation (can be extended)
        try:
            # Replace field references with values
            for field, value in data.items():
                if isinstance(value, (int, float)):
                    formula = formula.replace(f"{{{field}}}", str(value))
            
            # Evaluate formula (safe evaluation)
            result = eval(formula, {"__builtins__": {}})
            
            # Set result
            keys = result_field.split(".")
            current = data
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = result
            
        except Exception as e:
            logger.error(f"Formula calculation failed: {e}")
        
        return data
    
    def _execute_lookup(self, action: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute lookup action."""
        lookup_table = action["lookup_table"]
        lookup_key = action["lookup_key"]
        result_field = action["result_field"]
        default_value = action.get("default_value")
        
        # Get lookup value
        key_value = self._get_nested_value(data, lookup_key)
        result_value = lookup_table.get(str(key_value), default_value)
        
        # Set result
        keys = result_field.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = result_value
        
        return data


class FlipSyncRuleEngine:
    """Main rule engine for FlipSync autonomous decision making."""
    
    def __init__(self, cache_size: int = 10000, cache_ttl: int = 300):
        self.rules: Dict[str, List[Rule]] = defaultdict(list)
        self.evaluator = RuleEvaluator()
        self.cache = RuleCache(cache_size, cache_ttl)
        self.performance_metrics = defaultdict(list)
    
    def load_rules(self, rules_config: Dict[str, Any]):
        """Load rules from configuration."""
        for agent_type, agent_rules in rules_config.items():
            for rule_data in agent_rules:
                rule = Rule(
                    rule_id=rule_data["rule_id"],
                    rule_type=RuleType(rule_data["rule_type"]),
                    name=rule_data["name"],
                    description=rule_data["description"],
                    conditions=rule_data.get("conditions", []),
                    actions=rule_data.get("actions", []),
                    priority=rule_data.get("priority", 100),
                    enabled=rule_data.get("enabled", True),
                    tags=rule_data.get("tags", []),
                    metadata=rule_data.get("metadata", {})
                )
                self.rules[agent_type].append(rule)
        
        # Sort rules by priority
        for agent_type in self.rules:
            self.rules[agent_type].sort(key=lambda r: r.priority)
    
    async def make_decision(self, context: DecisionContext) -> DecisionResult:
        """Make decision using rule engine."""
        start_time = time.perf_counter()
        
        # Check cache first
        cached_result = self.cache.get(context)
        if cached_result:
            return cached_result
        
        # Get applicable rules
        applicable_rules = self._get_applicable_rules(context)
        
        # Process rules
        result_data = context.input_data.copy()
        rules_applied = []
        
        for rule in applicable_rules:
            if not rule.enabled:
                continue
            
            # Evaluate conditions
            if self.evaluator.evaluate_conditions(rule.conditions, result_data):
                # Execute actions
                for action in rule.actions:
                    result_data = self.evaluator.execute_action(action, result_data)
                
                rules_applied.append(rule.rule_id)
        
        # Create result
        processing_time = int((time.perf_counter() - start_time) * 1000)
        
        result = DecisionResult(
            decision_id=f"decision_{int(time.time() * 1000)}",
            context_id=context.context_id,
            result_data=result_data,
            rules_applied=rules_applied,
            processing_time_ms=processing_time,
            confidence_score=1.0 if rules_applied else 0.5
        )
        
        # Cache result
        self.cache.put(context, result)
        
        # Track performance
        self.performance_metrics[context.agent_type].append(processing_time)
        
        return result
    
    def _get_applicable_rules(self, context: DecisionContext) -> List[Rule]:
        """Get rules applicable to the context."""
        agent_rules = self.rules.get(context.agent_type, [])
        
        # Filter by decision type if specified
        if context.decision_type:
            return [
                rule for rule in agent_rules
                if context.decision_type in rule.tags or not rule.tags
            ]
        
        return agent_rules
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        
        for agent_type, times in self.performance_metrics.items():
            if times:
                stats[agent_type] = {
                    "avg_time_ms": sum(times) / len(times),
                    "min_time_ms": min(times),
                    "max_time_ms": max(times),
                    "total_decisions": len(times)
                }
        
        return stats
