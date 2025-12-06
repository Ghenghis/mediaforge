"""
LM Studio MCP Server
====================
Simple MCP server for connecting Windsurf to local LM Studio models
for better content generation without content filters.

Usage:
1. Start LM Studio with your preferred model
2. Run this MCP server
3. Configure Windsurf to connect to MCP server
"""

import asyncio
import json
import sys
import time
from typing import Any, Dict, List, Optional
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    ListResourcesRequest,
    ListResourcesResult,
    ListToolsRequest,
    ListToolsResult,
    Prompt,
    Resource,
    TextContent,
    Tool,
)

# Load configuration
def load_config():
    """Load configuration from config.json"""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        # Fallback to defaults
        return {
            "lm_studio": {
                "base_url": "http://localhost:1234",
                "timeout": 60,
                "retry_attempts": 3,
                "retry_delay": 1
            },
            "server": {
                "name": "lm-studio-mcp",
                "version": "1.0.0"
            },
            "model_selection": {
                "active_mode": "windsurf",
                "modes": {
                    "windsurf": {"name": "Windsurf Built-in", "enabled": True},
                    "local": {"name": "Local LM Studio", "enabled": True, "model_name": None}
                }
            }
        }

# Load model recommendations
def load_model_recommendations():
    """Load model recommendations database"""
    try:
        with open("model_recommendations.json", "r") as f:
            return json.load(f)
    except:
        return {"model_database": {}, "use_case_guides": {}, "age_group_guidance": {}}

CONFIG = load_config()
MODEL_RECOMMENDATIONS = load_model_recommendations()
LM_STUDIO_BASE_URL = CONFIG["lm_studio"]["base_url"]
MODEL_NAME = None  # Will auto-detect from LM Studio

# Initialize MCP server
server = Server("lm-studio-mcp")

class LMStudioClient:
    """Client for LM Studio API with retry logic"""
    
    def __init__(self, config: Dict = None):
        self.config = config or CONFIG["lm_studio"]
        self.base_url = self.config["base_url"]
        self.model_name = None
        self.timeout = self.config["timeout"]
        self.retry_attempts = self.config["retry_attempts"]
        self.retry_delay = self.config["retry_delay"]
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def _retry_request(self, func, *args, **kwargs):
        """Retry a request with exponential backoff"""
        last_error = None
        for attempt in range(self.retry_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"All {self.retry_attempts} attempts failed")
        raise last_error
    
    async def _fetch_models_data(self) -> Dict:
        """Shared method to fetch models data from LM Studio - reduces duplication"""
        async def _get():
            response = await self.client.get(f"{self.base_url}/v1/models")
            if response.status_code == 200:
                return response.json()
            raise Exception(f"HTTP {response.status_code}")
        
        return await self._retry_request(_get)
    
    async def get_models(self) -> List[str]:
        """Get available models from LM Studio"""
        try:
            data = await self._fetch_models_data()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    async def get_current_model(self) -> Optional[str]:
        """Get currently loaded model"""
        try:
            data = await self._fetch_models_data()
            models = data.get("data", [])
            return models[0]["id"] if models else None
        except Exception as e:
            print(f"Error getting current model: {e}")
            return None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Optional[str]:
        """Get chat completion from LM Studio"""
        async def _get():
            # Get current model if not set
            if not self.model_name:
                self.model_name = await self.get_current_model()
            
            if not self.model_name:
                return "Error: No model loaded in LM Studio"
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Add any additional parameters
            payload.update(kwargs)
            
            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"LM Studio returned {response.status_code}")
        
        try:
            return await self._retry_request(_get)
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global LM Studio client
lm_client = LMStudioClient()

