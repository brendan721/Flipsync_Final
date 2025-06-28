import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np
from sklearn.ensemble import RandomForestRegressor

from fs_agt_clean.core.metrics.collector import MetricsCollector
from fs_agt_clean.core.services.campaign.campaign_manager import CampaignManager
from fs_agt_clean.core.services.communication import Event, EventBus, EventType
from fs_agt_clean.core.services.resource_management import ResourceManager
from fs_agt_clean.services.campaign_analytics.models import (
    Alert,
    AlertConfig,
    AlertSeverity,
    AnalyticsDashboard,
    CampaignPerformance,
    MetricType,
    MetricValue,
    PerformanceComparison,
    PerformanceMetric,
    PerformancePrediction,
    PredictionInterval,
)

"\nCampaign performance analytics engine.\n"
logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Analyzes campaign performance across platforms."""

    def __init__(
        self,
        event_bus: EventBus,
        campaign_manager: CampaignManager,
        resource_manager: ResourceManager,
        metrics_collector: MetricsCollector,
        update_interval: int = 300,
        prediction_confidence: float = 0.95,
    ):
        self.event_bus = event_bus
        self.campaign_manager = campaign_manager
        self.resource_manager = resource_manager
        self.metrics_collector = metrics_collector
        self.update_interval = update_interval
        self.prediction_confidence = prediction_confidence
        self.alert_configs: Dict[str, Dict[MetricType, AlertConfig]] = {}
        self.prediction_models: Dict[MetricType, RandomForestRegressor] = {}
        asyncio.create_task(self._update_loop())
        # Don't set up subscriptions here - do it in create()

    @classmethod
    async def create(
        cls,
        event_bus: EventBus,
        campaign_manager: CampaignManager,
        resource_manager: ResourceManager,
        metrics_collector: MetricsCollector,
        update_interval: int = 300,
        prediction_confidence: float = 0.95,
    ) -> "AnalyticsEngine":
        """Create and initialize an AnalyticsEngine instance."""
        engine = cls(
            event_bus=event_bus,
            campaign_manager=campaign_manager,
            resource_manager=resource_manager,
            metrics_collector=metrics_collector,
            update_interval=update_interval,
            prediction_confidence=prediction_confidence,
        )
        await engine._setup_subscriptions()
        return engine

    async def _setup_subscriptions(self) -> None:
        """Set up event subscriptions."""
        await self.event_bus.subscribe(
            EventType.CAMPAIGN_UPDATED, self._handle_campaign_update
        )

    async def _handle_campaign_update(self, event: Event) -> None:
        """Handle campaign update events."""
        try:
            campaign_id = event.data.get("campaign_id")
            seller_id = event.data.get("seller_id")
            if campaign_id and seller_id:
                campaign = await self.campaign_manager.get_campaign(campaign_id)
                performance = await self._calculate_performance(campaign)
                await self.create_dashboard(seller_id)
        except Exception as e:
            logger.error("Error handling campaign update: %s", str(e))
            await self._publish_error(str(e))

    async def create_dashboard(self, seller_id: str) -> AnalyticsDashboard:
        """Create analytics dashboard for a seller."""
        try:
            campaigns = await self.campaign_manager.get_seller_campaigns(seller_id)
            performances = {}
            for campaign in campaigns:
                performance = await self._calculate_performance(campaign)
                performances[campaign.id] = performance
            comparisons = await self._calculate_comparisons(seller_id, performances)
            recommendations = await self._generate_recommendations(
                seller_id, performances, comparisons
            )
            dashboard = AnalyticsDashboard(
                seller_id=seller_id,
                campaign_performances=performances,
                comparisons=comparisons,
                overall_health_score=self._calculate_health_score(
                    performances, comparisons
                ),
                recommendations=recommendations,
                last_updated=datetime.utcnow(),
            )
            await self._publish_dashboard_created(dashboard)
            return dashboard
        except Exception as e:
            logger.error("Error creating dashboard: %s", str(e))
            await self._publish_error(str(e))
            raise

    async def configure_alerts(
        self, seller_id: str, configs: Dict[MetricType, AlertConfig]
    ) -> None:
        """Configure alert thresholds for a seller."""
        try:
            self.alert_configs[seller_id] = configs
            await self._publish_alerts_configured(seller_id, configs)
        except Exception as e:
            logger.error("Error configuring alerts: %s", str(e))
            await self._publish_error(str(e))
            raise

    async def predict_performance(
        self,
        campaign_id: str,
        metric_type: MetricType,
        interval: PredictionInterval = PredictionInterval.DAY,
    ) -> PerformancePrediction:
        try:
            # Get historical data
            historical_data = await self._get_historical_data(
                campaign_id, metric_type, interval
            )

            # Prepare features for prediction
            features = self._prepare_prediction_features(
                [historical_data[-1]] if historical_data else [], interval
            )

            # Fit model if we have historical data
            model = RandomForestRegressor(random_state=42)
            if historical_data:
                X = [
                    self._prepare_prediction_features([data], interval)
                    for data in historical_data
                ]
                y = [float(data.value) for data in historical_data]
                model.fit(X, y)
                prediction = float(model.predict([features])[0])
            else:
                # If no historical data, return a default value
                prediction = 0.0

            # Since RandomForestRegressor doesn't support predict_proba, we'll set a default confidence
            confidence = 0.7 if historical_data else 0.5

            # Log the prediction
            await self.metrics_collector.record_metric(
                name=str(MetricType.ROI),
                value=confidence,
                labels={"campaign_id": campaign_id},
                metadata={"prediction_type": "confidence"},
            )

            # Return prediction with confidence interval
            return PerformancePrediction(
                metric_type=metric_type,
                predicted_value=prediction,
                confidence_interval=(
                    prediction - 0.1,
                    prediction + 0.1,
                ),  # Simple confidence interval for now
                prediction_interval=interval,
                features_used=[
                    "historical_mean",
                    "historical_std",
                    "trend",
                    "hour",
                    "day",
                    "month",
                ],
                model_version="1.0",
                timestamp=datetime.now(),
            )

        except Exception as e:
            error_msg = f"Error predicting performance: {str(e)}"
            logging.error(error_msg)

            # Create and publish error event
            error_event = Event(
                id=f"error_{datetime.utcnow().timestamp()}",
                type=EventType.ERROR_OCCURRED,
                source="analytics_engine",
                data={
                    "error": error_msg,
                    "campaign_id": campaign_id,
                    "metric_type": metric_type.value,
                },
                timestamp=datetime.utcnow(),
            )
            await self.event_bus.publish(error_event)

            # Re-raise the exception
            raise

    async def _update_loop(self) -> None:
        """Periodic update loop."""
        while True:
            try:
                for seller_id in self.alert_configs.keys():
                    await self.create_dashboard(seller_id)
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error("Error in update loop: %s", str(e))
                await self._publish_error(str(e))
                await asyncio.sleep(self.update_interval)

    async def _calculate_performance(self, campaign) -> CampaignPerformance:
        """Calculate performance metrics for a campaign."""
        metrics = {}
        alerts = []
        predictions = {}
        for metric_type in MetricType:
            current = await self._calculate_metric(campaign, metric_type)
            historical = await self._get_historical_values(campaign, metric_type)
            trend = self._calculate_trend(historical)
            metric = PerformanceMetric(
                metric_type=metric_type,
                current_value=current,
                historical_values=historical,
                trend=trend,
                baseline=self._calculate_baseline(historical),
                alert_threshold=self._get_alert_threshold(
                    campaign.seller_id, metric_type
                ),
                prediction_model="random_forest",
            )
            metrics[metric_type] = metric
            alert = await self._check_alert(campaign, metric)
            if alert:
                alerts.append(alert)
            prediction = await self.predict_performance(
                campaign.id, metric_type, PredictionInterval.DAY
            )
            predictions[metric_type] = prediction
        return CampaignPerformance(
            campaign_id=campaign.id,
            seller_id=campaign.seller_id,
            metrics=metrics,
            alerts=alerts,
            predictions=predictions,
            last_updated=datetime.utcnow(),
            data_quality_score=self._calculate_data_quality(metrics),
        )

    def _calculate_trend(self, historical: List[MetricValue]) -> float:
        """Calculate metric trend."""
        if len(historical) < 2:
            return 0.0
        values = [h.value for h in historical]
        times = [
            (h.timestamp - historical[0].timestamp).total_seconds() for h in historical
        ]
        return np.polyfit(times, values, 1)[0]

    def _calculate_baseline(self, historical: List[MetricValue]) -> float:
        """Calculate metric baseline."""
        if not historical:
            return 0.0
        return np.mean([h.value for h in historical])

    def _calculate_data_quality(
        self, metrics: Dict[MetricType, PerformanceMetric]
    ) -> float:
        """Calculate data quality score."""
        scores = []
        for metric in metrics.values():
            if len(metric.historical_values) > 0:
                latest = max((v.timestamp for v in metric.historical_values))
                age = (datetime.utcnow() - latest).total_seconds()
                freshness = max(0, 1 - age / (24 * 3600))
                scores.append(freshness)
            confidence_scores = [v.confidence_score for v in metric.historical_values]
            if confidence_scores:
                scores.append(np.mean(confidence_scores))
        return np.mean(scores) if scores else 0.0

    def _calculate_health_score(
        self,
        performances: Dict[str, CampaignPerformance],
        comparisons: Dict[MetricType, PerformanceComparison],
    ) -> float:
        """Calculate overall health score."""
        scores = []
        for performance in performances.values():
            roi_metric = performance.metrics.get(MetricType.ROI)
            if roi_metric:
                roi_score = max(0, min(1, roi_metric.current_value.value / 2))
                scores.append(roi_score * 0.4)
            scores.append(performance.data_quality_score * 0.2)
            severity_scores = {
                AlertSeverity.LOW: 0.9,
                AlertSeverity.MEDIUM: 0.7,
                AlertSeverity.HIGH: 0.4,
                AlertSeverity.CRITICAL: 0.1,
            }
            if performance.alerts:
                worst_severity = max((a.severity for a in performance.alerts))
                scores.append(severity_scores[worst_severity] * 0.2)
        for comparison in comparisons.values():
            scores.append(comparison.percentile_rank / 100 * 0.2)
        return np.mean(scores) if scores else 0.0

    def _get_prediction_model(self, metric_type: MetricType) -> RandomForestRegressor:
        """Get or create prediction model."""
        if metric_type not in self.prediction_models:
            self.prediction_models[metric_type] = RandomForestRegressor(
                n_estimators=100, random_state=42
            )
        return self.prediction_models[metric_type]

    def _get_feature_names(self) -> List[str]:
        """Get feature names for prediction."""
        return [
            "historical_mean",
            "historical_std",
            "trend",
            "hour_of_day",
            "day_of_week",
            "is_weekend",
        ]

    async def _publish_dashboard_created(self, dashboard: AnalyticsDashboard) -> None:
        """Publish dashboard creation event."""
        await self.event_bus.publish(
            Event(
                id=f"dashboard_{datetime.utcnow().timestamp()}",
                type=EventType.DASHBOARD_CREATED,
                source="analytics_engine",
                data={"dashboard": dashboard},
                timestamp=datetime.utcnow(),
                metadata={"target_agents": ["all"]},
            )
        )

    async def _publish_alerts_configured(
        self, seller_id: str, configs: Dict[MetricType, AlertConfig]
    ) -> None:
        """Publish alert configuration event."""
        await self.event_bus.publish(
            Event(
                id=f"alerts_{datetime.utcnow().timestamp()}",
                type=EventType.ALERTS_CONFIGURED,
                source="analytics_engine",
                data={"seller_id": seller_id, "configs": configs},
                timestamp=datetime.utcnow(),
                metadata={"target_agents": ["all"]},
            )
        )

    async def _publish_prediction_made(self, prediction: PerformancePrediction) -> None:
        """Publish prediction event."""
        await self.event_bus.publish(
            Event(
                id=f"prediction_{datetime.utcnow().timestamp()}",
                type=EventType.PREDICTION_MADE,
                source="analytics_engine",
                data={"prediction": prediction},
                timestamp=datetime.utcnow(),
                metadata={"target_agents": ["all"]},
            )
        )

    async def _publish_error(self, error_message: str) -> None:
        """Publish error event."""
        event = Event(
            id=f"error_{datetime.utcnow().timestamp()}",
            type=EventType.ERROR_OCCURRED,
            source="analytics_engine",
            data={"error_message": error_message},
            timestamp=datetime.utcnow(),
            metadata={"target_agents": ["all"]},
        )
        try:
            await self.event_bus.publish(event)
        except Exception as e:
            logger.error("Error publishing error event: %s", str(e))

    async def _get_historical_data(
        self,
        campaign_id: str,
        metric_type: MetricType,
        interval: PredictionInterval = PredictionInterval.DAY,
    ) -> List[MetricValue]:
        """Get historical data for a campaign metric."""
        try:
            campaign = await self.campaign_manager.get_campaign(campaign_id)
            return await self._get_historical_values(campaign, metric_type, interval)
        except Exception as e:
            logger.error("Error getting historical data: %s", str(e))
            return []

    async def _get_historical_values(
        self,
        campaign,
        metric_type: MetricType,
        interval: PredictionInterval = PredictionInterval.DAY,
    ) -> List[MetricValue]:
        """Get historical values for a campaign metric."""
        try:
            # Adjust time range based on interval
            if interval == PredictionInterval.HOUR:
                days = 1
            elif interval == PredictionInterval.DAY:
                days = 30
            elif interval == PredictionInterval.WEEK:
                days = 90
            else:  # MONTH
                days = 365

            metrics = await self.metrics_collector.get_metrics(
                campaign.id,
                metric_type,
                start_time=datetime.utcnow() - timedelta(days=days),
                end_time=datetime.utcnow(),
            )
            return [
                MetricValue(
                    value=float(m.value),
                    timestamp=m.timestamp,
                    confidence_score=float(m.confidence_score),
                    source_platform=m.source_platform,
                    is_predicted=m.is_predicted,
                )
                for m in metrics
            ]
        except Exception as e:
            logger.error("Error getting historical values: %s", str(e))
            return []

    def _prepare_prediction_features(
        self,
        historical_data: List[MetricValue],
        interval: PredictionInterval = PredictionInterval.DAY,
    ) -> List[float]:
        """Prepare features for prediction."""
        if not historical_data:
            return [0.0] * len(self._get_feature_names())

        values = [h.value for h in historical_data]
        timestamps = [h.timestamp for h in historical_data]

        # Calculate basic statistics
        mean_value = float(np.mean(values)) if values else 0.0
        std_value = float(np.std(values)) if len(values) > 1 else 0.0
        trend = float(self._calculate_trend(historical_data))

        # Calculate time-based features based on interval
        latest_time = max(timestamps) if timestamps else datetime.utcnow()
        hour = float(latest_time.hour)
        day = float(latest_time.weekday())
        is_weekend = 1.0 if day >= 5 else 0.0

        return [mean_value, std_value, trend, hour, day, is_weekend]

    async def _calculate_metric(self, campaign, metric_type: MetricType) -> MetricValue:
        """Calculate current metric value."""
        try:
            metrics = await self.metrics_collector.get_metrics(
                campaign.id,
                metric_type,
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow(),
            )
            if metrics:
                latest = max(metrics, key=lambda m: m.timestamp)
                return MetricValue(
                    value=latest.value,
                    timestamp=latest.timestamp,
                    confidence_score=latest.confidence_score,
                    source_platform=latest.source_platform,
                    is_predicted=latest.is_predicted,
                )
            return MetricValue(
                value=0.0,
                timestamp=datetime.utcnow(),
                confidence_score=0.0,
                source_platform="unknown",
                is_predicted=True,
            )
        except Exception as e:
            logger.error("Error calculating metric: %s", str(e))
            return MetricValue(
                value=0.0,
                timestamp=datetime.utcnow(),
                confidence_score=0.0,
                source_platform="unknown",
                is_predicted=True,
            )

    async def _calculate_comparisons(
        self, seller_id: str, performances: Dict[str, CampaignPerformance]
    ) -> Dict[MetricType, PerformanceComparison]:
        """Calculate performance comparisons."""
        try:
            comparisons = {}
            for metric_type in MetricType:
                seller_metrics = {}
                for campaign_id, performance in performances.items():
                    if metric_type in performance.metrics:
                        seller_metrics[campaign_id] = performance.metrics[
                            metric_type
                        ].current_value.value

                if seller_metrics:
                    # Get industry metrics for comparison
                    industry_metrics = (
                        await self.metrics_collector.get_industry_metrics(metric_type)
                    )
                    industry_values = [m.value for m in industry_metrics]

                    if industry_values:
                        industry_avg = float(np.mean(industry_values))
                        seller_avg = float(np.mean(list(seller_metrics.values())))
                        percentile = float(
                            np.percentile(
                                industry_values,
                                np.searchsorted(np.sort(industry_values), seller_avg)
                                / len(industry_values)
                                * 100,
                            )
                        )
                    else:
                        industry_avg = 0.0
                        percentile = 50.0

                    comparisons[metric_type] = PerformanceComparison(
                        metric_type=metric_type,
                        seller_metrics=seller_metrics,
                        industry_average=industry_avg,
                        percentile_rank=percentile,
                        timestamp=datetime.utcnow(),
                    )

            return comparisons
        except Exception as e:
            logger.error("Error calculating comparisons: %s", str(e))
            return {}

    async def _generate_recommendations(
        self,
        seller_id: str,
        performances: Dict[str, CampaignPerformance],
        comparisons: Dict[MetricType, PerformanceComparison],
    ) -> List[str]:
        """Generate performance recommendations."""
        try:
            recommendations = []

            # Check overall performance
            for metric_type, comparison in comparisons.items():
                if comparison.percentile_rank < 25:
                    recommendations.append(
                        f"Your {metric_type.value} performance is in the bottom quartile. "
                        "Consider reviewing and optimizing your campaign strategy."
                    )
                elif comparison.percentile_rank > 75:
                    recommendations.append(
                        f"Your {metric_type.value} performance is in the top quartile. "
                        "Consider increasing investment in successful strategies."
                    )

            # Check individual campaign performance
            for campaign_id, performance in performances.items():
                for metric_type, metric in performance.metrics.items():
                    if metric.trend < -0.1:
                        recommendations.append(
                            f"Campaign {campaign_id} shows declining {metric_type.value}. "
                            "Review recent changes and adjust strategy."
                        )
                    elif metric.trend > 0.1:
                        recommendations.append(
                            f"Campaign {campaign_id} shows improving {metric_type.value}. "
                            "Consider scaling up successful tactics."
                        )

            return recommendations
        except Exception as e:
            logger.error("Error generating recommendations: %s", str(e))
            return []

    def _get_alert_threshold(self, seller_id: str, metric_type: MetricType) -> float:
        """Get alert threshold for a metric."""
        try:
            if (
                seller_id in self.alert_configs
                and metric_type in self.alert_configs[seller_id]
            ):
                return self.alert_configs[seller_id][metric_type].threshold
            return 0.0
        except Exception as e:
            logger.error("Error getting alert threshold: %s", str(e))
            return 0.0

    async def _check_alert(
        self, campaign, metric: PerformanceMetric
    ) -> Optional[Alert]:
        """Check if metric should trigger an alert."""
        try:
            if campaign.seller_id not in self.alert_configs:
                return None

            config = self.alert_configs[campaign.seller_id].get(metric.metric_type)
            if not config or not config.enabled:
                return None

            # Check if in cooldown period
            if (
                config.last_triggered
                and (datetime.utcnow() - config.last_triggered).total_seconds()
                < config.cooldown_period
            ):
                return None

            current_value = metric.current_value.value
            if current_value < config.threshold:
                alert = Alert(
                    campaign_id=campaign.id,
                    metric_type=metric.metric_type,
                    current_value=current_value,
                    threshold=config.threshold,
                    severity=config.severity,
                    timestamp=datetime.utcnow(),
                )
                # Update last triggered time
                config.last_triggered = datetime.utcnow()
                return alert

            return None
        except Exception as e:
            logger.error("Error checking alert: %s", str(e))
            return None
