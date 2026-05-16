---
name: the studio game world context
description: World setting, characters, asset categories Luis is producing for his the studio side-scrolling fantasy game
type: reference
---

Luis works at the studio (<maintainer-email>). His ComfyUI work is for a specific game project.

## Game setting

- **Genre:** Side-scrolling 2D medieval fantasy mobile game
- **World:** Anthropomorphic animal/mythical creature civilization (no humans depicted)
- **Player character:** A Shiba (the hero/main adventurer)
- **Tone:** Chibi-friendly, vibrant, charming, mobile-game polished
- **Camera:** Side-scrolling, hero-shot illustrations later sliced for parallax layers in Photoshop

## CRITICAL: three distinct character categories — DIFFERENT visual rules

Luis's game has **three distinct character types**, each with its own visual rules. **Do not mix the rules across categories.**

| Category | Anthropomorphic? | Direction | Style |
|---|---|---|---|
| **Hero (Shiba)** — player character | YES, anthropomorphic bipedal warrior | **Faces LEFT** (Luis's universal convention — ALL characters face left in his pipeline) | Cel-shaded |
| **Enemies / Monsters** — what the Shiba fights | **NO — explicitly NOT anthropomorphic.** Magical monsters, cursed beings, relic entities, shrine horrors, possessed forms. NOT animal warriors / beastfolk. | **Faces LEFT** | Cel-shaded — see `references/22_enemy_monster_framework.md` |
| **NPCs / Roster** — helpers, merchants, oracles, etc. | YES, anthropomorphic. Frog/fox/snake style. Three sub-variants: Animal / Animal Hybrid / Creature | **Faces LEFT** | Cel-shaded — see `references/24_roster_npc_framework.md` |

**Universal rule (confirmed 2026-05-09 by Luis):** "Anything I create faces LEFT." This is a hard pipeline convention — Luis flips the asset in Photoshop downstream if the game needs it facing right. So every runner that generates characters should bake "facing LEFT in 3/4 left-facing view, head turned LEFT, eyes and pupils looking LEFT" into the positive prompt regardless of asset type.

**Statues in biomes** must be anthropomorphic creatures (NEVER humans) — see `references/23_biome_creation_framework.md`. This is independent of the enemy rule.

**The hero is NOT an enemy and NOT an NPC.** The Shiba is the player's character — a bipedal warrior, anthropomorphic, the camera-target. The CharacterDesigner GPT is for generating *enemies* the Shiba fights (variants), not for generating Shiba's design.

## Asset categories he's actively producing

Based on his `ComfyUI\output\` folder structure as of 2026-05-09:

### Characters (chibi anthropomorphic)
- Hero (Shiba), monster eggs, pets
- Specific recent character work: jerboa, owl_librarian, mole2, mouse, pillows
- See `references/18_example_house_style.md` § Characters for the visual rules

### UI icons (cel-shaded)
Full categories visible in output:
- Feature icons: dungeon dive, mounts, PvP, mounts friendship
- Object icons: runestone, scroll, mallet, gauntlet, tower, marketplace
- Status effect icons: ice, weaken
- Frame/decorative icons: mount startup frame
- Pack/bundle icons: pet egg pack, starterpack
- Rank icons: my_rank_icon
- Specific named: ignore_dominion, scroll_feather, peteggpack
- See `references/18_example_house_style.md` § UI icons for the visual rules

### Props / objects (painterly)
- Relics, rune stones, keys, outfits, scrolls
- See `references/18_example_house_style.md` § Props for the visual rules

### Biomes / environments (painterly 21:9)
- Tower Battle Biome (one of the canonical biome types he's iterated on through V11 versions of the Promptsmith)
- Generated as wide hero shots, then sliced in Photoshop
- See `references/18_example_house_style.md` § Biomes for the visual rules

## Key creative collaborators in his pipeline

- **ChatGPT custom GPTs** for prompt engineering (CharacterDesigner V1-V4, Tower Biome Promptsmith V1-V11, Roster Prompt Stylist V1-V2, Cel-Shaded Concept Art Stylist, Prop Promptsmith via object_rules.txt, Fantasy UI Icon Concept Generator, Fantasy Prop Builder)
- **Nano Banana Pro** (Google Gemini 2.5 Image) as primary generation backend
- **ComfyUI** with Nano Banana custom nodes for in-ComfyUI generation
- **Photoshop** for cleanup, layer separation, parallax slicing

## What the runners we build should target

1. **Style preservation:** every runner must respect the cel-shaded vs painterly distinction per asset type. Don't accidentally apply Style A rules to Style B assets.
2. **House style parameters baked in:** the verbose prompt frameworks Luis uses ARE production-tested. Runners should preserve them as positive-prompt scaffolds rather than simplifying.
3. **Reference-image input:** Nano Banana takes reference images as style anchors. Runners should accept reference image paths.
4. **Approximate hex codes:** when Luis describes colors, he wants hex codes in the prompt. Runners should accept hex inputs.
5. **Aspect ratio defaults:** icons square (1:1), characters 1:1 or 3:4, props 1:1 (white bg isolation), biomes 21:9 (hero shots).
6. **Output organization:** ComfyUI's output folder is already structured by asset name (`output/icon_*`, `output/pet_concepts/`, `output/relics/`, etc.). Runners should drop into the matching subfolder.

## Hard constraints (the "must never" rules across his world)

- No human characters, faces, or skulls
- All anthropomorphic figures must be animal/mythical, never human
- Statues in biomes must be anthropomorphic creatures, never humans
- No paws on icons (he explicitly bans this — he wants symbol-only icons)
- No text, letters, numbers in icon imagery
- No futuristic / sci-fi elements
- No PBR / 3D plastic look
- No muted palettes, gray shadows, or muddy tones
