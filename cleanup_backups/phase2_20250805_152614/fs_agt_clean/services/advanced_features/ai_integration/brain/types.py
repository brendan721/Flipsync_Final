from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Strategy:
    strategy_id: uuid
    name: str
    description: str
    rules: Dict[str, Any]
    parameters: Dict[str, Any]
    tags: set[str]


@dataclass
class MemoryManager:
    memory_id: uuid
    storage: Dict[str, Any]


@dataclass
class DecisionEngine:
    engine_id: uuid
    model: Any


@dataclass
class StrategyManager:
    strategies: Dict[uuid, Strategy]
