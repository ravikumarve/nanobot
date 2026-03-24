# Nanobot AI Agent Guidelines

## Development Commands

### Installation
```bash
pip install -e .[dev]
```

### Linting
```bash
# Run ruff linting
ruff check .

# Run ruff formatting
ruff format .

# Check with specific rules
ruff check --select E,F,I,N,W .
```

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=nanobot

# Run a single test file
pytest tests/test_message_tool.py

# Run a specific test function
pytest tests/test_message_tool.py::test_message_tool_send

# Run tests in verbose mode
pytest -v

# Run only failed tests from previous run
pytest --lf

# Run tests matching a keyword
pytest -k "memory"
```

### Building
```bash
# Build package
python -m build

# Install in development mode
pip install -e .
```

## Code Style Guidelines

### Python Version
- Target: Python 3.11+
- Use f-strings for string formatting (Python 3.6+)
- Use pathlib for file operations
- Use async/await for asynchronous operations

### Imports
1. Standard library imports first
2. Third-party imports second
3. Local application imports last
4. Each section separated by blank line
5. Within sections, sort alphabetically
6. Use absolute imports from project root

### Formatting
- Line length: 100 characters (configured in ruff)
- Indentation: 4 spaces
- No trailing whitespace
- Use blank lines to separate logical sections
- Maximum two blank lines between top-level definitions
- One blank line between method definitions in a class

### Types
- Use type hints for all function parameters and return values
- Use `Optional[T]` for values that can be None
- Use `List[T]`, `Dict[K, V]` for collections
- Use `Union` sparingly; prefer more specific types
- Use `Protocol` for structural typing when needed
- Use `TypedDict` for dictionary with specific keys
- Forward references with quotes for self-referencing types
- Use `Final` for constants that shouldn't be reassigned

### Naming Conventions
- Classes: PascalCase (e.g., `AgentLoop`, `MemoryManager`)
- Functions and variables: snake_case (e.g., `process_message`, `user_id`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_TOKENS`, `DEFAULT_TIMEOUT`)
- Private attributes/methods: single leading underscore (e.g., `_internal_state`)
- Special methods (dunder): as needed (e.g., `__init__`, `__str__`)
- Avoid single character names except for loop indices or trivial cases
- Descriptive names preferred over short ones
- Boolean variables: use `is_`, `has_`, `should_` prefixes (e.g., `is_valid`, `has_permission`)

### Error Handling
- Prefer specific exceptions over broad `Exception`
- Catch exceptions as close to the source as possible
- Use `try/except/else/finally` blocks appropriately
- Log exceptions with appropriate context before re-raising
- Define custom exception classes in `exceptions.py` modules
- Use `raise ... from ...` to preserve exception chains
- Validate inputs early and fail fast
- Use context managers (`with` statement) for resource management
- In async code, use `async with` for async context managers

### Documentation
- Use docstrings for all public modules, classes, and functions
- Follow Google or NumPy docstring style
- Include parameter types, return types, and exceptions in docstrings
- Use inline comments sparingly for complex logic
- Update docstrings when changing function signatures
- Use `# type: ignore` comments only when necessary and with explanation

### Async/Aware Code
- Use `async def` for coroutines
- Avoid blocking calls in async functions; use async alternatives
- Use `asyncio.gather()` for concurrent operations
- Handle cancellation properly with `try/except asyncio.CancelledError`
- Use `asyncio.shield()` when necessary to prevent cancellation
- Prefer `asyncio.create_task()` over `ensure_future()`
- Close async generators properly with `async for` and `aclose()`

### Testing Practices
- Write unit tests for all new functionality
- Use pytest fixtures for reusable test setup
- Mock external dependencies with `unittest.mock` or `pytest-mock`
- Test both success and failure cases
- Test edge cases and boundary conditions
- Keep tests independent and isolated
- Use descriptive test names that explain what is being tested
- Arrange, Act, Assert (AAA) pattern in tests
- Avoid testing private methods directly; test through public interface
- Use parametrized tests for multiple input scenarios
- For async tests, use `@pytest.mark.asyncio` or `pytest-asyncio` plugin

### Logging
- Use loguru logger (imported as `from loguru import logger`)
- Use appropriate log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General operational information
  - `WARNING`: Unexpected events that don't prevent operation
  - `ERROR`: Error events that prevent specific functionality
  - `CRITICAL`: Severe errors that prevent continued operation
- Include contextual information in log messages
- Avoid logging sensitive data (passwords, tokens, etc.)
- Use structured logging when beneficial
- Configure logging in application entry point

