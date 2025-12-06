"""
Story Integration Menu System
=============================
Interactive menu for story-driven image generation with:
- Actor profile viewing
- Scenery/Video/Background generation
- Age-appropriate content based on timeline
- Chat integration with LLM context
"""
import os
import sys
import json
import sqlite3
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# API Endpoints
API_ENDPOINTS = {
    "stories": "http://127.0.0.1:8195",
    "guardrails": "http://127.0.0.1:8200",
    "rating": "http://127.0.0.1:8198",
    "dashboard": "http://127.0.0.1:8100",
    "comfyui": "http://127.0.0.1:8204",
    "playwright": "http://127.0.0.1:8203"
}

# Age-based content rules
AGE_CONTENT_RULES = {
    "clothing_reduction": {
        # Age when characters can start showing less clothing
        "minimum_age": 18,
        "progression": {
            18: "casual_revealing",
            21: "intimate_scenes",
            25: "full_adult"
        }
    },
    "flirting_rules": {
        # Age when flirting/romance can begin
        "minimum_age": 16,
        "progression": {
            16: "innocent_crush",
            17: "light_flirting",
            18: "romantic_scenes",
            21: "adult_romance"
        }
    },
    "rule_breaking": {
        # When characters can "break family rules"
        "minimum_age": 16,
        "types": {
            "sneaking_out": 14,
            "secret_romance": 16,
            "adult_decisions": 18
        }
    }
}


