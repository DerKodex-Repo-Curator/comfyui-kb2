---
name: NPC Roster framework — frog/fox/snake style
description: Visual rules for generating NPC roster characters (helpers, merchants, healers, etc.) for the side-scrolling RPG. Source: "You are Roster Prompt Stylist_V2.txt". Distinct from enemies (ref 22) and biomes (ref 23).
type: reference
---

**Source:** `ComfyUI/output/Concepts/You are Roster Prompt Stylist_V2.txt`.

NPCs are the **non-hostile characters the player encounters** during travel — merchants, healers, innkeepers, oracles, scholars, etc. NPCs are anthropomorphic (frog/fox/snake style). This is **DISTINCT** from enemies (which are explicitly NOT anthropomorphic per ref 22).

## Three character categories per request

For every NPC request, the framework generates THREE design categories:

1. **ANIMAL VERSION** — clear anthropomorphic animal NPC (fox, raccoon, badger, owl, beaver, etc.). One strong animal choice that supports the role. Animal-like, NOT "human with animal ears."
2. **ANIMAL HYBRID VERSION** — combines TWO compatible animal traits (deer-rabbit healer, otter-ferret merchant, fox-owl scholar). Simple readable hybrid, one clean silhouette.
3. **CREATURE VERSION** — most unique/magical interpretation. Strange, mythical, invented. NOT a hybrid, NOT a normal animal. Examples: crescent-bodied oracle seer, soft potion-spirit healer, living bundle-of-pouches merchant, cozy hearth-spirit innkeeper.

For each category, generate **4 prompt sections:**

1. SIMPLIFIED PROMPT — SINGLE IMAGE
2. SIMPLIFIED PROMPT — 8 IMAGE SHEET
3. CHIBI INFLUENCED PROMPT — SINGLE IMAGE
4. CHIBI INFLUENCED PROMPT — 8 IMAGE SHEET

## Style guide block (every prompt opens with this)

```
Use the attached frog / fox / snake roster image as a STYLE GUIDE ONLY for render style, shape language, simplicity, line economy, and overall mobile game readability. Do NOT use it as a base design for the character itself. Match the reference image's clean simplified 2D cartoon render style: bold black outline, very limited inner line work, rounded appealing shapes, clean silhouette, simple facial features, hard 2 tone cel shading, and bright readable colors. The final character must feel like it belongs in the same roster as those reference characters.
```

## Style locks

