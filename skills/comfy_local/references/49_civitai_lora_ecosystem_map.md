---
name: civitai LoRA ecosystem map — verified picks by base model and use case
description: Curated LoRA findings from a real API browse against Luis's account (2026-05-09). Top picks per base model, ecosystem patterns observed, mapping to Luis's the studio asset categories. Also: top creators, Wan video motion LoRAs, and what civitai DOES vs DOESN'T have for game art.
type: reference
---

# civitai LoRA ecosystem map

**Method:** Ran `civitai_browse_v2.py` against Luis's API key on 2026-05-09. ~32 API calls, ~700 LoRA records collected and filtered for game-art relevance (cel-shaded / painterly / fantasy / cartoon / anthropomorphic — excluding photorealism / NSFW / detail-fixers / human-person LoRAs).

Reference 48 has the abstract API guide. This reference is the *actual curated picks* + what I learned about the LoRA ecosystem shape per base model.

---

## Ecosystem patterns observed

1. **Civitai's text search is brittle.** Free-text queries like `cel shaded` return almost nothing because creators don't put those phrases in titles. **Tag-based filtering is far more reliable.** Use `tag=style|concept|character|environment|clothing|poses|vehicle` to slice the catalog.

2. **Each base model has a distinct LoRA ecosystem culture:**

| Base model | Dominant content | Use for Luis's work |
|---|---|---|
| **Flux.1 D** | Realism, detail enhancers, NSFW, Midjourney-aesthetic transfers | Anthropomorphic fantasy, isometric assets, fantasy concepts. Use Flux LoRAs in `qwen_t2i_lightning.py` / `flux2_t2i.py` runners |
| **Pony** | Multi-style toolkits (645K-download tier!), anime artists, NSFW. Richest "art style" ecosystem | Cel-shaded with strong outlines, vector art, fantasy character styles |
| **Illustrious** | Modern anime artist styles (2024-2025 era post-Pony), cel-shaded, Asian artist styles | Anime/cartoon characters, cel-shading-with-soft-colors |
| **SDXL 1.0** | Largest backlog (Pixel Art, character design helpers, Disney franchise LoRAs) | Pixel art, character design sheets, multi-perspective helpers |
| **Qwen-Image** | **Empty.** No LoRAs surfaced via API search. Ecosystem hasn't migrated yet | Use ai-toolkit to train your own. No civitai community lore exists |
| **Wan Video** | 100% motion-effect I2V LoRAs (not style LoRAs) — animations, transformations | Animate static character art via `wan_t2v.py` once i2v DiT is downloaded |

3. **The "World Morph" pattern is interesting.** Several recent LoRAs are tagged for biome/scene transformation across multiple base models in one file (`F.1D/K9B/Chroma/Illu/Z-Image`) — meaning the same `.safetensors` works for Flux 1, Klein 9B, Chroma, Illustrious, AND Z-Image. These are flagged below.

4. **Articles API endpoint (`/api/v1/articles`) is dead** as of 2026-05-09 — returns 404 for all queries. Articles still exist on the web UI but no longer have a public API. To research training tutorials and workflow shares, browse civitai.com/articles directly in browser.

5. **Top creator by volume is `malcolmrey`** with 817 models. Other prolific creators: bionagato (92), donjo (59), CrasH (43), TallAndGreen (36), DSlater (34), allendimetri (23), harmonicdiffusion (18). The list reflects model count, not necessarily quality — but malcolmrey's huge catalog is worth a browse for variety.

---

## TIER 1 — Direct hits for the studio asset categories

### Character design sheets (Luis's `--mode sheet`)

- **`id=100435` Character Design Sheet (HELPER) (3-PERSPECTIVES)+(COLOR)** — SDXL — **95,361 downloads**. Multi-perspective character sheets with color separator. Direct application to `runners/character_cel_shaded.py --mode sheet`. Tags: lora, cartoon, game character, girls, characters.
- **`id=368139` character sheet** — Pony — 28,241 downloads. Generic "character sheet" LoRA for Pony.

### Anthropomorphic NPC roster (Luis's frog/fox/snake style)

- **`id=800718` Anthropomorphic Fantasy DnD Illustrations [FLUX/Pony]** — **1,511 dl**. Trigger: `In the style of anthr0dnd`. Identified in v1 browse as the strongest anthro match. Multi-base.

