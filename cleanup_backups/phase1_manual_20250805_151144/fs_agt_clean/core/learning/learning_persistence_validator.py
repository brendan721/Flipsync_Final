"""
Learning Persistence Validator for Cross-Restart Continuity
==========================================================

This module validates that learning data persists correctly across agent restarts
and provides comprehensive testing for learning state continuity.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import text
from .database_learning_engine import DatabaseLearningEngine

logger = logging.getLogger(__name__)


class LearningPersistenceValidator:
    """Validates learning data persistence across agent restarts."""

    def __init__(self, db_session, vector_store=None):
        """Initialize the learning persistence validator."""
        self.db_session = db_session
        self.vector_store = vector_store
        self.learning_engine = DatabaseLearningEngine(db_session, vector_store)

        logger.info("✅ LearningPersistenceValidator initialized")

    async def validate_cross_restart_continuity(self, agent_id: str) -> bool:
        """Validate that learning data persists across agent restarts."""
        try:
            logger.info(f"🧪 Testing cross-restart continuity for {agent_id}")

            # Store test learning data
            test_data = {
                "policy_weights": {"param1": 0.75, "param2": 0.23},
                "learning_metrics": [
                    {"accuracy": 0.85, "timestamp": datetime.now(timezone.utc)}
                ],
                "algorithm_state": {"convergence_history": [0.1, 0.05, 0.02]},
            }

            # Store the learning state
            store_success = await self.learning_engine.store_learning_state(
                agent_id, test_data
            )
            if not store_success:
                logger.error("❌ Failed to store learning state")
                return False

            # Simulate agent restart by creating new learning engine instance
            new_learning_engine = DatabaseLearningEngine(
                db_session=self.db_session, vector_store=self.vector_store
            )

            # Restore learning state
            restored_data = await new_learning_engine.restore_learning_state(agent_id)

            # Validate data integrity
            validation_results = {
                "policy_state_valid": self._validate_policy_state(
                    restored_data["policy_state"]
                ),
                "metrics_history_valid": self._validate_metrics_history(
                    restored_data["metrics_history"]
                ),
                "algorithm_state_valid": self._validate_algorithm_state(
                    restored_data["algorithm_state"]
                ),
                "cross_agent_insights_valid": self._validate_cross_agent_insights(
                    restored_data["cross_agent_insights"]
                ),
            }

            overall_success = all(validation_results.values())

            logger.info(
                f"✅ Cross-restart continuity validation: {'PASSED' if overall_success else 'FAILED'}"
            )
            logger.info(
                f"   Policy state: {'✅' if validation_results['policy_state_valid'] else '❌'}"
            )
            logger.info(
                f"   Metrics history: {'✅' if validation_results['metrics_history_valid'] else '❌'}"
            )
            logger.info(
                f"   Algorithm state: {'✅' if validation_results['algorithm_state_valid'] else '❌'}"
            )
            logger.info(
                f"   Cross-agent insights: {'✅' if validation_results['cross_agent_insights_valid'] else '❌'}"
            )

            return overall_success

        except Exception as e:
            logger.error(f"❌ Cross-restart continuity validation failed: {e}")
            return False

    def _validate_policy_state(self, policy_state: Dict[str, Any]) -> bool:
        """Validate policy state restoration."""
        try:
            # Check for required parameters
            if "param1" not in policy_state or "param2" not in policy_state:
                logger.error("❌ Policy state missing required parameters")
                return False

            # Validate parameter values
            param1_valid = abs(policy_state["param1"] - 0.75) < 0.01
            param2_valid = abs(policy_state["param2"] - 0.23) < 0.01

            if not (param1_valid and param2_valid):
                logger.error(
                    f"❌ Policy parameters incorrect: param1={policy_state['param1']}, param2={policy_state['param2']}"
                )
                return False

            logger.debug("✅ Policy state validation passed")
            return True

        except Exception as e:
            logger.error(f"❌ Policy state validation error: {e}")
            return False

    def _validate_metrics_history(self, metrics_history: List[Dict[str, Any]]) -> bool:
        """Validate metrics history restoration."""
        try:
            if not metrics_history:
                logger.error("❌ Metrics history is empty")
                return False

            # Check for required fields in first metric
            first_metric = metrics_history[0]
            if "accuracy" not in first_metric or "timestamp" not in first_metric:
                logger.error("❌ Metrics history missing required fields")
                return False

            # Validate accuracy value
            accuracy = first_metric["accuracy"]
            if not isinstance(accuracy, (int, float)) or accuracy < 0 or accuracy > 1:
                logger.error(f"❌ Invalid accuracy value: {accuracy}")
                return False

            logger.debug("✅ Metrics history validation passed")
            return True

        except Exception as e:
            logger.error(f"❌ Metrics history validation error: {e}")
            return False

    def _validate_algorithm_state(self, algorithm_state: Dict[str, Any]) -> bool:
        """Validate algorithm state restoration."""
        try:
            if "convergence_history" not in algorithm_state:
                logger.error("❌ Algorithm state missing convergence_history")
                return False

            convergence_history = algorithm_state["convergence_history"]
            if (
                not isinstance(convergence_history, list)
                or len(convergence_history) != 3
            ):
                logger.error(f"❌ Invalid convergence history: {convergence_history}")
                return False

            # Validate convergence values
            expected_values = [0.1, 0.05, 0.02]
            for i, (actual, expected) in enumerate(
                zip(convergence_history, expected_values)
            ):
                if abs(actual - expected) > 0.01:
                    logger.error(
                        f"❌ Convergence value {i} incorrect: {actual} vs {expected}"
                    )
                    return False

            logger.debug("✅ Algorithm state validation passed")
            return True

        except Exception as e:
            logger.error(f"❌ Algorithm state validation error: {e}")
            return False

    def _validate_cross_agent_insights(
        self, cross_agent_insights: Dict[str, Any]
    ) -> bool:
        """Validate cross-agent insights restoration."""
        try:
            # Cross-agent insights can be empty for new agents
            if not isinstance(cross_agent_insights, dict):
                logger.error("❌ Cross-agent insights not a dictionary")
                return False

            # If insights exist, validate their structure
            for insight_id, insight_data in cross_agent_insights.items():
                if not isinstance(insight_data, dict):
                    logger.error(f"❌ Invalid insight data for {insight_id}")
                    return False

                # Check for required fields
                required_fields = ["content", "effectiveness", "adoption_rate"]
                for field in required_fields:
                    if field not in insight_data:
                        logger.error(f"❌ Insight {insight_id} missing field: {field}")
                        return False

            logger.debug("✅ Cross-agent insights validation passed")
            return True

        except Exception as e:
            logger.error(f"❌ Cross-agent insights validation error: {e}")
            return False

    async def validate_learning_data_integrity(self, agent_id: str) -> Dict[str, Any]:
        """Comprehensive validation of learning data integrity."""
        try:
            logger.info(f"🔍 Validating learning data integrity for {agent_id}")

            # Test multiple store/restore cycles
            integrity_results = {
                "single_cycle_success": False,
                "multiple_cycles_success": False,
                "data_consistency_success": False,
                "performance_acceptable": False,
            }

            # Single cycle test
            start_time = datetime.now()
            single_cycle_success = await self.validate_cross_restart_continuity(
                agent_id
            )
            single_cycle_time = (datetime.now() - start_time).total_seconds()

            integrity_results["single_cycle_success"] = single_cycle_success
            integrity_results["performance_acceptable"] = (
                single_cycle_time < 5.0
            )  # 5 second limit

            # Multiple cycles test
            if single_cycle_success:
                multiple_success = True
                for cycle in range(3):
                    cycle_success = await self.validate_cross_restart_continuity(
                        f"{agent_id}_cycle_{cycle}"
                    )
                    if not cycle_success:
                        multiple_success = False
                        break

                integrity_results["multiple_cycles_success"] = multiple_success
                integrity_results["data_consistency_success"] = multiple_success

            overall_success = all(integrity_results.values())

            logger.info(
                f"✅ Learning data integrity validation: {'PASSED' if overall_success else 'FAILED'}"
            )
            return {
                "success": overall_success,
                "results": integrity_results,
                "execution_time": single_cycle_time,
            }

        except Exception as e:
            logger.error(f"❌ Learning data integrity validation failed: {e}")
            return {"success": False, "error": str(e), "results": {}}

    async def cleanup_test_data(self, agent_id: str) -> bool:
        """Clean up test data after validation."""
        try:
            # Clean up test records from all tables
            cleanup_queries = [
                "DELETE FROM policy_optimization_history WHERE agent_id LIKE :pattern",
                "DELETE FROM learning_performance_metrics WHERE agent_id LIKE :pattern",
                "DELETE FROM learning_knowledge_base WHERE agent_id LIKE :pattern",
                "DELETE FROM cross_agent_learning_insights WHERE source_agent_id LIKE :pattern",
            ]

            pattern = f"{agent_id}%"

            for query in cleanup_queries:
                try:
                    await self.db_session.execute(text(query), {"pattern": pattern})
                except Exception as e:
                    logger.warning(f"Cleanup query failed: {e}")

            await self.db_session.commit()
            logger.info(f"✅ Test data cleaned up for {agent_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to cleanup test data: {e}")
            await self.db_session.rollback()
            return False