- **Direction:** facing LEFT in 3/4 left-facing view, head turned LEFT, eyes and pupils looking LEFT (NOT looking at camera)
- **Background:** pure white (#FFFFFF)
- **Resolution:** 2K
- **Render:** clean stylized 2D cel-shaded 2-tone art, strong black outlines (#000000), hard-edged shadows, vibrant saturated colors (including shadows), very few inner black lines, large readable shapes, no tiny clutter
- **Outline:** thick black outlines (#000000)
- **Required phrase in every prompt:** *"Prompt a clean stylized 2D Cel Shaded 2 tone Art version with strong black outlines."*

## NPC Cuteness Control Rule (CRITICAL)

**NPCs should NOT default to cute/friendly/babyish.** They should feel like world inhabitants the player encounters — NOT cheerful pets, plush toys, or eager helpers.

Avoid defaulting to:
- Huge innocent eyes
- Constant happy smiles
- Tiny helpless bodies
- Baby-like faces
- Overly rounded harmless expressions
- Excited welcoming poses
- Cute mascot energy
- Childlike proportions
- Adorable plush-toy personality
- Every NPC looking sweet and helpful
- Every NPC looking like they want to be liked

Use varied NPC attitude: neutral, aloof, busy, practical, transactional, mildly annoyed, unimpressed, skeptical, reserved, focused, tired, mysterious, watchful, stern, quietly confident, eccentric, self-interested, calm, detached.

**Benchmark:** the frog barter character — appealing and readable, but NOT overly cute, NOT eager, NOT bubbly, NOT trying to charm the player. Feels like a creature with its own priorities.

Chonky proportions are fine — but chonky should NOT mean baby-like. Chonky = bold, readable, compact, sturdy, stylized. NOT infantile.

## Role-based expression guidance

| Role | Expression / personality |
|---|---|
| Merchant / Shopkeeper / Barter | Transactional, self-contained, practical, mildly interested, skeptical, sly, neutral, unimpressed, busy. May be friendly but not always. |
| Reward Distributor | Proud, self-important, showy, transactional, pleased with their own treasure, mildly smug, neutral. NOT purely cheerful. |
| Innkeeper | Warm but grounded, tired, practical, observant, patient, busy, quietly watchful. |
| Healer / Cleric | Calm, composed, focused, empathetic but NOT overly sweet, spiritual, reserved, quietly serious. |
| Oracle | Mysterious, unreadable, serene, detached, solemn, cryptic, watchful, neutral, selectively helpful. |
| Blacksmith / Armorer | Focused, rugged, tired, practical, busy, stern, dependable, mildly impatient. |
| Quest Giver / Guide | Helpful, cautious, serious, curious, guarded, neutral. |
| Hermit / Traveler / Wanderer | Detached, eccentric, weathered, thoughtful, distracted, quietly helpful. |
| Arena / Battle Master | Authoritative, stern, proud, unimpressed, commanding, confident. |
| Disguised Noble | Guarded, politely distant, secretive, observant, calm, faintly suspicious. |
| Scholar / Archivist | Focused, distracted, analytical, reserved, mildly annoyed by interruption, quietly curious. |
| Builder / Carpenter | Busy, practical, focused, satisfied with their work, mildly distracted, matter-of-fact. |

## Body language rule

NPCs should NOT all stand in cheerful toy-like poses. Use role-appropriate posture:

- Relaxed but guarded
- Standing with purpose
- Busy with a task
- Hanging out / leaning on a prop
- Offering an item without enthusiasm
- Reading / working / watching the player
- Sitting or resting
- Cross-armed calmly observing
- Mid-barter gesture
- Reserved stance with subtle attitude
- Slightly slouched from work
- Holding a prop casually
- Looking mildly interrupted
- Quietly waiting

## Chonky proportion rule

Default chonky proportions:
- Big rounded head
- Compact torso
- Short thick limbs
- Broad blunt paws/hands
- Large readable props
- Strong big-medium-small shape hierarchy
- Toy-like mobile game silhouette
- Sturdy grounded body mass

For CHIBI INFLUENCED prompts, push proportions further:
- Huge rounded head
- Tiny compact body
- Extra short thick limbs
- Larger rounded cheeks/face shapes
- Oversized readable props
- Extra rounded silhouette
- Still NOT babyish unless the user explicitly asks

Chibi influenced ≠ infantile / helpless / extra cute. It means stronger shape exaggeration for readability.

## 8-image sheet rule (CRITICAL)

The 8 IMAGE SHEET prompt must generate **EXACTLY 8 character variations** in a clean **4×2 contact sheet** layout (4 across top row, 4 across bottom row). NO extra characters, NO bonus poses, NO mini figures, NO duplicate small characters, NO icon-like side characters.

**Required sentences in every 8-image-sheet prompt:**

```
Create exactly 8 total character variations arranged in a clean 4x2 contact sheet, with 4 characters on the top row and 4 characters on the bottom row, no extra characters, no bonus poses, no additional mini figures.
```

```
Preserve the same level of polish and readable detail as the single image version; do not turn the characters into tiny simplified thumbnails.
```

Each of the 8 variations:
- Full body
- Large enough to see costume details
- Facing LEFT in 3/4 left-facing view
- Head turned LEFT, eyes and pupils looking LEFT
- Centered in its own space, evenly spaced
- Fully visible, NOT cropped
- Pure white background (#FFFFFF)
- NO labels, NO text, NO extra characters

The 8 variations explore: different body types, scaled proportions, complimentary palettes, clothing variations, props, silhouette emphasis, expressions, personalities — but stay connected as the SAME role family.

## Role-specific prop requirements (for 8-image sheets)

Every variation must clearly show the role through visible props:

- **Healer:** potions, herbs, bandages, charms, pouches
- **Merchant:** goods, parcels, potion bottles, bags, oddities
- **Innkeeper:** keys, ledgers, towels, cozy clothing, inn tokens
- **Armorer:** helmets, shields, armor pieces, padded aprons, gear tools
- **Reward Distributor:** treasure, coins, gems, prize items, reward containers
- **Oracle:** vision symbols, prophecy props, crescent motifs, seeing-eye motifs, divination objects
- **Builder:** beams, planks, measuring tools, mallets, aprons, work pouches

Use **large readable details**, NOT tiny detail.

## Magic rule (NPCs)

Magic reads through:
- Color blocking, symbols, props, emblems, potions, charms
- Surface markings, solid shape design
- Unusual silhouette, mythical body forms

DO NOT use: glow, aura, sparkles, floating symbols, mist, smoke, vapor, energy trails, light bloom (unless user explicitly requests).

## Eye direction rule

**Eyes ALWAYS face LEFT with visible pupils.** Do NOT use:
- Constant happy smile
- Eager grin
- Baby-like innocent eyes
- Smug / smirk / sly grin (unless appropriate)
- Sinister expression (unless requested)
- Blank eyes / pupil-less eyes / glowing eyes
- Forward-facing eyes on a left-facing body

## Color rule

Vibrant colors with hard 2-tone cel shading. Complimentary palettes per role:

| Role | Palette |
|---|---|
| Healer | Cream, teal, coral, soft pink, red HP potion, blue MP potion, green herbs |
| Innkeeper | Burgundy, forest green, cream, warm brown, muted gold |
| Merchant | Blue, teal, tan, gold, colorful goods |
| Armorer | Slate blue, charcoal, bronze, dull steel, tan |
| Reward Distributor | Rich blue, red, gold, purple, gems |
| Disguised Noble | Taupe cloak, purple clothing, gold accents, jewel color |
| Builder | Chestnut, navy apron, tan wood, teal markings |
| Oracle | Midnight blue, lavender, pale cream, gold, moonlit teal, deep violet |
| Scholar | Indigo, parchment tan, warm brown, muted brass, pale blue accents |

Avoid making every design green-heavy or maroon-heavy. Use variety.

## Negative style rules

Avoid: photorealism, 3D render, painterly rendering, gradients, soft airbrush, glow, bloom, emissive eyes, emissive cracks, internal light, floating magic effects (unless requested), sparkles (unless requested), smoke, vapor, mist, tiny item clutter, busy trim, realistic texture, realistic fur, realistic metal texture, background scenes, furniture, shop stalls (unless requested), architecture, text labels, weapons (unless requested), human hands, human faces, forward-facing eyes on left-facing body, excessive black inner linework, overly cute mascot energy, baby-like proportions, constant happy smiles, eager helper expression, adorable plush-toy personality.

For 8-image sheets, also avoid: more than 8 characters, extra rows, extra columns, bonus characters, duplicate mini figures, icon-like side characters, decorative props that look like additional characters.

## Reference image roles

| Reference type | Role |
|---|---|
| Style guide image | Render style and simplicity ONLY. Don't copy character design. |
| Character reference image | Character identity, build, clothing, props. Don't copy exactly — redesign into roster style. |
| Expression reference image | Attitude / facial mood ONLY. Don't copy character design. |
| Prop / outfit reference image | Item or clothing inspiration ONLY. |

## How runners should apply this

When building `runners/roster_npc.py`:
1. CLI: `--role <role_name>` (healer, merchant, etc.) or `--description "<text>"`, `--reference <path>` (style anchor), `--variant {animal, hybrid, creature, all}` (default: all three)
2. For each variant, generate the SIMPLIFIED + CHIBI-INFLUENCED prompts
3. Optional `--mode {single, 8sheet}` (default: single; 8sheet uses the 4×2 grid pattern)
4. Always inject the verbatim style guide block, the cuteness-control rule, the role-specific palette, and the role-appropriate expression guidance
5. NEVER make NPCs anthropomorphic-as-an-enemy by accident — that's the enemy framework (ref 22), not roster
