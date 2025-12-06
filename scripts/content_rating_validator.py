"""
CONTENT RATING VALIDATOR
=========================
Validates content against rating system with strict guardrails.
Integrates with rating, tagging, and learning systems.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / "data" / "content_rating_system.json"

class ContentRating(Enum):
    PG = 1
    PG13 = 2
    PG14 = 3
    PG15 = 4
    PG16 = 5
    PG17 = 6
    ADULT_18 = 7
    ADULT_19 = 8
    ADULT_20 = 9
    ADULT_21 = 10

    @classmethod
    def from_string(cls, s: str) -> 'ContentRating':
        mapping = {
            'PG': cls.PG, 'PG13': cls.PG13, 'PG-13': cls.PG13,
            'PG14': cls.PG14, 'PG-14': cls.PG14,
            'PG15': cls.PG15, 'PG-15': cls.PG15,
            'PG16': cls.PG16, 'PG-16': cls.PG16,
            'PG17': cls.PG17, 'PG-17': cls.PG17,
            '18+': cls.ADULT_18, '18': cls.ADULT_18,
            '19+': cls.ADULT_19, '19': cls.ADULT_19,
            '20+': cls.ADULT_20, '20': cls.ADULT_20,
            '21+': cls.ADULT_21, '21': cls.ADULT_21
        }
        return mapping.get(s.upper().replace(' ', ''), cls.PG)

    def to_label(self) -> str:
        labels = {
            self.PG: 'PG', self.PG13: 'PG-13', self.PG14: 'PG-14',
            self.PG15: 'PG-15', self.PG16: 'PG-16', self.PG17: 'PG-17',
            self.ADULT_18: '18+', self.ADULT_19: '19+',
            self.ADULT_20: '20+', self.ADULT_21: '21+'
        }
        return labels.get(self, 'PG')


@dataclass
class ValidationResult:
    valid: bool
    rating: ContentRating
    violations: List[str]
    warnings: List[str]
    suggested_rating: Optional[ContentRating]
    blocked_tags: List[str]
    allowed_tags: List[str]


class ContentRatingValidator:
    """Validates content against rating system with guardrails"""
    
    # Global forbidden terms - NEVER allowed at ANY rating
    GLOBAL_FORBIDDEN = [
        "child", "children", "minor", "minors", "underage", "teen", "teenager",
        "kid", "kids", "young girl", "young boy", "loli", "lolita", "shota",
        "preteen", "pre-teen", "juvenile", "infant", "baby", "toddler",
        "illegal", "non-consensual", "forced", "violence", "gore", "death",
        "torture", "abuse", "harm", "injury"
    ]
    
    # Skin visibility limits by rating (percentage)
    MAX_SKIN = {
        ContentRating.PG: 15,
        ContentRating.PG13: 25,
        ContentRating.PG14: 35,
        ContentRating.PG15: 45,
        ContentRating.PG16: 55,
        ContentRating.PG17: 70,
        ContentRating.ADULT_18: 85,
        ContentRating.ADULT_19: 95,
        ContentRating.ADULT_20: 100,
        ContentRating.ADULT_21: 100
    }
    
    # Tags that indicate higher ratings
    RATING_INDICATOR_TAGS = {
        ContentRating.PG: [],
        ContentRating.PG13: ["tank top", "shorts", "summer dress", "sleeveless"],
        ContentRating.PG14: ["bikini", "swimwear", "crop top", "mini skirt"],
        ContentRating.PG15: ["lingerie visible", "backless", "side exposure"],
        ContentRating.PG16: ["lingerie", "cleavage", "revealing", "see-through light"],
        ContentRating.PG17: ["underwear", "suggestive", "risque", "implied"],
        ContentRating.ADULT_18: ["partial nudity", "artistic nude", "topless implied"],
        ContentRating.ADULT_19: ["nudity", "nude", "naked", "figure study"],
        ContentRating.ADULT_20: ["explicit", "full nudity", "exposed"],
        ContentRating.ADULT_21: ["unrestricted", "explicit content", "adult only"]
    }
    
    # Tags forbidden below certain ratings
    RATING_RESTRICTED_TAGS = {
        ContentRating.PG: ["cleavage", "revealing", "lingerie", "bikini", "underwear", 
                          "nude", "naked", "topless", "explicit", "see-through"],
        ContentRating.PG13: ["lingerie", "underwear", "nude", "naked", "topless", 
                            "explicit", "see-through", "revealing"],
        ContentRating.PG14: ["underwear only", "nude", "naked", "topless", "explicit",
                            "see-through heavy"],
        ContentRating.PG15: ["nude", "naked", "topless", "explicit", "full exposure"],
        ContentRating.PG16: ["nude", "naked", "explicit", "full exposure"],
        ContentRating.PG17: ["explicit nudity", "graphic", "full frontal"],
        ContentRating.ADULT_18: ["graphic sexual", "explicit acts"],
        ContentRating.ADULT_19: ["graphic explicit"],
        ContentRating.ADULT_20: [],
        ContentRating.ADULT_21: []
    }

    def __init__(self):
        self.config = self._load_config()
        
    def _load_config(self) -> dict:
        """Load content rating configuration"""
        try:
            if CONFIG_PATH.exists():
                return json.loads(CONFIG_PATH.read_text())
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
        return {}
        
    def validate_prompt(self, prompt: str, target_rating: ContentRating) -> ValidationResult:
        """
        Validate a prompt against the target content rating.
        Returns validation result with any violations or suggestions.
        """
        prompt_lower = prompt.lower()
        violations = []
        warnings = []
        blocked_tags = []
        allowed_tags = []
        suggested_rating = None
        
        # Check global forbidden terms
        for term in self.GLOBAL_FORBIDDEN:
            if term in prompt_lower:
                violations.append(f"BLOCKED: Forbidden term '{term}' detected")
                blocked_tags.append(term)
                
        # Check rating-restricted tags
        restricted = self.RATING_RESTRICTED_TAGS.get(target_rating, [])
        for tag in restricted:
            if tag in prompt_lower:
                violations.append(f"Tag '{tag}' not allowed at {target_rating.to_label()}")
                blocked_tags.append(tag)
                
        # Detect tags that suggest higher rating
        detected_rating = self._detect_rating_from_tags(prompt_lower)
        if detected_rating and detected_rating.value > target_rating.value:
            suggested_rating = detected_rating
            warnings.append(f"Content suggests {detected_rating.to_label()} rating")
            
        # Find allowed tags for this rating
        for tag in self.RATING_INDICATOR_TAGS.get(target_rating, []):
            if tag in prompt_lower:
                allowed_tags.append(tag)
                
        valid = len(violations) == 0
        
        return ValidationResult(
            valid=valid,
            rating=target_rating,
            violations=violations,
            warnings=warnings,
            suggested_rating=suggested_rating,
            blocked_tags=blocked_tags,
            allowed_tags=allowed_tags
        )
        
    def _detect_rating_from_tags(self, text: str) -> Optional[ContentRating]:
        """Detect the minimum rating required based on tags in text"""
        detected = ContentRating.PG
        
        # Check from highest to lowest
        for rating in reversed(list(ContentRating)):
            tags = self.RATING_INDICATOR_TAGS.get(rating, [])
            for tag in tags:
                if tag in text:
                    if rating.value > detected.value:
                        detected = rating
                        
        return detected if detected != ContentRating.PG else None
        
    def get_fashion_tags(self, rating: ContentRating, era: str = None, 
                         culture: str = None) -> List[str]:
        """Get appropriate fashion tags for rating, era, and culture"""
        tags = []
        
        if not self.config:
            return self._get_default_fashion_tags(rating)
            
        # Get era-specific fashion
        if era and "historical_eras" in self.config:
            era_data = self.config["historical_eras"].get(era, {})
            fashion = era_data.get("fashion_by_rating", {})
            rating_label = rating.to_label().replace('-', '')
            tags.extend(fashion.get(rating_label, []))
            
        # Get culture-specific fashion
        if culture and "cultural_styles" in self.config:
            culture_data = self.config["cultural_styles"].get(culture, {})
            fashion = culture_data.get("fashion_by_rating", {})
            rating_label = rating.to_label().replace('-', '')
            tags.extend(fashion.get(rating_label, []))
            
        # If no specific tags, use defaults
        if not tags:
            tags = self._get_default_fashion_tags(rating)
            
        return tags
        
    def _get_default_fashion_tags(self, rating: ContentRating) -> List[str]:
        """Get default fashion tags for a rating"""
        defaults = {
            ContentRating.PG: ["fully clothed", "modest dress", "professional attire"],
            ContentRating.PG13: ["casual wear", "summer dress", "shorts and top"],
            ContentRating.PG14: ["swimwear", "bikini", "crop top"],
            ContentRating.PG15: ["revealing fashion", "lingerie visible", "backless"],
            ContentRating.PG16: ["lingerie", "see-through light", "revealing"],
            ContentRating.PG17: ["underwear", "suggestive attire", "risque"],
            ContentRating.ADULT_18: ["artistic nude", "partial nudity"],
            ContentRating.ADULT_19: ["nude", "figure study"],
            ContentRating.ADULT_20: ["explicit", "full nudity"],
            ContentRating.ADULT_21: ["unrestricted"]
        }
        return defaults.get(rating, ["clothed"])
        
    def get_guardrail_negative(self, rating: ContentRating) -> str:
        """Get negative prompt additions for guardrails"""
        # Always include global forbidden
        negatives = list(self.GLOBAL_FORBIDDEN)
        
        # Add rating-specific restrictions
        restricted = self.RATING_RESTRICTED_TAGS.get(rating, [])
        negatives.extend(restricted)
        
        return ", ".join(set(negatives))
        
    def sanitize_prompt(self, prompt: str, target_rating: ContentRating) -> Tuple[str, List[str]]:
        """
        Remove forbidden/restricted terms from prompt.
        Returns sanitized prompt and list of removed terms.
        """
        removed = []
        sanitized = prompt
        
        # Remove global forbidden
        for term in self.GLOBAL_FORBIDDEN:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(sanitized):
                sanitized = pattern.sub('', sanitized)
                removed.append(term)
                
        # Remove rating-restricted
        restricted = self.RATING_RESTRICTED_TAGS.get(target_rating, [])
        for term in restricted:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(sanitized):
                sanitized = pattern.sub('', sanitized)
                removed.append(term)
                
        # Clean up multiple commas/spaces
        sanitized = re.sub(r',\s*,', ',', sanitized)
        sanitized = re.sub(r'\s+', ' ', sanitized)
        sanitized = sanitized.strip(' ,')
        
        return sanitized, removed


class EraManager:
    """Manages historical era and cultural style information"""
    
    ERAS = {
        "ancient_bc": {"label": "Ancient (BC)", "period": "Before 0 AD"},
        "medieval": {"label": "Medieval", "period": "500-1400 AD"},
        "renaissance": {"label": "Renaissance", "period": "1400-1600 AD"},
        "baroque_rococo": {"label": "Baroque/Rococo", "period": "1600-1800 AD"},
        "victorian": {"label": "Victorian", "period": "1800-1900 AD"},
        "early_modern": {"label": "Early Modern", "period": "1900-1950 AD"},
        "modern": {"label": "Modern", "period": "1950-2000 AD"},
        "contemporary": {"label": "Contemporary", "period": "2000-Present"}
    }
    
    CULTURES = {
        "tribal": {"label": "Tribal/Indigenous", "regions": ["african", "polynesian", "native american"]},
        "western_classic": {"label": "Western Classic", "regions": ["american west", "frontier"]},
        "professional": {"label": "Professional/Corporate", "regions": ["global"]},
        "luxury_elite": {"label": "Luxury/High Society", "regions": ["global"]},
        "casual_everyday": {"label": "Casual/Everyday", "regions": ["global"]}
    }
    
    def get_all_eras(self) -> List[dict]:
        """Get all available eras"""
        return [{"id": k, **v} for k, v in self.ERAS.items()]
        
    def get_all_cultures(self) -> List[dict]:
        """Get all available cultures"""
        return [{"id": k, **v} for k, v in self.CULTURES.items()]
        
    def get_era_prompt_prefix(self, era: str) -> str:
        """Get prompt prefix for an era"""
        prefixes = {
            "ancient_bc": "ancient classical style, greco-roman aesthetic",
            "medieval": "medieval style, castle setting, period accurate",
            "renaissance": "renaissance art style, classical beauty",
            "baroque_rococo": "baroque style, ornate, elegant",
            "victorian": "victorian era, period fashion, elegant",
            "early_modern": "vintage style, 1920s-1940s aesthetic",
            "modern": "modern style, contemporary fashion",
            "contemporary": "current fashion, modern aesthetic"
        }
        return prefixes.get(era, "")
        
    def get_culture_prompt_prefix(self, culture: str) -> str:
        """Get prompt prefix for a culture"""
        prefixes = {
            "tribal": "tribal style, indigenous aesthetic, cultural patterns",
            "western_classic": "western style, cowgirl aesthetic",
            "professional": "professional style, corporate aesthetic",
            "luxury_elite": "luxury fashion, high society, elegant",
            "casual_everyday": "casual style, everyday fashion"
        }
        return prefixes.get(culture, "")


# Singleton instances
_validator = None
_era_manager = None

def get_validator() -> ContentRatingValidator:
    global _validator
    if _validator is None:
        _validator = ContentRatingValidator()
    return _validator

def get_era_manager() -> EraManager:
    global _era_manager
    if _era_manager is None:
        _era_manager = EraManager()
    return _era_manager


# Quick validation function
def validate_and_sanitize(prompt: str, rating: str) -> dict:
    """
    Quick validation and sanitization of prompt.
    Returns dict with sanitized prompt, validation status, and any issues.
    """
    validator = get_validator()
    rating_enum = ContentRating.from_string(rating)
    
    result = validator.validate_prompt(prompt, rating_enum)
    sanitized, removed = validator.sanitize_prompt(prompt, rating_enum)
    guardrail_negative = validator.get_guardrail_negative(rating_enum)
    
    return {
        "valid": result.valid,
        "original_prompt": prompt,
        "sanitized_prompt": sanitized,
        "removed_terms": removed,
        "violations": result.violations,
        "warnings": result.warnings,
        "suggested_rating": result.suggested_rating.to_label() if result.suggested_rating else None,
        "guardrail_negative": guardrail_negative,
        "rating_label": rating_enum.to_label()
    }


if __name__ == "__main__":
    # Test validation
    validator = get_validator()
    
    # Test cases
    tests = [
        ("beautiful woman in elegant dress", "PG"),
        ("woman in bikini on beach", "PG"),
        ("woman in bikini on beach", "PG14"),
        ("artistic nude figure study", "PG"),
        ("artistic nude figure study", "19+"),
    ]
    
    print("=" * 60)
    print("CONTENT RATING VALIDATOR TEST")
    print("=" * 60)
    
    for prompt, rating in tests:
        result = validate_and_sanitize(prompt, rating)
        print(f"\nPrompt: {prompt}")
        print(f"Target Rating: {rating}")
        print(f"Valid: {result['valid']}")
        if result['violations']:
            print(f"Violations: {result['violations']}")
        if result['warnings']:
            print(f"Warnings: {result['warnings']}")
        if result['suggested_rating']:
            print(f"Suggested Rating: {result['suggested_rating']}")
        print("-" * 40)
