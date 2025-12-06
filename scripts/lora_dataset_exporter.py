"""
LoRA Training Dataset Exporter
Creates Kohya-compatible datasets from learned preferences
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
import sqlite3

DB_PATH = Path(r"c:\Users\Admin\civitai\data\preferences.db")
OUTPUT_DIR = Path(r"G:\Github\ComfyUI\output")
DATASET_EXPORT_DIR = Path(r"c:\Users\Admin\civitai\data\lora_training")

class LoRADatasetExporter:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH))
        DATASET_EXPORT_DIR.mkdir(exist_ok=True)
        
    def export_kohya_dataset(self, dataset_name: str = None, min_rating: int = 4) -> dict:
        """Export dataset in Kohya format for LoRA training"""
        
        if not dataset_name:
            dataset_name = f"lora_dataset_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
        dataset_dir = DATASET_EXPORT_DIR / dataset_name
        images_dir = dataset_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        cursor = self.conn.cursor()
        
        # Get highly rated images
        cursor.execute('''
            SELECT filename, prompt, tags, rating 
            FROM images 
            WHERE rating >= ?
            ORDER BY rating DESC
        ''', (min_rating,))
        
        images = cursor.fetchall()
        exported = 0
        
        for filename, prompt, tags, rating in images:
            # Find the actual image file
            src_path = OUTPUT_DIR / filename
            
            # Try to find with pattern matching
            if not src_path.exists():
                matches = list(OUTPUT_DIR.glob(f"*{filename.split('_')[0]}*.png"))
                if matches:
                    src_path = matches[0]
                    
            if src_path.exists():
                # Copy image
                dst_path = images_dir / f"{exported+1:04d}.png"
                shutil.copy(src_path, dst_path)
                
                # Create caption file
                caption_path = images_dir / f"{exported+1:04d}.txt"
                
                # Build caption from tags
                tag_list = json.loads(tags) if tags else []
                caption = ", ".join(tag_list[:30])  # Limit tags
                
                with open(caption_path, 'w', encoding='utf-8') as f:
                    f.write(caption)
                    
                exported += 1
                
        # Create config file
        config = {
            "dataset_name": dataset_name,
            "created_at": datetime.now().isoformat(),
            "total_images": exported,
            "min_rating": min_rating,
            "format": "kohya",
            "structure": {
                "images_dir": str(images_dir),
                "caption_extension": ".txt"
            }
        }
        
        with open(dataset_dir / "config.json", 'w') as f:
            json.dump(config, f, indent=2)
            
        # Create Kohya dataset config
        kohya_config = {
            "general": {
                "shuffle_caption": True,
                "caption_extension": ".txt",
                "keep_tokens": 1
            },
            "datasets": [{
                "resolution": [512, 768],
                "batch_size": 1,
                "keep_tokens": 1,
                "subsets": [{
                    "image_dir": str(images_dir),
                    "num_repeats": 10,
                    "caption_extension": ".txt"
                }]
            }]
        }
        
        with open(dataset_dir / "dataset_config.toml", 'w') as f:
            f.write(f"[general]\n")
            f.write(f"shuffle_caption = true\n")
            f.write(f"caption_extension = '.txt'\n")
            f.write(f"keep_tokens = 1\n\n")
            f.write(f"[[datasets]]\n")
            f.write(f"resolution = [512, 768]\n")
            f.write(f"batch_size = 1\n\n")
            f.write(f"[[datasets.subsets]]\n")
            f.write(f"image_dir = '{images_dir}'\n")
            f.write(f"num_repeats = 10\n")
            
        return {
            "status": "success",
            "dataset_name": dataset_name,
            "path": str(dataset_dir),
            "images_exported": exported,
            "config_files": ["config.json", "dataset_config.toml"]
        }
        
    def export_preference_weights(self) -> dict:
        """Export learned tag weights for training guidance"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT tag, category, weight, likes, dislikes FROM tag_weights ORDER BY weight DESC')
        weights = cursor.fetchall()
        
        export = {
            "exported_at": datetime.now().isoformat(),
            "positive_tags": [],
            "negative_tags": [],
            "neutral_tags": []
        }
        
        for tag, category, weight, likes, dislikes in weights:
            entry = {"tag": tag, "category": category, "weight": weight, "likes": likes, "dislikes": dislikes}
            if weight > 0.6:
                export["positive_tags"].append(entry)
            elif weight < 0.4:
                export["negative_tags"].append(entry)
            else:
                export["neutral_tags"].append(entry)
                
        export_path = DATASET_EXPORT_DIR / "preference_weights.json"
        with open(export_path, 'w') as f:
            json.dump(export, f, indent=2)
            
        return {
            "status": "success",
            "path": str(export_path),
            "positive": len(export["positive_tags"]),
            "negative": len(export["negative_tags"]),
            "neutral": len(export["neutral_tags"])
        }
        
    def close(self):
        self.conn.close()


if __name__ == "__main__":
    print("="*60)
    print("  LORA DATASET EXPORTER")
    print("="*60)
    
    exporter = LoRADatasetExporter()
    
    # Export preference weights
    print("\n📊 Exporting preference weights...")
    result = exporter.export_preference_weights()
    print(f"   Path: {result['path']}")
    print(f"   Positive tags: {result['positive']}")
    print(f"   Negative tags: {result['negative']}")
    
    # Export Kohya dataset
    print("\n📁 Exporting Kohya dataset...")
    result = exporter.export_kohya_dataset(min_rating=4)
    print(f"   Path: {result['path']}")
    print(f"   Images: {result['images_exported']}")
    
    exporter.close()
    print("\n✅ Export complete!")
