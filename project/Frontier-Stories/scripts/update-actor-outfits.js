/**
 * Update Actor Outfits Script - Advanced Version
 * Creates sexy supermodel outfits tailored to each character's:
 * - Gender (male vs female)
 * - Era (historical 1870s vs modern 2020s)
 * - Tribe/ethnicity (incorporating cultural elements)
 * - Role/profession
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Female indicators - check these FIRST (higher priority)
const femaleIndicators = [
  // Female roles
  'woman', 'women', 'girl', 'lady', 'female', 'she ', ' her ', 'mother', 'grandmother',
  'daughter', 'sister', 'wife', 'bride', 'princess', 'queen', 'miss ', 'mrs ', 'ms ',
  'maiden', 'beauty', 'gorgeous', 'beautiful', 'stunning', 'pretty', 'lovely',
  // Female-typical roles
  'nurse', 'midwife', 'seamstress', 'washerwoman', 'maid', 'nanny',
  'wedding planner', 'interior designer', 'florist', 'makeup artist',
  // Female names/patterns
  'pageant', 'miss indian', 'beauty queen'
];

// Clearly female first names
const femaleNames = [
  'dune', 'peony', 'dahlia', 'tulip', 'azalea', 'magnolia', 'marigold', 'sunflower',
  'lavender', 'rose', 'violet', 'lily', 'iris', 'jasmine', 'daisy', 'willow', 'sage',
  'meadow', 'brook', 'river', 'sky', 'star', 'moon', 'dawn', 'aurora', 'ember',
  'phoenix', 'raven', 'dove', 'sparrow', 'wren', 'luna', 'sierra', 'amber', 'jade',
  'silver', 'crystal', 'opal', 'ruby', 'pearl', 'coral', 'autumn', 'summer', 'winter',
  'spring', 'storm', 'rain', 'snow', 'breeze', 'wind', 'cloud', 'misty', 'sunny',
  'cherry', 'apple', 'berry', 'honey', 'sweet', 'fawn', 'doe', 'mare',
  // Native female names
  'olathe', 'nita', 'mitena', 'lulu', 'winona', 'kaya', 'aiyana', 'aponi', 'chenoa',
  'dyani', 'halona', 'imala', 'kachina', 'mika', 'nahla', 'onida', 'polikwaptiwa',
  'sahkyo', 'takoda', 'una', 'wyanet', 'zaltana', 'aquene', 'citlali', 'enola',
  'nova', 'nina', 'maya', 'leah', 'anna', 'sarah', 'mary', 'elizabeth', 'emma',
  'maria', 'sophia', 'isabella', 'olivia', 'ava', 'mia', 'emily', 'abigail', 'ella'
];

// Male indicators - specific roles/titles that are clearly male
const maleRoles = [
  'chief', 'warrior', 'brave', 'medicine man', 'hunter', 'scout', 'stuntman',
  'father', 'grandfather', 'husband', 'king', 'prince', 'brule warrior',
  'oglala warrior', 'lakota chief', 'sioux chief', 'war leader', 'war chief'
];

// Historical male figures - exact name matches
const historicalMales = [
  'crazy horse', 'sitting bull', 'red cloud', 'geronimo', 'iron shell', 
  'spotted tail', 'black hawk', 'tall bull', 'dull knife', 'little wolf', 
  'american horse', 'rain in the face', 'gall', 'crow king', 'hump', 
  'lame deer', 'two moons', 'little big man', 'touch the clouds', 'low dog',
  'quanah parker', 'cochise', 'mangas coloradas', 'victorio', 'nana',
  'satanta', 'lone wolf', 'big tree', 'kicking bird', 'white bear'
];

// Detect if actor is male based on bio, role, and name
function isMale(actor) {
  const fullName = (actor.full_name || '').toLowerCase();
  const firstName = (actor.first_name || '').toLowerCase();
  const role = (actor.role || '').toLowerCase();
  const bio = (actor.bio || '').toLowerCase();
  const searchText = `${fullName} ${role} ${bio}`;
  
  // Check if it's a known historical male figure (highest priority)
  if (historicalMales.some(name => fullName.includes(name))) {
    return true;
  }
  
  // Check for STRONG male roles FIRST (before female name check)
  // These override any female name detection
  const strongMaleRoles = ['stuntman', 'warrior', 'chief', 'medicine man', 'hunter', 'scout', 'brave'];
  for (const maleRole of strongMaleRoles) {
    const regex = new RegExp(`\\b${maleRole}\\b`, 'i');
    if (regex.test(role)) {
      return true;
    }
  }
  
  // Check if first name is clearly female (and role doesn't override)
  if (femaleNames.includes(firstName)) {
    return false;
  }
  
  // Check for female indicators in role/bio
  if (femaleIndicators.some(indicator => searchText.includes(indicator))) {
    return false;
  }
  
  // Check for other male roles (use word boundaries via regex for accuracy)
  for (const maleRole of maleRoles) {
    const regex = new RegExp(`\\b${maleRole}\\b`, 'i');
    if (regex.test(searchText)) {
      return true;
    }
  }
  
  // Default to female for this dataset (majority are female)
  return false;
}

// Get tribe from metadata or tags
function getTribe(actor) {
  if (actor.metadata?.tribe) return actor.metadata.tribe;
  const tribes = ['Lakota', 'Cherokee', 'Navajo', 'Apache', 'Comanche', 'Crow', 
                  'Blackfeet', 'Cheyenne', 'Sioux', 'Brule', 'Oglala', 'Hunkpapa'];
  for (const tribe of tribes) {
    if (actor.tags?.includes(tribe)) return tribe;
    if (actor.bio?.includes(tribe)) return tribe;
  }
  return null;
}

// Get era
function getEra(actor) {
  return actor.era || '2020s';
}

// ============ FEMALE OUTFIT TEMPLATES ============

// Modern female - sexy contemporary modeling
const modernFemaleOutfits = [
  {
    outfit: "Fitted heather-grey sleeveless crop top ending just above the navel, paired with black lace-trimmed bikini bottoms and delicate turquoise belly chain. Soft knit fabric hugging curves naturally.",
    pose_style: "Arms raised overhead, fingers through tousled hair, back arched. One hip shifted creating an S-curve.",
    expression_style: "Sultry half-lidded gaze, parted lips, confident allure."
  },
  {
    outfit: "Light grey cropped muscle tee revealing toned midriff, worn with black lace high-cut panties and silver ankle bracelet. Casual fabric draped suggestively.",
    pose_style: "One hand tugging top hem up, other on hip. Weight on one leg, dynamic tension.",
    expression_style: "Playful smirk, chin down, eyes up through lashes."
  },
  {
    outfit: "Grey ribbed knit crop sweater clinging to curves, stopping at ribcage, with sheer black lace boyshorts. Tribal-pattern arm cuff accessory.",
    pose_style: "Both arms stretched overhead in morning stretch, torso elongated and twisted. Natural sensuality.",
    expression_style: "Dreamy expression, soft eyes, gentle inviting smile."
  },
  {
    outfit: "Oversized grey tee knotted at one side exposing hip and stomach, black French-cut lace underwear, beaded choker necklace.",
    pose_style: "Leaning forward, one shoulder dropped seductively, hands adjusting hair near exposed hip.",
    expression_style: "Intense focused gaze, pursed lips, exuding confidence."
  },
  {
    outfit: "Form-fitting grey mock-neck crop ending mid-ribcage, black mesh-panel bikini bottoms, delicate dreamcatcher pendant.",
    pose_style: "Profile three-quarters to camera, looking over shoulder, back arched. One arm reaching to touch hair.",
    expression_style: "Mysterious side-glance, raised eyebrow, subtle pout."
  },
  {
    outfit: "Grey baby tee cropped high above waist, black lace thong at hip line, thin gold body chain across stomach.",
    pose_style: "Standing legs apart, hands pulling shirt hem, about to lift higher. Dynamic motion.",
    expression_style: "Teasing expression, tongue touching upper lip, mischievous eyes."
  }
];

// Traditional Native female - sexy modeling version of cultural dress
const traditionalFemaleOutfits = {
  Lakota: [
    {
      outfit: "Sexy beaded doeskin micro-dress with deep V-cut and thigh-high side slits, intricate Lakota geometric beadwork across bust, bare midriff section, matching beaded armbands.",
      pose_style: "Hip cocked to side, one hand running through long flowing hair, shoulders back showcasing beadwork.",
      expression_style: "Proud warrior-princess gaze, lips slightly parted, fierce beauty."
    },
    {
      outfit: "White fringed leather bikini top with elaborate quillwork, matching high-cut fringed bottom, bone hairpipe choker, silver concho belt low on hips.",
      pose_style: "Arms overhead emphasizing toned midriff, one knee bent, fringes swaying.",
      expression_style: "Confident Native beauty queen energy, warm inviting eyes."
    }
  ],
  Cherokee: [
    {
      outfit: "Burgundy velvet crop halter with Cherokee rose beadwork, matching high-waisted thong with shell fringe, tear-drop turquoise earrings.",
      pose_style: "Torso twisted showing curves, one hand at throat, other on hip.",
      expression_style: "Regal elegance mixed with sensuality, knowing smile."
    },
    {
      outfit: "Sexy Cherokee ribbon-shirt style crop top in red with ribbon strips barely covering, black lace bottoms, silver gorget necklace.",
      pose_style: "Leaning back slightly, chest forward, hair flowing.",
      expression_style: "Strong Cherokee beauty, direct confident gaze."
    }
  ],
  Navajo: [
    {
      outfit: "Turquoise and coral beaded bralette with traditional Navajo patterns, matching string bikini bottom, heavy squash blossom necklace framing cleavage.",
      pose_style: "Standing tall with desert-goddess energy, hands on hips, shoulders back.",
      expression_style: "Mysterious southwestern beauty, smoky eyes, soft lips."
    },
    {
      outfit: "Black velvet crop top with silver Navajo buttons down front (several undone), high-cut traditional-print bottoms, concho belt.",
      pose_style: "One hand unbuttoning top further, the other in hair, hip jutted.",
      expression_style: "Seductive southwest model, bedroom eyes."
    }
  ],
  Apache: [
    {
      outfit: "Fringed buckskin bralette with Apache sunrise beadwork, matching fringed micro-skirt barely covering, tin cone dangles accenting movement.",
      pose_style: "Dynamic warrior-woman pose, one arm raised like drawing bow, curves emphasized.",
      expression_style: "Fierce Apache warrior beauty, intense passionate eyes."
    }
  ],
  Comanche: [
    {
      outfit: "Painted leather bustier with Comanche horse motifs, matching loincloth-style bikini bottom with long side fringes, silver arm bands.",
      pose_style: "Wild untamed energy, hair windswept, stance wide and powerful.",
      expression_style: "Free-spirited Comanche beauty, wild passionate gaze."
    }
  ],
  Crow: [
    {
      outfit: "Elk-teeth decorated crop top (teeth forming patterns across bust), matching beaded bikini with geometric Crow designs, elaborate hair-bone ornaments.",
      pose_style: "Elegant elongated pose showing off decorated attire, arms gracefully positioned.",
      expression_style: "Sophisticated Crow beauty, elegant yet alluring."
    }
  ],
  Blackfeet: [
    {
      outfit: "Ermine-trimmed white leather bralette with Blackfeet painted symbols, matching high-cut bottoms with ermine tails, face paint accents.",
      pose_style: "Mystical medicine woman energy, hands raised slightly, otherworldly presence.",
      expression_style: "Spiritual beauty, deep knowing eyes, serene sensuality."
    }
  ],
  Cheyenne: [
    {
      outfit: "Yellow-painted deerskin halter with Cheyenne morning star beadwork, matching painted bikini bottom, bone breastplate worn as necklace between breasts.",
      pose_style: "Morning star rising pose, stretching upward, body elongated.",
      expression_style: "Radiant Cheyenne beauty, warm golden energy."
    }
  ]
};

// Generic traditional female (when tribe not specified)
const genericTraditionalFemale = [
  {
    outfit: "Beaded buckskin bikini top with intricate tribal patterns, matching fringed bottom with shell decorations, bone choker, feathered hair ornaments.",
    pose_style: "Classic Native princess pose, one hand in flowing hair, hip cocked, curves displayed.",
    expression_style: "Proud indigenous beauty, regal yet inviting."
  },
  {
    outfit: "White doeskin micro-halter with geometric beadwork, matching thong with long trailing fringes, turquoise and silver jewelry adorning.",
    pose_style: "Sensual dance-inspired pose, body in motion, fringes swaying.",
    expression_style: "Enchanting ceremonial beauty, mystical allure."
  },
  {
    outfit: "Painted leather bandeau with tribal symbols, matching high-cut bottom with side ties, elaborate beaded breastplate worn as belly decoration.",
    pose_style: "Warrior woman stance, powerful yet feminine, muscles defined.",
    expression_style: "Strong indigenous goddess energy, fierce and beautiful."
  }
];

// ============ MALE OUTFIT TEMPLATES ============

// Modern male - sexy male model look
const modernMaleOutfits = [
  {
    outfit: "Fitted grey henley with sleeves pushed up showing forearms, partially unbuttoned revealing chest, dark fitted jeans, turquoise and leather bracelet.",
    pose_style: "Confident stance, one hand running through hair, other thumbed in pocket. Strong masculine presence.",
    expression_style: "Smoldering intensity, strong jaw set, eyes commanding attention."
  },
  {
    outfit: "Charcoal athletic tank showing sculpted shoulders and arms, grey sweatpants hanging low on hips showing V-line, native-design pendant.",
    pose_style: "Athletic pose, arms slightly flexed, torso twisted to show physique.",
    expression_style: "Confident athlete energy, easy smile with piercing eyes."
  },
  {
    outfit: "Open chambray shirt revealing chiseled abs and chest, dark boxer-briefs, silver and leather cuff, hair slightly tousled.",
    pose_style: "Casually leaning, shirt open and flowing, one hand on belt line.",
    expression_style: "Relaxed masculine confidence, bedroom eyes, slight smirk."
  },
  {
    outfit: "Form-fitting grey v-neck tee stretched across broad chest, fitted dark shorts, beaded anklet, tribal tattoo visible on arm.",
    pose_style: "Standing tall and powerful, arms crossed showing biceps, dominant presence.",
    expression_style: "Strong silent type, intense focused gaze."
  }
];

// Traditional male - sexy warrior/chief modeling look
const traditionalMaleOutfits = [
  {
    outfit: "Bare muscular chest with elaborate bone hairpipe breastplate, fitted buckskin breechcloth showing powerful thighs, war paint accents, feathered arm bands.",
    pose_style: "Powerful warrior stance, chest out, arms at sides showing muscles. Commanding masculine presence.",
    expression_style: "Fierce warrior intensity, proud and powerful, eyes burning with strength."
  },
  {
    outfit: "Single eagle feather in flowing hair, bare oiled chest with battle scars, traditional loincloth-style covering, bone knife at hip.",
    pose_style: "Hunting stance, muscles tensed, body coiled with potential energy.",
    expression_style: "Predator focus, dangerous attractiveness, primal magnetism."
  },
  {
    outfit: "Chief's bone necklace on bare chest, elaborate feather headdress, minimal buckskin covering, face paint in traditional patterns.",
    pose_style: "Regal leader pose, standing tall and proud, ceremonial dignity.",
    expression_style: "Wise leader presence, strong and noble, commanding respect and desire."
  },
  {
    outfit: "Painted war symbols across muscular bare torso, fitted leather pants, coup stick and shield held, warpaint on face.",
    pose_style: "Battle-ready stance, muscles defined, powerful coiled energy.",
    expression_style: "Warrior's fierce gaze, protective strength, magnetic intensity."
  }
];

// Common metadata
const commonMetadata = {
  camera_style: "Waist-up or upper-thigh-up portrait, 3/4 angle or straight-on, shallow depth of field with creamy bokeh.",
  lighting_style: "Soft golden-hour daylight streaming through tall windows, creating warm highlights on skin and gentle cinematic shadows sculpting features.",
  background_style: "Artistic backdrop complementing character - loft with brick walls and tall windows for modern, natural landscape or teepee interior for traditional.",
  framing: "Crop from upper thighs or waist up, showcasing the outfit and pose while maintaining artistic sensuality.",
  inspiration_reference: "High-fashion editorial supermodel aesthetic: sensual, confident, culturally authentic yet undeniably sexy."
};

// Main function to assign appropriate outfit
function assignOutfit(actor, index) {
  const male = isMale(actor);
  const tribe = getTribe(actor);
  const era = getEra(actor);
  const isHistorical = era.includes('1870') || era.includes('1880') || era.includes('1890') || era.includes('1800');
  
  let outfitSet;
  
  if (male) {
    // Male outfits
    outfitSet = isHistorical ? traditionalMaleOutfits : modernMaleOutfits;
  } else {
    // Female outfits
    if (isHistorical || (tribe && actor.bio?.toLowerCase().includes('traditional'))) {
      // Use tribe-specific traditional outfit if available
      if (tribe && traditionalFemaleOutfits[tribe]) {
        outfitSet = traditionalFemaleOutfits[tribe];
      } else {
        outfitSet = genericTraditionalFemale;
      }
    } else {
      outfitSet = modernFemaleOutfits;
    }
  }
  
  // Select from outfit set with variety
  const template = outfitSet[index % outfitSet.length];
  
  return {
    ...template,
    ...commonMetadata,
    // Customize background based on era
    background_style: isHistorical 
      ? "Natural outdoor setting with soft-focus prairie landscape, or intimate teepee interior with firelight creating dramatic shadows."
      : "Industrial loft interior with exposed brick walls, floor-to-ceiling windows with dark curtains partially drawn, soft-focus urban backdrop."
  };
}

// Read the actors file
const actorsPath = path.join(__dirname, 'actors.json');
console.log('Reading actors.json...');
const actorsData = JSON.parse(fs.readFileSync(actorsPath, 'utf8'));

console.log(`Found ${actorsData.data.length} actors to update`);

let maleCount = 0;
let femaleCount = 0;
let historicalCount = 0;
let modernCount = 0;

// Update each actor with appropriate outfit styling
actorsData.data.forEach((actor, index) => {
  const male = isMale(actor);
  const era = getEra(actor);
  const isHistorical = era.includes('1870') || era.includes('1880') || era.includes('1890') || era.includes('1800');
  
  if (male) maleCount++;
  else femaleCount++;
  if (isHistorical) historicalCount++;
  else modernCount++;
  
  const outfitData = assignOutfit(actor, index);
  
  // Update metadata preserving existing fields
  actor.metadata = {
    ...actor.metadata,
    outfit: outfitData.outfit,
    pose_style: outfitData.pose_style,
    expression_style: outfitData.expression_style,
    camera_style: outfitData.camera_style,
    lighting_style: outfitData.lighting_style,
    background_style: outfitData.background_style,
    framing: outfitData.framing,
    inspiration_reference: outfitData.inspiration_reference
  };
});

// Write updated data back
const outputPath = path.join(__dirname, 'actors.json');
console.log('Writing updated actors.json...');
fs.writeFileSync(outputPath, JSON.stringify(actorsData, null, 2), 'utf8');

console.log('');
console.log('✅ Successfully updated all actor outfits with sexy supermodel styles!');
console.log(`   📊 Statistics:`);
console.log(`      - Males: ${maleCount}`);
console.log(`      - Females: ${femaleCount}`);
console.log(`      - Historical era: ${historicalCount}`);
console.log(`      - Modern era: ${modernCount}`);
console.log(`   🎨 Features:`);
console.log(`      - Tribe-specific traditional outfits (Lakota, Cherokee, Navajo, etc.)`);
console.log(`      - Gender-appropriate sexy modeling looks`);
console.log(`      - Era-specific styling (historical vs modern)`);
console.log(`      - High-fashion supermodel aesthetic throughout`);
