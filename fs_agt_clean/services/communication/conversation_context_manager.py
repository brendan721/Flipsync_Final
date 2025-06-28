import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class MilestoneMarker:
    """Marks important points in the conversation where context can be reset"""

    timestamp: datetime
    description: str
    completed_tasks: List[str]
    state: Dict[str, any]


@dataclass
class ConversationContext:
    """Manages the active context of the conversation"""

    active_tasks: List[str] = field(default_factory=list)
    current_focus: Optional[str] = None
    error_context: List[str] = field(default_factory=list)
    last_successful_state: Dict[str, any] = field(default_factory=dict)
    milestones: List[MilestoneMarker] = field(default_factory=list)


class ContextManager:
    def __init__(self):
        self.context = ConversationContext()

    def add_milestone(
        self, description: str, completed_tasks: List[str], state: Dict[str, any]
    ):
        """Add a milestone marker to potentially reset context later"""
        milestone = MilestoneMarker(
            timestamp=datetime.utcnow(),
            description=description,
            completed_tasks=completed_tasks,
            state=state,
        )
        self.context.milestones.append(milestone)

    def reset_to_milestone(self, milestone_index: int) -> bool:
        """Reset context to a specific milestone"""
        if 0 <= milestone_index < len(self.context.milestones):
            milestone = self.context.milestones[milestone_index]
            self.context.active_tasks = []
            self.context.error_context = []
            self.context.last_successful_state = milestone.state.copy()
            self.context.current_focus = None
            return True
        return False

    def set_focus(self, task: str):
        """Set the current focus of the conversation"""
        self.context.current_focus = task
        if task not in self.context.active_tasks:
            self.context.active_tasks.append(task)

    def add_error_context(self, error: str):
        """Add error context that might be relevant for debugging"""
        self.context.error_context.append(error)

    def clear_error_context(self):
        """Clear error context after resolution"""
        self.context.error_context = []

    def update_state(self, state_update: Dict[str, any]):
        """Update the last successful state"""
        self.context.last_successful_state.update(state_update)

    def get_relevant_context(self) -> Dict[str, any]:
        """Get the current relevant context"""
        return {
            "current_focus": self.context.current_focus,
            "active_tasks": self.context.active_tasks,
            "error_context": self.context.error_context,
            "last_state": self.context.last_successful_state,
        }

    def save_context(self, filepath: str):
        """Save the current context to a file"""
        context_data = {
            "active_tasks": self.context.active_tasks,
            "current_focus": self.context.current_focus,
            "error_context": self.context.error_context,
            "last_successful_state": self.context.last_successful_state,
            "milestones": [
                {
                    "timestamp": m.timestamp.isoformat(),
                    "description": m.description,
                    "completed_tasks": m.completed_tasks,
                    "state": m.state,
                }
                for m in self.context.milestones
            ],
        }
        with open(filepath, "w") as f:
            json.dump(context_data, f, indent=2)

    def load_context(self, filepath: str) -> bool:
        """Load context from a file"""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            self.context.active_tasks = data["active_tasks"]
            self.context.current_focus = data["current_focus"]
            self.context.error_context = data["error_context"]
            self.context.last_successful_state = data["last_successful_state"]
            self.context.milestones = [
                MilestoneMarker(
                    timestamp=datetime.fromisoformat(m["timestamp"]),
                    description=m["description"],
                    completed_tasks=m["completed_tasks"],
                    state=m["state"],
                )
                for m in data["milestones"]
            ]
            return True
        except Exception:
            return False
