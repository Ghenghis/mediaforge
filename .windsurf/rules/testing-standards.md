# Testing Standards
# Activation: Glob pattern *test*, *spec*

## Test Structure
- Use descriptive test names explaining what is tested
- Follow Arrange-Act-Assert pattern
- One assertion per test when possible
- Group related tests in classes/suites

## Mocking
- Mock external dependencies
- Use fixtures for common test data
- Implement factory functions for test objects
- Clean up mocks after tests

## Coverage
- Aim for 80%+ code coverage
- Focus on critical paths first
- Test edge cases and error conditions
- Include integration tests for APIs