### UI icons (Luis's `runners/icon_cel_shaded.py` style)

- **`id=2280495` Flux_2D game UI Flat Vector style** — **229 dl**. No trigger — activates from LoRA load. Description matches icon style verbatim.
- **`id=120096` Pixel Art XL** — SDXL — **109,469 dl**. Pixel art is a different aesthetic than your house style but useful if you want a pixel-art asset path.
- **`id=124609` Logo.Redmond** — SDXL — 72,624 dl. Logo style. Could be used for badge/seal icons.
- **`id=176555` Harrlogos XL** — SDXL — 34,045 dl. Custom text generation in SD — useful for icons that need readable text.

### Painterly biomes / environments (Luis's `runners/biome_painterly.py` aesthetic)

- **`id=1169932` Background - Arcane 2 [FLUX] LoRA** — Flux — **696 dl**. **Arcane (Netflix) painterly aesthetic** — closest civitai LoRA to your V11 painterly biome target. Trigger: `Arcane Background`.
- **`id=757504` DevinElleKurtz - Style [FLUX] LoRA** — Flux — 421 dl. Popular fantasy landscape artist's style. Trigger: `DevinElleKurtz`.
- **`id=1441966` Artify's Fantastic Flux Landscape Lora V2.0** — Flux — 1,378 dl. Fantasy landscape. Trigger: `artilands02`.
- **`id=20412` Wakfu Environments** — Flux — 2,259 dl. Wakfu (French animated game) cel-shaded environments. Closer match for cel-shaded biome work than Arcane.

### "World morph" biome LoRAs (multi-base — Flux/Klein/Chroma/Illustrious/Z-Image!)

These are unusual: ONE `.safetensors` file works across multiple model families.

- **`id=1890368` Crystal Plague (World Morph/Style) [F1D/K9B/Chrm/Illu/ZImg]** — 335 dl. Trigger: `CrystalPl4gu3`. Crystallized-everything biome morph.
- **`id=2498950` Lotus Mountain - World Morph [F.1D/K9B/Chroma/Illu/Z-Image]** — 152 dl. Trigger: `l0tus`. Asian-inspired mountain biome.
- **`id=2563277` Seeping — Bioluminescent World Morph** — 215 dl. Trigger: `s33ping`. Bioluminescent everything.

Worth testing with `runners/zimage_t2i.py` AND `runners/qwen_t2i_lightning.py` since they support Z-Image and Flux respectively.

### Fantasy character + magical NPCs

- **`id=599757` Velvet's Mythic Fantasy Styles [Flux+Pony+Illustrious]** — **199,644 dl**. Multi-base fantasy art. Trigger: `SharpL1nes`. Top-rated relevant LoRA found.
- **`id=308147` Fantasy Wizard & Witches** — Flux — **21,414 dl**. Trigger: `hkmagic`. Wizard/witch concept LoRA for magical NPCs.
- **`id=810000` NEW FANTASY CORE [ILL-FLUX-PONY-SDXL]** — Flux — 21,821 dl. Multi-base fantasy concept LoRA.
- **`id=210095` Wizard's Vintage Comic Book Cover** — Flux — 16,915 dl. Comic-book-cover-style fantasy.

### Isometric game asset / level design

- **`id=1063807` F1 Isometric 3D medieval building and Props Design** — Flux — 478 dl. Isometric medieval buildings + props. **DIRECT GAME ASSET PIPELINE LoRA.**
- **`id=1062259` F1 Isometric 3D Grid, Tile, Cube, Block Design** — Flux — 294 dl. Same author. Isometric tiles/blocks — for tile-based maps.
- **`id=347185` Whitebox Style SDXL - Environment & Level Design Concept Art** — SDXL — 677 dl. White-box level design (greybox/whitebox stage of game environment design).
- **`id=1054335` XL Hades Isometric Grid Map, Tile Map, Level, Scene** — SDXL — 535 dl. Hades-game-style isometric maps.
- **`id=1052283` XL FFTA Isometric Grid Map** — SDXL — 429 dl. Final Fantasy Tactics Advance isometric.

---

## TIER 2 — Style accessories worth knowing about

### Cel-shaded / flat-color anime adjacent

