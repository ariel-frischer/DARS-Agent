"""
Expansion strategies for DARS agent following Open/Closed Principle.

Strategies are open for extension but closed for modification.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import re
from sweagent.agent.interfaces import IExpansionStrategy
from sweagent.agent.node_manager import DARSNode


class BaseExpansionStrategy(IExpansionStrategy):
    """
    Base expansion strategy following Open/Closed Principle.

    New strategies can extend this without modifying existing code.
    """

    def __init__(self, config, model_interface, logger):
        """
        Initialize expansion strategy.

        Args:
            config: DARS configuration
            model_interface: Interface to query models
            logger: Logger instance
        """
        self.config = config
        self.model = model_interface
        self.logger = logger

    @abstractmethod
    def should_expand(self, node: DARSNode, config: Any) -> bool:
        """Determine if node should be expanded."""
        pass

    @abstractmethod
    def get_expansion_candidates(self, node: DARSNode, num_samples: int) -> List[Tuple]:
        """Generate expansion candidates."""
        pass

    @abstractmethod
    def select_best_expansion(self, candidates: List[Any]) -> int:
        """Select best expansion from candidates."""
        pass


class ActionLimitExpansionStrategy(BaseExpansionStrategy):
    """
    Expansion strategy based on action limits.

    Follows SRP: Only handles expansion decisions based on action limits.
    """

    def should_expand(self, node: DARSNode, config: Any) -> bool:
        """
        Determine if node should expand based on action limits.

        Args:
            node: Node to evaluate
            config: DARS configuration

        Returns:
            True if node should expand
        """
        allowed_actions = self._get_allowed_actions(node, config)
        if not node.action:
            return False

        action_type = node.action.split()[0]
        if not allowed_actions or action_type not in allowed_actions:
            return False

        if node._action_expansion_limit is not None:
            return node._action_expansion_limit.get(action_type, 0) > 0

        return False

    def _get_allowed_actions(self, node: DARSNode, config: Any) -> List[str]:
        """
        Get allowed actions for expansion.

        Args:
            node: Current node
            config: DARS configuration

        Returns:
            List of allowed action types
        """
        if not node.expansion_history:
            return (list(config.action_expansion_limit.keys())
                    if config.action_expansion_limit is not None
                    else [])

        first_action = node.expansion_history[0]
        if first_action not in config.allowed_action_in_expansion:
            return []

        allowed_actions = set(config.allowed_action_in_expansion[first_action])

        for action in node.expansion_history[1:]:
            if action not in config.allowed_action_in_expansion:
                return []
            allowed_actions.intersection_update(config.allowed_action_in_expansion[action])
            if not allowed_actions:
                return []

        if config.action_expansion_limit is not None:
            allowed_actions.intersection_update(config.action_expansion_limit.keys())

        return list(allowed_actions)

    def get_expansion_candidates(self, node: DARSNode, num_samples: int) -> List[Tuple]:
        """
        Generate expansion candidates through model sampling.

        Args:
            node: Node to expand from
            num_samples: Number of samples to generate

        Returns:
            List of (thought, action, output) tuples
        """
        candidates = []
        expansion_context = self._get_expansion_prompt(node)

        for _ in range(num_samples):
            # Generate candidate through model
            thought, action, output = self._generate_candidate(
                node,
                expansion_context,
                temperature=self.config.DARS.expansion_temperature
            )
            candidates.append((thought, action, output))

        return candidates

    def _get_expansion_prompt(self, node: DARSNode) -> str:
        """
        Get prompt for expansion based on action type.

        Args:
            node: Node to expand

        Returns:
            Expansion prompt string
        """
        command_handlers = {
            'edit': self.config.DARS_prompts.edit_expansion_prompt_template,
            'insert': self.config.DARS_prompts.insert_expansion_prompt_template,
            'append': self.config.DARS_prompts.append_expansion_prompt_template,
            'submit': self.config.DARS_prompts.submit_expansion_prompt_template,
            'create': self.config.DARS_prompts.create_expansion_prompt_template,
        }

        if not node.parent or not node.parent.action:
            return ""

        action = node.parent.action.split()[0]
        prompt_template = command_handlers.get(action, '')

        if action not in ['create', 'submit']:
            context = self._build_lookahead_context(node)
            return prompt_template.format(action=node.parent.action, prev_traj=context)

        return prompt_template

    def _build_lookahead_context(self, node: DARSNode) -> str:
        """Build context from lookahead trajectory."""
        lookahead = self.config.DARS.n_lookahead
        context = ""
        patch = ""
        tmp = node.parent

        while lookahead and tmp:
            if tmp.action and tmp.action.split()[0] == "submit":
                patch = tmp.children[0].content if tmp.children else ""
                if self.config.DARS.summarize_expansion_context:
                    break

            if tmp.action:
                context += f"ACTION: {tmp.action}\n"
            if tmp.children:
                context += f"OBSERVATION: {tmp.children[0].content[-10000:]}\n\n"

            if not tmp.children or not tmp.children[0].children:
                break

            tmp = tmp.children[0].children[0]
            lookahead -= 1

        if self.config.DARS.summarize_expansion_context:
            context = self._summarize_context(context, patch)

        return context

    def _summarize_context(self, context: str, patch: str) -> str:
        """Summarize context using model."""
        # Placeholder - would use model to summarize
        return context

    def _generate_candidate(self, node: DARSNode, expansion_context: str, temperature: float) -> Tuple[str, str, str]:
        """Generate a candidate expansion."""
        # Placeholder - would use model interface
        return ("", "", "")

    def select_best_expansion(self, node: DARSNode, candidates: List[str]) -> int:
        """
        Select best expansion using critic model.

        Args:
            node: Current node
            candidates: List of candidate actions

        Returns:
            Index of best candidate
        """
        actions_context = ""
        for i, action in enumerate(candidates):
            actions_context += f"Action {i}:\n{action}\n"

        critic_prompt = self.config.DARS_prompts.critic_expansion_prompt_template.replace(
            "{actions}", f'\n{"".join(candidates)}'
        ).replace("{previous_action}", node.children[0].action if node.children else "")

        # Query critic model
        try:
            response = self._query_critic(node, critic_prompt)
            action_index = self._extract_best_action_index(response)
            return action_index
        except Exception as e:
            self.logger.warning(f"Error in selecting expansion: {e}")
            return 0

    def _query_critic(self, node: DARSNode, prompt: str) -> str:
        """Query critic model for evaluation."""
        # Placeholder - would use model interface
        return ""

    def _extract_best_action_index(self, response: str) -> int:
        """Extract best action index from critic response."""
        pattern = r'<best_action_index>(\d+)</best_action_index>'
        match = re.search(pattern, response)
        if match:
            return int(match.group(1))
        raise ValueError("No best action index found in response")


class GreedyExpansionStrategy(BaseExpansionStrategy):
    """
    Greedy expansion strategy that always takes first available action.

    Example of extending base strategy without modifying it.
    """

    def should_expand(self, node: DARSNode, config: Any) -> bool:
        """Always expand if node has children."""
        return len(node.children) == 0 and node.depth < config.DARS.max_branch_depth

    def get_expansion_candidates(self, node: DARSNode, num_samples: int) -> List[Tuple]:
        """Generate single greedy candidate."""
        return [("greedy", "greedy_action", "greedy_output")]

    def select_best_expansion(self, candidates: List[Any]) -> int:
        """Always select first candidate."""
        return 0


class ExpansionStrategyFactory:
    """
    Factory for creating expansion strategies.

    Follows Open/Closed: New strategies can be registered without modifying factory.
    """

    _strategies: Dict[str, type] = {
        'action_limit': ActionLimitExpansionStrategy,
        'greedy': GreedyExpansionStrategy,
    }

    @classmethod
    def register_strategy(cls, name: str, strategy_class: type) -> None:
        """
        Register a new expansion strategy.

        Args:
            name: Strategy identifier
            strategy_class: Strategy class to register
        """
        cls._strategies[name] = strategy_class

    @classmethod
    def create(cls, strategy_name: str, config, model_interface, logger) -> BaseExpansionStrategy:
        """
        Create an expansion strategy.

        Args:
            strategy_name: Name of strategy to create
            config: Configuration object
            model_interface: Model interface
            logger: Logger instance

        Returns:
            Expansion strategy instance

        Raises:
            ValueError: If strategy name not found
        """
        if strategy_name not in cls._strategies:
            raise ValueError(f"Unknown expansion strategy: {strategy_name}")

        strategy_class = cls._strategies[strategy_name]
        return strategy_class(config, model_interface, logger)
