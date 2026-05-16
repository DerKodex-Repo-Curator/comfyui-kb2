---
name: Canonical icon prompt templates (single / 2x4 / 4x5 / ideas mode)
description: Verbatim positive-prompt templates and rule locks for Luis's POP UI icon generators. Source - BACKUP for Custom GPTS Cel-Shaded Concept Art Prompt Stylist.txt. Use when building icon runners or assembling icon prompts.
type: reference
---

# Canonical icon prompt templates

**Source:** `ComfyUI/output/Concepts/BACKUP for Custom GPTS_Cel-Shaded Concept Art Prompt Stylist.txt`

This file is the single biggest custom GPT compendium Luis maintains. It bundles five separate generator personas. Reference 18 (`example_house_style.md`) summarizes the look; this file captures the **verbatim prompt templates and rule locks** the icon runner should use when assembling output.

## The 5 personas in this BACKUP

1. **Cel-Shaded Concept Art Prompt Stylist** — turns image/character description into cel-shaded prompt (full body, 3/4 front, white BG)
2. **POP Nano Banana Pro Icon Generator** — conversation-flow icon generator with mode picker (single / 2x4 / 4x5)
3. **SINGLE UI Icon Prompt Generator** — minimal one-icon generator
4. **Multiple Fantasy UI Icon Prompt Generator (20 Icons)** — exact 4x5 contact sheet generator
5. **Fantasy UI Icon Concept Generator** — ideas-only generator (numbered lists, no full prompts unless asked)

These map cleanly to runner patterns: `runners/icon_cel_shaded.py` already implements Modes A and C (single + 4x5). Mode B (2x4) and ideas mode are not yet runners.

## POP Nano Banana Pro Icon Generator — conversation flow

When activated as a chat persona, the GPT asks ONLY:
1. "Which output do you want: single, 2 x 4, or 4 x 5?"
2. After the user picks, "What icon would you like to generate?"

If user provides icon subject without mode -> ask for mode. If user provides mode without subject -> ask for subject. Don't generate prompts until both are known.

**Grid math rule:** Always state count explicitly as `columns x rows = total icons`:
- 2 x 4 = 8 icons total
- 4 x 5 = 20 icons total
- 4 x 6 = 24 icons total

Then enforce EXACTLY that many icons in the prompt.

**Reference image handling:** If user uploads one image, it's the style anchor. If multiple, first image = style anchor, others = optional composition references. **Never say "coin" in the prompt — always say "reference image."**

## Style anchor rules (must be in EVERY icon prompt)

> Use the reference image as style anchor. Match its simplicity, chunky silhouette, bold black outline thickness, minimal inner linework, flat 2D cel shading, and the same 3/4 backward tilt perspective feel. Keep the design as simple as the reference image.

## Perspective rules (must be enforced in every icon prompt)

- Same 3/4 backward tilt as reference
- Top face plane slightly visible
- Bottom-right thickness and shadow plane clearly visible AND larger than top rim
- Silhouette feels leaning back, not flat front-facing
- Tilt consistent across all icons in a contact sheet

## Simplicity rules

- No decorations or accessories
- No micro details, no tiny parts
- No text, no numbers, no symbols, no labels
- **Maximum 3 materials per icon**

## Linework rules

- Bold clean black outer outline
- Inner linework minimal like reference
- **Use only 2 inset inner contour lines total per icon:**
  - One inner rim or thickness break line
  - One inner face or main plate break line
- Optional one very short line only if absolutely necessary to separate one major part
- No texture lines, no engraving, no hatching

## Color vibrance and saturation rules

- Vivid, high saturation, game UI readable
- Clean, punchy hues with strong color separation between materials
- Avoid muted palettes, dusty tones, washed out colors, "realistic" desaturation
- Saturation strong across ALL tones including shadow tones (no gray shadows, no muddy shadows)
- Shadow tone = deeper, richer version of base hue, not neutral gray
- Bright highlight colors and rich, colorful shadows that still read as the same material

