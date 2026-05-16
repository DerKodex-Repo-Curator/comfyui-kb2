---
name: Enemy / monster variant framework (the studio)
description: Visual rules and prompt structure for generating ENEMIES and MONSTERS for the side-scrolling RPG. Source: CharacterDesigner_V4.txt. Distinct from NPC roster (ref 24) and hero character.
type: reference
---

**Source:** `ComfyUI/output/Concepts/CharacterDesigner_V4.txt` (Luis's GPT framework, V4).

This is for generating **enemies / monsters / bosses** that the player fights, NOT for NPC roster characters (see `references/24_roster_npc_framework.md`) and NOT for the player character (the Shiba hero).

## Hard rules (the don't-violate-these list)

### Direction
- **Enemies face LEFT** in a 3/4 left-facing view (the Shiba hero approaches from the left)

### Anthropomorphism — NOT for enemies
**Enemies are NOT anthropomorphic.** This contradicts the NPC roster rule. Enemies must read as magical monsters, NOT as animal warriors / beastfolk. Specifically banned:
- Animal heads on humanoid bodies
- Upright animal warriors
- Beastfolk adventurers / fantasy classes
- Animal-person silhouettes
- Familiar real-world beasts (bear, wolf, lion, tiger, panther, gorilla, hound, boar)
- Generic enchanted-animal-with-magic looks

### Default creature bias
Default to weird magical monsters: cursed beings, shrine horrors, relic entities, possessed forms, folklore creatures, abstract aberrations, dungeon-born creatures, animated objects (cursed candles, ritual masks, lantern parasites, shrine bell beasts, etc.)

### Allowed body plans
- Humanoid monster (still must read as monster, not adventurer)
- Hunched, crawling, floating, blob-like
- Many-limbed, serpentine, asymmetrical
- Object-creature, squat dungeon beast, living mass, hovering entity
- Non-natural quadrupedal form

### Hand rule
3 fingers + thumb (consistent with the world).

### NO human skull rule
No realistic human skulls, no undead human skull faces, no human cranium helmets. If a skull motif is used, it must be a non-human creature/relic/fantasy-anthropomorphic skull.

### NO anthropomorphic rule (enemy-specific)
Humanoid silhouettes are allowed but they must clearly read as inhuman, magical, cursed, masked, or ritualistic, NOT as a normal humanoid playable race or class character.

## Design principles

### Single gimmick rule
Each enemy is built around ONE strong readable gimmick (giant eye, lantern heart, floating mask, ritual bell body, crystal spine, slime body, shrine halo, etc.). Don't stack many equal ideas.

### Mystical anchor + danger accent
Every enemy has:
- ONE clear **mystical anchor** integrated into the body (lantern heart, crystal growths, fungal antlers, shrine mask, glowing relic chest). Avoid floating objects around the character.
- ONE clear **danger accent** (hostile eyes, claws, fangs, sharp weapon edges, glowing corruption seams, horns, unstable magical core)

### Combat role visual communication
Designs should visually communicate role: ranger / brute / caster / assassin / sentinel / summoner.

### Shape language
- **Triangle/angular** = aggressive, dangerous, predatory
- **Square/blocky** = strong, defensive, brute-like
- **Rounded** = magical, unstable, strange

### Silhouette test rule
If filled with solid black, the silhouette should still communicate identity and threat (head shape, weapon read, shoulder/mantle, limb proportions, mystical anchor).

### Head-and-mantle silhouette
Many strong enemies derive identity from the head/shoulders/mantle/fur mass: antlers, long fur or hair mass, ritual collars, bark crowns, horned masks, branch-like protrusions, draped robes, oversized shoulders, tail-like bead strands.

## Style anchor

- Clean stylized 2D cel-shaded 2-tone art
- Thick black outlines (#000000)
- Hard-edged shadows
- Saturated colors (including shadows)
- Clean tapered inner line art (5-7 px)
- White background (#FFFFFF)

**Avoid:** 3D rendering, photorealism, painterly gradients, plastic surfaces, rim lighting, futuristic/sci-fi/robotic elements, mech armor, cyborg limbs, glowing tech cores.

**Materials palette:** bark, bone, stone, fungus, crystal, cloth, leather, relic metal, roots, chitin, feathers, volcanic rock, enchanted wood, magical flame, sacred light, cursed growths.

### Mandatory phrase
"Prompt a clean stylized 2D Cel-Shaded 2 tone Art version with strong black outlines and simple color blocking."

## Variant generation rules

### 50% faithful rule
When given a reference creature, variants should remain ~50% faithful to the original — preserve core creature identity, base anatomy, primary silhouette idea, weapon type, core magical identity. Modify armor style, materials, magical features, danger accents, biome influence, faction styling, secondary silhouette, color palette.

### Biome adaptation
If a biome is provided, adapt the creature so it feels native (materials, magical effects, mystical anchor expression, danger accents, color palette, cultural flavor).

Biome example mutations:
- **Forest** → bark armor, moss growth, leaf mantles, seed/root magic
- **Swamp** → algae growth, fungal patches, lantern organs, toxic slime
- **Volcanic** → obsidian armor, magma cracks, furnace hearts, ash cloth
- **Desert** → sandstone armor, bone relics, dried wraps, sun-baked shell
- **Crystal** → crystal growths, reflective shards, glowing crystal cores, prismatic energy

### Power escalation
Variant escalation modifies existing elements rather than replacing — stronger mystical anchor, heavier armor, larger weapon, more intense magical glow, dominant ritual identity. Should still feel like the same enemy family.

### Possession / evil influence
Enemy concepts should often feel altered by an external hostile force (curse, possession, relic influence, shrine corruption, biome mutation, parasitic transformation, ritual alteration, abyssal influence). This affects anatomy, silhouette, eye expression, mystical anchor, danger accents, materials, posture.

## Output format

Always return TWO prompts in this order:

1. **SIMPLIFIED PROMPT** — main production variant
2. **CHIBI-INFLUENCED PROMPT** — slightly more stylized while still reading as enemy

The chibi-influenced version uses cleaner shapes, slightly rounder forms where helpful, simplified armor geometry, exaggerated enemy features for clarity. NOT full chibi proportions, NOT cute, NOT mascot-like.

## Prompt structure

Open with:
- Full-body hostile enemy or boss
- Facing LEFT in 3/4 left-facing view
- Centered in frame
- Pure white background (#FFFFFF)
- Clean stylized 2D cel-shaded 2-tone art
- Thick black outlines (#000000)
- Readable side-scrolling silhouette

Then describe:
- Creature identity (faithfulness to original concept)
- Biome/material adaptation (if relevant)
- Mystical anchor
- Danger accent
- Combat role
- Key negative constraints

Close with bias statement:
- Favor weird magical creatures, cursed entities, relic beings, shrine monsters, folklore horrors, possessed forms, magical aberrations
- Negative: do not create animal-person, beastfolk warrior, humanoid animal, anthropomorphic fantasy creature, or familiar natural beast silhouette

## Eye style
- Simple stylized eyes
- Bold shapes, strong contrast, readable hostile expressions
- NOT realistic human eyes, NOT complex iris detail, NOT glossy anime eyes

## Inhuman face rule
Heads/faces strongly favor inhuman monster identity:
- Beast skull masks, carved wooden faces, horned masks, eyeless masks
- Glowing eye slits, spirit faces, elongated heads, ritual helmets
- Bone or bark visages, abstract non-human facial structures

NOT ordinary human faces, NOT friendly mascot faces, NOT cute creature faces, NOT conventional heroic character faces.

## How runners should apply this

When building `runners/enemy_variant.py`:
1. Read this reference for the enemy-specific rules (don't apply NPC roster rules from ref 24)
2. Default output is TWO prompts (Simplified + Chibi-Influenced)
3. CLI: `--reference <enemy_image>` for variant of existing enemy; `--biome <biome_name>` for biome adaptation; `--description "<text>"` for text-only concept
4. Always inject the verbatim style anchor ("clean stylized 2D Cel-Shaded 2 tone...") and the no-anthropomorphic / no-human-skull / inhuman-face rules
