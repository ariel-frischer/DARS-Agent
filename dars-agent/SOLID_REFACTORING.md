# SOLID Principles Refactoring

This document describes the SOLID principles refactoring applied to the dars-agent codebase.

## Overview

The refactoring extracted responsibilities from large monolithic classes into focused, single-purpose classes following SOLID principles.

## 1. Single Responsibility Principle (SRP)

### Agent Class Refactoring

**Before:** The `Agent` class had multiple responsibilities:
- Model interaction and querying
- History management
- Command parsing and pattern matching
- Action splitting and execution
- Environment variable setup
- Subroutine management

**After:** Extracted into separate classes:

1. **`IHistoryManager` / `ListHistoryManager`** (`history_manager.py`)
   - Responsibility: Manage conversation history
   - Methods: `append()`, `get_history()`, `clear()`

2. **`ICommandParser` / `RegexCommandParser`** (`command_parser.py`)
   - Responsibility: Parse commands and split actions
   - Methods: `parse_command_patterns()`, `get_first_match()`, `split_actions()`, `guard_multiline_input()`

3. **`IModelInteraction` / `ModelQueryHandler`** (`model_interaction.py`)
   - Responsibility: Handle model queries and response parsing
   - Methods: `query_model()`, `parse_response()`

4. **`RetryHandler`** (`model_interaction.py`)
   - Responsibility: Handle retry logic for errors
   - Methods: `retry_after_format_fail()`, `retry_after_blocklist_fail()`, `check_format_and_requery()`

### SWEEnv Class Refactoring

**Before:** The `SWEEnv` class handled:
- Container lifecycle management
- Git operations
- Conda environment installation
- Communication with containers
- Code graph initialization
- Repository management

**After:** Extracted into:

1. **`IContainerManager` / `DockerContainerManager`** (`container_manager.py`)
   - Responsibility: Manage Docker container lifecycle
   - Methods: `create_container()`, `get_container_object()`, `remove_container()`, `pause_container()`

2. **`ICommunicationHandler` / `BashCommunicationHandler`** (`communication_handler.py`)
   - Responsibility: Handle container communication
   - Methods: `communicate()`, `check_syntax()`

3. **`IEnvironmentInstaller` / `CondaEnvironmentInstaller`** (`environment_installer.py`)
   - Responsibility: Install and configure conda environments
   - Methods: `install()`, `get_install_config()`, `conda_environment_exists()`

## 2. Open/Closed Principle (OCP)

**Extension point created:** Strategy patterns for extensibility without modification

1. **`IPromptStrategy`** (`strategies.py`)
   - Multiple implementations: `InitialPromptStrategy`, `NextStepPromptStrategy`, `CodeGraphPromptStrategy`, `NoOutputPromptStrategy`
   - Factory pattern: `PromptStrategyFactory` selects appropriate strategy
   - New prompt types can be added without modifying existing code

2. **`IActionExecutionStrategy`** (`strategies.py`)
   - Implementations: `StandardActionStrategy`, `SearchRepoActionStrategy`
   - `ActionExecutor` uses strategies to handle different action types
   - New action types can be added by creating new strategies

## 3. Liskov Substitution Principle (LSP)

All interfaces and abstract base classes follow LSP:

- `IHistoryManager` implementations can be substituted without breaking functionality
- `ICommandParser` implementations are interchangeable
- `IContainerManager` implementations (Docker, future Podman) are substitutable
- `IPromptStrategy` implementations can be swapped based on context

## 4. Interface Segregation Principle (ISP)

**Before:** Large monolithic hook interfaces forced implementations to define many unused methods:
```python
class AgentHook:
    def on_init(self): ...
    def on_run_start(self): ...
    def on_step_start(self): ...
    def on_actions_generated(self, ...): ...
    def on_sub_action_started(self, ...): ...
    def on_sub_action_executed(self, ...): ...
    def on_step_done(self, ...): ...
    def on_run_done(self): ...
    def on_model_query(self, ...): ...
    def on_query_message_added(self, ...): ...
```

**After:** Segregated into focused interfaces (`hook_interfaces.py`):

