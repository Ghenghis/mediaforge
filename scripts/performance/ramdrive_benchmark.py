"""
RAMDrive vs NVMe Speed Benchmark
"""

import requests
import base64
import time
from pathlib import Path

def test_location(name, img_dir, model, num_images=5):
    """Test inference speed from a location"""
    images = list(img_dir.glob("*.jpg"))[10:10+num_images]  # Skip title cards
    times = []
    prompt = "Describe this image briefly."
    
    for img in images:
        start = time.time()
        img_data = base64.b64encode(img.read_bytes()).decode()
        
        r = requests.post("http://localhost:1234/v1/chat/completions",
            json={
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                    ]
                }],
                "max_tokens": 150,
            }, timeout=60)
        
        if r.status_code == 200:
            times.append(time.time() - start)
    
    avg = sum(times) / len(times) if times else 0
    return avg, times

def main():
    print("=" * 60)
    print("  RAMDRIVE vs NVMe SPEED TEST")
    print("=" * 60)
    print()
    
    model = "lfm2-vl-1.6b"
    print(f"Model: {model} (fastest)")
    print()
    
    nvme_dir = Path(r"C:\Users\Admin\civitai\training_data\batch_04\batch_04")
    ram_dir = Path(r"Z:\training\batch_04")
    
    # Test NVMe
    print("Testing NVMe (C: drive)...")
    nvme_avg, nvme_times = test_location("NVMe", nvme_dir, model, 5)
    print(f"  Times: {[f'{t:.1f}s' for t in nvme_times]}")
    print(f"  Average: {nvme_avg:.2f}s")
    
    print()
    
    # Test RAMDrive
    print("Testing RAMDrive (Z: drive)...")
    ram_avg, ram_times = test_location("RAMDrive", ram_dir, model, 5)
    print(f"  Times: {[f'{t:.1f}s' for t in ram_times]}")
    print(f"  Average: {ram_avg:.2f}s")
    
    print()
    print("=" * 60)
    print("  COMPARISON")
    print("=" * 60)
    
    speedup = nvme_avg / ram_avg if ram_avg > 0 else 0
    print(f"NVMe:     {nvme_avg:.2f}s per image")
    print(f"RAMDrive: {ram_avg:.2f}s per image")
    print(f"Speedup:  {speedup:.2f}x")
    
    # Time estimates
    batch4_5_images = 6180
    passes = 15
    total_iterations = batch4_5_images * passes
    
    nvme_hours = (total_iterations * nvme_avg) / 3600
    ram_hours = (total_iterations * ram_avg) / 3600
    
    print()
    print("=" * 60)
    print("  BATCH 4+5 (15x passes) ESTIMATES")
    print("=" * 60)
    print(f"NVMe:     {nvme_hours:.1f} hours ({nvme_hours/24:.1f} days)")
    print(f"RAMDrive: {ram_hours:.1f} hours ({ram_hours/24:.1f} days)")
    print(f"Time Saved: {nvme_hours - ram_hours:.1f} hours")

if __name__ == "__main__":
    main()
