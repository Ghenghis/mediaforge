"""
Quick status check and model cleanup for Ollama and LM Studio
"""

import requests
import json
import sys

def check_lmstudio():
    """Check LM Studio status"""
    try:
        r = requests.get('http://localhost:1234/v1/models', timeout=5)
        if r.status_code == 200:
            models = r.json().get('data', [])
            print(f"LM Studio: OK - {len(models)} models available")
            if models:
                print(f"  Current: {models[0]['id']}")
            return True
    except Exception as e:
        print(f"LM Studio: NOT RESPONDING - {e}")
    return False

def check_ollama():
    """Check Ollama status and loaded models"""
    try:
        r = requests.get('http://localhost:11434/api/ps', timeout=5)
        if r.status_code == 200:
            data = r.json()
            running = data.get('models', [])
            print(f"Ollama: OK - {len(running)} models loaded")
            for m in running:
                print(f"  Loaded: {m.get('name', 'unknown')}")
            return running
    except Exception as e:
        print(f"Ollama: NOT RESPONDING - {e}")
    return []

def unload_ollama_models():
    """Unload all Ollama models to free memory"""
    print("\nUnloading Ollama models...")
    try:
        r = requests.get('http://localhost:11434/api/ps', timeout=5)
        if r.status_code == 200:
            models = r.json().get('models', [])
            for m in models:
                name = m.get('name', '')
                if name:
                    requests.post(
                        'http://localhost:11434/api/generate',
                        json={'model': name, 'keep_alive': 0},
                        timeout=30
                    )
                    print(f"  Unloaded: {name}")
            print("All Ollama models unloaded!")
            return True
    except Exception as e:
        print(f"Error unloading: {e}")
    return False

def test_api():
    """Quick API response test"""
    print("\n=== API TEST ===")
    try:
        r = requests.post('http://localhost:1234/v1/chat/completions',
            json={
                'messages': [{'role': 'user', 'content': 'Say hello in 3 words'}],
                'max_tokens': 20,
                'temperature': 0
            }, timeout=30)
        if r.status_code == 200:
            resp = r.json()['choices'][0]['message']['content']
            print(f"API Test: SUCCESS")
            print(f"Response: {resp[:100]}")
            return True
        else:
            print(f"API Test: FAILED - Status {r.status_code}")
    except requests.exceptions.Timeout:
        print("API Test: TIMEOUT - Model may be loading or frozen")
    except Exception as e:
        print(f"API Test: ERROR - {e}")
    return False

def main():
    print("=" * 50)
    print("  SERVICE STATUS CHECK")
    print("=" * 50)
    
    lm_ok = check_lmstudio()
    ollama_models = check_ollama()
    
    # Unload Ollama if requested
    if '--unload' in sys.argv and ollama_models:
        unload_ollama_models()
    
    # Test API if requested
    if '--test' in sys.argv:
        test_api()
    
    print("\n" + "=" * 50)
    if lm_ok:
        print("  Status: READY")
    else:
        print("  Status: LM STUDIO NOT RESPONDING")
        print("  Please load a model in LM Studio")
    print("=" * 50)

if __name__ == "__main__":
    main()
