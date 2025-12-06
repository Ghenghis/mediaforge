# LM Studio MCP Server

Simple MCP server for connecting Windsurf to local LM Studio models for better content generation without content filters.

## Features

- **Direct Chat**: Chat with your local LM Studio model
- **Prompt Enhancement**: Enhance image generation prompts with content rating awareness
- **Content Validation**: Validate prompts for appropriate rating levels
- **Status Check**: Monitor LM Studio connection and loaded model
- **Retry Logic**: Automatic retry with exponential backoff on connection issues
- **Configurable**: Easy configuration via `config.json`

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start LM Studio:**
   - Download and install LM Studio from https://lmstudio.ai
   - Load your preferred uncensored model (e.g., Dolphin, Wizard-Vicuna)
   - Ensure the server is running (default: http://localhost:1234)

3. **Configure the server** (optional):
   Edit `config.json` to change settings:
   ```json
   {
     "lm_studio": {
       "base_url": "http://localhost:1234",
       "timeout": 60,
       "retry_attempts": 3,
       "retry_delay": 1
     }
   }
   ```

4. **Start the MCP server:**
   ```bash
   python lm_studio_mcp.py
   ```

## Windsurf Integration

1. Open Windsurf settings
2. Navigate to MCP Server configuration
3. Add new MCP server:
   - Name: `lm-studio-mcp`
   - Command: `python`
   - Args: `C:/Users/Admin/civitai/mcp_server/lm_studio_mcp.py`
   - Working Directory: `C:/Users/Admin/civitai/mcp_server`

4. Restart Windsurf to load the server

## Available Tools

### 1. lm_studio_chat
Chat directly with your local model.

**Parameters:**
- `prompt` (required): The prompt to send
- `temperature` (optional): 0.0-1.0, default 0.7
- `max_tokens` (optional): Default 2048
- `system_prompt` (optional): System prompt to guide the model

### 2. lm_studio_enhance_prompt
Enhance image generation prompts with quality tags and style improvements.

**Parameters:**
- `base_prompt` (required): Base image generation prompt
- `content_rating` (optional): PG, R, XXX, etc.
- `theme` (optional): western, tribal, fantasy, etc.
- `era` (optional): Historical era

### 3. lm_studio_validate_content
Validate if content is appropriate for a specific rating level.

**Parameters:**
- `prompt` (required): Prompt to validate
- `target_rating` (required): Target content rating

**Returns:**
- `VALID`: Appropriate for rating
- `INVALID: [reason]`: Not appropriate
- `GREY_AREA: [concern]`: Borderline

### 4. lm_studio_status
Check LM Studio connection and show loaded model.

**Returns:**
- Connection status
- Available models count
- Current model name
- Server readiness

## Usage Examples

### Basic Chat
```
Use lm_studio_chat with:
- prompt: "Write a western story about a sheriff"
- temperature: 0.8
```

### Enhance Image Prompt
```
Use lm_studio_enhance_prompt with:
- base_prompt: "portrait of a woman"
- content_rating: "PG"
- theme: "western"
- era: "1870s"
```

### Validate Content
```
Use lm_studio_validate_content with:
- prompt: "elegant woman in sheer evening gown"
- target_rating: "SOFT"
```

## Troubleshooting

### "No model loaded in LM Studio"
- Ensure LM Studio is running
- Load a model in LM Studio
- Check the model is fully loaded (green status)

### Connection Errors
- Verify LM Studio port (default 1234)
- Check if another application is using the port
- Update `base_url` in `config.json` if needed

### Windsurf Not Connecting
- Check the MCP server is running
- Verify the path in Windsurf settings
- Restart Windsurf after configuration

## Recommended Models

For best results with content generation:

1. **Dolphin Models** - Uncensored, instruction-following
2. **Wizard-Vicuna-Uncensored** - Creative writing focused
3. **MythosMax** - Good for detailed descriptions
4. **Stheno-Hermes** - Balanced for various tasks

## Content Ratings Support

The server supports all content rating levels:
- **Family Safe**: EL, L, PG, PG13, PG17
- **Mature**: SOFT, MED, R
- **Adult (21+)**: HARD, HC, X, XXX

Each rating has appropriate guardrails and validation rules.

## Advanced Configuration

### Multiple LM Studio Instances
Edit `config.json` to use different ports:
```json
{
  "lm_studio": {
    "base_url": "http://localhost:1235"
  }
}
```

### Custom Retry Settings
```json
{
  "lm_studio": {
    "retry_attempts": 5,
    "retry_delay": 2
  }
}
```

## Integration with Western Story Generator

This MCP server integrates perfectly with the Western Story Generator project:
- Enhance actor image prompts
- Validate content for appropriate ratings
- Generate story dialogues
- Create character descriptions

Use it alongside the Rating Studio Ultra and Story Generator API for a complete workflow.