- **`id=180891` Flat Colour Anime** — Flux — 25,036 dl. Trigger: `Flat colour anime style image showing...`. Closest "flat color" Flux LoRA.
- **`id=128568` Cyberpunk Anime Style** — Flux — 39,989 dl. Cyberpunk + anime. Trigger: `anime`.
- **`id=295100` Aesthetic Anime LoRA** — SDXL — 28,889 dl. Generic aesthetic anime.
- **`id=721039` Retro Anime Flux - Style** — Flux — 22,952 dl. 80s/90s retro anime.
- **`id=830230` Comic book | Tome 1** — Flux — 23,993 dl. Comic book style.
- **`id=858800` Illustration | Tome 1** — Flux — 22,311 dl. Generic illustration.

### Pony power-tools (essential when running Pony for any aesthetic)

- **`id=264290` Not Artists Styles for Pony Diffusion V6 XL** — **645,410 dl** (highest-downloaded LoRA in this whole survey). Trigger: `abstractionism, brush stroke, traditional...`. Multi-style toolkit. **Essential when running Pony.**
- **`id=888250` Vixon's Classic Art Styles - detailed painting** — Pony — 38,658 dl. Classical painted art.
- **`id=888231` Vixon's Pony Styles - gothic neon** — Pony — 98,841 dl. Gothic neon style.

### Illustrious power-tools (essential when running Illustrious)

- **`id=929497` Aesthetic Quality Modifiers - Masterpiece** — Illustrious — **110,007 dl**. The canonical "masterpiece, best quality" booster. Always include when running Illustrious.
- **`id=971952` Stabilizer IL/NAI/CK** — Illustrious — **146,248 dl**. Image stability booster for Illustrious base. Always include.
- **`id=176554` 薄塗り / USNR STYLE** — Illustrious — 82,076 dl. Trigger: `usnr`. Japanese "thin coating" illustration style — could be cel-shaded-adjacent.
- **`id=362745` CAT - Citron Styles** — Illustrious — 101,170 dl. Multi-style toolkit.

### SDXL slider helpers

- **`id=122359` Detail Tweaker XL** — SDXL — **421,746 dl**. The canonical SDXL detail slider. Use with negative strength to simplify, positive to add detail.
- **`id=402462` Detail Slider LoRA | PonyXL SDXL** — Pony — 58,439 dl. Pony version of same.
- **`id=438059` Dynamic Poses slider PONYXL** — Pony — 35,357 dl. Pose dynamism slider.
- **`id=1105685` Dramatic Lighting Slider** — Pony — 59,167 dl.
- **`id=468146` Body Type Slider - Pony / Illustrious** — 68,505 dl.

---

## Wan 2.1 I2V motion LoRAs (animate a still character image)

Wan video LoRAs on civitai are almost ALL **image-to-video motion effects** — they take a still image and animate it with a specific motion. Once Luis downloads the Wan i2v DiT (currently only t2v is installed per ref 07), these would be useful for animating cel-shaded characters into action shots.

| ID | Effect | Downloads |
|---|---|---|
| 1346623 | 360 Degree Rotation (Microwave Rotation) | 20,364 |
| 1340141 | Squish Effect | 7,531 |
| 1408239 | Wan2.1 Camera Controls (panning, dolly, etc.) | 3,962 |
| 1348626 | Flying Effect | 3,922 |
| 1475368 | Bullet Time | 3,201 |
| 1344147 | Cakeify Effect | 2,826 |
| 1379629 | 360 Camera Orbit | 2,686 |
| 1375382 | Super Saiyan Transformation | 2,426 |
| 1409524 | 360DegreeTracking | 2,016 |
| 1445917 | Strong Wind | 1,862 |
| 1369426 | Westworld Robot Face Reveal | 1,594 |
| 1346480 | Inflate Effect | 1,567 |
| 1360349 | Particalize (dissolve/disintegrate) | 1,479 |
| 1344298 | Deflate Effect | 1,478 |

Pattern: `Wan2.1 [Effect Name] (I2V LoRA)` with a randomized trigger word like `r0t4tion`, `sq41sh`, `c4k3`, etc. To use: stack with the Wan i2v DiT, point at the still image, generate.

---

## Practical picks for Luis's POP house style

If Luis wanted to download just 5-7 LoRAs to start experimenting with right now, the recommended starter set is:

