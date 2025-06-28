import atexit
import os
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fs_agt_clean.services.conversation_context.context_manager import ContextManager


class ConversationService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self, context_dir: str = "conversation_contexts", auto_save_interval: int = 300
    ):
        if not hasattr(self, "initialized"):
            self.context_manager = ContextManager()
            self.context_dir = context_dir
            self.auto_save_interval = auto_save_interval
            self.current_conversation_id = None
            os.makedirs(context_dir, exist_ok=True)

            # Start background auto-save thread
            self._stop_auto_save = threading.Event()
            self._auto_save_thread = threading.Thread(
                target=self._auto_save_loop, daemon=True
            )
            self._auto_save_thread.start()

            # Register cleanup on program exit
            atexit.register(self._cleanup)
            self.initialized = True

    def _auto_save_loop(self):
        """Background thread that automatically saves context periodically"""
        while not self._stop_auto_save.is_set():
            if self.current_conversation_id:
                self.save_conversation_state(self.current_conversation_id)
            time.sleep(self.auto_save_interval)

    def _cleanup(self):
        """Cleanup method called on program exit"""
        self._stop_auto_save.set()
        if self.current_conversation_id:
            self.save_conversation_state(self.current_conversation_id)

    def start_conversation(self, conversation_id: str):
        """Start or resume a conversation"""
        if self.current_conversation_id:
            self.save_conversation_state(self.current_conversation_id)

        self.current_conversation_id = conversation_id
        if not self.load_conversation_state(conversation_id):
            # If no existing state, initialize new conversation
            self.context_manager = ContextManager()

    def start_new_task(self, task: str):
        """Start focusing on a new task"""
        self.context_manager.set_focus(task)

    def complete_task(self, task: str, state: Dict[str, any]):
        """Mark a task as complete and create a milestone"""
        if task in self.context_manager.context.active_tasks:
            self.context_manager.add_milestone(
                description=f"Completed task: {task}",
                completed_tasks=[task],
                state=state,
            )
            self.context_manager.context.active_tasks.remove(task)
            # Auto-save on milestone
            if self.current_conversation_id:
                self.save_conversation_state(self.current_conversation_id)

    def handle_error(self, error: str):
        """Handle an error by storing its context"""
        self.context_manager.add_error_context(error)

    def resolve_error(self):
        """Clear error context after resolution"""
        self.context_manager.clear_error_context()

    def get_current_context(self) -> Dict[str, any]:
        """Get the current conversation context"""
        return self.context_manager.get_relevant_context()

    def save_conversation_state(self, conversation_id: str):
        """Save the current conversation state"""
        filepath = os.path.join(self.context_dir, f"{conversation_id}.json")
        self.context_manager.save_context(filepath)

    def load_conversation_state(self, conversation_id: str) -> bool:
        """Load a previous conversation state"""
        filepath = os.path.join(self.context_dir, f"{conversation_id}.json")
        return self.context_manager.load_context(filepath)

    def reset_to_last_milestone(self) -> bool:
        """Reset the context to the last milestone"""
        milestones = self.context_manager.context.milestones
        if milestones:
            return self.context_manager.reset_to_milestone(len(milestones) - 1)
        return False

    def summarize_progress(self) -> Dict[str, any]:
        """Summarize the conversation progress"""
        milestones = self.context_manager.context.milestones
        active_tasks = self.context_manager.context.active_tasks

        return {
            "completed_tasks": [
                {
                    "description": m.description,
                    "timestamp": m.timestamp,
                    "tasks": m.completed_tasks,
                }
                for m in milestones
            ],
            "active_tasks": active_tasks,
            "current_focus": self.context_manager.context.current_focus,
            "milestone_count": len(milestones),
            "conversation_id": self.current_conversation_id,
        }