# Model switching functions
def save_config():
    """Save current configuration to file"""
    try:
        with open("config.json", "w") as f:
            json.dump(CONFIG, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_active_mode():
    """Get currently active model mode"""
    return CONFIG.get("model_selection", {}).get("active_mode", "windsurf")

def set_active_mode(mode: str):
    """Set active model mode"""
    if mode in CONFIG["model_selection"]["modes"]:
        CONFIG["model_selection"]["active_mode"] = mode
        return save_config()
    return False

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available MCP tools"""
    return [
        Tool(
            name="switch_model",
            description="Switch between Windsurf built-in and local LM Studio models",
            inputSchema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "description": "Model mode to switch to",
                        "enum": ["windsurf", "local"]
                    }
                },
                "required": ["mode"]
            }
        ),
        Tool(
            name="get_model_status",
            description="Get current model selection and status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="recommend_model",
            description="Get model recommendations based on content rating and use case",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_rating": {
                        "type": "string",
                        "description": "Target content rating",
                        "enum": ["EL", "L", "PG", "PG13", "PG17", "SOFT", "MED", "R", "HARD", "HC", "X", "XXX"]
                    },
                    "use_case": {
                        "type": "string",
                        "description": "Intended use case",
                        "enum": ["story_generation", "character_dialogue", "image_prompts", "adult_content"]
                    },
                    "age_group": {
                        "type": "string",
                        "description": "Target age group",
                        "enum": ["child", "teen", "young_adult", "adult"]
                    }
                }
            }
        ),
        Tool(
            name="detect_content_rating",
            description="Automatically detect appropriate content rating from prompt",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to analyze"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="setup_wizard",
            description="Step-by-step guidance for setting up local models",
            inputSchema={
                "type": "object",
                "properties": {
                    "step": {
                        "type": "integer",
                        "description": "Wizard step (1-6, or 0 for all steps)",
                        "minimum": 0,
                        "maximum": 6,
                        "default": 0
                    }
                }
            }
        ),
        Tool(
            name="check_installed_models",
            description="Check which recommended models are installed in LM Studio",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="lm_studio_chat",
            description="Chat with local LM Studio model for content generation",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to send to the model"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Temperature (0.0-1.0, default 0.7)",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.7
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens to generate (default 2048)",
                        "default": 2048,
                        "minimum": 1,
                        "maximum": 8192
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Optional system prompt to guide the model"
                    }
                },
                "required": ["prompt"]
            }
        ),
        Tool(
            name="lm_studio_enhance_prompt",
            description="Enhance an image generation prompt with local model",
            inputSchema={
                "type": "object",
                "properties": {
                    "base_prompt": {
                        "type": "string",
                        "description": "The base image generation prompt"
                    },
                    "content_rating": {
                        "type": "string",
                        "description": "Content rating (PG, R, XXX, etc.)",
                        "enum": ["EL", "L", "PG", "PG13", "PG17", "SOFT", "MED", "R", "HARD", "HC", "X", "XXX"]
                    },
                    "theme": {
                        "type": "string",
                        "description": "Theme (western, tribal, fantasy, etc.)",
                        "enum": ["western", "tribal", "native_american", "fantasy", "medieval", "asian", "scifi", "modern"]
                    },
                    "era": {
                        "type": "string",
                        "description": "Historical era",
                        "enum": ["ancient_bc", "medieval", "renaissance", "baroque", "victorian", "early_modern", "modern", "contemporary"]
                    }
                },
                "required": ["base_prompt"]
            }
        ),
        Tool(
            name="lm_studio_validate_content",
            description="Validate content for appropriate rating level",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to validate"
                    },
                    "target_rating": {
                        "type": "string",
                        "description": "Target content rating",
                        "enum": ["EL", "L", "PG", "PG13", "PG17", "SOFT", "MED", "R", "HARD", "HC", "X", "XXX"]
                    }
                },
                "required": ["prompt", "target_rating"]
            }
        ),
        Tool(
            name="lm_studio_status",
            description="Check LM Studio connection and loaded model",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

# ============================================
# TOOL HANDLERS - Split for reduced complexity
# ============================================

async def _handle_switch_model(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle switch_model tool"""
    mode = arguments.get("mode", "")
    
    if mode not in ["windsurf", "local"]:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: Mode must be 'windsurf' or 'local'")]
        )
    
    success = set_active_mode(mode)
    
    if not success:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: Failed to switch model")]
        )
    
    mode_info = CONFIG["model_selection"]["modes"][mode]
    current_model = None
    
    if mode == "local":
        current_model = await lm_client.get_current_model()
        CONFIG["model_selection"]["modes"]["local"]["model_name"] = current_model
        save_config()
    
    status = f"""✅ Model switched to: {mode_info['name']}
📝 Description: {mode_info['description']}
🔄 Active mode: {mode}
{'🎯 Local model: ' + str(current_model) if mode == 'local' else ''}"""
    
    return CallToolResult(content=[TextContent(type="text", text=status)])


