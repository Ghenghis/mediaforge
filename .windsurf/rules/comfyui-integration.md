# ComfyUI Integration Rules
# Activation: Glob pattern *comfyui*, *workflow*

## Workflow Standards
- Validate JSON structure before submission
- Check node connections for completeness
- Verify model paths exist before execution
- Handle queue timeouts gracefully

## API Integration
- Use websocket for real-time progress updates
- Implement retry logic for failed generations
- Cache workflow templates
- Validate output paths before saving

## Image Processing
- Check VRAM availability before large generations
- Implement batch processing for multiple images
- Add metadata to generated images
- Use proper color space handling