1. **`ILifecycleHook`**
   - `on_init()`, `on_run_start()`, `on_run_done()`

2. **`IStepHook`**
   - `on_step_start()`, `on_step_done()`

3. **`IActionHook`**
   - `on_actions_generated()`, `on_sub_action_started()`, `on_sub_action_executed()`

4. **`IQueryHook`**
   - `on_model_query()`, `on_query_message_added()`

5. **`CompositeAgentHook`**
   - Provides default no-op implementations for backward compatibility
   - Clients only override methods they need

Similarly for environment hooks:

1. **`IEnvLifecycleHook`** - `on_init()`, `on_close()`
2. **`IEnvSetupHook`** - `on_copy_repo_started()`, `on_install_env_started()`
3. **`CompositeEnvHook`** - Composite with defaults

## 5. Dependency Inversion Principle (DIP)

**Before:** Direct dependencies on concrete implementations

**After:** Dependencies on abstractions (interfaces)

### Key Abstractions:

1. **History Management:** Depend on `IHistoryManager` instead of specific list implementation
2. **Command Parsing:** Depend on `ICommandParser` instead of regex implementation
3. **Model Interaction:** Depend on `IModelInteraction` instead of concrete handler
4. **Container Management:** Depend on `IContainerManager` instead of Docker specifics
5. **Communication:** Depend on `ICommunicationHandler` instead of bash specifics
6. **Environment Installation:** Depend on `IEnvironmentInstaller` instead of conda specifics

## Benefits

1. **Testability:** Each component can be tested in isolation with mock implementations
2. **Maintainability:** Single responsibility makes code easier to understand and modify
3. **Extensibility:** New features can be added through new implementations without changing existing code
4. **Flexibility:** Different implementations can be swapped based on needs (e.g., Docker vs Podman)
5. **Reusability:** Focused components can be reused in different contexts

## Usage Examples

### Using Command Parser
```python
from sweagent.agent.command_parser import RegexCommandParser

parser = RegexCommandParser()
parser.parse_command_patterns(config)
actions = parser.split_actions(action_string, agent_name)
```

### Using Container Manager
```python
from sweagent.environment.container_manager import DockerContainerManager

manager = DockerContainerManager(persistent=True)
container, pids = manager.create_container(image_name, container_name)
container_obj = manager.get_container_object(container_name)
```

### Using Prompt Strategies
```python
from sweagent.agent.strategies import PromptStrategyFactory

factory = PromptStrategyFactory(config)
strategy = factory.create_strategy(observation, last_role, is_demo, codegraph_context)
prompt = strategy.generate_prompt(context)
```

### Using Segregated Hooks
```python
from sweagent.agent.hook_interfaces import ILifecycleHook, IStepHook

class MyHook(ILifecycleHook):
    def on_init(self):
        print("Initialized")

    def on_run_start(self):
        print("Run started")

    def on_run_done(self):
        print("Run completed")
```

## Migration Path

The original classes (`Agent`, `DARSAgent`, `SWEEnv`) remain unchanged for backward compatibility. New code should use the refactored components. Future updates can gradually migrate to the new architecture.

## File Structure

```
sweagent/
├── agent/
│   ├── command_parser.py          # Command parsing (SRP)
│   ├── history_manager.py         # History management (SRP)
│   ├── model_interaction.py       # Model interaction (SRP)
│   ├── hook_interfaces.py         # Segregated hooks (ISP)
│   ├── strategies.py              # Strategy patterns (OCP)
│   ├── agents.py                  # Original Agent class
│   └── dars_agent.py             # Original DARSAgent class
├── environment/
│   ├── container_manager.py       # Container management (SRP, DIP)
│   ├── communication_handler.py   # Communication (SRP, DIP)
│   ├── environment_installer.py   # Environment setup (SRP, DIP)
│   └── swe_env.py                # Original SWEEnv class
└── SOLID_REFACTORING.md          # This document
```

## Future Enhancements

1. Create factory classes for easier component instantiation
2. Add dependency injection container
3. Implement additional strategies (e.g., different parsing strategies)
4. Add more specialized hooks for specific use cases
5. Create adapter patterns for legacy code migration
