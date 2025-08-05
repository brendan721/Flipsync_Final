"""
Conflict Resolution Module for FlipSync Phase 4
===============================================

Advanced conflict resolution and distributed consensus systems.
"""

from .distributed_consensus_engine import (
    DistributedConsensusEngine,
    ConflictType,
    ConsensusState,
    VoteType,
    ConflictResolutionRequest,
    ConsensusVote,
    ConsensusResult
)

__all__ = [
    "DistributedConsensusEngine",
    "ConflictType",
    "ConsensusState", 
    "VoteType",
    "ConflictResolutionRequest",
    "ConsensusVote",
    "ConsensusResult"
]
