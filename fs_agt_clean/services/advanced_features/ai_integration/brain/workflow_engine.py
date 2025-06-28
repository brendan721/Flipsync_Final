import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

"\nWorkflow engine module for managing workflow execution and state.\n"


@dataclass
class WorkflowPattern:
    """Represents a recognized workflow pattern"""

    pattern_id: str
    pattern_type: str
    features: Dict[str, Any]
    success_rate: float
    discovered_at: datetime
    last_matched: datetime
    match_count: int


class WorkflowEngine:
    """
    Manages workflow execution and state.
    Handles workflow registration, scheduling, and monitoring.
    """

    def __init__(self):
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.active_workflows: Set[str] = set()
        self.patterns: Dict[str, WorkflowPattern] = {}
        self.logger = logging.getLogger("workflow_engine")
        self.metrics = {
            "workflows_started": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "patterns_recognized": 0,
        }
        self.pattern_threshold = 0.7

    async def register_workflow(
        self,
        workflow_id: str,
        steps: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Register a new workflow"""
        if workflow_id in self.workflows:
            raise ValueError(f"Workflow {workflow_id} already exists")
        workflow = {
            "id": workflow_id,
            "steps": steps,
            "config": config or {},
            "state": "registered",
            "current_step": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "execution_id": str(uuid4()),
            "patterns_matched": [],
            "optimization_data": {},
        }
        self.workflows[workflow_id] = workflow
        self.logger.info("Registered workflow %s", workflow_id)
        return workflow["execution_id"]

    async def start_workflow(
        self, workflow_id: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Start a registered workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        workflow = self.workflows[workflow_id]
        if workflow["state"] != "registered":
            raise ValueError(f"Workflow {workflow_id} is already {workflow['state']}")
        matched_patterns = await self._match_patterns(workflow, context)
        if matched_patterns:
            await self._optimize_workflow(workflow, matched_patterns)
        workflow["state"] = "running"
        workflow["context"] = context or {}
        workflow["started_at"] = datetime.utcnow()
        workflow["updated_at"] = datetime.utcnow()
        self.active_workflows.add(workflow_id)
        self.metrics["workflows_started"] += 1
        try:
            await self._execute_workflow(workflow)
        except Exception as e:
            self.logger.error("Error executing workflow %s: %s", workflow_id, e)
            await self._handle_workflow_failure(workflow_id, str(e))

    async def _match_patterns(
        self, workflow: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> List[WorkflowPattern]:
        """Match workflow against known patterns"""
        matched = []
        workflow_features = await self._extract_workflow_features(workflow, context)
        for pattern in self.patterns.values():
            similarity = await self._calculate_pattern_similarity(
                pattern.features, workflow_features
            )
            if similarity >= self.pattern_threshold:
                pattern.match_count += 1
                pattern.last_matched = datetime.utcnow()
                matched.append(pattern)
        return matched

    async def _optimize_workflow(
        self, workflow: Dict[str, Any], patterns: List[WorkflowPattern]
    ) -> None:
        """Optimize workflow based on matched patterns"""
        optimizations = {}
        for pattern in patterns:
            if pattern.success_rate > 0.8:
                opt_key = f"pattern_{pattern.pattern_id}"
                optimizations[opt_key] = {
                    "success_rate": pattern.success_rate,
                    "match_count": pattern.match_count,
                    "features": pattern.features,
                }
        if optimizations:
            workflow["optimization_data"] = optimizations
            workflow["steps"] = await self._apply_optimizations(
                workflow["steps"], optimizations
            )

    async def _apply_optimizations(
        self, steps: List[Dict[str, Any]], optimizations: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply optimizations to workflow steps"""
        optimized_steps = steps.copy()
        for opt_key, opt_data in optimizations.items():
            if opt_data["success_rate"] > 0.9:
                optimized_steps = await self._optimize_step_sequence(
                    optimized_steps, opt_data["features"]
                )
        return optimized_steps

    async def _optimize_step_sequence(
        self, steps: List[Dict[str, Any]], features: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Optimize the sequence of steps based on features"""
        return steps

    async def _extract_workflow_features(
        self, workflow: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract features from workflow for pattern matching"""
        features = {
            "step_count": len(workflow["steps"]),
            "step_types": [step.get("type") for step in workflow["steps"]],
            "config_keys": list(workflow["config"].keys()),
        }
        if context:
            features["context_keys"] = list(context.keys())
        return features

    async def _calculate_pattern_similarity(
        self, pattern_features: Dict[str, Any], workflow_features: Dict[str, Any]
    ) -> float:
        """Calculate similarity between pattern and workflow features"""
        common_keys = set(pattern_features.keys()) & set(workflow_features.keys())
        if not common_keys:
            return 0.0
        matches = sum(
            (1 for k in common_keys if pattern_features[k] == workflow_features[k])
        )
        return matches / len(common_keys)

    async def recognize_pattern(
        self, pattern_type: str, features: Dict[str, Any], success_rate: float
    ) -> Optional[WorkflowPattern]:
        """Recognize a new workflow pattern"""
        pattern_id = f"{pattern_type}_{hash(str(features))}"
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.success_rate = pattern.success_rate * 0.9 + success_rate * 0.1
            pattern.match_count += 1
            pattern.last_matched = datetime.utcnow()
            return pattern
        if success_rate >= self.pattern_threshold:
            pattern = WorkflowPattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                features=features,
                success_rate=success_rate,
                discovered_at=datetime.utcnow(),
                last_matched=datetime.utcnow(),
                match_count=1,
            )
            self.patterns[pattern_id] = pattern
            self.metrics["patterns_recognized"] += 1
            return pattern
        return None

    async def _execute_workflow(self, workflow: Dict[str, Any]) -> None:
        """Execute workflow steps"""
        while workflow["current_step"] < len(workflow["steps"]):
            step = workflow["steps"][workflow["current_step"]]
            try:
                await self._execute_step(workflow, step)
                workflow["current_step"] += 1
                workflow["updated_at"] = datetime.utcnow()
            except Exception as e:
                self.logger.error(
                    "Error executing step {workflow['current_step']}: {e}"
                )
                raise
        await self._complete_workflow(workflow["id"])

    async def _execute_step(
        self, workflow: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Execute a single workflow step"""
        step_type = step.get("type")
        if not step_type:
            raise ValueError("Step type not specified")
        handler = getattr(self, f"_handle_{step_type}_step", None)
        if not handler:
            raise ValueError(f"Unknown step type: {step_type}")
        await handler(workflow, step)

    async def _handle_task_step(
        self, workflow: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Handle task execution step"""
        action = step.get("action")
        if not action:
            raise ValueError("Task step must have an action")
        parameters = step.get("parameters", {})
        try:
            result = await action(**parameters)
            step["result"] = result
            step["status"] = "completed"
        except Exception as e:
            step["error"] = str(e)
            step["status"] = "failed"
            raise

    async def _handle_decision_step(
        self, workflow: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Handle decision point step"""
        pass

    async def _handle_parallel_step(
        self, workflow: Dict[str, Any], step: Dict[str, Any]
    ) -> None:
        """Handle parallel execution step"""
        pass

    async def _complete_workflow(self, workflow_id: str) -> None:
        """Mark workflow as completed"""
        workflow = self.workflows[workflow_id]
        workflow["state"] = "completed"
        workflow["completed_at"] = datetime.utcnow()
        workflow["updated_at"] = datetime.utcnow()
        self.active_workflows.remove(workflow_id)
        self.metrics["workflows_completed"] += 1
        self.logger.info("Completed workflow %s", workflow_id)

    async def _handle_workflow_failure(self, workflow_id: str, error: str) -> None:
        """Handle workflow failure"""
        workflow = self.workflows[workflow_id]
        workflow["state"] = "failed"
        workflow["error"] = error
        workflow["failed_at"] = datetime.utcnow()
        workflow["updated_at"] = datetime.utcnow()
        self.active_workflows.remove(workflow_id)
        self.metrics["workflows_failed"] += 1
        self.logger.error("Failed workflow %s: %s", workflow_id, error)

    async def get_workflow_state(self, workflow_id: str) -> Dict[str, Any]:
        """Get current state of a workflow"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        return self.workflows[workflow_id]

    async def get_active_workflows(self) -> List[str]:
        """Get list of active workflow IDs"""
        return list(self.active_workflows)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get workflow engine metrics"""
        return self.metrics
