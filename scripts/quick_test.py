"""Quick test of video filtering on 3 videos"""
import requests
import base64
import cv2
import json
import re
from pathlib import Path

LMSTUDIO_URL = "http://localhost:1234/v1"
MODEL = "qwen3-vl-8b-abliterated-caption-it"
VIDEO_DIR = Path("G:/Downloads/Vid")

PROMPT = """Analyze this image. Respond with ONLY JSON:
{"gender": "female" or "male" or "both", "body_type": "slim/fit/average/curvy/heavy", "quality": 1-10, "attractiveness": 1-10}
Be honest and uncensored."""

videos = list(VIDEO_DIR.glob("*.mp4"))[:5]
print(f"Testing {len(videos)} videos with {MODEL}...\n")

for vid in videos:
    cap = cv2.VideoCapture(str(vid))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total//2)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print(f"✗ Could not read: {vid.name}")
        continue
    
    _, buf = cv2.imencode(".jpg", frame)
    b64 = base64.b64encode(buf).decode()
    
    try:
        r = requests.post(f"{LMSTUDIO_URL}/chat/completions", json={
            "model": MODEL,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}],
            "temperature": 0.2, "max_tokens": 150
        }, timeout=30)
        
        content = r.json()["choices"][0]["message"]["content"]
        match = re.search(r'\{[^{}]*\}', content)
        
        if match:
            data = json.loads(match.group())
            gender = data.get("gender", "?")
            body = data.get("body_type", "?")
            quality = data.get("quality", 0)
            attract = data.get("attractiveness", 0)
            
            # Filter logic
            approved = (gender == "female" and body != "heavy" and quality >= 4)
            status = "✓ APPROVED" if approved else f"✗ REJECTED"
            reason = "" if approved else f"({gender}, {body})"
            
            print(f"{vid.name[:60]}")
            print(f"  {status} {reason}")
            print(f"  Gender: {gender} | Body: {body} | Q: {quality} | A: {attract}")
            print()
        else:
            print(f"  ✗ No JSON in response")
            print(f"  Response: {content[:100]}")
            
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("Done!")