class StoryIntegrationMenu:
    """Main menu system for story integration"""
    
    def __init__(self):
        self.db_path = DATA_DIR / "story_integration.db"
        self.current_family = None
        self.current_actor = None
        self.current_chapter = None
        self.context_window = 160000  # Default 160k context
        self._init_db()
        self._check_services()
    
    def _init_db(self):
        """Initialize local database for session tracking"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute('''CREATE TABLE IF NOT EXISTS session_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_start TEXT,
            actions TEXT,
            context_used INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS generation_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id TEXT,
            generation_type TEXT,
            prompt TEXT,
            age_at_generation INTEGER,
            rating TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS actor_timeline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_id TEXT,
            story_date TEXT,
            event_type TEXT,
            description TEXT,
            content_unlocked TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()
    
    def _check_services(self):
        """Check which services are running"""
        self.services_status = {}
        for name, url in API_ENDPOINTS.items():
            try:
                r = requests.get(url, timeout=2)
                self.services_status[name] = r.status_code == 200
            except:
                self.services_status[name] = False
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str):
        self.clear_screen()
        print("=" * 60)
        print(f"  MEDIAFORGE - {title}")
        print("=" * 60)
        print()
    
    def print_services_status(self):
        print("Service Status:")
        for name, status in self.services_status.items():
            icon = "✓" if status else "✗"
            print(f"  [{icon}] {name.title()}: {API_ENDPOINTS[name]}")
        print()
    
    def main_menu(self):
        """Display main menu"""
        while True:
            self.print_header("STORY INTEGRATION MENU")
            self.print_services_status()
            
            print("Options:")
            print("-" * 40)
            print("  1. Actor Management")
            print("  2. Family Photo Collections")
            print("  3. Story Chapters & Timelines")
            print("  4. Generate Scenery/Backgrounds")
            print("  5. Generate Character Images")
            print("  6. Age Progression Viewer")
            print("  7. Content Rating Settings")
            print("  8. LLM Context Settings")
            print("  9. View Generation Queue")
            print("  0. Exit")
            print("-" * 40)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                self.actor_menu()
            elif choice == "2":
                self.collection_menu()
            elif choice == "3":
                self.chapter_menu()
            elif choice == "4":
                self.scenery_menu()
            elif choice == "5":
                self.character_generation_menu()
            elif choice == "6":
                self.age_progression_menu()
            elif choice == "7":
                self.rating_settings_menu()
            elif choice == "8":
                self.llm_settings_menu()
            elif choice == "9":
                self.queue_menu()
            elif choice == "0":
                print("\nExiting...")
                break
            else:
                print("Invalid option. Press Enter to continue...")
                input()
    
    def actor_menu(self):
        """Actor management menu"""
        while True:
            self.print_header("ACTOR MANAGEMENT")
            
            print("Options:")
            print("-" * 40)
            print("  1. View All Actors")
            print("  2. Search Actor by Name")
            print("  3. View Actor Profile")
            print("  4. View Actor Age at Date")
            print("  5. Generate 525 Actors")
            print("  6. View Actor Content Unlocks")
            print("  0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                self._view_all_actors()
            elif choice == "2":
                self._search_actor()
            elif choice == "3":
                self._view_actor_profile()
            elif choice == "4":
                self._view_actor_age()
            elif choice == "5":
                self._generate_525_actors()
            elif choice == "6":
                self._view_content_unlocks()
            elif choice == "0":
                break
    
    def _view_all_actors(self):
        """View all actors from API"""
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/actors")
            data = r.json()
            
            self.print_header("ALL ACTORS")
            print(f"Total Actors: {data.get('count', 0)}")
            print("-" * 60)
            
            for actor in data.get('actors', [])[:20]:
                age_info = self._get_actor_age_info(actor)
                print(f"  {actor['actor_id']}: {actor['first_name']} {actor['last_name']}")
                print(f"    Role: {actor['role']} | Theme: {actor['theme']}")
                print(f"    Birth: {actor['birth_date']} | Current Age: {age_info['age']}")
                print(f"    Max Rating: {age_info['max_rating']}")
                print()
            
            if data.get('count', 0) > 20:
                print(f"  ... and {data['count'] - 20} more actors")
            
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _get_actor_age_info(self, actor: dict) -> dict:
        """Get actor's current age and rating info"""
        story_date = datetime.now().strftime("%Y-%m-%d")
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/age/{actor['actor_id']}/{story_date}")
            return r.json()
        except:
            return {"age": 0, "max_rating": "PG"}
    
    def _view_actor_profile(self):
        """View detailed actor profile"""
        actor_id = input("Enter Actor ID: ").strip()
        
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/actor/{actor_id}")
            actor = r.json()
            
            if "error" in actor:
                print(f"Error: {actor['error']}")
            else:
                self.print_header(f"ACTOR PROFILE: {actor['first_name']} {actor['last_name']}")
                
                print(f"ID: {actor['actor_id']}")
                print(f"Role: {actor['role']}")
                print(f"Theme: {actor['theme']}")
                print(f"Gender: {actor['gender']}")
                print(f"Birth Date: {actor['birth_date']}")
                print(f"Family: {actor.get('family_id', 'None')}")
                print(f"Family Role: {actor.get('family_role', 'N/A')}")
                print()
                
                # Get current age info
                age_info = self._get_actor_age_info(actor)
                print("Current Status:")
                print(f"  Age: {age_info.get('age', 'Unknown')}")
                print(f"  Age Group: {age_info.get('age_group', 'Unknown')}")
                print(f"  Max Rating: {age_info.get('max_rating', 'Unknown')}")
                print()
                
                # Show content unlocks based on age
                self._show_content_progression(age_info.get('age', 0))
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _show_content_progression(self, age: int):
        """Show what content is unlocked at this age"""
        print("Content Progression:")
        print("-" * 40)
        
        # Clothing
        clothing = AGE_CONTENT_RULES["clothing_reduction"]
        if age < clothing["minimum_age"]:
            print(f"  Clothing: Fully modest (age {clothing['minimum_age']} required)")
        else:
            for min_age, level in clothing["progression"].items():
                if age >= min_age:
                    print(f"  Clothing: {level.replace('_', ' ').title()} unlocked")
        
        # Flirting
        flirting = AGE_CONTENT_RULES["flirting_rules"]
        if age < flirting["minimum_age"]:
            print(f"  Romance: Not allowed (age {flirting['minimum_age']} required)")
        else:
            for min_age, level in flirting["progression"].items():
                if age >= min_age:
                    print(f"  Romance: {level.replace('_', ' ').title()} unlocked")
        
        # Rule breaking
        rules = AGE_CONTENT_RULES["rule_breaking"]
        unlocked = [f"{t} ({a}+)" for t, a in rules["types"].items() if age >= a]
        if unlocked:
            print(f"  Story Conflicts: {', '.join(unlocked)}")
    
    def _generate_525_actors(self):
        """Generate all 525 actors"""
        print("\nGenerating 525 actors... This may take a while.")
        confirm = input("Continue? (y/n): ").strip().lower()
        
        if confirm == 'y':
            try:
                r = requests.post(f"{API_ENDPOINTS['stories']}/api/generate-525")
                result = r.json()
                print(f"\nGenerated {result.get('total_actors', 0)} actors")
                print(f"Families: {result.get('total_families', 0)}")
            except Exception as e:
                print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def collection_menu(self):
        """Photo collection menu"""
        while True:
            self.print_header("FAMILY PHOTO COLLECTIONS")
            
            print("Collection Sizes:")
            print("  - Minimal: 100 photos")
            print("  - Standard: 300 photos (default)")
            print("  - Expanded: 500 photos")
            print("  - Complete: 750 photos")
            print()
            
            print("Options:")
            print("-" * 40)
            print("  1. View All Collections")
            print("  2. Create New Collection")
            print("  3. View Collection Details")
            print("  4. Generate Photos for Collection")
            print("  0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                self._view_collections()
            elif choice == "2":
                self._create_collection()
            elif choice == "3":
                self._view_collection_details()
            elif choice == "4":
                self._generate_collection_photos()
            elif choice == "0":
                break
    
    def _view_collections(self):
        """View all collections"""
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/collections")
            data = r.json()
            
            self.print_header("ALL COLLECTIONS")
            print(f"Total: {data.get('count', 0)}")
            print("-" * 60)
            
            for col in data.get('collections', []):
                progress = f"{col.get('current_count', 0)}/{col.get('target_count', 300)}"
                print(f"  {col['collection_id']}: {col['name']}")
                print(f"    Size: {col.get('collection_size', 'standard')} | Progress: {progress}")
                print(f"    Status: {col.get('status', 'pending')}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _generate_collection_photos(self):
        """Generate photos for a collection"""
        family_id = input("Enter Family ID: ").strip()
        timeline_id = input("Enter Timeline ID: ").strip()
        
        print("\nCollection sizes: minimal, standard, expanded, complete")
        size = input("Enter size (default: standard): ").strip() or "standard"
        
        try:
            r = requests.post(
                f"{API_ENDPOINTS['stories']}/api/collection/generate",
                json={
                    "family_id": family_id,
                    "timeline_id": timeline_id,
                    "size": size,
                    "create_chapters": True
                }
            )
            result = r.json()
            
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                print(f"\nCollection Created: {result.get('collection_id')}")
                print(f"Photos Generated: {result.get('photos_generated')}")
                print(f"Chapters Created: {result.get('chapters_created')}")
                print(f"Date Range: {result.get('date_range')}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def chapter_menu(self):
        """Story chapters menu"""
        while True:
            self.print_header("STORY CHAPTERS & TIMELINES")
            
            print("Options:")
            print("-" * 40)
            print("  1. View All Chapters")
            print("  2. View Chapter Images")
            print("  3. Create New Chapter")
            print("  4. Advance Timeline")
            print("  5. View Restriction Releases")
            print("  0. Back to Main Menu")
            print("-" * 40)
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                self._view_chapters()
            elif choice == "2":
                self._view_chapter_images()
            elif choice == "3":
                self._create_chapter()
            elif choice == "4":
                self._advance_timeline()
            elif choice == "5":
                self._view_restriction_releases()
            elif choice == "0":
                break
    
    def _view_chapters(self):
        """View all chapters"""
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/chapters")
            data = r.json()
            
            self.print_header("ALL CHAPTERS")
            print(f"Total: {data.get('count', 0)}")
            print("-" * 60)
            
            for ch in data.get('chapters', []):
                print(f"  Chapter {ch['chapter_number']}: {ch['title']}")
                print(f"    Family: {ch['family_id']}")
                print(f"    Date Range: {ch.get('story_date_start')} to {ch.get('story_date_end')}")
                print(f"    Images: {ch.get('image_count', 0)}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def scenery_menu(self):
        """Scenery/background generation menu"""
        self.print_header("SCENERY & BACKGROUNDS")
        
        print("Generation Types:")
        print("-" * 40)
        print("  1. Landscape Backgrounds")
        print("  2. Interior Settings")
        print("  3. Weather/Atmosphere")
        print("  4. Time of Day Variants")
        print("  5. Seasonal Variants")
        print("  0. Back")
        print("-" * 40)
        
        choice = input("\nSelect option: ").strip()
        
        # Queue scenery generation
        if choice in ["1", "2", "3", "4", "5"]:
            self._queue_scenery_generation(choice)
        
        input("\nPress Enter to continue...")
    
    def _queue_scenery_generation(self, gen_type: str):
        """Queue scenery for generation"""
        types = {
            "1": "landscape",
            "2": "interior",
            "3": "weather",
            "4": "time_of_day",
            "5": "seasonal"
        }
        
        print(f"\nQueuing {types[gen_type]} generation...")
        
        conn = sqlite3.connect(str(self.db_path))
        conn.execute('''INSERT INTO generation_queue 
            (generation_type, prompt, status) VALUES (?, ?, ?)''',
            (types[gen_type], f"Generate {types[gen_type]} background", "pending"))
        conn.commit()
        conn.close()
        
        print("Added to queue!")
    
    def llm_settings_menu(self):
        """LLM context settings"""
        self.print_header("LLM CONTEXT SETTINGS")
        
        print(f"Current Context Window: {self.context_window:,} tokens")
        print()
        print("Recommended Models by Context:")
        print("-" * 40)
        print("  160K context: Mistral-NeMo, Qwen2.5")
        print("  200K context: Claude-compatible models")
        print("  1M+ context: Gemini-compatible models")
        print()
        
        print("Options:")
        print("  1. Set to 160K (fast)")
        print("  2. Set to 200K (standard)")
        print("  3. Set to 500K (extended)")
        print("  4. Custom value")
        print("  0. Back")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            self.context_window = 160000
        elif choice == "2":
            self.context_window = 200000
        elif choice == "3":
            self.context_window = 500000
        elif choice == "4":
            try:
                val = int(input("Enter context size: "))
                self.context_window = val
            except:
                print("Invalid value")
        
        print(f"\nContext window set to {self.context_window:,} tokens")
        input("\nPress Enter to continue...")
    
    def age_progression_menu(self):
        """View age progression for actors"""
        self.print_header("AGE PROGRESSION VIEWER")
        
        actor_id = input("Enter Actor ID: ").strip()
        
        try:
            # Get actor
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/actor/{actor_id}")
            actor = r.json()
            
            if "error" in actor:
                print(f"Error: {actor['error']}")
            else:
                print(f"\nActor: {actor['first_name']} {actor['last_name']}")
                print(f"Birth Date: {actor['birth_date']}")
                print()
                print("Age Progression:")
                print("-" * 50)
                
                # Show progression at key ages
                from datetime import datetime
                birth_year = int(actor['birth_date'].split('-')[0])
                
                key_ages = [5, 10, 13, 16, 18, 21, 25, 30, 40, 50]
                
                for age in key_ages:
                    year = birth_year + age
                    story_date = f"{year}-06-15"
                    
                    try:
                        r2 = requests.get(f"{API_ENDPOINTS['stories']}/api/age/{actor_id}/{story_date}")
                        info = r2.json()
                        
                        print(f"  Age {age} ({year}):")
                        print(f"    Group: {info.get('age_group', 'N/A')}")
                        print(f"    Max Rating: {info.get('max_rating', 'N/A')}")
                        
                        # Show content unlocks
                        self._show_content_progression(age)
                        print()
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def queue_menu(self):
        """View generation queue"""
        self.print_header("GENERATION QUEUE")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute('''SELECT * FROM generation_queue ORDER BY created_at DESC LIMIT 20''')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            print(f"Recent Queue Items ({len(rows)}):")
            print("-" * 60)
            for row in rows:
                print(f"  ID: {row[0]} | Type: {row[2]} | Status: {row[5]}")
                print(f"  Created: {row[6]}")
                print()
        else:
            print("Queue is empty")
        
        input("\nPress Enter to continue...")
    
    def character_generation_menu(self):
        """Character image generation"""
        self.print_header("CHARACTER IMAGE GENERATION")
        
        print("Options:")
        print("-" * 40)
        print("  1. Generate Portrait")
        print("  2. Generate Full Body")
        print("  3. Generate Scene with Character")
        print("  4. Generate Age Progression Set")
        print("  0. Back")
        print("-" * 40)
        
        choice = input("\nSelect option: ").strip()
        
        if choice in ["1", "2", "3", "4"]:
            actor_id = input("Enter Actor ID: ").strip()
            story_date = input("Story Date (YYYY-MM-DD): ").strip() or datetime.now().strftime("%Y-%m-%d")
            
            # Check age restrictions
            try:
                r = requests.get(f"{API_ENDPOINTS['stories']}/api/age/{actor_id}/{story_date}")
                info = r.json()
                
                print(f"\nActor Age: {info.get('age')}")
                print(f"Max Rating: {info.get('max_rating')}")
                print(f"Allowed content: ", end="")
                self._show_content_progression(info.get('age', 0))
                
                # Queue generation
                gen_types = {
                    "1": "portrait",
                    "2": "full_body",
                    "3": "scene",
                    "4": "age_progression"
                }
                
                conn = sqlite3.connect(str(self.db_path))
                conn.execute('''INSERT INTO generation_queue 
                    (actor_id, generation_type, age_at_generation, rating, status)
                    VALUES (?, ?, ?, ?, ?)''',
                    (actor_id, gen_types[choice], info.get('age', 0), 
                     info.get('max_rating', 'PG'), 'pending'))
                conn.commit()
                conn.close()
                
                print("\nAdded to generation queue!")
                
            except Exception as e:
                print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def rating_settings_menu(self):
        """Content rating settings"""
        self.print_header("CONTENT RATING SETTINGS")
        
        print("Age Groups & Maximum Ratings:")
        print("-" * 50)
        
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/age-groups")
            groups = r.json()
            
            for name, data in groups.items():
                print(f"  {name}: ages {data['range']} -> max {data['max_rating']}")
            
        except:
            print("  (Could not load from API)")
        
        print()
        print("Content Unlock Rules:")
        print("-" * 50)
        print(f"  Clothing reduction starts at: {AGE_CONTENT_RULES['clothing_reduction']['minimum_age']}")
        print(f"  Flirting starts at: {AGE_CONTENT_RULES['flirting_rules']['minimum_age']}")
        print(f"  Rule breaking starts at: {AGE_CONTENT_RULES['rule_breaking']['minimum_age']}")
        
        input("\nPress Enter to continue...")
    
    def _view_restriction_releases(self):
        """View when restrictions are released for an actor"""
        actor_id = input("Enter Actor ID: ").strip()
        
        try:
            r = requests.post(
                f"{API_ENDPOINTS['stories']}/api/actor/restrictions",
                json={"actor_id": actor_id}
            )
            data = r.json()
            
            print(f"\nRestriction Releases for {actor_id}:")
            print("-" * 50)
            
            for release in data.get('releases', []):
                print(f"  Date: {release['release_date']}")
                print(f"  Age: {release['age_at_release']}")
                print(f"  Rating: {release['previous_max_rating']} -> {release['new_max_rating']}")
                print(f"  Reason: {release.get('reason', 'Age progression')}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _view_actor_age(self):
        """View actor age at specific date"""
        actor_id = input("Enter Actor ID: ").strip()
        story_date = input("Story Date (YYYY-MM-DD): ").strip()
        
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/age/{actor_id}/{story_date}")
            info = r.json()
            
            print(f"\nActor: {info.get('actor_name', actor_id)}")
            print(f"At Date: {story_date}")
            print(f"Age: {info.get('age')} years")
            print(f"Age Group: {info.get('age_group')}")
            print(f"Max Rating: {info.get('max_rating')}")
            print()
            self._show_content_progression(info.get('age', 0))
            
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _search_actor(self):
        """Search for actor by name"""
        query = input("Enter name to search: ").strip().lower()
        
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/actors")
            data = r.json()
            
            matches = []
            for actor in data.get('actors', []):
                full_name = f"{actor['first_name']} {actor['last_name']}".lower()
                if query in full_name:
                    matches.append(actor)
            
            print(f"\nFound {len(matches)} matches:")
            print("-" * 50)
            for actor in matches[:10]:
                print(f"  {actor['actor_id']}: {actor['first_name']} {actor['last_name']}")
                print(f"    Role: {actor['role']} | Theme: {actor['theme']}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _view_content_unlocks(self):
        """View content unlocks for actor"""
        actor_id = input("Enter Actor ID: ").strip()
        
        try:
            r = requests.post(
                f"{API_ENDPOINTS['stories']}/api/actor/age-history",
                json={"actor_id": actor_id}
            )
            data = r.json()
            
            print(f"\nAge History for {actor_id}:")
            print("-" * 50)
            
            for snapshot in data.get('snapshots', [])[-10:]:
                print(f"  Date: {snapshot['story_date']}")
                print(f"  Age: {snapshot['age_years']} ({snapshot['age_group']})")
                print(f"  Max Rating: {snapshot['max_rating']}")
                print()
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _create_collection(self):
        """Create new photo collection"""
        family_id = input("Enter Family ID: ").strip()
        name = input("Collection Name: ").strip()
        
        print("\nSizes: minimal, standard, expanded, complete")
        size = input("Size (default: standard): ").strip() or "standard"
        
        try:
            r = requests.post(
                f"{API_ENDPOINTS['stories']}/api/collection",
                json={
                    "family_id": family_id,
                    "name": name,
                    "size": size
                }
            )
            result = r.json()
            print(f"\nCreated: {result.get('collection_id')}")
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _view_collection_details(self):
        """View collection details"""
        collection_id = input("Enter Collection ID: ").strip()
        
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/collection/{collection_id}")
            col = r.json()
            
            if "error" in col:
                print(f"Error: {col['error']}")
            else:
                print(f"\nCollection: {col['name']}")
                print(f"ID: {col['collection_id']}")
                print(f"Family: {col['family_id']}")
                print(f"Size: {col.get('collection_size', 'standard')}")
                print(f"Target: {col.get('target_count', 300)}")
                print(f"Current: {col.get('current_count', 0)}")
                print(f"Status: {col.get('status', 'pending')}")
                
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _view_chapter_images(self):
        """View images in a chapter"""
        chapter_id = input("Enter Chapter ID: ").strip()
        
        try:
            r = requests.get(f"{API_ENDPOINTS['stories']}/api/chapter/{chapter_id}")
            ch = r.json()
            
            if "error" in ch:
                print(f"Error: {ch['error']}")
            else:
                print(f"\nChapter: {ch['title']}")
                print(f"Images: {len(ch.get('images', []))}")
                print("-" * 50)
                
                for img in ch.get('images', [])[:10]:
                    print(f"  {img.get('image_id', 'N/A')}")
                    print(f"    Date: {img.get('story_date')}")
                    print(f"    Rating: {img.get('rating')}")
                    
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _create_chapter(self):
        """Create new chapter"""
        family_id = input("Family ID: ").strip()
        timeline_id = input("Timeline ID: ").strip()
        number = int(input("Chapter Number: ").strip() or "1")
        title = input("Chapter Title: ").strip()
        
        try:
            r = requests.post(
                f"{API_ENDPOINTS['stories']}/api/chapter",
                json={
                    "family_id": family_id,
                    "timeline_id": timeline_id,
                    "chapter_number": number,
                    "title": title
                }
            )
            result = r.json()
            print(f"\nCreated: {result.get('chapter_id')}")
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")
    
    def _advance_timeline(self):
        """Advance a timeline to new date"""
        timeline_id = input("Timeline ID: ").strip()
        new_date = input("New Date (YYYY-MM-DD): ").strip()
        
        try:
            r = requests.post(
                f"{API_ENDPOINTS['stories']}/api/timeline/advance",
                json={
                    "timeline_id": timeline_id,
                    "new_date": new_date
                }
            )
            result = r.json()
            print(f"\nTimeline advanced to: {result.get('new_date')}")
        except Exception as e:
            print(f"Error: {e}")
        
        input("\nPress Enter to continue...")


def main():
    print("Starting Story Integration Menu...")
    menu = StoryIntegrationMenu()
    menu.main_menu()


if __name__ == "__main__":
    main()
