"""
Database migration to add metrics and monitoring tables.

This migration creates the following tables:
- metric_data_points: Individual metric data points
- system_metrics: System-level metrics snapshots
- agent_metrics: UnifiedAgent-specific metrics
- alert_records: Alert records with lifecycle management
- metric_thresholds: Metric thresholds for alerting
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """Create metrics and monitoring tables."""
    
    # Create metric_data_points table
    op.create_table(
        'metric_data_points',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('type', sa.Enum('GAUGE', 'COUNTER', 'HISTOGRAM', 'SUMMARY', name='metrictype'), nullable=False),
        sa.Column('category', sa.Enum('SYSTEM', 'PERFORMANCE', 'BUSINESS', 'SECURITY', 'AGENT', 'CONVERSATION', 'DECISION', 'MOBILE', 'API', name='metriccategory'), nullable=False),
        sa.Column('labels', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('agent_id', sa.String(255), nullable=True, index=True),
        sa.Column('service_name', sa.String(255), nullable=True, index=True),
    )
    
    # Create indexes for metric_data_points
    op.create_index('idx_metric_name_timestamp', 'metric_data_points', ['name', 'timestamp'])
    op.create_index('idx_metric_category_timestamp', 'metric_data_points', ['category', 'timestamp'])
    op.create_index('idx_metric_agent_timestamp', 'metric_data_points', ['agent_id', 'timestamp'])
    op.create_index('idx_metric_service_timestamp', 'metric_data_points', ['service_name', 'timestamp'])
    
    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('cpu_usage_percent', sa.Float, nullable=True),
        sa.Column('memory_total_bytes', sa.BigInteger, nullable=True),
        sa.Column('memory_used_bytes', sa.BigInteger, nullable=True),
        sa.Column('memory_usage_percent', sa.Float, nullable=True),
        sa.Column('disk_total_bytes', sa.BigInteger, nullable=True),
        sa.Column('disk_used_bytes', sa.BigInteger, nullable=True),
        sa.Column('disk_usage_percent', sa.Float, nullable=True),
        sa.Column('network_bytes_sent', sa.BigInteger, nullable=True),
        sa.Column('network_bytes_received', sa.BigInteger, nullable=True),
        sa.Column('process_cpu_percent', sa.Float, nullable=True),
        sa.Column('process_memory_percent', sa.Float, nullable=True),
        sa.Column('process_memory_rss', sa.BigInteger, nullable=True),
        sa.Column('process_memory_vms', sa.BigInteger, nullable=True),
        sa.Column('process_num_threads', sa.Integer, nullable=True),
        sa.Column('process_num_fds', sa.Integer, nullable=True),
        sa.Column('hostname', sa.String(255), nullable=True),
        sa.Column('service_name', sa.String(255), nullable=True, index=True),
    )
    
    # Create agent_metrics table
    op.create_table(
        'agent_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(255), nullable=False, index=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('uptime_seconds', sa.Float, nullable=True),
        sa.Column('error_count', sa.Integer, nullable=False, default=0),
        sa.Column('last_error_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_success_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requests_total', sa.Integer, nullable=True, default=0),
        sa.Column('requests_success', sa.Integer, nullable=True, default=0),
        sa.Column('requests_failed', sa.Integer, nullable=True, default=0),
        sa.Column('avg_response_time_ms', sa.Float, nullable=True),
        sa.Column('peak_response_time_ms', sa.Float, nullable=True),
        sa.Column('cpu_usage_percent', sa.Float, nullable=True),
        sa.Column('memory_usage_percent', sa.Float, nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
    )
    
    # Create indexes for agent_metrics
    op.create_index('idx_agent_metrics_agent_timestamp', 'agent_metrics', ['agent_id', 'timestamp'])
    op.create_index('idx_agent_metrics_status_timestamp', 'agent_metrics', ['status', 'timestamp'])
    
    # Create alert_records table
    op.create_table(
        'alert_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('alert_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('level', sa.Enum('INFO', 'WARNING', 'ERROR', 'CRITICAL', name='alertlevel'), nullable=False, index=True),
        sa.Column('category', sa.Enum('SYSTEM', 'PERFORMANCE', 'SECURITY', 'BUSINESS', 'AGENT', 'CONVERSATION', 'DECISION', 'MOBILE', 'API', name='alertcategory'), nullable=False, index=True),
        sa.Column('source', sa.Enum('SYSTEM', 'USER', 'AGENT', 'MONITORING', 'SECURITY', name='alertsource'), nullable=False, index=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('labels', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('acknowledged', sa.Boolean, nullable=False, default=False),
        sa.Column('acknowledged_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
        sa.Column('correlation_id', sa.String(255), nullable=True, index=True),
        sa.Column('fingerprint', sa.String(255), nullable=True, index=True),
        sa.Column('resolved', sa.Boolean, nullable=False, default=False),
        sa.Column('resolved_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(255), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
    )
    
    # Create indexes for alert_records
    op.create_index('idx_alert_level_timestamp', 'alert_records', ['level', 'timestamp'])
    op.create_index('idx_alert_category_timestamp', 'alert_records', ['category', 'timestamp'])
    op.create_index('idx_alert_source_timestamp', 'alert_records', ['source', 'timestamp'])
    op.create_index('idx_alert_acknowledged_timestamp', 'alert_records', ['acknowledged', 'timestamp'])
    op.create_index('idx_alert_resolved_timestamp', 'alert_records', ['resolved', 'timestamp'])
    
    # Create metric_thresholds table
    op.create_table(
        'metric_thresholds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_name', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('warning_threshold', sa.Float, nullable=True),
        sa.Column('critical_threshold', sa.Float, nullable=True),
        sa.Column('enabled', sa.Boolean, nullable=False, default=True),
        sa.Column('comparison_operator', sa.String(10), nullable=False, default='>='),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=True),
        sa.Column('updated_by', sa.String(255), nullable=True),
    )


def downgrade():
    """Drop metrics and monitoring tables."""
    
    # Drop tables in reverse order
    op.drop_table('metric_thresholds')
    op.drop_table('alert_records')
    op.drop_table('agent_metrics')
    op.drop_table('system_metrics')
    op.drop_table('metric_data_points')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS alertsource')
    op.execute('DROP TYPE IF EXISTS alertcategory')
    op.execute('DROP TYPE IF EXISTS alertlevel')
    op.execute('DROP TYPE IF EXISTS metriccategory')
    op.execute('DROP TYPE IF EXISTS metrictype')
