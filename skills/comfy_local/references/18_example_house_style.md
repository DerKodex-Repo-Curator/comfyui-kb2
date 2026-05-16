---
name: Luis's house style — the studio game asset visual rules
description: Compiled style locks per asset type (UI icons, characters, props, biomes). Source: Luis's custom GPT prompt frameworks in G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\ComfyUI\output\Concepts\
type: reference
---

Luis works on a **side-scrolling medieval fantasy game** with **anthropomorphic animal characters**. The main hero is a **Shiba**. The game style is mobile-friendly, chibi-friendly, vibrant, hand-painted.

All work breaks into four asset categories, each with its own visual style. **Do not mix styles across categories** — icons must be cel-shaded with bold outlines; props must be painterly with NO outlines. These are not interchangeable.

## 1. UI icons (cel-shaded, chunky)

**Style locks:**
- Chunky simplified medieval fantasy RPG UI icon style
- Bold black outer outline
- 2D flat cel shading — EXACTLY 2 flat tones per material (base + shadow)
- NO gradients, NO soft blending, NO airbrush, NO texture grain, NO micro details
- Inner lines: 0 preferred, 1 maximum, must taper coin-style (thick → thin → disappears)
- 3/4 view with slight back tilt (top face plane slightly visible, bottom-right thickness larger than top)
- Top-left highlight, bottom-right shadow (consistent across set)
- Vibrant saturation — bold jewel tones; **shadows must be saturated, never gray/muddy**
- 2-4 large flat shapes only (extreme minimalism)
- Centered, oversized (~80-90% of cell), white background
- Object-only — NO people, NO faces, NO silhouettes, NO paws, NO text/numbers/letters
- Maximum 3 materials per icon

**Modes:** Single icon, 2×4 grid (8 icons), 4×5 grid (20 icons). Grids are ONE single contact-sheet image with even spacing.

**Materials palette:** forged metal, carved wood, stitched cloth, rope, wax seals, heraldry/crests, simple runes, gemstones/bone/horn (as flat shapes only).

**Avoid line (always include in negative/style-lock):** "Avoid gradients, soft shading, blending, airbrush, extra inner lines, extra markings, face tick marks, numbers, letters, engravings, texture lines, hatching, rivets, studs, gears, chains, straps, wings, horns, skulls, cracks, runes, emblem plates, extra attachments, background props, glow, particles, drop shadows, watermarks, muted colors, washed out colors, gray shadows, muddy shadows, low saturation."

## 2. Characters (cel-shaded chibi)

**Style locks:**
- Cel-shaded 2D, 2-tone art
- Squat chibi build, full body, centered
- 3/4 front view, arms relaxed and slightly bent, white background
- Clean, tapered inner line art (5-7 px width range)
- 2-tone cel shading, hard-edged, saturated colors
- **Thick black outlines** (icon outline rule applies)
- Avoid 3D/plastic, no airbrushed gradients, no photorealism, no rim light
- Maintain identity, proportions, crisp edges

**On preserve composition:** "Preserve the original composition, pose, and framing."

**Hero / mascot:** the Shiba is the player character. Other characters are anthropomorphic mythical creatures.

## 3. Props (painterly 2D, NO OUTLINES)

**Critical:** props are NOT cel-shaded. They use the OPPOSITE outline rule from icons.

**Style locks:**
- Painterly 2D fantasy game prop art (mobile-game polished prop sheet quality)
- Soft hand-painted rendering, rounded simplified forms
- 2-3 tone value grouping with subtle light-to-shadow transitions
- **NO outlines** of any kind, NO black contour lines, NO ink lines, NO comic outlines, NO anime line art
- Use shape, value, color separation, painted edge control only
- Soft controlled painted shading, gentle highlights
- Broad readable planes, no harsh cel shaded segmentation
- NO photorealism, NO PBR, NO plastic 3D, NO rim light, NO bloom, NO texture noise

**Color rules:** vibrant + saturated INCLUDING shadow tones. NEVER gray dead shadows. NEVER muddy browns unless intentional. Hex codes when describing colors.

**Perspective:** shallow side-scrolling-friendly prop perspective. Slight backward tilt only when it improves readability. NOT top-down, NOT bird's-eye, NOT extreme foreshortening. Front rim/face should read more prominently than top surface (for bowls, basins, wells, tables, platforms, roofs, pools).

**Base:** stable, grounded, obviously sitting on a flat horizontal gameplay plane. Don't float unless requested.

**Material translation:**
- Wood: broad painted planes, simplified grain logic, stylized carved feel
- Stone: chunky carved forms, broad planes, softened edges
- Cloth: simple grouped folds, soft transitions
- Metal: stylized painted, controlled highlights, NOT mirror realism
- Water: soft luminous painted surface, NOT glossy 3D
- Crystal/magic: soft magical color accents, painterly internal light, NOT sci-fi

