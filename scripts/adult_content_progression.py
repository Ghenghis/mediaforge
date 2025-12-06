"""
Adult Content Progression System
=================================
Manages age-based content unlocking and clothing progression for 21+ story content.
Integrates with Frontier Stories for story-driven adult content generation.

Features:
- Age verification slider (18-65+)
- Content rating progression (PG → R → X)
- Clothing state progression (dressed → see-through → unclothing → nude)
- Story timeline integration
- User preference learning
"""
import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum, IntEnum
import random

# Configuration
CIVITAI_PATH = Path("c:/Users/Admin/civitai")
DATA_DIR = CIVITAI_PATH / "data"


class ContentRating(IntEnum):
    """Content rating levels (age-gated)"""
    PG = 0           # General audiences
    PG13 = 13        # Teen content
    SOFT_R = 17      # Soft adult (suggestive)
    R = 18           # Adult (implied)
    HARD_R = 19      # Adult explicit (partial)
    NC17 = 20        # Adult explicit (full)
    X = 21           # Extreme adult (21+ only)


class ClothingState(IntEnum):
    """Clothing progression states"""
    FULLY_DRESSED = 0        # Complete outfit
    CASUAL_DRESS = 1         # Relaxed clothing
    LIGHT_DRESS = 2          # Light/thin clothing
    REVEALING = 3            # Revealing outfit
    SEE_THROUGH = 4          # See-through fabrics
    PARTIAL_UNDRESS = 5      # Partially undressed
    MINIMAL = 6              # Minimal coverage
    TOPLESS = 7              # Top removed
    BOTTOMLESS = 8           # Bottom removed
    NUDE = 9                 # Full nude


class TimeOfDay(Enum):
    """Time periods affecting intimacy levels"""
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"
    LATE_NIGHT = "late_night"


class IntimacyLevel(IntEnum):
    """Intimacy progression in story"""
    STRANGERS = 0
    ACQUAINTANCE = 1
    FRIENDLY = 2
    CLOSE_FRIENDS = 3
    ROMANTIC_INTEREST = 4
    DATING = 5
    INTIMATE = 6
    LOVERS = 7
    PASSIONATE = 8
    UNINHIBITED = 9


@dataclass
class AgeVerification:
    """Age verification data"""
    verified: bool = False
    birth_date: Optional[str] = None
    verified_at: Optional[str] = None
    verification_method: str = "slider"
    
    @property
    def age(self) -> int:
        if not self.birth_date:
            return 0
        try:
            bd = datetime.fromisoformat(self.birth_date).date()
            today = date.today()
            return today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        except:
            return 0
    
    @property
    def can_view_adult(self) -> bool:
        return self.verified and self.age >= 21
    
    @property
    def max_rating(self) -> ContentRating:
        if not self.verified:
            return ContentRating.PG
        age = self.age
        if age >= 21:
            return ContentRating.X
        elif age >= 18:
            return ContentRating.HARD_R
        elif age >= 17:
            return ContentRating.SOFT_R
        elif age >= 13:
            return ContentRating.PG13
        return ContentRating.PG


@dataclass
class CharacterClothingState:
    """Track clothing state for a character"""
    actor_id: str
    actor_name: str
    current_state: ClothingState = ClothingState.FULLY_DRESSED
    current_outfit: str = ""
    revealed_parts: List[str] = field(default_factory=list)
    intimacy_level: IntimacyLevel = IntimacyLevel.STRANGERS
    
    def progress_clothing(self, steps: int = 1) -> ClothingState:
        """Progress to next clothing state"""
        new_state = min(self.current_state + steps, ClothingState.NUDE)
        self.current_state = ClothingState(new_state)
        return self.current_state
    
    def regress_clothing(self, steps: int = 1) -> ClothingState:
        """Regress to previous clothing state"""
        new_state = max(self.current_state - steps, ClothingState.FULLY_DRESSED)
        self.current_state = ClothingState(new_state)
        return self.current_state


@dataclass
class StoryMoment:
    """A moment in the story with content rating"""
    moment_id: str
    story_id: str
    scene_number: int
    moment_number: int
    title: str
    description: str
    actors: List[str]
    time_of_day: TimeOfDay
    content_rating: ContentRating
    clothing_states: Dict[str, ClothingState] = field(default_factory=dict)
    intimacy_level: IntimacyLevel = IntimacyLevel.STRANGERS
    image_prompt: str = ""
    generated_image: Optional[str] = None


