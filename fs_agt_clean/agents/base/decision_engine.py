"""Decision Engine Module
Implements autonomous decision-making capabilities
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

try:
    import numpy as np
except ImportError:
    logging.error(
        "numpy is required for DecisionEngine. Please install it with: pip install numpy"
    )
    raise
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.learning.learning_module import LearningModule
from fs_agt_clean.services.inventory.ai_marketing import AIMarketingUnifiedAgent

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class Decision:
    decision_id: str
    timestamp: datetime
    decision_type: str
    parameters: Dict[str, Any]
    confidence: float
    rationale: str
    metadata: Dict[str, Any]


class DecisionEngine:
    """Core decision-making engine for autonomous operations"""

    def __init__(
        self,
        learning_module: LearningModule,
        ai_marketing_agent: AIMarketingUnifiedAgent,
        config_manager: ConfigManager,
    ):
        self.learning_module = learning_module
        self.ai_marketing_agent = ai_marketing_agent
        self.config = config_manager.config.get("decision_engine", {})
        self.decisions: List[Decision] = []
        self.performance_metrics: Dict[str, List[float]] = {
            "accuracy": [],
            "roi": [],
            "confidence": [],
        }
        logger.info("Initialized Decision Engine")

    async def make_decision(
        self, context: Dict[str, Any], decision_type: str
    ) -> Decision:
        """Make an autonomous decision based on context"""
        try:
            logger.info("Making %s decision", decision_type)
            predictions = await self.learning_module.make_decision(context)
            marketing_data = await self.ai_marketing_agent.get_recommendations(context)
            decision_params = self._combine_insights(
                predictions, marketing_data, context
            )
            risk_assessment = self._assess_risk(decision_params, context)
            decision = Decision(
                decision_id=f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(),
                decision_type=decision_type,
                parameters=decision_params,
                confidence=self._calculate_confidence(predictions, risk_assessment),
                rationale=self._generate_rationale(
                    decision_params, predictions, risk_assessment
                ),
                metadata={
                    "risk_assessment": risk_assessment,
                    "market_conditions": context.get("market_conditions", {}),
                    "model_predictions": predictions,
                },
            )
            self.decisions.append(decision)
            logger.info("Made decision: %s", decision)
            return decision
        except Exception as e:
            logger.error("Error making decision: %s", str(e))
            raise

    def _combine_insights(
        self,
        predictions: Dict[str, Any],
        marketing_data: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Combine various insights to form decision parameters"""
        try:
            predicted_price = predictions["optimal_price"]
            predicted_strategy = predictions["recommended_strategy"]
            market_price = marketing_data["pricing"]["suggested_price"]
            price_confidence = predictions["confidence_scores"]["price"]
            if price_confidence > 0.8:
                final_price = predicted_price
            else:
                final_price = predicted_price * price_confidence + market_price * (
                    1 - price_confidence
                )
            strategy_params = self._get_strategy_parameters(
                predicted_strategy, marketing_data["recommendations"], context
            )
            return {
                "price": final_price,
                "strategy": strategy_params,
                "marketing_actions": marketing_data["promotions"],
                "timing": self._determine_timing(context),
            }
        except Exception as e:
            logger.error("Error combining insights: %s", str(e))
            raise

    def _assess_risk(
        self, decision_params: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Assess risks associated with the decision"""
        try:
            price_volatility = self._calculate_price_volatility(
                context.get("historical_prices", [])
            )
            market_risk = self._calculate_market_risk(
                context.get("market_conditions", {})
            )
            competition_risk = self._calculate_competition_risk(
                context.get("competitor_data", {})
            )
            overall_risk = np.mean([price_volatility, market_risk, competition_risk])
            return {
                "overall_risk": float(overall_risk),
                "price_volatility": float(price_volatility),
                "market_risk": float(market_risk),
                "competition_risk": float(competition_risk),
            }
        except Exception as e:
            logger.error("Error assessing risk: %s", str(e))
            raise

    def _calculate_confidence(
        self, predictions: Dict[str, Any], risk_assessment: Dict[str, float]
    ) -> float:
        """Calculate overall confidence in the decision"""
        try:
            model_confidence = np.mean(
                [
                    predictions["confidence_scores"]["price"],
                    predictions["confidence_scores"]["strategy"],
                ]
            )
            risk_factor = 1 - risk_assessment["overall_risk"]
            confidence = model_confidence * risk_factor
            return float(confidence)
        except Exception as e:
            logger.error("Error calculating confidence: %s", str(e))
            raise

    def _generate_rationale(
        self,
        decision_params: Dict[str, Any],
        predictions: Dict[str, Any],
        risk_assessment: Dict[str, float],
    ) -> str:
        """Generate explanation for the decision"""
        try:
            rationale_parts = [
                f"Price set to {decision_params['price']:.2f} based on:",
                f"- Model prediction: {predictions['optimal_price']:.2f} (confidence: {predictions['confidence_scores']['price']:.2f})",
                f"- Market conditions and risk assessment (overall risk: {risk_assessment['overall_risk']:.2f})",
                f"Strategy: {decision_params['strategy']['name']} ({predictions['confidence_scores']['strategy']:.2f} confidence)",
            ]
            return " ".join(rationale_parts)
        except Exception as e:
            logger.error("Error generating rationale: %s", str(e))
            raise

    def _calculate_price_volatility(self, historical_prices: List[float]) -> float:
        """Calculate price volatility risk"""
        if not historical_prices:
            return 0.5
        try:
            prices = np.array(historical_prices)
            return float(np.std(prices) / np.mean(prices))
        except Exception:
            return 0.5

    def _calculate_market_risk(self, market_conditions: Dict[str, Any]) -> float:
        """Calculate market-related risk"""
        try:
            factors = [
                market_conditions.get("demand_volatility", 0.5),
                market_conditions.get("supply_risk", 0.5),
                market_conditions.get("market_uncertainty", 0.5),
            ]
            return float(np.mean(factors))
        except Exception:
            return 0.5

    def _calculate_competition_risk(self, competitor_data: Dict[str, Any]) -> float:
        """Calculate competition-related risk"""
        try:
            factors = [
                competitor_data.get("price_war_risk", 0.5),
                competitor_data.get("market_share_threat", 0.5),
                competitor_data.get("new_entrant_threat", 0.5),
            ]
            return float(np.mean(factors))
        except Exception:
            return 0.5

    def _get_strategy_parameters(
        self,
        predicted_strategy: str,
        recommendations: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Get detailed strategy parameters"""
        try:
            base_params = {
                "conservative": {
                    "name": "conservative",
                    "budget_multiplier": 0.8,
                    "risk_tolerance": 0.3,
                    "bid_adjustment": 0.9,
                },
                "balanced": {
                    "name": "balanced",
                    "budget_multiplier": 1.0,
                    "risk_tolerance": 0.5,
                    "bid_adjustment": 1.0,
                },
                "aggressive": {
                    "name": "aggressive",
                    "budget_multiplier": 1.2,
                    "risk_tolerance": 0.7,
                    "bid_adjustment": 1.1,
                },
            }
            params = base_params.get(predicted_strategy, base_params["balanced"])
            if "strategy_adjustments" in recommendations:
                adjustments = recommendations["strategy_adjustments"]
                for key in params:
                    if key in adjustments:
                        params[key] *= adjustments[key]
            return params
        except Exception as e:
            logger.error("Error getting strategy parameters: %s", str(e))
            return base_params["balanced"]

    def _determine_timing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine optimal timing for decision execution"""
        try:
            current_time = datetime.now()
            market_hours = context.get("market_hours", {})
            timing = {
                "execute_immediately": True,
                "scheduled_time": None,
                "valid_until": current_time.timestamp() + 3600,
                "check_interval": 300,
            }
            if market_hours:
                timing.update(
                    {
                        "market_open": market_hours.get("open"),
                        "market_close": market_hours.get("close"),
                        "optimal_window": market_hours.get("optimal_window"),
                    }
                )
            return timing
        except Exception as e:
            logger.error("Error determining timing: %s", str(e))
            return {
                "execute_immediately": True,
                "valid_until": datetime.now().timestamp() + 3600,
            }

    async def evaluate_decision(
        self, decision: Decision, outcomes: Dict[str, Any]
    ) -> Dict[str, float]:
        """Evaluate the performance of a past decision"""
        try:
            price_accuracy = (
                1
                - abs(outcomes["actual_price"] - decision.parameters["price"])
                / outcomes["actual_price"]
            )
            strategy_success = float(
                outcomes["strategy_performance"]
                > decision.parameters["strategy"]["risk_tolerance"]
            )
            roi = (outcomes["revenue"] - outcomes["costs"]) / outcomes["costs"]
            metrics = {
                "accuracy": float(np.mean([price_accuracy, strategy_success])),
                "roi": float(roi),
                "confidence_correlation": float(decision.confidence * price_accuracy),
            }
            for key, value in metrics.items():
                if key in self.performance_metrics:
                    self.performance_metrics[key].append(value)
            logger.info("Decision evaluation metrics: %s", metrics)
            return metrics
        except Exception as e:
            logger.error("Error evaluating decision: %s", str(e))
            raise

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of decision engine performance"""
        try:
            summary = {}
            for metric, values in self.performance_metrics.items():
                if values:
                    summary[metric] = {
                        "current": float(values[-1]),
                        "average": float(np.mean(values)),
                        "trend": float(
                            np.mean(np.diff(values[-10:])) if len(values) > 10 else 0
                        ),
                    }
                else:
                    summary[metric] = {"current": 0.0, "average": 0.0, "trend": 0.0}
            return summary
        except Exception as e:
            logger.error("Error getting performance summary: %s", str(e))
            raise