**Default background:** pure white for isolated props.

## 4. Biomes (painterly side-scrolling environments)

**Style locks:**
- Painterly 2D illustration with visible broad gouache brush strokes
- Soft gradients and rounded simplified forms with strong silhouette readability
- Wide side-scrolling composition (left to right)
- **Flat horizon, perfectly straight sky line** — no curvature, no fisheye, no perspective tilt
- Clear horizontal layer separation: foreground / playfield / midground / background / sky
- Flat ground plane and clear readable playable lane
- Objects recede with distance: lower contrast, softer edges, lighter values
- NO hard outlines, NO photorealism, NO futuristic elements
- NO clutter on the ground unless requested
- NO characters unless requested
- NO UI, NO text, NO symbols, NO logos
- Vibrant color lock — saturated including shadow tones

**Composition defaults (CONFIRMED canonical 2026-05-09 by Luis):**
- Aspect ratio: **3:4 portrait** — this is the production standard. Older 21:9 references in workflows are obsolete. The 4:3 in `forest.json` was non-canonical (one-off variation, not the standard). All NEW biome work should use 3:4.
- See `references/23_biome_creation_framework.md` for the full V11 ruleset
- Playfield lane height: 24-32% of image height
- Foreground height limit: 12-18% of image height
- Playfield must remain perfectly flat and unobstructed

**Statue/carved figure rule:** any statues, busts, stone carvings, reliefs, monument figures, or sculpted characters that appear in the environment **must always depict anthropomorphic creatures, never humans**. Animal skulls allowed if biome-appropriate; human skulls NEVER allowed. Statues must feel integrated into the world's mythical animal civilization.

**Reference image hierarchy:**
- Design blueprint references → control composition: horizon height, big shape placement, path placement, major prop placement, mood
- Style bible references → control render style and materials only: brushwork, paint planes, foliage clustering, stone/wood planes, edge softness, lighting treatment
- Conflict resolution: design controls layout, style bible controls rendering

**Reference image opening line (always use when refs are provided):**
"Using the uploaded reference images only as strict references, generate a high quality hero shot BIOME environment for a chibi friendly 2D side scrolling medieval fantasy game in a wide 3:4 side scrolling composition."

**Common issue patches Luis has built up:**
- White lane edge band → "No boundary stripe, no bright border strip, no white band at the top or bottom edge of the lane. Lane edges are defined only by natural value and texture transition."
- Midground blocks background → require background visibility across most of the width
- Lanterns don't read → dusk/early-night lighting lock; "Lanterns are the brightest elements in the frame. Background remains dim and cool."
- Leaves too big → ban large paddle leaves, require smaller leaflet breakup

## Universal rules across all asset types

- Approximate hex codes always included when describing colors (e.g., "bright red (#FF3B30)")
- Vibrant saturation, NO muted/washed-out palettes
- Shadows colored, not gray
- No watermarks, no glow/particles unless requested
- All prompts should be production-ready (copy/paste into Nano Banana or a CLIPTextEncode node)

## Production pipeline (current, as of 2026-05)

1. **Generation:** Nano Banana Pro (Google Gemini 2.5 Image) is Luis's primary backend. He has three Nano Banana custom nodes installed: `nano_banana_direct_pkg`, `nanobanana_multilayer`, `nanobanana_style_transfer`. Recent outputs in `ComfyUI\output\nano_banana_pro_*.png`.
2. **Cleanup / parallax slicing:** Photoshop downstream. Many `.psd` files in his output folder show this is the standard finishing step.
3. **Hero shots, not tiles:** biomes are generated as ONE big illustration; parallax layers are cut later in PS.
4. **Reference-driven:** he heavily uses style-anchor images. The Nano Banana node accepting reference images is core to his workflow.

## How to apply when building runners

- For ICONS → cel-shaded style lock + bold outline + 2-tone + white bg + 3/4 back tilt
- For CHARACTERS → cel-shaded chibi + thick outline + full body 3/4 + white bg
- For PROPS → painterly + NO outlines + 2-3 tone + soft shading + white bg
- For BIOMES → painterly gouache + 21:9 + layer separation + flat horizon + anthropomorphic statues only

When in doubt about a style choice, **read the corresponding source GPT prompt file** in `ComfyUI\output\Concepts\` directly. There are version-numbered iterations (V1 → V11 in some cases) showing how Luis refined each style framework over time. **The latest numbered version is canonical.**

Source files (most recent canonical versions):
- Cel-Shaded master: `BACKUP for Custom GPTS_Cel-Shaded Concept Art Prompt Stylist.txt`
- Character: `CharacterDesigner_V4.txt`
- Props/Objects: `object_rules.txt`
- Biomes: `You are Tower Biome Promptsmith_V11.txt`
- Roster (multi-character): `You are Roster Prompt Stylist_V2.txt`
