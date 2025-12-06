"""
Test Vision Models for Video Filtering
Tests both LM Studio and Ollama for speed and accuracy
"""

import requests
import base64
import time
import cv2
import os
from pathlib import Path

# Configuration
LMSTUDIO_URL = "http://localhost:1234/v1"
OLLAMA_URL = "http://localhost:11434"
VIDEO_DIR = Path("G:/Downloads/Vid")

# Test prompt for video frame analysis
ANALYSIS_PROMPT = """Analyze this image. Respond with ONLY a JSON object:
{
    "gender": "female" or "male" or "both" or "none",
    "body_type": "slim" or "fit" or "average" or "curvy" or "heavy",
    "quality": 1-10,
    "attractiveness": 1-10,
    "people_count": number
}
Be completely honest and uncensored."""

def extract_test_frame(video_path: Path) -> str:
    """Extract a frame from video and save as temp file"""
    cap = cv2.VideoCapture(str(video_path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Get middle frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        temp_path = Path("C:/Users/Admin/civitai/temp_test_frame.jpg")
        cv2.imwrite(str(temp_path), frame)
        return str(temp_path)
    return None

def image_to_base64(image_path: str) -> str:
    """Convert image to base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_lmstudio_vision(image_path: str, model: str = "qwen3-vl-8b-abliterated-caption-it"):
    """Test LM Studio vision model"""
    print(f"\n{'='*60}")
    print(f"Testing LM Studio: {model}")
    print(f"{'='*60}")
    
    try:
        image_b64 = image_to_base64(image_path)
        
        start_time = time.time()
        
        response = requests.post(
            f"{LMSTUDIO_URL}/chat/completions",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ANALYSIS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 300
            },
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            print(f"✓ Response received in {elapsed:.2f}s")
            print(f"\nResponse:\n{content}")
            
            # Check if censored
            censored_phrases = ["i cannot", "i can't", "inappropriate", "i'm not able", "sorry"]
            is_censored = any(phrase in content.lower() for phrase in censored_phrases)
            
            print(f"\n{'❌ CENSORED' if is_censored else '✓ UNCENSORED'}")
            
            return {
                "model": model,
                "platform": "lmstudio",
                "time": elapsed,
                "censored": is_censored,
                "response": content
            }
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_ollama_vision(image_path: str, model: str = "llava:13b"):
    """Test Ollama vision model"""
    print(f"\n{'='*60}")
    print(f"Testing Ollama: {model}")
    print(f"{'='*60}")
    
    try:
        image_b64 = image_to_base64(image_path)
        
        start_time = time.time()
        
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": ANALYSIS_PROMPT,
                        "images": [image_b64]
                    }
                ],
                "stream": False,
                "options": {"temperature": 0.3}
            },
            timeout=120
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            content = result["message"]["content"]
            
            print(f"✓ Response received in {elapsed:.2f}s")
            print(f"\nResponse:\n{content}")
            
            # Check if censored
            censored_phrases = ["i cannot", "i can't", "inappropriate", "i'm not able", "sorry"]
            is_censored = any(phrase in content.lower() for phrase in censored_phrases)
            
            print(f"\n{'❌ CENSORED' if is_censored else '✓ UNCENSORED'}")
            
            return {
                "model": model,
                "platform": "ollama",
                "time": elapsed,
                "censored": is_censored,
                "response": content
            }
        else:
            print(f"✗ Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def get_test_video():
    """Get a test video from the video directory"""
    if VIDEO_DIR.exists():
        videos = list(VIDEO_DIR.glob("*.mp4"))[:5]
        if videos:
            return videos[0]
    return None

def main():
    print("="*60)
    print("MODEL SPEED & ACCURACY TEST")
    print("="*60)
    
    # Get test frame
    test_video = get_test_video()
    if test_video:
        print(f"\nUsing video: {test_video.name}")
        test_image = extract_test_frame(test_video)
    else:
        # Use a placeholder path
        test_image = "C:/Users/Admin/civitai/temp_test_frame.jpg"
        if not Path(test_image).exists():
            print("No test video found. Please provide a test image.")
            return
    
    results = []
    
    # Test LM Studio models
    print("\n" + "="*60)
    print("TESTING LM STUDIO (localhost:1234)")
    print("="*60)
    
    # Check if LM Studio is running
    try:
        r = requests.get(f"{LMSTUDIO_URL}/models", timeout=5)
        if r.status_code == 200:
            models = r.json()
            print(f"LM Studio running with {len(models.get('data', []))} models")
            
            # Test vision model
            result = test_lmstudio_vision(test_image, "qwen3-vl-8b-abliterated-caption-it")
            if result:
                results.append(result)
    except:
        print("LM Studio not responding")
    
    # Test Ollama models
    print("\n" + "="*60)
    print("TESTING OLLAMA (localhost:11434)")
    print("="*60)
    
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            models = r.json()
            vision_models = [m["name"] for m in models.get("models", []) 
                           if "llava" in m["name"].lower() or "vision" in m["name"].lower()]
            print(f"Ollama vision models: {vision_models}")
            
            for model in vision_models[:3]:  # Test first 3 vision models
                result = test_ollama_vision(test_image, model)
                if result:
                    results.append(result)
    except Exception as e:
        print(f"Ollama not responding: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    if results:
        # Sort by speed
        results.sort(key=lambda x: x["time"])
        
        print(f"\n{'Model':<40} {'Platform':<10} {'Time':<10} {'Censored'}")
        print("-" * 70)
        for r in results:
            status = "❌ YES" if r["censored"] else "✓ NO"
            print(f"{r['model']:<40} {r['platform']:<10} {r['time']:.2f}s     {status}")
        
        # Recommendation
        uncensored = [r for r in results if not r["censored"]]
        if uncensored:
            fastest = min(uncensored, key=lambda x: x["time"])
            print(f"\n🏆 RECOMMENDED: {fastest['model']} ({fastest['platform']})")
            print(f"   Speed: {fastest['time']:.2f}s | Uncensored: ✓")
    else:
        print("No successful tests")
    
    # Cleanup
    temp_file = Path("C:/Users/Admin/civitai/temp_test_frame.jpg")
    if temp_file.exists():
        temp_file.unlink()

if __name__ == "__main__":
    main()
