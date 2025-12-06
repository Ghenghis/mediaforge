"""
AI Training Dashboard - Full Screen Real-Time Stats
====================================================
Efficient layout using all available space
"""

import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from datetime import datetime

STATS_FILE = Path(r"C:\Users\Admin\civitai\logs\realtime_stats.json")
REFRESH_MS = 500  # Faster refresh

class TrainingDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Training Dashboard")
        self.root.geometry("1400x800")
        self.root.configure(bg='#0d1117')
        self.root.resizable(False, False)  # Fixed size - no bouncing!
        
        self.stats = {}
        self.labels = {}
        self.gauges = {}
        self.all_tags = {}  # Tag database: {tag: count}
        self.tag_file = Path(r"C:\Users\Admin\civitai\logs\tag_database.json")
        self.load_tags()
        
        self.create_ui()
        self.update_stats()
    
    def load_tags(self):
        """Load tag database"""
        try:
            if self.tag_file.exists():
                with open(self.tag_file, 'r') as f:
                    self.all_tags = json.load(f)
        except:
            self.all_tags = {}
    
    def save_tags(self):
        """Save tag database"""
        try:
            with open(self.tag_file, 'w') as f:
                json.dump(self.all_tags, f, indent=2)
        except:
            pass
    
    def create_ui(self):
        """Create fixed-size dashboard with 4 columns"""
        
        # Header bar - FIXED HEIGHT
        header = tk.Frame(self.root, bg='#161b22', height=35, width=1400)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🧠 AI TRAINING MONITOR", 
                font=('Consolas', 12, 'bold'), fg='#58a6ff', bg='#161b22').pack(side='left', padx=10, pady=5)
        
        self.status_label = tk.Label(header, text="● RUNNING", 
                                     font=('Consolas', 10, 'bold'), fg='#3fb950', bg='#161b22')
        self.status_label.pack(side='left', padx=20)
        
        self.tag_count_label = tk.Label(header, text="TAGS: 0", 
                                        font=('Consolas', 10), fg='#a371f7', bg='#161b22')
        self.tag_count_label.pack(side='left', padx=20)
        
        self.clock_label = tk.Label(header, text="", font=('Consolas', 10), fg='#8b949e', bg='#161b22')
        self.clock_label.pack(side='right', padx=10)
        
        # Main container - FIXED SIZE with 4 columns
        main = tk.Frame(self.root, bg='#0d1117', width=1400, height=680)
        main.pack(fill='both', expand=False, padx=5, pady=5)
        main.pack_propagate(False)
        
        # COL 1: Session/Progress (width=280)
        col1 = tk.Frame(main, bg='#0d1117', width=280, height=680)
        col1.pack(side='left', fill='y', padx=2)
        col1.pack_propagate(False)
        
        # COL 2: Learning (width=320)
        col2 = tk.Frame(main, bg='#0d1117', width=320, height=680)
        col2.pack(side='left', fill='y', padx=2)
        col2.pack_propagate(False)
        
        # COL 3: Quality/Output (width=340)
        col3 = tk.Frame(main, bg='#0d1117', width=340, height=680)
        col3.pack(side='left', fill='y', padx=2)
        col3.pack_propagate(False)
        
        # COL 4: TAGS (width=440)
        col4 = tk.Frame(main, bg='#0d1117', width=440, height=680)
        col4.pack(side='left', fill='y', padx=2)
        col4.pack_propagate(False)
        
        # === COLUMN 1: SESSION & PROGRESS ===
        self.create_fixed_box(col1, "SESSION", 130, [
            ("current_phase", "PHASE", "phase"),
            ("elapsed_seconds", "ELAPSED", "time"),
            ("phase_time_remaining", "REMAIN", "time"),
            ("model_name", "MODEL", "text"),
        ])
        
        self.create_fixed_box(col1, "PROGRESS", 130, [
            ("current_pass", "PASS", "int"),
            ("total_passes", "TOTAL", "int"),
            ("images_in_pass", "DONE", "int"),
            ("images_total", "IMAGES", "int"),
            ("pass_progress_pct", "PASS%", "pct"),
            ("iterations_completed", "ITERS", "int"),
        ])
        
        self.create_fixed_box(col1, "SPEED", 130, [
            ("current_speed_sec", "NOW", "sec"),
            ("avg_speed_sec", "AVG", "sec"),
            ("min_speed_sec", "MIN", "sec"),
            ("max_speed_sec", "MAX", "sec"),
            ("throughput_per_min", "/MIN", "float"),
            ("throughput_per_hour", "/HR", "int"),
        ])
        
        self.create_fixed_box(col1, "QUALITY", 100, [
            ("success_count", "OK", "int"),
            ("error_count", "ERR", "int"),
            ("success_rate_pct", "RATE", "pct"),
        ])
        
        # === COLUMN 2: LEARNING ===
        self.create_learning_panel(col2)
        
        # === COLUMN 3: OUTPUT & TRAINING ===
        self.create_fixed_box(col3, "VIDEO", 60, [
            ("video_frames_processed", "FRAMES", "int"),
            ("video_passes_completed", "PASSES", "int"),
        ])
        
        self.create_fixed_box(col3, "IMAGE", 60, [
            ("image_frames_processed", "IMAGES", "int"),
            ("image_passes_completed", "PASSES", "int"),
        ])
        
        self.create_output_panel(col3)
        
        # === COLUMN 4: TAGS ===
        self.create_tag_panel(col4)
        
        # Bottom progress bar - FIXED HEIGHT
        self.create_progress_bar()
    
    def create_fixed_box(self, parent, title, height, fields):
        """Create a FIXED SIZE stat box"""
        frame = tk.LabelFrame(parent, text=f" {title} ", font=('Consolas', 8, 'bold'),
                             fg='#58a6ff', bg='#161b22', width=270, height=height)
        frame.pack(fill='x', padx=2, pady=2)
        frame.pack_propagate(False)
        
        inner = tk.Frame(frame, bg='#161b22')
        inner.pack(fill='both', expand=True, padx=5, pady=2)
        
        cols = 3
        for i, (key, label, fmt) in enumerate(fields):
            row, col = i // cols, i % cols
            
            cell = tk.Frame(inner, bg='#161b22', width=80)
            cell.grid(row=row, column=col, padx=2, pady=1, sticky='w')
            
            tk.Label(cell, text=label, font=('Consolas', 6), fg='#8b949e', bg='#161b22').pack(anchor='w')
            val = tk.Label(cell, text="--", font=('Consolas', 11, 'bold'), fg='#f0f6fc', bg='#161b22')
            val.pack(anchor='w')
            
            self.labels[key] = (val, fmt)
    
    def create_tag_panel(self, parent):
        """Create the tag categorization panel"""
        # Tag categories
        TAG_CATEGORIES = {
            "BODY": ["slim", "athletic", "curvy", "petite", "tall", "busty", "flat", "thick"],
            "CHEST": ["small", "medium", "large", "huge", "perky", "natural", "fake"],
            "BUTT": ["small", "round", "big", "flat", "bubble", "athletic"],
            "HAIR": ["blonde", "brunette", "redhead", "black", "long", "short", "curly", "straight"],
            "AGE": ["teen", "young", "20s", "30s", "40s", "milf", "mature"],
            "FACE": ["pretty", "cute", "beautiful", "sexy", "innocent", "exotic"],
            "STYLE": ["casual", "glamour", "artistic", "amateur", "professional"],
            "POSE": ["standing", "sitting", "lying", "kneeling", "bending"],
            "LOOK": ["natural", "makeup", "glam", "goth", "tan", "pale"],
        }
        
        # Main tag frame
        tag_frame = tk.LabelFrame(parent, text=" 🏷️ TAG DATABASE ", font=('Consolas', 9, 'bold'),
                                 fg='#a371f7', bg='#161b22', width=430, height=650)
        tag_frame.pack(fill='both', padx=2, pady=2)
        tag_frame.pack_propagate(False)
        
        # Category panels
        self.tag_labels = {}
        
        for cat_name, cat_tags in TAG_CATEGORIES.items():
            cat_frame = tk.Frame(tag_frame, bg='#161b22')
            cat_frame.pack(fill='x', padx=3, pady=1)
            
            # Category header
            tk.Label(cat_frame, text=f"{cat_name}:", font=('Consolas', 7, 'bold'), 
                    fg='#f0883e', bg='#161b22', width=6, anchor='w').pack(side='left')
            
            # Tags in this category
            tags_container = tk.Frame(cat_frame, bg='#161b22')
            tags_container.pack(side='left', fill='x', expand=True)
            
            for tag in cat_tags:
                tag_btn = tk.Label(tags_container, text=tag, font=('Consolas', 7),
                                  fg='#8b949e', bg='#21262d', padx=3, pady=1)
                tag_btn.pack(side='left', padx=1)
                self.tag_labels[f"{cat_name}_{tag}"] = tag_btn
        
        # Separator
        tk.Frame(tag_frame, bg='#30363d', height=1).pack(fill='x', pady=5)
        
        # Live extracted tags section
        live_frame = tk.LabelFrame(tag_frame, text=" LIVE EXTRACTED TAGS ", font=('Consolas', 8, 'bold'),
                                   fg='#3fb950', bg='#161b22')
        live_frame.pack(fill='both', expand=True, padx=3, pady=2)
        
        self.live_tags_text = tk.Text(live_frame, font=('Consolas', 8), fg='#7ee787', bg='#0d1117',
                                      height=10, wrap='word', state='disabled')
        self.live_tags_text.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Tag stats
        stats_frame = tk.Frame(tag_frame, bg='#161b22')
        stats_frame.pack(fill='x', padx=3, pady=2)
        
        self.unique_tags_label = tk.Label(stats_frame, text="Unique: 0", font=('Consolas', 8),
                                          fg='#8b949e', bg='#161b22')
        self.unique_tags_label.pack(side='left', padx=5)
        
        self.total_tags_label = tk.Label(stats_frame, text="Total: 0", font=('Consolas', 8),
                                         fg='#8b949e', bg='#161b22')
        self.total_tags_label.pack(side='left', padx=5)
        
        self.top_tag_label = tk.Label(stats_frame, text="Top: --", font=('Consolas', 8),
                                      fg='#f0883e', bg='#161b22')
        self.top_tag_label.pack(side='left', padx=5)
    
    def update_tags(self, caption: str):
        """Extract and update tags from caption"""
        if not caption:
            return
        
        caption_lower = caption.lower()
        
        # Keywords to extract as tags
        tag_keywords = {
            # Body
            "slim": "BODY", "athletic": "BODY", "curvy": "BODY", "petite": "BODY",
            "tall": "BODY", "busty": "BODY", "thick": "BODY",
            # Chest
            "small breasts": "CHEST", "large breasts": "CHEST", "big breasts": "CHEST",
            "perky": "CHEST", "natural": "CHEST",
            # Butt
            "round butt": "BUTT", "big butt": "BUTT", "bubble": "BUTT",
            # Hair
            "blonde": "HAIR", "brunette": "HAIR", "redhead": "HAIR", "black hair": "HAIR",
            "long hair": "HAIR", "short hair": "HAIR", "curly": "HAIR", "straight hair": "HAIR",
            # Age
            "young": "AGE", "teen": "AGE", "milf": "AGE", "mature": "AGE",
            # Face
            "pretty": "FACE", "cute": "FACE", "beautiful": "FACE", "sexy": "FACE",
            # Pose
            "standing": "POSE", "sitting": "POSE", "lying": "POSE", "kneeling": "POSE",
            # Style
            "natural": "STYLE", "makeup": "STYLE", "glamour": "STYLE",
            # General
            "woman": "GENERAL", "girl": "GENERAL", "female": "GENERAL",
            "indoor": "SETTING", "outdoor": "SETTING", "bedroom": "SETTING",
        }
        
        extracted = []
        for keyword, category in tag_keywords.items():
            if keyword in caption_lower:
                tag = f"{category}:{keyword}"
                extracted.append(tag)
                
                # Update tag count
                if tag not in self.all_tags:
                    self.all_tags[tag] = 0
                self.all_tags[tag] += 1
                
                # Highlight in UI
                tag_key = f"{category}_{keyword.split()[-1]}"
                if tag_key in self.tag_labels:
                    self.tag_labels[tag_key].configure(fg='#3fb950', bg='#238636')
        
        # Update live tags display
        if extracted:
            self.live_tags_text.configure(state='normal')
            self.live_tags_text.insert('1.0', ', '.join(extracted) + '\n')
            # Keep only last 500 chars
            content = self.live_tags_text.get('1.0', 'end')
            if len(content) > 500:
                self.live_tags_text.delete('250.0', 'end')
            self.live_tags_text.configure(state='disabled')
        
        # Update stats
        self.unique_tags_label.configure(text=f"Unique: {len(self.all_tags)}")
        total = sum(self.all_tags.values())
        self.total_tags_label.configure(text=f"Total: {total}")
        
        if self.all_tags:
            top_tag = max(self.all_tags, key=self.all_tags.get)
            self.top_tag_label.configure(text=f"Top: {top_tag} ({self.all_tags[top_tag]})")
        
        # Update header
        self.tag_count_label.configure(text=f"TAGS: {len(self.all_tags)}")
        
        # Save periodically
        if total % 50 == 0:
            self.save_tags()
    
    def create_stat_box(self, parent, title, fields):
        """Create a stat box with grid layout"""
        frame = tk.LabelFrame(parent, text=f" {title} ", font=('Consolas', 9, 'bold'),
                             fg='#58a6ff', bg='#161b22', padx=8, pady=5)
        frame.pack(fill='x', padx=2, pady=2)
        
        cols = min(3, len(fields))
        for i, (key, label, fmt) in enumerate(fields):
            row, col = i // cols, i % cols
            
            cell = tk.Frame(frame, bg='#161b22')
            cell.grid(row=row, column=col, padx=8, pady=3, sticky='w')
            
            tk.Label(cell, text=label, font=('Consolas', 7), fg='#8b949e', bg='#161b22').pack(anchor='w')
            val = tk.Label(cell, text="--", font=('Consolas', 14, 'bold'), fg='#f0f6fc', bg='#161b22')
            val.pack(anchor='w')
            
            self.labels[key] = (val, fmt)
    
    def create_learning_panel(self, parent):
        """Create the main learning quality panel"""
        # Big learning score display
        score_frame = tk.LabelFrame(parent, text=" 🎯 LEARNING SCORE ", font=('Consolas', 10, 'bold'),
                                   fg='#f0883e', bg='#161b22', padx=10, pady=10)
        score_frame.pack(fill='x', padx=2, pady=2)
        
        self.learning_score_label = tk.Label(score_frame, text="--", 
                                             font=('Consolas', 48, 'bold'), fg='#3fb950', bg='#161b22')
        self.learning_score_label.pack()
        
        self.learning_status_label = tk.Label(score_frame, text="INITIALIZING...", 
                                              font=('Consolas', 12), fg='#8b949e', bg='#161b22')
        self.learning_status_label.pack()
        
        # Learning metrics grid
        metrics_frame = tk.LabelFrame(parent, text=" 📊 LEARNING METRICS ", font=('Consolas', 9, 'bold'),
                                     fg='#a371f7', bg='#161b22', padx=8, pady=5)
        metrics_frame.pack(fill='x', padx=2, pady=2)
        
        metrics = [
            ("caption_consistency", "CONSISTENCY", "pct"),
            ("vocab_diversity", "VOCABULARY", "pct"),
            ("avg_confidence", "CONFIDENCE", "pct"),
            ("tag_agreement", "TAG AGREE", "pct"),
            ("description_quality", "DESC QUALITY", "pct"),
        ]
        
        for i, (key, label, fmt) in enumerate(metrics):
            row = tk.Frame(metrics_frame, bg='#161b22')
            row.pack(fill='x', pady=2)
            
            tk.Label(row, text=label, font=('Consolas', 8), fg='#8b949e', 
                    bg='#161b22', width=12, anchor='w').pack(side='left')
            
            # Progress bar for metric
            bar_frame = tk.Frame(row, bg='#30363d', height=16)
            bar_frame.pack(side='left', fill='x', expand=True, padx=5)
            bar_frame.pack_propagate(False)
            
            bar = tk.Frame(bar_frame, bg='#238636', height=16)
            bar.place(x=0, y=0, relwidth=0.5, relheight=1)
            
            val = tk.Label(row, text="--", font=('Consolas', 10, 'bold'), 
                          fg='#f0f6fc', bg='#161b22', width=8)
            val.pack(side='right')
            
            self.labels[key] = (val, fmt)
            self.gauges[key] = bar
        
        # Epoch tracking
        epoch_frame = tk.LabelFrame(parent, text=" 📈 EPOCH STATUS ", font=('Consolas', 9, 'bold'),
                                   fg='#f0883e', bg='#161b22', padx=8, pady=5)
        epoch_frame.pack(fill='x', padx=2, pady=2)
        
        epoch_fields = [
            ("current_epoch", "EPOCH", "int"),
            ("epoch_loss", "LOSS", "loss"),
            ("epoch_accuracy", "ACCURACY", "pct"),
            ("convergence", "STATUS", "text"),
        ]
        
        for key, label, fmt in epoch_fields:
            row = tk.Frame(epoch_frame, bg='#161b22')
            row.pack(fill='x', pady=1)
            
            tk.Label(row, text=label+":", font=('Consolas', 8), fg='#8b949e', 
                    bg='#161b22', width=10, anchor='w').pack(side='left')
            val = tk.Label(row, text="--", font=('Consolas', 11, 'bold'), 
                          fg='#f0f6fc', bg='#161b22')
            val.pack(side='left')
            
            self.labels[key] = (val, fmt)
        
        # Recommendation
        rec_frame = tk.LabelFrame(parent, text=" 💡 RECOMMENDATION ", font=('Consolas', 9, 'bold'),
                                 fg='#3fb950', bg='#161b22', padx=8, pady=8)
        rec_frame.pack(fill='x', padx=2, pady=2)
        
        self.rec_label = tk.Label(rec_frame, text="Collecting data...", 
                                  font=('Consolas', 11), fg='#f0f6fc', bg='#161b22',
                                  wraplength=300)
        self.rec_label.pack()
    
    def create_output_panel(self, parent):
        """Create output/current item panel"""
        frame = tk.LabelFrame(parent, text=" 📝 CURRENT OUTPUT ", font=('Consolas', 9, 'bold'),
                             fg='#58a6ff', bg='#161b22', padx=8, pady=5)
        frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # File name
        tk.Label(frame, text="FILE:", font=('Consolas', 7), fg='#8b949e', bg='#161b22').pack(anchor='w')
        self.file_label = tk.Label(frame, text="--", font=('Consolas', 9), 
                                   fg='#f0f6fc', bg='#161b22', wraplength=350, anchor='w')
        self.file_label.pack(anchor='w', fill='x')
        
        # Caption
        tk.Label(frame, text="CAPTION:", font=('Consolas', 7), fg='#8b949e', bg='#161b22').pack(anchor='w', pady=(5,0))
        self.caption_label = tk.Label(frame, text="--", font=('Consolas', 9), 
                                      fg='#7ee787', bg='#161b22', wraplength=350, 
                                      justify='left', anchor='nw')
        self.caption_label.pack(anchor='w', fill='both', expand=True)
    
    def create_progress_bar(self):
        """Create progress bar section"""
        progress_frame = tk.Frame(self.root, bg='#0f3460', height=80)
        progress_frame.pack(fill='x', side='bottom')
        progress_frame.pack_propagate(False)
        
        inner = tk.Frame(progress_frame, bg='#0f3460')
        inner.pack(fill='x', padx=20, pady=15)
        
        # Pass progress
        tk.Label(inner, text="Pass Progress:", font=('Segoe UI', 10), 
                fg='white', bg='#0f3460').pack(anchor='w')
        
        self.pass_progress = ttk.Progressbar(inner, length=500, mode='determinate')
        self.pass_progress.pack(fill='x', pady=5)
        
        # Overall progress
        tk.Label(inner, text="Overall Progress:", font=('Segoe UI', 10), 
                fg='white', bg='#0f3460').pack(anchor='w')
        
        self.overall_progress = ttk.Progressbar(inner, length=500, mode='determinate')
        self.overall_progress.pack(fill='x', pady=5)
    
    def format_value(self, value, fmt):
        """Format value based on type"""
        if value is None or value == "--":
            return "--"
        
        try:
            if fmt == "int":
                return str(int(value))
            elif fmt == "float":
                return f"{float(value):.1f}"
            elif fmt == "pct":
                return f"{float(value):.1f}%"
            elif fmt == "sec":
                return f"{float(value):.2f}s"
            elif fmt == "time":
                v = float(value)
                return f"{int(v//60)}m {int(v%60)}s"
            elif fmt == "loss":
                return f"{float(value):.4f}"
            elif fmt == "phase":
                return str(value).upper()
            else:
                return str(value)[:30]
        except:
            return str(value)[:30]
    
    def update_stats(self):
        """Update stats from JSON file"""
        try:
            if STATS_FILE.exists():
                with open(STATS_FILE, 'r') as f:
                    self.stats = json.load(f)
                
                # Update all labeled stats
                for key, data in self.labels.items():
                    label, fmt = data
                    value = self.stats.get(key, "--")
                    formatted = self.format_value(value, fmt)
                    label.configure(text=formatted)
                    
                    # Color coding for phase
                    if key == "current_phase":
                        if formatted == "VIDEO":
                            label.configure(fg='#f97583')
                        elif formatted == "IMAGE":
                            label.configure(fg='#56d4dd')
                        else:
                            label.configure(fg='#3fb950')
                    
                    # Color coding for convergence
                    if key == "convergence":
                        if "improv" in str(value).lower():
                            label.configure(fg='#3fb950')
                        elif "stable" in str(value).lower():
                            label.configure(fg='#f0883e')
                        else:
                            label.configure(fg='#f85149')
                
                # Update gauge bars
                for key, bar in self.gauges.items():
                    value = self.stats.get(key, 0)
                    try:
                        pct = min(100, max(0, float(value))) / 100
                        bar.place(relwidth=pct)
                        # Color based on value
                        if pct >= 0.7:
                            bar.configure(bg='#238636')
                        elif pct >= 0.4:
                            bar.configure(bg='#f0883e')
                        else:
                            bar.configure(bg='#f85149')
                    except:
                        pass
                
                # Update big learning score
                score = self.stats.get("learning_score", 0)
                try:
                    score_val = float(score)
                    self.learning_score_label.configure(text=f"{score_val:.1f}")
                    
                    # Color and status based on score
                    if score_val >= 70:
                        self.learning_score_label.configure(fg='#3fb950')
                        self.learning_status_label.configure(text="✓ LEARNING WELL", fg='#3fb950')
                    elif score_val >= 50:
                        self.learning_score_label.configure(fg='#f0883e')
                        self.learning_status_label.configure(text="⚡ LEARNING OK", fg='#f0883e')
                    elif score_val > 0:
                        self.learning_score_label.configure(fg='#f85149')
                        self.learning_status_label.configure(text="⚠ NEEDS ATTENTION", fg='#f85149')
                    else:
                        self.learning_status_label.configure(text="⏳ COLLECTING DATA...", fg='#8b949e')
                except:
                    pass
                
                # Update recommendation
                action = self.stats.get("recommended_action", "Continue training")
                trend = self.stats.get("quality_trend", "")
                improvement = self.stats.get("pass_improvement", 0)
                try:
                    imp_val = float(improvement)
                    if imp_val > 0:
                        rec_text = f"{trend} | Improving by {imp_val:.1f}pts | {action}"
                    else:
                        rec_text = f"{trend} | {action}"
                    self.rec_label.configure(text=rec_text)
                except:
                    self.rec_label.configure(text=str(action))
                
                # Update file and caption
                self.file_label.configure(text=str(self.stats.get("last_image_name", "--"))[:50])
                caption = str(self.stats.get("last_caption_preview", "--"))
                self.caption_label.configure(text=caption[:200] + "..." if len(caption) > 200 else caption)
                
                # Extract tags from caption
                self.update_tags(caption)
                
                # Update progress bars
                pass_pct = float(self.stats.get("pass_progress_pct", 0))
                self.pass_progress['value'] = pass_pct
                
                current_pass = self.stats.get("current_pass", 0)
                total_passes = self.stats.get("total_passes", 5)
                if total_passes > 0:
                    overall = ((current_pass - 1) / total_passes * 100) + (pass_pct / total_passes)
                    self.overall_progress['value'] = overall
                
                # Update header status
                phase = self.stats.get("current_phase", "unknown")
                if phase == "complete":
                    self.status_label.configure(text="✓ COMPLETE", fg='#3fb950')
                elif phase in ["video", "image"]:
                    self.status_label.configure(text=f"● {phase.upper()}", fg='#f0883e')
                else:
                    self.status_label.configure(text="● RUNNING", fg='#3fb950')
        
        except Exception as e:
            pass
        
        # Update clock
        self.clock_label.configure(text=datetime.now().strftime("%H:%M:%S"))
        
        # Schedule next update
        self.root.after(REFRESH_MS, self.update_stats)


def main():
    root = tk.Tk()
    
    # Style configuration
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TProgressbar", 
                   background='#00ff88',
                   troughcolor='#333',
                   borderwidth=0,
                   lightcolor='#00ff88',
                   darkcolor='#00ff88')
    
    app = TrainingDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
