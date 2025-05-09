"""Base Task Agent."""

import abc
from typing import Any, Dict, List, Optional, Union

class TaskAgent(abc.ABC):
    """Base class for all task agents."""

    @abc.abstractmethod
    def perform_task(self, task: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Perform a task and return the result."""
        pass

    def __call__(self, task: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Call the agent to perform a task."""
        return self.perform_task(task, **kwargs)