@dataclass
class AdultStoryArc:
    """Complete story arc with progression"""
    arc_id: str
    title: str
    description: str
    actors: List[str]
    dwelling: str
    era: str = "1870s"
    moments: List[StoryMoment] = field(default_factory=list)
    total_images: int = 300
    adult_images: int = 250  # 21+ rated images
    current_moment: int = 0
    
    @property
    def pg_images(self) -> int:
        return self.total_images - self.adult_images


class ClothingProgressionGenerator:
    """Generate clothing progression prompts"""
    
    CLOTHING_DESCRIPTIONS = {
        ClothingState.FULLY_DRESSED: {
            "female": [
                "wearing traditional buckskin dress, fully covered",
                "in ceremonial outfit with intricate beadwork",
                "dressed in layered tribal clothing, modest",
            ],
            "male": [
                "wearing traditional breechcloth and leather tunic",
                "in full warrior regalia with feathered headdress",
                "dressed in frontier clothing, shirt and pants",
            ]
        },
        ClothingState.CASUAL_DRESS: {
            "female": [
                "relaxed in simple cotton dress, slightly loose",
                "comfortable in soft leather dress, casual fit",
            ],
            "male": [
                "casual in open-collar shirt, relaxed",
                "comfortable in loose tunic, relaxed pose",
            ]
        },
        ClothingState.LIGHT_DRESS: {
            "female": [
                "in thin cotton slip, light fabric draping softly",
                "wearing light summer dress, fabric flowing",
            ],
            "male": [
                "shirtless, wearing only loose pants",
                "in thin linen shirt, open at chest",
            ]
        },
        ClothingState.REVEALING: {
            "female": [
                "in low-cut buckskin dress showing cleavage",
                "wearing short dress revealing legs and shoulders",
                "outfit with strategic cutouts showing skin",
            ],
            "male": [
                "bare-chested, muscular torso visible",
                "in minimal warrior attire showing physique",
            ]
        },
        ClothingState.SEE_THROUGH: {
            "female": [
                "thin wet fabric clinging to body, translucent",
                "sheer nightgown, silhouette visible through fabric",
                "gossamer fabric barely concealing curves",
            ],
            "male": [
                "wet shirt clinging to muscular chest",
                "thin fabric showing body definition",
            ]
        },
        ClothingState.PARTIAL_UNDRESS: {
            "female": [
                "dress slipping off one shoulder, partially undone",
                "top loosened revealing upper chest area",
                "clothing in state of being removed",
            ],
            "male": [
                "shirt removed, working on belt",
                "upper body bare, removing remaining clothes",
            ]
        },
        ClothingState.MINIMAL: {
            "female": [
                "in minimal undergarments only",
                "wearing only essential coverings",
                "barely covered, artistic pose",
            ],
            "male": [
                "in minimal loincloth only",
                "wearing only essential covering",
            ]
        },
        ClothingState.TOPLESS: {
            "female": [
                "topless, tasteful artistic pose, arms positioned modestly",
                "upper body bare, natural pose by firelight",
            ],
            "male": [
                "bare-chested, powerful stance",
                "upper body exposed, confident pose",
            ]
        },
        ClothingState.BOTTOMLESS: {
            "female": [
                "covered above, lower body exposed, artistic angle",
            ],
            "male": [
                "torso covered, lower body exposed",
            ]
        },
        ClothingState.NUDE: {
            "female": [
                "fully nude, artistic pose, tasteful lighting",
                "natural nude, confident and beautiful",
                "nude by firelight, warm glow on skin",
            ],
            "male": [
                "nude, powerful stance, artistic lighting",
                "natural nude, confident masculine pose",
            ]
        }
    }
    
    INTIMACY_ACTIONS = {
        IntimacyLevel.STRANGERS: ["meeting", "noticing", "observing from afar"],
        IntimacyLevel.ACQUAINTANCE: ["talking", "exchanging glances", "brief touch"],
        IntimacyLevel.FRIENDLY: ["laughing together", "comfortable proximity", "casual touch"],
        IntimacyLevel.CLOSE_FRIENDS: ["embracing", "holding hands", "intimate conversation"],
        IntimacyLevel.ROMANTIC_INTEREST: ["lingering looks", "blushing", "nervous proximity"],
        IntimacyLevel.DATING: ["first kiss", "romantic embrace", "tender moment"],
        IntimacyLevel.INTIMATE: ["passionate kiss", "close embrace", "undressing"],
        IntimacyLevel.LOVERS: ["making love", "intertwined bodies", "passionate union"],
        IntimacyLevel.PASSIONATE: ["intense passion", "wild abandon", "deep connection"],
        IntimacyLevel.UNINHIBITED: ["complete freedom", "pure passion", "ultimate intimacy"],
    }
    
    def get_clothing_prompt(self, state: ClothingState, gender: str = "female") -> str:
        """Get clothing description for state"""
        descriptions = self.CLOTHING_DESCRIPTIONS.get(state, {}).get(gender, [])
        return random.choice(descriptions) if descriptions else "tastefully posed"
    
    def get_intimacy_action(self, level: IntimacyLevel) -> str:
        """Get action for intimacy level"""
        actions = self.INTIMACY_ACTIONS.get(level, ["together"])
        return random.choice(actions)


