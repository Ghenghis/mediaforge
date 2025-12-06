# Automation Scripts Rules
# Activation: Glob pattern *.ps1, *.bat, *scheduler*, *pipeline*

## Script Standards
- NO interactive prompts - scripts must run unattended
- Use environment variables for configuration
- Implement proper logging with timestamps
- Add error handling with meaningful messages
- Support dry-run mode for testing

## Scheduling
- Use Windows Task Scheduler compatible formats
- Implement idempotent operations
- Add lock files to prevent concurrent runs
- Log start/end times and duration

## Pipeline Operations
- Validate inputs before processing
- Implement checkpoint/resume capability
- Clean up temporary files on completion
- Report status via API or file output
