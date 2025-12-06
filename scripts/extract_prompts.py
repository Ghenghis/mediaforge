"""
Extract Prompts from image_data.md
Parses the user's prompt data and creates structured JSON files for automation
"""
import json
import re
from pathlib import Path
from collections import defaultdict

DATA_FILE = Path(r"c:\Users\Admin\civitai\image_data.md")
OUTPUT_DIR = Path(r"c:\Users\Admin\civitai\data")

def parse_image_data():
    """Parse the image_data.md file and extract prompts"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by double newlines to separate entries
    entries = content.split('\n\n')
    
    prompts = []
    current_entry = {}
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines or not lines[0].strip():
            continue
            
        entry_data = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for negative prompt
            if line.startswith('Negative prompt:'):
                entry_data['negative'] = line.replace('Negative prompt:', '').strip()
            # Check for settings line (starts with Steps:)
            elif line.startswith('Steps:'):
                settings = parse_settings(line)
                entry_data['settings'] = settings
            # Otherwise it's a positive prompt
            elif 'negative' not in entry_data and 'Steps:' not in line:
                if 'positive' not in entry_data:
                    entry_data['positive'] = line
                else:
                    entry_data['positive'] += ' ' + line
        
        if entry_data.get('positive'):
            prompts.append(entry_data)
    
    return prompts

def parse_settings(settings_line):
    """Parse generation settings from a line"""
    settings = {}
    
    # Extract common settings
    patterns = {
        'steps': r'Steps:\s*(\d+)',
        'cfg': r'CFG scale:\s*([\d.]+)',
        'sampler': r'Sampler:\s*([^,]+)',
        'seed': r'Seed:\s*(\d+)',
        'size': r'Size:\s*(\d+x\d+)',
        'model': r'Model:\s*([^,]+)',
        'clip_skip': r'Clip skip:\s*(\d+)',
        'denoise': r'Denoising strength:\s*([\d.]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, settings_line)
        if match:
            settings[key] = match.group(1).strip()
    
    return settings

def categorize_prompts(prompts):
    """Categorize prompts by style"""
    categories = defaultdict(list)
    
    for idx, p in enumerate(prompts):
        positive = p.get('positive', '').lower()
        
        # Detect style category
        if 'tribal' in positive or 'face paint' in positive or 'war paint' in positive:
            categories['tribal'].append(p)
        elif 'anime' in positive or 'illustr' in positive or 'manga' in positive:
            categories['anime'].append(p)
        elif 'realistic' in positive or 'photo' in positive or 'dslr' in positive:
            categories['realistic'].append(p)
        elif 'fantasy' in positive or 'mystical' in positive or 'ethereal' in positive:
            categories['fantasy'].append(p)
        elif 'character' in positive or 'cosplay' in positive:
            categories['character'].append(p)
        else:
            categories['general'].append(p)
    
    return dict(categories)

def extract_common_elements(prompts):
    """Extract common positive and negative elements"""
    positive_terms = defaultdict(int)
    negative_terms = defaultdict(int)
    
    for p in prompts:
        # Count positive terms
        pos = p.get('positive', '')
        for term in pos.split(','):
            term = term.strip().lower()
            if term and len(term) > 3:
                positive_terms[term] += 1
        
        # Count negative terms
        neg = p.get('negative', '')
        for term in neg.split(','):
            term = term.strip().lower()
            if term and len(term) > 3:
                negative_terms[term] += 1
    
    # Get top terms
    top_positive = sorted(positive_terms.items(), key=lambda x: -x[1])[:50]
    top_negative = sorted(negative_terms.items(), key=lambda x: -x[1])[:50]
    
    return {
        'positive': [t[0] for t in top_positive],
        'negative': [t[0] for t in top_negative]
    }

def create_style_templates(categories):
    """Create style templates for each category"""
    templates = {}
    
    for cat, prompts in categories.items():
        if not prompts:
            continue
            
        # Get common elements from this category
        common = extract_common_elements(prompts)
        
        # Get representative prompts
        sample_prompts = prompts[:5]
        
        templates[cat] = {
            'common_positive': common['positive'][:20],
            'common_negative': common['negative'][:20],
            'sample_prompts': [p.get('positive', '')[:500] for p in sample_prompts],
            'count': len(prompts)
        }
    
    return templates

def main():
    print("="*60)
    print("  EXTRACTING USER PROMPTS FROM image_data.md")
    print("="*60)
    
    # Parse data
    print("\n📖 Parsing image_data.md...")
    prompts = parse_image_data()
    print(f"   Found {len(prompts)} prompt entries")
    
    # Categorize
    print("\n📁 Categorizing by style...")
    categories = categorize_prompts(prompts)
    for cat, items in categories.items():
        print(f"   {cat}: {len(items)} prompts")
    
    # Extract common elements
    print("\n🔍 Extracting common elements...")
    common = extract_common_elements(prompts)
    print(f"   Top positive terms: {len(common['positive'])}")
    print(f"   Top negative terms: {len(common['negative'])}")
    
    # Create templates
    print("\n📝 Creating style templates...")
    templates = create_style_templates(categories)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Save outputs
    print("\n💾 Saving to JSON files...")
    
    # All prompts
    with open(OUTPUT_DIR / 'user_prompts.json', 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)
    print(f"   ✓ user_prompts.json ({len(prompts)} entries)")
    
    # Categorized prompts
    with open(OUTPUT_DIR / 'categorized_prompts.json', 'w', encoding='utf-8') as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    print(f"   ✓ categorized_prompts.json")
    
    # Style templates
    with open(OUTPUT_DIR / 'style_templates.json', 'w', encoding='utf-8') as f:
        json.dump(templates, f, indent=2, ensure_ascii=False)
    print(f"   ✓ style_templates.json")
    
    # Common elements (for quick reference)
    with open(OUTPUT_DIR / 'common_elements.json', 'w', encoding='utf-8') as f:
        json.dump(common, f, indent=2, ensure_ascii=False)
    print(f"   ✓ common_elements.json")
    
    # Print summary
    print("\n" + "="*60)
    print("  EXTRACTION COMPLETE!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   Total prompts: {len(prompts)}")
    print(f"   Categories: {', '.join(categories.keys())}")
    print(f"   Output: {OUTPUT_DIR}")
    
    # Print some example prompts for each category
    print("\n📋 Sample prompts per category:")
    for cat, items in categories.items():
        if items:
            sample = items[0].get('positive', '')[:100]
            print(f"\n   [{cat.upper()}]")
            print(f"   {sample}...")

if __name__ == "__main__":
    main()