## Color and shading rules

- No gradients, no soft blending, no airbrush
- 2D flat colors only
- **Exactly 2 flat tones per material: base and shadow**
- One simple flat highlight shape, one simple flat shadow shape only
- Lighting direction consistent: highlight top-left, shadow bottom-right
- Strong saturation across all colors including shadow tones

## Composition rules

- Centered and oversized
- Fills most of the frame
- Readable at small HUD size
- White background only

## Contact sheet rules (Mode B and Mode C)

- Output is ONE single image that is a contact sheet
- White background only
- Even spacing and margins
- Each cell contains one icon, centered, same scale and framing

## Uniqueness rules for contact sheets

- All icons clearly different at a glance without adding detail
- Uniqueness from BIG simple changes only:
  - Silhouette shape changes
  - Button shape changes
  - Bezel shape changes using only simple big shapes
  - Material palette changes
- No tiny features for uniqueness
- No near-duplicates
- If two designs look similar, push silhouette difference

## The avoid line (must be at end of EVERY icon prompt)

```
Avoid gradients, soft shading, blending, airbrush, extra inner lines, extra markings, face tick marks, numbers, letters, engravings, texture lines, hatching, rivets, studs, gears, chains, straps, wings, horns, skulls, cracks, runes, emblem plates, extra attachments, background props, glow, particles, drop shadows, watermarks, muted colors, washed out colors, gray shadows, muddy shadows, low saturation.
```

This is THE canonical avoid line. It's the most precise negative-style declaration Luis has refined. Every icon runner should append it verbatim.

## Mode A — Single icon Positive Prompt Template (verbatim)

```
Chunky simplified medieval fantasy game UI icon of [ICON SUBJECT], 3/4 view with a slight back tilt, bold black outer outline, minimal thin inner lines only for major seams, overlaps, openings, and big plane breaks, hard cel shading with exactly 2 flat tones per material, strong vibrant saturated colors including shadows (no muted shadows), top left highlight and bottom right shadow, clean white background, centered, oversized, not cropped, no ground shadow, no cast shadow on the background.
```

Replace `[ICON SUBJECT]` only. Keep everything else.

## Mode C — 4x5 Contact Sheet Positive Prompt Template (verbatim)

```
Chunky simplified medieval fantasy RPG UI icon contact sheet showing exactly 20 unique icons of [ICON SUBJECT] in a 4 x 5 grid (4 columns x 5 rows = 20 icons total). Global consistency lock across all icons: identical camera distance and zoom, identical straight-on 3/4 view with a slight back tilt, identical outline thickness, identical lighting direction (top-left highlight, bottom-right shadow), identical shading rules, identical rendering style, and the same clean white background across the entire sheet. Absolute layout lock: clean evenly spaced grid, consistent gutters, identical padding per cell. Each icon is centered, fully visible, not cropped, and scaled oversized to fill about 80-90% of its cell with consistent padding. 2D flat cel-shaded rule: flat 2D icon look (not 3D), hard cel shading with exactly 2 flat tones per material region (base + shadow), NO gradients, no soft shading, no texture grain, no micro details. Vibrant saturation rule: highly saturated vibrant colors only, bold jewel tones and rich warm tones, no muted or washed-out colors, shadows stay saturated and colorful. Outline rule: bold black outer outline on every icon. Extreme minimalism: each icon uses only 2-4 big flat shapes total, 0 inner lines preferred, 1 inner line maximum only if unavoidable and it must taper off thick-to-thin-to-nothing (coin-style), never full internal outlines. Medieval fantasy theme: forged metal, carved wood, stitched cloth, rope, wax seals, heraldry, simple runes, gemstones/bone/horn as flat shapes only. Content restrictions: object-only, no people, no silhouettes, no paws, no faces, no text or numbers. Uniqueness lock: every cell is a clearly different [ICON SUBJECT] concept with a distinct silhouette and identity; no duplicates, no near duplicates, no recolor-only variants, avoid similar adjacent designs. Use reference images for composition, scale and render style.
```

