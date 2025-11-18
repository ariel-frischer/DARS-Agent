"""Strategy patterns for agent behavior - Open/Closed Principle."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IPromptStrategy(ABC):
    """Strategy for generating prompts based on context."""

    @abstractmethod
    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate a prompt based on the given context."""
        pass


class InitialPromptStrategy(IPromptStrategy):
    """Strategy for initial instance prompts."""

    def __init__(self, instance_template: str, strategy_template: Optional[str] = None):
        self.instance_template = instance_template
        self.strategy_template = strategy_template

    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate initial prompt."""
        templates = [self.instance_template]
        if self.strategy_template is not None:
            templates.append(self.strategy_template)

        messages = []
        for template in templates:
            messages.append(template.format(**context))

        return "\n".join(messages)


class NextStepPromptStrategy(IPromptStrategy):
    """Strategy for next step prompts."""

    def __init__(self, next_step_template: str):
        self.next_step_template = next_step_template

    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate next step prompt."""
        return self.next_step_template.format(**context)


class CodeGraphPromptStrategy(IPromptStrategy):
    """Strategy for prompts with code graph context."""

    def __init__(self, codegraph_template: str):
        self.codegraph_template = codegraph_template

    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate code graph-aware prompt."""
        return self.codegraph_template.format(**context)


class NoOutputPromptStrategy(IPromptStrategy):
    """Strategy for prompts when there's no output."""

    def __init__(self, no_output_template: str):
        self.no_output_template = no_output_template

    def generate_prompt(self, context: Dict[str, Any]) -> str:
        """Generate no-output prompt."""
        return self.no_output_template.format(**context)


class PromptStrategyFactory:
    """Factory for creating appropriate prompt strategies."""

    def __init__(self, config):
        self.config = config

    def create_strategy(self, observation: str, last_role: str,
                       is_demo: bool, codegraph_context: Optional[str]) -> IPromptStrategy:
        """Create appropriate prompt strategy based on context."""
        if last_role == "system" or is_demo:
            return InitialPromptStrategy(
                self.config.instance_template,
                self.config.strategy_template
            )
        elif observation is None or observation.strip() == "":
            return NoOutputPromptStrategy(self.config.next_step_no_output_template)
        elif codegraph_context and codegraph_context.lower() != 'none':
            return CodeGraphPromptStrategy(self.config.next_step_codegraph_template)
        else:
            return NextStepPromptStrategy(self.config.next_step_template)


class IActionExecutionStrategy(ABC):
    """Strategy for executing different types of actions."""

    @abstractmethod
    def execute(self, action: str, env: Any) -> tuple[str, bool, Dict[str, Any]]:
        """Execute an action and return observation, done flag, and info."""
        pass

    @abstractmethod
    def can_handle(self, action: str) -> bool:
        """Check if this strategy can handle the given action."""
        pass


class StandardActionStrategy(IActionExecutionStrategy):
    """Standard action execution strategy."""

    def execute(self, action: str, env: Any) -> tuple[str, bool, Dict[str, Any]]:
        """Execute standard action in environment."""
        return env.step(action)

    def can_handle(self, action: str) -> bool:
        """Can handle any standard action."""
        return True


class SearchRepoActionStrategy(IActionExecutionStrategy):
    """Strategy for search_repo actions."""

    def __init__(self, get_codegraph_path_callback, logger=None):
        self.get_codegraph_path = get_codegraph_path_callback
        self.logger = logger

    def execute(self, action: str, env: Any) -> tuple[str, bool, Dict[str, Any]]:
        """Execute search_repo action."""
        search_term = action.split(' ', 1)[1] if len(action.split(' ', 1)) > 1 else ""
        codegraph_path = self.get_codegraph_path(env)

        if self.logger:
            self.logger.info(f'Calling Retrieve Graph with search term: {search_term}')

        obs = env.communicate(
            f'python /root/retrieve_graph.py --search_term {search_term} --codegraph_dir {codegraph_path}'
        )

        if self.logger:
            self.logger.info(f'Codegraph context:\n{obs}')

        return obs, False, {"codegraph_keyword": search_term, "codegraph_context": obs}

    def can_handle(self, action: str) -> bool:
        """Check if action is search_repo."""
        return 'search_repo' in action


class ActionExecutor:
    """Executes actions using appropriate strategy."""

    def __init__(self):
        self.strategies: List[IActionExecutionStrategy] = []

    def add_strategy(self, strategy: IActionExecutionStrategy) -> None:
        """Add an action execution strategy."""
        self.strategies.append(strategy)

    def execute(self, action: str, env: Any) -> tuple[str, bool, Dict[str, Any]]:
        """Execute action using first matching strategy."""
        for strategy in self.strategies:
            if strategy.can_handle(action):
                return strategy.execute(action, env)

        # Fallback to standard execution
        return env.step(action)
