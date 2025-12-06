# Python API Development Rules
# Activation: Glob pattern *.py

## FastAPI Standards
- Use async/await for all endpoint handlers
- Implement proper request validation with Pydantic models
- Return consistent response structures
- Add OpenAPI documentation to all endpoints
- Use dependency injection for shared resources

## Port Management
- Document all API ports in a central config
- Use port ranges: 8195-8220 for this project
- Implement health check endpoints on all services
- Add graceful shutdown handlers

## Error Handling
- Return proper HTTP status codes
- Include error details in response body
- Log all errors with request context
- Implement circuit breakers for external services

## Database
- Use connection pooling
- Implement proper transaction handling
- Add retry logic for transient failures
- Close connections in finally blocks