Replace `[ICON SUBJECT]` (appears 3 times — replace all).

## Mode B — 2x4 Contact Sheet (8 icons)

The BACKUP file does not include a verbatim 2x4 template. Synthesize one by taking the Mode C template and replacing:
- `20 unique icons` -> `8 unique icons`
- `4 x 5 grid (4 columns x 5 rows = 20 icons total)` -> `2 x 4 grid (2 columns x 4 rows = 8 icons total)`
- Add: include an 8 item variation list written left to right, top to bottom

Each variation list item must be a big simple variation, not a detail upgrade.

## Mode C variation list rule

When outputting Mode C, also include a 20-item variation list written left to right, top to bottom. Each item is a BIG simple variation, not a detail upgrade. Examples:

> 1. tall narrow tower silhouette, stone material
> 2. short wide squat silhouette, wood material
> 3. round circular silhouette, metal material
> ...etc

## Cel-Shaded Concept Art Prompt Stylist (full character template)

For cel-shaded character prompts (not icons), the canonical full-body template is:

```
Create a full-body [character type] in cel-shaded 2D art. Match the reference composition: squat chibi build, centered in frame, arms relaxed and slightly bent, 3/4 front view, white background. [Character physical description]. Outfit: [clothing]. Pose: [attitude or expression]. Render with clean, tapered inner line art (5-7 px), 2 tone cel shading, hard-edged, saturated colors. Avoid 3D/plastic or airbrushed gradients; no photorealism, no rim light. Maintain character composition, identity, proportions, and crisp edges. Thick black outlines. use the reference images as a guide for render style.
```

Behavior rules for this persona:
- When user uploads image, immediately offer "prompt a 2D Cel-Shaded 2 tone Art version"
- If user says "preserve composition" or asks for edit, include: "Preserve the original composition, pose, and framing."
- Default hint: 2K resolution where relevant
- When describing colors, always include approximate hex codes: e.g., "bright red (#FF3B30)"

## Fantasy UI Icon Concept Generator (ideas-only mode)

This persona outputs **numbered idea lists, not full prompts**, unless the user asks for prompts.

**World setting reminder:** "Bipedal animal and mythical creature medieval fantasy world. Main adventurer is a Shiba hero in a side scrolling game."

**Format rules:**
- Numbered lists, one line per idea, no long descriptions
- No contact sheets unless explicitly asked

**Friend system special logic** (Friends, Friend Requests, Suggested Friends, Blacklist):
- Offer 12 to 20 options
- Include 3 "most instantly readable" options at the top

**Materials mode:** If user asks for materials, output materials only. If they ask for tiers (Common, Rare, Epic, Legendary), group by tier.

**Hard constraints (honor when stated):**
- "no paws" -> don't use paws
- "no silhouettes" -> don't use silhouettes
- "object only" -> no characters or faces

## Apply this when building runners

For `runners/icon_cel_shaded.py` (already exists):
1. Mode A flag: `--mode single` -> use Mode A verbatim template, replace `[ICON SUBJECT]`
2. Mode B flag: `--mode 2x4` -> synthesize 2x4 template + 8-item variation list
3. Mode C flag: `--mode 4x5` -> use Mode C verbatim template + 20-item variation list
4. Always append the canonical avoid line at end
5. If `--reference <path>` provided, the prompt already says "Use the reference image as style anchor..."; pass the image to the loader node
6. Default output: white background, no ground shadow

The prompt is **input** to whatever generator backend the runner uses (Nano Banana via NanoBanana2Direct node, or Z-Image Turbo for free local generation, or Qwen-Image for highest quality). The style locks are model-agnostic — they belong in the prompt regardless of backend.

## When the user asks for icon ideas (no mode picked)

Respond as the Fantasy UI Icon Concept Generator: numbered list of 12-20 ideas, top 3 marked as "most instantly readable." Don't generate prompts unless asked.
