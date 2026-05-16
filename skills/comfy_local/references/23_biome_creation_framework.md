---
name: Biome / environment creation framework (V11)
description: Latest biome generation rules for the side-scrolling RPG. Source: "You are Tower Biome Promptsmith_V11.txt". Supersedes earlier 21:9 biome conventions.
type: reference
---

**Source:** `ComfyUI/output/Concepts/You are Tower Biome Promptsmith_V11.txt` (Luis's V11 — latest version of his biome framework).

**Important:** This V11 uses **3:4 portrait** aspect ratio, NOT the 21:9 I had previously documented in `references/18_example_house_style.md` § Biomes. V11 supersedes that. The older 21:9 hero-shot convention may still apply for some workflows but **3:4 portrait is the current default for biome generation.**

## Default scene rules

- **Aspect ratio:** 3:4 portrait
- **Camera:** straight side-scrolling side view, NOT top-down, NOT tilted ground plane, NOT fisheye, NO horizon curvature
- **Camera target:** the playfield (NOT the foreground)
- **Camera distance:** pulled back substantially — feels clearly zoomed out and spacious. Show significantly more environment above and behind the playfield than a neutral shot.
- **Composition layers (back to front):**
  - Sky
  - Far background
  - Mid background
  - Midground structures
  - **Playfield** (centered to slightly above center — main horizontal combat lane)
  - **Lower foreground** (clearly beneath the playfield as a separate band, occupies about bottom quarter)
- Major scenery sits behind the playfield, must NOT block gameplay readability

## Style rules

- **Painterly 2D illustration** — NOT polished splash-art rendering, NOT vector-clean edges
- **Broad gouache painterly brushwork is mandatory**
- **Visible large hand-painted brush masses are mandatory**
- Broad shape-based rendering, grouped value masses, soft painted transitions, simplified readable forms
- Clear silhouettes for side-scrolling combat readability

**Avoid:**
- Thin fussy rendering, micro-detail noise
- Polished splash-art, vector-clean edges, airbrushed plastic
- Hard outlines, black contour lines, comic line art
- Photorealism, futuristic elements
- Top-down angle, tilted ground plane, fisheye, horizon curvature
- Text, UI, logos
- Characters (unless explicitly requested)

## Chonk rules (V11-specific)

When the user asks for "chonk" / "chunky forms" / "extreme chonk":

- Selective form exaggeration **only where it improves readability, charm, scale clarity, or gameplay silhouette strength**
- Chonk = thicker, broader, heavier, puffier, more simplified massing with less spindly detail and more visual weight
- **Apply to:** tree trunks, root masses, canopy clumps, bushes, mushrooms, rocks, boulders, cliffs, ruins, platforms, bridges, arena structures, shrine bases, carved silhouettes, major prop masses
- **Don't:** inflate every object equally; let chonk block the combat lane; merge depth layers
- **Strongest in midground/playfield-adjacent**, lighter in far background, controlled in lower foreground
- Small detail clusters should usually simplify rather than enlarge

## Color rules

- Favor rich, vibrant, controlled color
- Do NOT let the image become muddy, chalky, washed out, gray-killed, dirty, or desaturated
- Preserve hue separation between major materials and major depth layers
- Keep shadows colorful, NOT flat gray
- Playfield must have the clearest color readability
- Lower foreground supports composition without overpowering
- Background steps back via softer contrast, lighter values, softer edges, less texture density

## Lighting rules

- **Always include a lighting block** in the prompt
- **Default lighting:** soft neutral outer lighting with subtle warm influence from the upper right and very soft cool notes in shadow-facing planes
- Lighting supports shape readability, color separation, painterly depth
- Do NOT use neon, bloom, magical glow, or extreme stylized lighting unless explicitly requested

## Distance rules

- Objects recede with distance through: lower contrast, softer edges, lighter values, less texture density, simpler brush grouping
- Background layers feel more atmospheric and less dominant than the playfield

## Statue rule

- Any statues, carvings, busts, reliefs, or monument figures must depict **anthropomorphic creatures**, NOT humans
- Human statues, human faces, realistic human anatomy, and human skulls are NOT allowed
- Statues remain readable, stylized, must NOT block the playfield

## Required final line

**Every biome prompt must end with exactly:**
```
Maintain vibrant color saturation throughout including shadows.
```

## Reference image rule

If the user provides reference images, **begin the prompt with this exact line:**

```
Using the uploaded reference images only as strict references, generate a high quality 3:4 biome environment for a chibi friendly 2D medieval fantasy side scrolling game. Use the references to guide layer treatment, depth placement, spatial hierarchy, camera framing, playfield placement, lower foreground placement, and overall color balance. The camera must be centered on the playfield and pulled back substantially. The playfield must sit centered to slightly above center as the main horizontal combat lane. The lower foreground must remain clearly beneath it as a separate band and must occupy about the bottom quarter of the image. All major scenery must sit behind the playfield without blocking gameplay readability. Preserve a broad gouache painterly look with visible hand painted brush masses, soft painted transitions, large shape based rendering, rich controlled color, clear hue separation, and vibrant saturation throughout including shadows.
```

Then add a "Reference roles must be obeyed" header with these rules:

- **Design blueprint references control:** playfield placement, playfield height, lower foreground placement/height, horizon height, side framing masses, major background landmark placement, overall layer stack
- **Style bible references control:** broad gouache brushwork, visible paint masses, paint plane handling, foliage grouping, stone and wood treatment, edge softness, color balance, hue separation, saturation handling, lighting treatment
- **Conflict resolution:** design controls layout, style bible controls rendering and color treatment
- Do NOT copy exact silhouettes, exact layout, exact tree shapes, rock shapes, statue silhouettes, or prop placement

## Description-only mode

If the user says "description only" or "do not reference directly," include this exact sentence in the prompt:

```
This is a new image based on the written description below. Do not copy any exact layout from any reference.
```

Do NOT use the word "recreate."

## Palette summary rule

Every biome prompt should include a palette summary that defines:
- Dominant biome colors
- Secondary support colors
- Accent colors
- Temperature balance
- How the playfield separates from the lower foreground
- How the playfield separates from the background

## Final prompt structure (V11 canonical order)

```
Title
Core instruction line (the "Using the uploaded reference images..." line if refs exist)
Overview
Reference roles must be obeyed
Primary goal
Non negotiable style and camera
Color and mood
Palette summary
Material translation rule
Layer priority
Layer order back to front:
  Sky
  Far background
  Mid background
  Midground structures
  Playfield
  Lower foreground
Lighting
Distance rules
Safety locks and exclusions
Final line: "Maintain vibrant color saturation throughout including shadows."
```

## Fix-lock library (use only when needed)

Common patches Luis has accumulated through iteration:

- **Needs more chonk** → "Push selected biome forms toward extreme chonk with thicker, broader, heavier massing..."
- **Chonk too global** → "Do not apply chonk evenly to everything..."
- **Chonk blocking gameplay** → "Keep the playfield and traversal lane clear and readable..."
- **Too polished** → "Push the image toward broad gouache painterly brushwork..."
- **Playfield too low** → "Raise the playfield so it sits centered to slightly above center..."
- **Camera too low** → "Center the camera on the playfield instead of the foreground..."
- **Too zoomed in** → "Pull the camera back much farther..."
- **Foreground too small / too dominant** → corrective sentences for each
- **Colors too muddy** → "Use rich, vibrant, controlled color with stronger hue separation..."
- **Shadows lifeless** → "Keep shadows colorful and temperature-aware..."
- **Depth layers blending** → "Strengthen color separation between lower foreground, playfield, and background..."
- **Background too strong** → "All layers behind the playfield must be softer, lighter, less contrast-heavy..."
- **Scene too top-down** → "Straight side-scrolling side view. No top-down angle..."
- **Lane edge too artificial** → "No white band, no hard border stripe, no artificial highlighted divider..."

## Apply this when building runners

When building `runners/biome_painterly.py`:
1. Default aspect ratio = 3:4 (NOT 21:9 — that's old)
2. CLI: `--biome <name>` (e.g., "forest", "swamp", "volcanic"), `--reference <path>` for style anchor, `--blueprint <path>` for composition reference, `--chonk-level {none,subtle,extreme}`
3. Build the prompt in V11's canonical order
4. Always end with "Maintain vibrant color saturation throughout including shadows."
5. If references provided, open with the verbatim "Using the uploaded reference images..." line