**For Flux runners (qwen_t2i_lightning, flux2_t2i, qwen_edit_lightning):**
1. **id=100435** — Character Design Sheet HELPER (multi-perspective character sheets — drop into `--mode sheet`)
2. **id=800718** — Anthropomorphic Fantasy DnD (NPC roster)
3. **id=2280495** — Flux 2D game UI Flat Vector (icons)
4. **id=599757** — Velvet's Mythic Fantasy Styles (overall fantasy aesthetic)
5. **id=1169932** — Arcane Background (painterly biome reference)
6. **id=1063807** — F1 Isometric 3D medieval (game asset / map work)

**Bonus for Pony runs (if you want a cel-shaded path through Pony):**
7. **id=438813** — Flat Vector Art PDXL (verified in ref 48 v1 browse, 1,830 dl)
8. **id=264290** — Not Artists Styles (power-tool multi-style)

**Bonus for Illustrious:**
9. **id=971952** — Stabilizer IL (always-on quality booster)
10. **id=929497** — Aesthetic Quality Modifiers (always-on quality booster)

---

## What civitai DOES vs DOESN'T have for game art

**HAS:**
- Character design sheet helpers (95K-download tier)
- Fantasy art style LoRAs (Velvet's, Mythic Fantasy Core, Wizard & Witches)
- Isometric game asset LoRAs (Hades-style, FFTA-style, generic medieval)
- Wan video motion-effect LoRAs (lots, all I2V)
- Pony/Illustrious power-tools (sliders, stabilizers, masterpiece boosters)
- World morph LoRAs (multi-base biome transformers)
- Comic book / illustration style LoRAs

**DOESN'T HAVE (or very thin):**
- Cel-shaded LoRAs that actually call themselves "cel shaded" — find via tag `style` or browse Pony's "Drawn On" / "Flat Vector Art PDXL" instead
- Painterly / gouache biome LoRAs at scale — Arcane LoRA is the closest, world morph LoRAs are second
- Qwen-Image LoRAs (community hasn't migrated)
- Z-Image LoRAs as a categoriy (only world morphs that include Z-Image)
- Genuinely anthropomorphic / furry LoRAs that match Luis's tone (anthr0dnd is the rare on-target hit)
- Wan 2.1 t2v style LoRAs (only motion effects)
- Curated "POP-style" or any single-studio-style LoRA Luis could drop in

This is why **training your own POP house-style LoRA via ai-toolkit** is the right long-term play (per ref 45). Civitai gives you bridges and inspiration, not a perfect drop-in.

---

## How to use a downloaded LoRA in Luis's runners

Standard pattern — insert `LoraLoaderModelOnly` between the model loader and the sampling-shift node:

```python
"lora_pop": {
    "class_type": "LoraLoaderModelOnly",
    "inputs": {
        "model": ["model_loader", 0],
        "lora_name": "anthr0dnd_v2_flux.safetensors",  # filename in G:\models\loras\
        "strength_model": 0.85,
    },
},
"shift": {
    "class_type": "ModelSamplingAuraFlow",
    "inputs": {"model": ["lora_pop", 0], "shift": 3.0},   # was ["model_loader", 0]
},
```

If using Lightning LoRA + style LoRA together (e.g., on `qwen_t2i_lightning.py`), chain them:

```python
"lora_lightning": {... existing Lightning LoRA ...},
"lora_pop_style": {
    "class_type": "LoraLoaderModelOnly",
    "inputs": {
        "model": ["lora_lightning", 0],
        "lora_name": "Velvet_Mythic_Fantasy_flux.safetensors",
        "strength_model": 0.7,
    },
},
"shift": {
    "class_type": "ModelSamplingAuraFlow",
    "inputs": {"model": ["lora_pop_style", 0], "shift": 3.0},
},
```

**Strength tuning rule of thumb:** start at the LoRA's recommended strength from its civitai card (usually 0.7-1.0). Style LoRAs often work at 0.5-0.8 to avoid overpowering. Concept LoRAs (specific things like wizards) usually want 0.85-1.0.

---

## Refreshing the data

`civitai_browse_v2.py` lives at the project root. Re-run anytime:

```powershell
cd G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install
python civitai_browse_v2.py
```

Edit the `base_models`, `structural_tags`, or `article_queries` arrays in the script to add new searches. Output goes to `.civitai_results_v2/` (gitignored).

The articles section is currently 404'd — if civitai restores `/api/v1/articles` or moves it to `developer.civitai.com`, update the script's endpoint accordingly.