class AdultContentProgressionSystem:
    """Main system for adult content progression"""
    
    def __init__(self):
        self.db_path = DATA_DIR / "adult_content.db"
        self.clothing_gen = ClothingProgressionGenerator()
        self.age_verification: Optional[AgeVerification] = None
        self._init_db()
    
    def _init_db(self):
        """Initialize database"""
        conn = sqlite3.connect(str(self.db_path))
        
        conn.execute('''CREATE TABLE IF NOT EXISTS age_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            verified BOOLEAN,
            birth_date TEXT,
            verified_at TEXT,
            method TEXT,
            max_rating INTEGER
        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS story_arcs (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            actor_ids TEXT,
            dwelling TEXT,
            era TEXT,
            total_images INTEGER,
            adult_images INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS story_moments (
            id TEXT PRIMARY KEY,
            arc_id TEXT,
            scene_number INTEGER,
            moment_number INTEGER,
            title TEXT,
            description TEXT,
            actor_ids TEXT,
            time_of_day TEXT,
            content_rating INTEGER,
            clothing_states TEXT,
            intimacy_level INTEGER,
            image_prompt TEXT,
            generated_image TEXT,
            FOREIGN KEY (arc_id) REFERENCES story_arcs(id)
        )''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS content_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            preferred_rating INTEGER,
            preferred_clothing INTEGER,
            preferred_intimacy INTEGER,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
        conn.close()
    
    def verify_age(self, birth_year: int, birth_month: int = 1, birth_day: int = 1) -> AgeVerification:
        """Verify user age via slider input"""
        birth_date = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"
        
        verification = AgeVerification(
            verified=True,
            birth_date=birth_date,
            verified_at=datetime.now().isoformat(),
            verification_method="slider"
        )
        
        self.age_verification = verification
        print(f"✅ Age verified: {verification.age} years old")
        print(f"   Max content rating: {verification.max_rating.name}")
        
        return verification
    
    def generate_adult_story_arc(self, 
                                  actors: List[Dict],
                                  dwelling: str = "teepee",
                                  total_images: int = 300,
                                  adult_ratio: float = 0.83) -> AdultStoryArc:
        """Generate a story arc with adult content progression"""
        
        if not self.age_verification or not self.age_verification.can_view_adult:
            raise PermissionError("Age verification required for 21+ content")
        
        adult_images = int(total_images * adult_ratio)
        pg_images = total_images - adult_images
        
        arc = AdultStoryArc(
            arc_id=f"arc_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=f"Intimate Tales from the {dwelling.title()}",
            description=f"A story of love and passion among {len(actors)} characters",
            actors=[a.get('id', '') for a in actors],
            dwelling=dwelling,
            total_images=total_images,
            adult_images=adult_images
        )
        
        # Generate moments with progression
        moments = self._generate_story_moments(arc, actors, pg_images, adult_images)
        arc.moments = moments
        
        # Save to database
        self._save_arc(arc)
        
        return arc
    
    def _generate_story_moments(self, 
                                 arc: AdultStoryArc,
                                 actors: List[Dict],
                                 pg_count: int,
                                 adult_count: int) -> List[StoryMoment]:
        """Generate story moments with natural progression"""
        moments = []
        moment_id = 0
        
        # Phase 1: Introduction (PG content)
        intro_moments = self._generate_intro_phase(arc, actors, pg_count // 2)
        moments.extend(intro_moments)
        moment_id = len(moments)
        
        # Phase 2: Building tension (PG-13 to Soft R)
        tension_moments = self._generate_tension_phase(arc, actors, pg_count // 2, moment_id)
        moments.extend(tension_moments)
        moment_id = len(moments)
        
        # Phase 3: Romance develops (R rated)
        romance_moments = self._generate_romance_phase(arc, actors, adult_count // 4, moment_id)
        moments.extend(romance_moments)
        moment_id = len(moments)
        
        # Phase 4: Intimacy begins (Hard R)
        intimacy_moments = self._generate_intimacy_phase(arc, actors, adult_count // 4, moment_id)
        moments.extend(intimacy_moments)
        moment_id = len(moments)
        
        # Phase 5: Passion (NC17)
        passion_moments = self._generate_passion_phase(arc, actors, adult_count // 4, moment_id)
        moments.extend(passion_moments)
        moment_id = len(moments)
        
        # Phase 6: Climax (X rated, 21+ only)
        climax_moments = self._generate_climax_phase(arc, actors, adult_count // 4, moment_id)
        moments.extend(climax_moments)
        
        return moments
    
    def _generate_intro_phase(self, arc: AdultStoryArc, actors: List[Dict], count: int) -> List[StoryMoment]:
        """Generate introduction phase (PG)"""
        moments = []
        
        titles = [
            "First Meeting", "The Teepee", "Morning Light",
            "Shared Space", "Getting Acquainted", "Daily Routines"
        ]
        
        for i in range(count):
            clothing_states = {}
            for actor in actors:
                clothing_states[actor.get('id', f'actor_{i}')] = ClothingState.FULLY_DRESSED
            
            moment = StoryMoment(
                moment_id=f"{arc.arc_id}_m{i}",
                story_id=arc.arc_id,
                scene_number=1,
                moment_number=i,
                title=titles[i % len(titles)],
                description=f"Introduction scene {i+1}",
                actors=[a.get('id', '') for a in actors],
                time_of_day=TimeOfDay.MORNING if i % 2 == 0 else TimeOfDay.AFTERNOON,
                content_rating=ContentRating.PG,
                clothing_states=clothing_states,
                intimacy_level=IntimacyLevel.STRANGERS if i < 2 else IntimacyLevel.ACQUAINTANCE,
                image_prompt=self._build_prompt(actors, ClothingState.FULLY_DRESSED, IntimacyLevel.STRANGERS, arc.dwelling)
            )
            moments.append(moment)
        
        return moments
    
    def _generate_tension_phase(self, arc: AdultStoryArc, actors: List[Dict], count: int, start_id: int) -> List[StoryMoment]:
        """Generate tension building phase (PG-13 to Soft R)"""
        moments = []
        
        titles = [
            "Stolen Glances", "Close Quarters", "Evening Fire",
            "Unexpected Touch", "Growing Feelings", "Night Whispers"
        ]
        
        for i in range(count):
            clothing_states = {}
            state = ClothingState.CASUAL_DRESS if i < count // 2 else ClothingState.LIGHT_DRESS
            for actor in actors:
                clothing_states[actor.get('id', f'actor_{i}')] = state
            
            rating = ContentRating.PG13 if i < count // 2 else ContentRating.SOFT_R
            intimacy = IntimacyLevel.FRIENDLY if i < count // 2 else IntimacyLevel.CLOSE_FRIENDS
            
            moment = StoryMoment(
                moment_id=f"{arc.arc_id}_m{start_id + i}",
                story_id=arc.arc_id,
                scene_number=2,
                moment_number=start_id + i,
                title=titles[i % len(titles)],
                description=f"Tension building scene {i+1}",
                actors=[a.get('id', '') for a in actors],
                time_of_day=TimeOfDay.EVENING,
                content_rating=rating,
                clothing_states=clothing_states,
                intimacy_level=intimacy,
                image_prompt=self._build_prompt(actors, state, intimacy, arc.dwelling)
            )
            moments.append(moment)
        
        return moments
    
    def _generate_romance_phase(self, arc: AdultStoryArc, actors: List[Dict], count: int, start_id: int) -> List[StoryMoment]:
        """Generate romance phase (R rated)"""
        moments = []
        
        titles = [
            "First Kiss", "Tender Embrace", "By Firelight",
            "Revealing Feelings", "Closer Than Before", "Undeniable Attraction"
        ]
        
        for i in range(count):
            clothing_states = {}
            state = ClothingState.REVEALING if i < count // 2 else ClothingState.SEE_THROUGH
            for actor in actors:
                clothing_states[actor.get('id', f'actor_{i}')] = state
            
            intimacy = IntimacyLevel.ROMANTIC_INTEREST if i < count // 2 else IntimacyLevel.DATING
            
            moment = StoryMoment(
                moment_id=f"{arc.arc_id}_m{start_id + i}",
                story_id=arc.arc_id,
                scene_number=3,
                moment_number=start_id + i,
                title=titles[i % len(titles)],
                description=f"Romance scene {i+1}",
                actors=[a.get('id', '') for a in actors],
                time_of_day=TimeOfDay.NIGHT,
                content_rating=ContentRating.R,
                clothing_states=clothing_states,
                intimacy_level=intimacy,
                image_prompt=self._build_prompt(actors, state, intimacy, arc.dwelling)
            )
            moments.append(moment)
        
        return moments
    
    def _generate_intimacy_phase(self, arc: AdultStoryArc, actors: List[Dict], count: int, start_id: int) -> List[StoryMoment]:
        """Generate intimacy phase (Hard R)"""
        moments = []
        
        titles = [
            "Removing Barriers", "Skin on Skin", "Breathless Moments",
            "Growing Desire", "Unrestrained", "Complete Trust"
        ]
        
        for i in range(count):
            clothing_states = {}
            state = ClothingState.PARTIAL_UNDRESS if i < count // 2 else ClothingState.MINIMAL
            for actor in actors:
                clothing_states[actor.get('id', f'actor_{i}')] = state
            
            moment = StoryMoment(
                moment_id=f"{arc.arc_id}_m{start_id + i}",
                story_id=arc.arc_id,
                scene_number=4,
                moment_number=start_id + i,
                title=titles[i % len(titles)],
                description=f"Intimacy scene {i+1}",
                actors=[a.get('id', '') for a in actors],
                time_of_day=TimeOfDay.LATE_NIGHT,
                content_rating=ContentRating.HARD_R,
                clothing_states=clothing_states,
                intimacy_level=IntimacyLevel.INTIMATE,
                image_prompt=self._build_prompt(actors, state, IntimacyLevel.INTIMATE, arc.dwelling)
            )
            moments.append(moment)
        
        return moments
    
    def _generate_passion_phase(self, arc: AdultStoryArc, actors: List[Dict], count: int, start_id: int) -> List[StoryMoment]:
        """Generate passion phase (NC17)"""
        moments = []
        
        titles = [
            "Passionate Night", "Lovers Entwined", "Pure Desire",
            "Unbridled Passion", "Together as One", "Ecstasy"
        ]
        
        for i in range(count):
            clothing_states = {}
            state = ClothingState.TOPLESS if i < count // 2 else ClothingState.NUDE
            for actor in actors:
                clothing_states[actor.get('id', f'actor_{i}')] = state
            
            moment = StoryMoment(
                moment_id=f"{arc.arc_id}_m{start_id + i}",
                story_id=arc.arc_id,
                scene_number=5,
                moment_number=start_id + i,
                title=titles[i % len(titles)],
                description=f"Passion scene {i+1}",
                actors=[a.get('id', '') for a in actors],
                time_of_day=TimeOfDay.LATE_NIGHT,
                content_rating=ContentRating.NC17,
                clothing_states=clothing_states,
                intimacy_level=IntimacyLevel.LOVERS,
                image_prompt=self._build_prompt(actors, state, IntimacyLevel.LOVERS, arc.dwelling)
            )
            moments.append(moment)
        
        return moments
    
    def _generate_climax_phase(self, arc: AdultStoryArc, actors: List[Dict], count: int, start_id: int) -> List[StoryMoment]:
        """Generate climax phase (X rated, 21+ only)"""
        moments = []
        
        titles = [
            "Ultimate Union", "Complete Surrender", "Peak Passion",
            "Boundless Love", "Uninhibited", "Pure Bliss"
        ]
        
        for i in range(count):
            clothing_states = {}
            for actor in actors:
                clothing_states[actor.get('id', f'actor_{i}')] = ClothingState.NUDE
            
            intimacy = IntimacyLevel.PASSIONATE if i < count // 2 else IntimacyLevel.UNINHIBITED
            
            moment = StoryMoment(
                moment_id=f"{arc.arc_id}_m{start_id + i}",
                story_id=arc.arc_id,
                scene_number=6,
                moment_number=start_id + i,
                title=titles[i % len(titles)],
                description=f"Climax scene {i+1} - 21+ ONLY",
                actors=[a.get('id', '') for a in actors],
                time_of_day=TimeOfDay.LATE_NIGHT,
                content_rating=ContentRating.X,
                clothing_states=clothing_states,
                intimacy_level=intimacy,
                image_prompt=self._build_prompt(actors, ClothingState.NUDE, intimacy, arc.dwelling)
            )
            moments.append(moment)
        
        return moments
    
    def _build_prompt(self, actors: List[Dict], clothing_state: ClothingState, 
                      intimacy: IntimacyLevel, dwelling: str) -> str:
        """Build image generation prompt"""
        
        quality = "masterpiece, best quality, highly detailed, 8k, photorealistic"
        
        # Character descriptions
        char_parts = []
        for actor in actors[:3]:
            name = actor.get('full_name', 'character')
            tribe = actor.get('tribe', 'Native American')
            age = actor.get('age', 25)
            gender = "female" if any(x in actor.get('role', '').lower() for x in ['woman', 'maiden', 'wife', 'girl']) else "female"
            
            clothing_desc = self.clothing_gen.get_clothing_prompt(clothing_state, gender)
            char_parts.append(f"{name}, {tribe} {actor.get('role', '')}, {age} years old, {clothing_desc}")
        
        characters = "; ".join(char_parts)
        
        # Intimacy action
        action = self.clothing_gen.get_intimacy_action(intimacy)
        
        # Setting
        setting = f"inside traditional {dwelling}, firelight, warm atmosphere, 1870s frontier"
        
        # Content rating tag
        rating_tags = {
            ClothingState.FULLY_DRESSED: "tasteful, artistic",
            ClothingState.CASUAL_DRESS: "relaxed, natural",
            ClothingState.LIGHT_DRESS: "suggestive, artistic",
            ClothingState.REVEALING: "sensual, artistic",
            ClothingState.SEE_THROUGH: "erotic, artistic nudity",
            ClothingState.PARTIAL_UNDRESS: "explicit, artistic",
            ClothingState.MINIMAL: "explicit, adult",
            ClothingState.TOPLESS: "explicit, nude, adult",
            ClothingState.BOTTOMLESS: "explicit, nude, adult",
            ClothingState.NUDE: "explicit, full nude, adult, NSFW"
        }
        
        rating_tag = rating_tags.get(clothing_state, "artistic")
        
        prompt = f"""{quality}, {rating_tag},
{characters},
{action},
Setting: {setting},
Lighting: warm firelight, intimate atmosphere,
Style: photorealistic, cinematic, sensual photography"""
        
        return prompt
    
    def _save_arc(self, arc: AdultStoryArc):
        """Save story arc to database"""
        conn = sqlite3.connect(str(self.db_path))
        
        conn.execute('''INSERT OR REPLACE INTO story_arcs
            (id, title, description, actor_ids, dwelling, era, total_images, adult_images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (arc.arc_id, arc.title, arc.description, 
             json.dumps(arc.actors), arc.dwelling, arc.era,
             arc.total_images, arc.adult_images))
        
        for moment in arc.moments:
            conn.execute('''INSERT OR REPLACE INTO story_moments
                (id, arc_id, scene_number, moment_number, title, description,
                 actor_ids, time_of_day, content_rating, clothing_states,
                 intimacy_level, image_prompt, generated_image)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (moment.moment_id, arc.arc_id, moment.scene_number,
                 moment.moment_number, moment.title, moment.description,
                 json.dumps(moment.actors), moment.time_of_day.value,
                 int(moment.content_rating), json.dumps({k: int(v) for k, v in moment.clothing_states.items()}),
                 int(moment.intimacy_level), moment.image_prompt, moment.generated_image))
        
        conn.commit()
        conn.close()
    
    def get_arc_summary(self, arc: AdultStoryArc) -> str:
        """Generate summary of story arc"""
        rating_counts = {}
        for moment in arc.moments:
            rating = moment.content_rating.name
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        summary = f"""
╔══════════════════════════════════════════════════════════════════╗
║  ADULT STORY ARC: {arc.title[:40]:<40}  ║
╠══════════════════════════════════════════════════════════════════╣
║  Arc ID: {arc.arc_id}
║  Dwelling: {arc.dwelling}
║  Era: {arc.era}
║  
║  CONTENT DISTRIBUTION:
║  Total Images: {arc.total_images}
║  Adult (21+) Images: {arc.adult_images} ({arc.adult_images/arc.total_images*100:.1f}%)
║  
║  BY RATING:
"""
        for rating, count in sorted(rating_counts.items()):
            summary += f"║    {rating}: {count} images\n"
        
        summary += """║  
║  PHASES:
║    1. Introduction (PG) - Meeting, daily life
║    2. Tension Building (PG-13 to Soft R) - Growing attraction
║    3. Romance (R) - First kiss, revealing feelings
║    4. Intimacy (Hard R) - Physical closeness, undressing
║    5. Passion (NC-17) - Love making
║    6. Climax (X, 21+) - Uninhibited passion
╚══════════════════════════════════════════════════════════════════╝
"""
        return summary


def main():
    """Demonstration"""
    print("=" * 70)
    print("  ADULT CONTENT PROGRESSION SYSTEM")
    print("  Age-verified story content with natural progression")
    print("=" * 70)
    
    system = AdultContentProgressionSystem()
    
    # Simulate age verification (21+ user)
    print("\n🔞 Age Verification Required")
    print("   Please verify your age using the slider...")
    
    # Verify as 25 year old (born 2000)
    verification = system.verify_age(2000, 6, 15)
    
    if verification.can_view_adult:
        print(f"\n✅ Access granted to 21+ content")
        
        # Create sample actors
        actors = [
            {"id": "actor1", "full_name": "Morning Star", "tribe": "Lakota", "role": "Tribal Maiden", "age": 23},
            {"id": "actor2", "full_name": "Swift Eagle", "tribe": "Lakota", "role": "Young Warrior", "age": 25},
            {"id": "actor3", "full_name": "Gentle River", "tribe": "Lakota", "role": "Healer Woman", "age": 24},
        ]
        
        print(f"\n🎭 Actors:")
        for actor in actors:
            print(f"   - {actor['full_name']} ({actor['role']}, {actor['age']})")
        
        # Generate story arc
        print("\n📖 Generating Adult Story Arc...")
        arc = system.generate_adult_story_arc(
            actors=actors,
            dwelling="teepee",
            total_images=300,
            adult_ratio=0.83  # 250 adult images out of 300
        )
        
        print(system.get_arc_summary(arc))
        
        # Show sample prompts from each phase
        print("\n📝 Sample Prompts by Phase:")
        phases = [
            ("Introduction (PG)", ContentRating.PG),
            ("Romance (R)", ContentRating.R),
            ("Intimacy (Hard R)", ContentRating.HARD_R),
            ("Climax (X, 21+)", ContentRating.X)
        ]
        
        for phase_name, rating in phases:
            moment = next((m for m in arc.moments if m.content_rating == rating), None)
            if moment:
                print(f"\n   {phase_name}:")
                print(f"   Title: {moment.title}")
                prompt_preview = moment.image_prompt[:150] + "..."
                print(f"   Prompt: {prompt_preview}")
    else:
        print("\n❌ Age verification failed. 21+ content not available.")


if __name__ == "__main__":
    main()