async def _handle_get_model_status(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle get_model_status tool"""
    active_mode = get_active_mode()
    modes = CONFIG["model_selection"]["modes"]
    active_info = modes[active_mode]
    
    local_status = ""
    if active_mode == "local":
        models = await lm_client.get_models()
        current_model = await lm_client.get_current_model()
        local_status = f"""
📦 Available Models: {len(models)}
🎯 Current Model: {current_model or 'None'}
🔗 LM Studio: {CONFIG['lm_studio']['base_url']}"""
    
    status = f"""Model Selection Status:
✅ Active Mode: {active_info['name']} ({active_mode})
📝 Description: {active_info['description']}

Available Modes:
• Windsurf Built-in - Default Windsurf model
• Local LM Studio - Uncensored local model{local_status}

Use 'switch_model' tool to change modes."""
    
    return CallToolResult(content=[TextContent(type="text", text=status)])


def _detect_content_category(content_rating: str) -> str:
    """Determine content category from rating"""
    if content_rating in ["EL", "L", "PG", "PG13", "PG17"]:
        return "family_safe"
    if content_rating in ["SOFT", "MED", "R"]:
        return "mature"
    return "adult"


async def _handle_recommend_model(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle recommend_model tool"""
    content_rating = arguments.get("content_rating", "")
    use_case = arguments.get("use_case", "")
    age_group = arguments.get("age_group", "")
    
    model_db = MODEL_RECOMMENDATIONS.get("model_database", {})
    use_case_guides = MODEL_RECOMMENDATIONS.get("use_case_guides", {})
    age_guidance = MODEL_RECOMMENDATIONS.get("age_group_guidance", {})
    
    category = _detect_content_category(content_rating)
    rating_models = model_db.get(category, {}).get(content_rating, {}).get("models", [])
    
    recommendations = []
    
    # Filter by use case if specified
    if use_case and use_case in use_case_guides:
        preferred_rating = use_case_guides[use_case]["model_preferences"].get(age_group or "adult", "")
        if preferred_rating:
            for model in rating_models:
                if preferred_rating in model["name"].lower():
                    recommendations.insert(0, model)
    
    recommendations.extend([m for m in rating_models if m not in recommendations])
    
    # Build response
    response = f"🎯 Model Recommendations for {content_rating}"
    if use_case:
        response += f" ({use_case})"
    if age_group:
        response += f" - Age: {age_group}"
    response += "\n\n"
    
    if recommendations:
        for i, model in enumerate(recommendations[:3], 1):
            response += f"""{i}. {model['name']} ({model['size']})
   📝 {model['description']}
   💾 RAM Required: {model['ram_required']}
   ✨ Strengths: {', '.join(model['strengths'])}
   🎭 Use Cases: {', '.join(model['use_cases'])}
   🔗 LM Studio ID: {model['lm_studio_id']}

"""
    else:
        response += "No specific models found for this combination.\nTry a different rating or use case.\n"
    
    if age_group and age_group in age_guidance:
        guide = age_guidance[age_group]
        response += f"""
👥 Age Group Guidance ({guide['age_range']}):
• Allowed Ratings: {', '.join(guide['allowed_ratings'])}
• Restrictions: {guide['content_restrictions']}
• Recommended: {', '.join(guide['recommended_models'])}
"""
    
    response += """
💡 Next Steps:
1. Download recommended model from HuggingFace
2. Load in LM Studio
3. Use 'switch_model' to activate local mode
4. Start generating content!"""
    
    return CallToolResult(content=[TextContent(type="text", text=response)])


def _detect_rating_from_prompt(prompt: str) -> str:
    """Detect content rating from prompt keywords"""
    prompt_lower = prompt.lower()
    
    adult_keywords = ["nude", "naked", "explicit", "sexual", "intimate", "erotic", "xxx", "hardcore"]
    mature_keywords = ["sheer", "transparent", "lingerie", "sensual", "suggestive", "revealing", "sexy"]
    teen_keywords = ["dating", "romance", "kiss", "relationship", "crush", "teenager"]
    
    if any(word in prompt_lower for word in adult_keywords):
        if any(word in prompt_lower for word in ["hardcore", "xxx", "extreme"]):
            return "XXX"
        if any(word in prompt_lower for word in ["hard", "explicit", "graphic"]):
            return "HC"
        return "R"
    
    if any(word in prompt_lower for word in mature_keywords):
        if any(word in prompt_lower for word in ["sheer", "transparent"]):
            return "SOFT"
        return "MED"
    
    if any(word in prompt_lower for word in teen_keywords):
        return "PG13"
    
    return "PG"


async def _handle_detect_content_rating(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle detect_content_rating tool"""
    prompt = arguments.get("prompt", "")
    detected_rating = _detect_rating_from_prompt(prompt)
    
    response = f"""🔍 Content Rating Detection
📝 Analyzed Prompt: "{prompt[:100]}{'...' if len(prompt) > 100 else ''}"

🎯 Detected Rating: {detected_rating}

📊 Confidence: High (based on keyword analysis)

💡 Recommendation:
Use 'recommend_model' with content_rating="{detected_rating}" to get the best model for this content.

⚠️ Note: This is automated detection. You can override by specifying a different rating."""
    
    return CallToolResult(content=[TextContent(type="text", text=response)])


async def _handle_setup_wizard(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle setup_wizard tool"""
    step = arguments.get("step", 0)
    wizard = MODEL_RECOMMENDATIONS.get("setup_wizard", {})
    
    if step == 0:
        response = "🧙‍♂️ Local Model Setup Wizard\n\n"
        for i in range(1, 7):
            step_info = wizard.get(f"step_{i}", {})
            response += f"Step {i}: {step_info.get('title', '')}\n"
            response += f"  {step_info.get('description', '')}\n\n"
        response += "💡 Use 'setup_wizard' with step=1 to begin, or specify any step (1-6)"
    else:
        step_info = wizard.get(f"step_{step}", {})
        if not step_info:
            response = "❌ Invalid step. Use step 1-6 or 0 for all steps."
        else:
            response = f"""🧙‍♂️ Setup Wizard - Step {step}
📋 {step_info.get('title', '')}
📝 {step_info.get('description', '')}

🎯 Action: {step_info.get('action', '')}

💡 Next: Use step {step + 1} to continue (or 0 to see all steps)"""
    
    return CallToolResult(content=[TextContent(type="text", text=response)])


async def _handle_check_installed_models(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle check_installed_models tool"""
    installed_models = await lm_client.get_models()
    model_db = MODEL_RECOMMENDATIONS.get("model_database", {})
    
    all_recommended = []
    for category in model_db.values():
        for rating_data in category.values():
            all_recommended.extend(rating_data.get("models", []))
    
    installed_recs = []
    missing_recs = []
    
    for model in all_recommended:
        lm_studio_id = model.get("lm_studio_id", "")
        if any(lm_studio_id in installed for installed in installed_models):
            installed_recs.append(model)
        else:
            missing_recs.append(model)
    
    response = f"""📦 Model Installation Check
✅ Total models in LM Studio: {len(installed_models)}
🎯 Recommended models installed: {len(installed_recs)}
⬜ Missing recommended models: {len(missing_recs)}

✅ INSTALLED RECOMMENDED MODELS:
"""
    for model in installed_recs[:5]:
        response += f"• {model['name']} ({model['size']}) - {model['description']}\n"
    
    if len(installed_recs) > 5:
        response += f"... and {len(installed_recs) - 5} more\n"
    
    response += "\n⬜ MISSING RECOMMENDED MODELS:\n"
    for model in missing_recs[:5]:
        response += f"• {model['name']} - Download: {model['download_url']}\n"
    
    if len(missing_recs) > 5:
        response += f"... and {len(missing_recs) - 5} more\n"
    
    response += f"""
💡 Quick Setup:
1. Download missing models from the URLs above
2. Load them in LM Studio
3. Use 'switch_model' mode="local" to activate

🔗 All models available at: https://lmstudio.ai"""
    
    return CallToolResult(content=[TextContent(type="text", text=response)])


async def _handle_lm_studio_chat(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle lm_studio_chat tool"""
    prompt = arguments.get("prompt", "")
    temperature = arguments.get("temperature", 0.7)
    max_tokens = arguments.get("max_tokens", 2048)
    system_prompt = arguments.get("system_prompt", "")
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = await lm_client.chat_completion(
        messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    
    return CallToolResult(content=[TextContent(type="text", text=response or "No response")])


async def _handle_lm_studio_enhance_prompt(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle lm_studio_enhance_prompt tool"""
    base_prompt = arguments.get("base_prompt", "")
    content_rating = arguments.get("content_rating", "PG")
    theme = arguments.get("theme", "general")
    era = arguments.get("era", "contemporary")
    
    system_prompt = f"""You are an expert prompt engineer for AI image generation. 
Enhance the given prompt while respecting the content rating and theme guidelines.

Content Rating: {content_rating}
Theme: {theme}
Era: {era}

Guidelines:
- Add quality tags (masterpiece, 8k, detailed)
- Enhance character descriptions
- Add appropriate lighting and atmosphere
- Respect content rating restrictions
- Keep the core intent of the original prompt
- Return only the enhanced prompt, no explanations"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Enhance this prompt: {base_prompt}"}
    ]
    
    response = await lm_client.chat_completion(messages=messages, temperature=0.3, max_tokens=500)
    return CallToolResult(content=[TextContent(type="text", text=response or base_prompt)])


async def _handle_lm_studio_validate_content(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle lm_studio_validate_content tool"""
    prompt = arguments.get("prompt", "")
    target_rating = arguments.get("target_rating", "PG")
    
    system_prompt = f"""You are a content validator for AI image generation.
Check if the following prompt is appropriate for the {target_rating} rating level.

Rating Guidelines:
- EL/L: Fully modest, all ages
- PG: Family appropriate, modest attire
- PG13/PG17: Teen appropriate, light revealing
- SOFT: Sheer fabrics, tasteful, not nude
- MED/R: Adult content, artistic
- HARD/HC/X/XXX: Unrestricted adult

Respond with:
VALID: if appropriate for rating
INVALID: [reason]: if not appropriate
GREY_AREA: [concern]: if borderline

Prompt to validate:"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    response = await lm_client.chat_completion(messages=messages, temperature=0.1, max_tokens=100)
    return CallToolResult(content=[TextContent(type="text", text=response or "Unable to validate")])


async def _handle_lm_studio_status(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle lm_studio_status tool"""
    models = await lm_client.get_models()
    current_model = await lm_client.get_current_model()
    
    status = f"""LM Studio MCP Server Status:
✅ Connected: {LM_STUDIO_BASE_URL}
📦 Available Models: {len(models)}
🎯 Current Model: {current_model or 'None'}
📋 Models: {', '.join(models[:5])}{'...' if len(models) > 5 else ''}

Server is ready for Windsurf integration!"""
    
    return CallToolResult(content=[TextContent(type="text", text=status)])


# Tool handler registry - maps tool names to handlers
TOOL_HANDLERS = {
    "switch_model": _handle_switch_model,
    "get_model_status": _handle_get_model_status,
    "recommend_model": _handle_recommend_model,
    "detect_content_rating": _handle_detect_content_rating,
    "setup_wizard": _handle_setup_wizard,
    "check_installed_models": _handle_check_installed_models,
    "lm_studio_chat": _handle_lm_studio_chat,
    "lm_studio_enhance_prompt": _handle_lm_studio_enhance_prompt,
    "lm_studio_validate_content": _handle_lm_studio_validate_content,
    "lm_studio_status": _handle_lm_studio_status,
}


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls - dispatches to specific handlers"""
    handler = TOOL_HANDLERS.get(name)
    
    if handler:
        return await handler(arguments)
    
    return CallToolResult(
        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
    )


@server.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List available prompts"""
    return [
        Prompt(
            name="content_generator",
            description="Generate content with local model",
            arguments=[
                {
                    "name": "topic",
                    "description": "Topic to generate content about",
                    "required": True
                },
                {
                    "name": "style",
                    "description": "Writing style",
                    "required": False
                }
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
    """Get a specific prompt"""
    if name == "content_generator":
        topic = arguments.get("topic", "")
        style = arguments.get("style", "neutral")
        
        prompt_message = f"""Generate content about {topic} in a {style} style.
Be creative and detailed."""
        
        return GetPromptResult(
            description=f"Content generation for {topic}",
            messages=[
                {"role": "user", "content": prompt_message}
            ]
        )
    
    return GetPromptResult(
        description="Unknown prompt",
        messages=[]
    )

async def main():
    """Main server function"""
    print("=" * 60)
    print("  LM STUDIO MCP SERVER")
    print("=" * 60)
    print(f"🔗 Connecting to: {LM_STUDIO_BASE_URL}")
    
    # Test connection to LM Studio
    models = await lm_client.get_models()
    if not models:
        print("⚠️  Warning: Could not connect to LM Studio")
        print("   Make sure LM Studio is running with a model loaded")
    else:
        current_model = await lm_client.get_current_model()
        print(f"✅ Connected! Model: {current_model}")
        print(f"📦 Available models: {len(models)}")
    
    print("\n🚀 Starting MCP server...")
    print("   Configure Windsurf to connect to this server")
    print("=" * 60)
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )
    
    # Cleanup
    await lm_client.close()

if __name__ == "__main__":
    asyncio.run(main())
