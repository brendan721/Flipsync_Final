-- FlipSync Learning Data Database Schemas
-- Phase 3 Step 3: Learning Data Database Persistence
-- Production Database: flipsync_agentic_test on 174.138.77.110:5432

-- =====================================================
-- POLICY OPTIMIZER LEARNING PERSISTENCE
-- =====================================================

-- Policy optimization history and strategy evolution
CREATE TABLE IF NOT EXISTS policy_optimization_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    optimization_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Policy data
    current_policy JSONB NOT NULL,
    optimized_policy JSONB NOT NULL,
    optimization_objective VARCHAR(100) NOT NULL,
    optimization_algorithm VARCHAR(100) NOT NULL,
    
    -- Performance metrics
    performance_metrics JSONB NOT NULL,
    improvement_score DECIMAL(10, 6) DEFAULT 0.0,
    confidence_score DECIMAL(10, 6) DEFAULT 0.0,
    
    -- Learning parameters
    learning_rate DECIMAL(10, 6) DEFAULT 0.01,
    iteration_count INTEGER DEFAULT 1,
    convergence_status VARCHAR(50) DEFAULT 'in_progress',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing for performance
    CONSTRAINT unique_agent_optimization UNIQUE(agent_id, optimization_id)
);

-- Policy strategy evolution tracking
CREATE TABLE IF NOT EXISTS policy_strategy_evolution (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    strategy_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Strategy data
    strategy_name VARCHAR(255) NOT NULL,
    strategy_parameters JSONB NOT NULL,
    strategy_version INTEGER DEFAULT 1,
    
    -- Performance tracking
    success_rate DECIMAL(10, 6) DEFAULT 0.0,
    average_performance DECIMAL(10, 6) DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    
    -- Evolution metadata
    parent_strategy_id UUID REFERENCES policy_strategy_evolution(strategy_id),
    evolution_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing
    CONSTRAINT unique_agent_strategy UNIQUE(agent_id, strategy_name, strategy_version)
);

-- =====================================================
-- LEARNING MODULE KNOWLEDGE PERSISTENCE
-- =====================================================

-- Learning patterns and knowledge base (complementing vector store)
CREATE TABLE IF NOT EXISTS learning_knowledge_base (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    knowledge_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Knowledge data
    knowledge_type VARCHAR(100) NOT NULL,
    knowledge_content JSONB NOT NULL,
    knowledge_source VARCHAR(100) NOT NULL, -- 'feedback', 'pattern', 'cross_agent'
    
    -- Learning metrics
    confidence_score DECIMAL(10, 6) DEFAULT 0.0,
    usage_frequency INTEGER DEFAULT 0,
    success_rate DECIMAL(10, 6) DEFAULT 0.0,
    
    -- Relationships
    related_asin VARCHAR(50),
    related_context JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing
    CONSTRAINT unique_agent_knowledge UNIQUE(agent_id, knowledge_id)
);

