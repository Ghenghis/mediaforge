"""
Test script for model switching functionality
"""
import asyncio
import json
from lm_studio_mcp import CONFIG, get_active_mode, set_active_mode, save_config

async def test_model_switching():
    print("=" * 60)
    print("  MODEL SWITCHING TEST")
    print("=" * 60)
    
    # Test initial state
    print(f"\n1. Initial active mode: {get_active_mode()}")
    
    # Test switching to local
    print("\n2. Switching to local mode...")
    success = set_active_mode("local")
    print(f"   Switch successful: {success}")
    print(f"   New active mode: {get_active_mode()}")
    
    # Test switching to windsurf
    print("\n3. Switching to windsurf mode...")
    success = set_active_mode("windsurf")
    print(f"   Switch successful: {success}")
    print(f"   New active mode: {get_active_mode()}")
    
    # Test invalid mode
    print("\n4. Testing invalid mode...")
    success = set_active_mode("invalid")
    print(f"   Switch successful: {success}")
    print(f"   Active mode unchanged: {get_active_mode()}")
    
    # Show final config
    print("\n5. Final configuration:")
    print(json.dumps(CONFIG, indent=2))
    
    print("\n" + "=" * 60)
    print("  Model switching test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_model_switching())