### Security
- Validate and sanitize all external inputs
- Use parameterized queries for database operations
- Handle secrets properly; never hardcode credentials
- Use environment variables or secure vaults for secrets
- Implement proper authentication and authorization
- Keep dependencies updated
- Follow principle of least privilege
- Use secure defaults for security-related configurations

## Agent-Specific Guidelines

### Tool Development
- All tools must inherit from `BaseTool` class
- Implement `_execute` method for tool logic
- Provide clear tool descriptions in docstrings
- Handle errors gracefully and return meaningful error messages
- Type all parameters and return values
- Use async/await for I/O operations
- Validate tool inputs before processing
- Register tools in the tool registry
- Follow existing patterns in `nanobot/agent/tools/`

### Memory Management
- Use appropriate memory types (short-term, long-term, episodic)
- Implement proper memory consolidation strategies
- Handle memory limits gracefully
- Ensure thread/process safety for concurrent access
- Serialize/deserialize memory objects properly
- Implement memory pruning policies

### Agent Loop
- Handle initialization and cleanup properly
- Manage agent state transitions
- Process incoming messages in order
- Handle tool execution and result processing
- Implement proper error recovery mechanisms
- Respect agent configuration and limits
- Maintain conversation context appropriately

### Channels
- Follow channel-specific protocols
- Handle connection lifecycle (connect, disconnect, reconnect)
- Normalize incoming/outgoing messages
- Handle rate limiting and backpressure
- Implement proper error handling for channel-specific issues
- Secure channel communications when required
- Follow existing patterns in `nanobot/channels/`

### Skills
- Keep skills focused and single-purpose
- Follow skill template structure
- Handle skill loading and unloading properly
- Isolate skill dependencies when possible
- Document skill requirements and capabilities
- Test skills in isolation and integration

### Configuration
- Use Pydantic models for configuration validation
- Provide sensible defaults
- Support environment variable overrides
- Validate configuration at startup
- Keep sensitive configuration out of version control
- Use configuration hierarchy (base, overrides, environment-specific)

## File Organization
- Keep modules focused and small (<500 lines preferred)
- Group related functionality in packages
- Use descriptive module and package names
- Avoid deep nesting (max 3-4 levels)
- Place interfaces/abstract base classes in appropriate locations
- Separate concerns: models, services, controllers, views
- Keep tests close to the code they test (same directory structure)
- Documentation in `docs/` directory
- Scripts in `scripts/` directory
- Configuration examples in `examples/` directory

## Continuous Integration
- Format code before committing (`ruff format .`)
- Lint code before committing (`ruff check .`)
- Run tests before committing (`pytest`)
- Keep builds green
- Update dependencies regularly
- Follow semantic versioning for releases

## Review Process
- Self-review code before requesting review
- Ensure all tests pass
- Verify linting passes
- Check that documentation is updated
- Confirm type hints are complete
- Ensure error handling is adequate
- Validate security considerations
- Check performance implications
- Verify backward compatibility

## Roadmap & Feature Planning

### Phase 1: Foundation (Stability & Performance) ✅ COMPLETED
- **Rate Limiting & Throttling** — Per-channel, per-user rate limits
- **Tool Result Caching** — TTL-based cache for expensive operations
- **Plugin Hot-Loading** — Dynamic skill loading without restart
- **Error Recovery** — Graceful degradation patterns

### Phase 2: Intelligence (Context & Memory)
- **Vector-based Memory** — Semantic search with embedding model
- **Multi-Agent Collaboration** — Inter-agent communication protocol
- **Undo/History Mechanism** — Action rollback with audit trail
- **Better Reasoning** — Multi-step planning and reflection

### Phase 3: Experience (Multi-Modal & UI)
- **Multi-modal Input** — Image, voice, video processing
- **Web Dashboard** — Real-time monitoring UI
- **Calendar Integration** — Google Calendar/Outlook sync
- **Email Templates** — Rich HTML responses

### Phase 4: Ecosystem (Community & Growth)
- **Plugin Marketplace** — Public skill repository
- **Self-Improvement** — Feedback learning
- **Analytics & Metrics** — Usage tracking
- **Internationalization** — Multi-language support

### Implementation Guidelines
1. Start with Phase 1 features for stability ✅ COMPLETED
2. Each feature needs tests and documentation ✅ COMPLETED
3. Follow existing architecture patterns ✅ COMPLETED
4. Maintain backward compatibility ✅ COMPLETED
5. Use feature flags for experimental features ✅ COMPLETED