-- Learning feedback processing results
CREATE TABLE IF NOT EXISTS learning_feedback_history (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    feedback_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Feedback data
    asin VARCHAR(50) NOT NULL,
    feedback_data JSONB NOT NULL,
    processing_result JSONB NOT NULL,
    
    -- Learning outcomes
    patterns_discovered JSONB DEFAULT '[]'::jsonb,
    knowledge_updated JSONB DEFAULT '[]'::jsonb,
    performance_impact DECIMAL(10, 6) DEFAULT 0.0,
    
    -- Processing metadata
    processing_time_ms INTEGER DEFAULT 0,
    llm_used BOOLEAN DEFAULT FALSE,
    vector_store_updated BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning performance metrics over time
CREATE TABLE IF NOT EXISTS learning_performance_metrics (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    metric_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Performance data
    metric_type VARCHAR(100) NOT NULL, -- 'decision_accuracy', 'learning_speed', 'adaptation_rate'
    metric_value DECIMAL(10, 6) NOT NULL,
    baseline_value DECIMAL(10, 6) DEFAULT 0.0,
    improvement_percentage DECIMAL(10, 6) DEFAULT 0.0,
    
    -- Context
    measurement_context JSONB,
    measurement_period VARCHAR(50), -- 'daily', 'weekly', 'monthly'
    
    -- Metadata
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- CROSS-AGENT LEARNING COORDINATION
-- =====================================================

-- Cross-agent learning insights and knowledge sharing
CREATE TABLE IF NOT EXISTS cross_agent_learning_insights (
    id SERIAL PRIMARY KEY,
    insight_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Source and target agents
    source_agent_id VARCHAR(255) NOT NULL,
    source_agent_type VARCHAR(50) NOT NULL,
    target_agents JSONB NOT NULL, -- Array of agent IDs that received this insight
    
    -- Insight data
    insight_type VARCHAR(100) NOT NULL,
    insight_content JSONB NOT NULL,
    insight_context JSONB,
    
    -- Effectiveness tracking
    effectiveness_score DECIMAL(10, 6) DEFAULT 0.0,
    adoption_rate DECIMAL(10, 6) DEFAULT 0.0,
    impact_metrics JSONB DEFAULT '{}'::jsonb,
    
    -- Sharing metadata
    shared_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing
    CONSTRAINT unique_insight UNIQUE(insight_id)
);

-- Cross-agent learning coordination state
CREATE TABLE IF NOT EXISTS cross_agent_coordination_state (
    id SERIAL PRIMARY KEY,
    coordination_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Coordination participants
    participating_agents JSONB NOT NULL,
    coordination_type VARCHAR(100) NOT NULL, -- 'knowledge_sharing', 'collective_learning', 'conflict_resolution'
    
    -- Coordination data
    coordination_data JSONB NOT NULL,
    coordination_status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'failed'
    
    -- Results
    coordination_results JSONB DEFAULT '{}'::jsonb,
    success_metrics JSONB DEFAULT '{}'::jsonb,
    
    -- Metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning conflict resolution for contradictory insights
CREATE TABLE IF NOT EXISTS learning_conflict_resolution (
    id SERIAL PRIMARY KEY,
    conflict_id UUID NOT NULL DEFAULT gen_random_uuid(),
    
    -- Conflict participants
    conflicting_agents JSONB NOT NULL,
    conflict_type VARCHAR(100) NOT NULL,
    
    -- Conflict data
    conflicting_insights JSONB NOT NULL,
    conflict_context JSONB,
    
    -- Resolution
    resolution_strategy VARCHAR(100), -- 'majority_vote', 'performance_weighted', 'expert_agent', 'hybrid'
    resolution_result JSONB,
    resolution_confidence DECIMAL(10, 6) DEFAULT 0.0,
    
    -- Metadata
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexing
    CONSTRAINT unique_conflict UNIQUE(conflict_id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================

-- Policy optimization indexes
CREATE INDEX IF NOT EXISTS idx_policy_optimization_agent_id ON policy_optimization_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_policy_optimization_created_at ON policy_optimization_history(created_at);
CREATE INDEX IF NOT EXISTS idx_policy_strategy_agent_id ON policy_strategy_evolution(agent_id);

-- Learning module indexes
CREATE INDEX IF NOT EXISTS idx_learning_knowledge_agent_id ON learning_knowledge_base(agent_id);
CREATE INDEX IF NOT EXISTS idx_learning_knowledge_type ON learning_knowledge_base(knowledge_type);
CREATE INDEX IF NOT EXISTS idx_learning_knowledge_asin ON learning_knowledge_base(related_asin);
CREATE INDEX IF NOT EXISTS idx_learning_feedback_agent_id ON learning_feedback_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_learning_feedback_asin ON learning_feedback_history(asin);

-- Cross-agent learning indexes
CREATE INDEX IF NOT EXISTS idx_cross_agent_insights_source ON cross_agent_learning_insights(source_agent_id);
CREATE INDEX IF NOT EXISTS idx_cross_agent_insights_type ON cross_agent_learning_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_cross_agent_coordination_status ON cross_agent_coordination_state(coordination_status);

-- Performance metrics indexes
CREATE INDEX IF NOT EXISTS idx_learning_performance_agent_id ON learning_performance_metrics(agent_id);
CREATE INDEX IF NOT EXISTS idx_learning_performance_type ON learning_performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_learning_performance_measured_at ON learning_performance_metrics(measured_at);

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE policy_optimization_history IS 'Stores PolicyOptimizer optimization history and strategy evolution for learning persistence';
COMMENT ON TABLE learning_knowledge_base IS 'Stores LearningModule knowledge base complementing vector store data';
COMMENT ON TABLE cross_agent_learning_insights IS 'Stores insights shared between agents for collective intelligence';
COMMENT ON TABLE learning_conflict_resolution IS 'Handles resolution of contradictory learning insights between agents';
