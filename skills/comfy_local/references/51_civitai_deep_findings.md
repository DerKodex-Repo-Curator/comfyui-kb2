---
name: civitai deep findings — patterns from re-mining the pulled data
description: Second-pass synthesis from the existing civitai data pulls. Resolution canonicals, creator portfolios worth following, multi-base LoRAs, trigger word patterns, prompt grammar conventions per base model. No new API calls — all from data already on disk in .civitai_results/, .civitai_results_v2/, .civitai_workflows_v3/.
type: reference
---

# civitai deep findings

Synthesized from data already on disk. Reference 49 mapped the LoRA ecosystem; reference 50 mapped the workflow recipe patterns. This goes one layer deeper into both, plus adds individual-recipe study and prompt grammar.

**Method:** mined three local data caches (`.civitai_results/`, `.civitai_results_v2/`, `.civitai_workflows_v3/`) for cross-cutting patterns. No new API calls.

---

## 1. Resolution canonicals (community winners)

From 56 top-engagement workflow images, the resolutions that win likes are:

| Resolution | Count | What it indicates |
|---|---|---|
| **832×1216** | 18 (32%) | **THE Flux/SDXL portrait canonical** — 13:19 aspect, the reigning standard for character work |
| **1024×1024** | 14 (25%) | Square — used heavily for icons, concepts, single-subject shots |
| **896×1440** | 3 | Tall portrait — 14:22.5, used for full-body cinematic |
| **1024×1536** | 3 | Tall portrait — 2:3 |
| **896×1152** | 1 | Pony canonical — 7:9 |
| **768×1344** | 2 | Tall portrait at lower res |
| **1216×832** | 1 | Landscape variant of 832×1216 |
| **2204×2844** | 1 | Upscaled high-res output |
| **1080×1920** | 1 | 9:16 phone wallpaper |
| **512×512** | 2 | Legacy SD 1.5 size |

**Implication for Luis's runners:** my runners default to `1024×1024` (icons) and `3:4` portrait (characters/biomes). The community converges on **`832×1216`** for character work. Worth adding `832×1216` as an option to `runners/character_cel_shaded.py` since that's the size top community character workflows use.

## 2. Creator portfolios worth following

Cross-referencing v2's broad LoRA sweep, top creators by relevant-model count:

| Creator | LoRA count | Specialty | Why follow |
|---|---|---|---|
| **denrakeiw** | 12 | Vehicles, clothing, outfits, Flux LoRAs | Prolific multi-base creator |
| **Remade** | 10 | **Wan2.1 I2V motion-effect LoRAs** (Deflate, Inflate, Squish, Westworld, etc.) | THE motion-LoRA author — owns most of the Wan video animations |
| **ntc** | 8 | Slider LoRAs ("extremely detailed", "crowd of people", "dark dramatic chiaroscuro") | Slider specialist — every workflow benefits from his sliders |
| **AIDigitalMediaAgency** | 8 | Flux style LoRAs, FLUX [pro] series, Midjourney mimics | Top-tier Flux author, one of their LoRAs hit the top-10 community workflows |
| **klaabu** | 7 | Sliders (Dramatic Lighting, Pony Realism, Real Skin) | Counterpoint to ntc — different slider styles |
| **Deformer_Toby** | 6 | **Video game style LoRAs** (Elden Ring, Shadow of the Colossus, Bleak Faith, etc.) | **Direct relevance for Luis's game art aesthetic** — these are the game-style-transfer LoRAs |
| **YeiYeiArt** | 4 | **Created the Character Design Sheet HELPER (id=100435, 95K dl)** + Disney character LoRAs | Author of the most-relevant LoRA for Luis's character runner |
| **WhiteCaliberFox** | 5 | Illustrious artist-style LoRAs (Reppjongg, Soraawoolf, Bad Shade) | Modern Illustrious cel-shaded artist styles |
| **cyberAngel_** | 6 | Honkai/Genshin character LoRAs | Anime character specialist |
| **ButtleKneck45** | 7 | Cartoon character LoRAs (Caldina, Cleo, Fifi la Fume) | Disney/Looney Tunes era characters |

**Bookmark for follow-ups:** **Deformer_Toby** for game-aesthetic transfers (Elden Ring particularly relevant), **YeiYeiArt** for character design tools, **Remade** for video animation effects, **ntc** for slider toolkit.

## 3. Multi-base LoRAs (single .safetensors works on multiple model families)

These ship as ONE file but the author trained against multiple base models so the LoRA generalizes across them. Useful when you don't know which base you'll be running:

| ID | Name | Bases supported | Downloads |
|---|---|---|---|
| **599757** | Velvet's Mythic Fantasy Styles | Flux + Pony + Illustrious | 199,644 |
| **632900** | Warhammer 40K Space Marines | Flux + Pony + Illustrious | 30,776 |
| **245889** | Dissolve Style | FLUX + SDXL + SD1.5 | 26,388 |
| **332248** | Dynamic Poses | FLUX + SDXL | 19,066 |
| **800718** | Anthropomorphic Fantasy DnD | FLUX / Pony | 1,511 |
| **1890368** | Crystal Plague (World Morph) | **F1D + K9B + Chroma + Illustrious + Z-Image** | 335 |
| **2498950** | Lotus Mountain (World Morph) | **F1D + K9B + Chroma + Illustrious + Z-Image** | 152 |
| **2563277** | Seeping (Bioluminescent World Morph) | (multi — naming pattern matches above) | 215 |

**The 5-base "World Morph" LoRAs are unusual.** A single `.safetensors` file works against Flux 1, Klein 9B, Chroma, Illustrious, AND Z-Image. The author re-trained the same concept against five different base models and concatenated. Especially compelling for Luis because they support both Flux AND Z-Image which his runners use.

## 4. LoRAs surfacing across MULTIPLE search buckets (cross-cutting community favorites)

| ID | Name | Buckets | Downloads |
|---|---|---|---|
| 411088 | Detailed Perfection style | **6 buckets** | 118,507 |
| 599757 | Velvet's Mythic Fantasy Styles | 5 buckets | 199,644 |
| 580857 | Realistic Skin Texture style | 5 buckets | 154,786 |
| 200255 | Hands XL | 4 buckets | 284,195 |
| 212532 | All Disney Princess XL | 4 buckets | 196,390 |
| 468146 | Body Type Slider (Pony/Illustrious) | 4 buckets | 68,505 |

When a LoRA appears in 4+ search buckets, that's the strongest signal of community value.

## 5. Trigger word naming patterns (from 368 LoRA records)

| Pattern | Count (% of total) | Examples | When to use |
|---|---|---|---|
| **No trigger** | 135 (37%) | Style activates from LoRA load alone | Pure-style LoRAs, slider LoRAs |
| **Descriptive** | 97 (26%) | "cel shading", "flat color", "anime style" | Style descriptors that double as English text |
| **CamelCase** | 56 (15%) | `SharpL1nes`, `TinkerWaifu` | Character / unique concept identifiers |
| **Composite** | 42 (11%) | `score_9, score_8_up, masterpiece` | Pony/Illustrious quality-tag bundles |
| **Leetspeak** | 38 (10%) | `anthr0dnd`, `hkmagic`, `sq41sh`, `c4k3` | Deliberately rare tokens to avoid collisions |

**When training your POP house-style LoRA**, the **leetspeak pattern** is the safest choice — `pop_h5tyle` won't collide with any natural English usage. The CamelCase pattern works too but `popStyle` could activate accidentally if someone writes about Pop Art styles. Avoid descriptive triggers for proprietary styles — too easy to activate accidentally.

---

## 6. Per-recipe study — top 12 community workflows decoded

### #1 — Pony classic (id=12097475, 16,296 likes, by Stellaaa)

```
prompt:    "score_9, score_8_up, score_7_up, san, 1girl, full body, squatting,
            solo, short hair, brown hair, gray eyes, headband, face paint,
            earrings, white sleeveless top, navy under dress, arm cuffs,
            fur headdress, fur cape, light-skinned female, female focus,
            looking at viewer, smiling, forest, (blush:1.1)
            <lora:pony/twilight_style:0.8> concept art, realistic,
            <lora:pony/expressiveh:0.8> expressiveh,
            <lora:pony/kenva:0.8> knva,
            <lora:pony/san_pony_v4>
            <lora:sdxl/sinfully_stylish_sdxl>"
negative:  "score_6, score_5, score_4"
sampler:   Euler a Karras
cfg:       7
steps:     25
size:      896x1152
LoRAs:     5 stacked
```

**What this teaches:** Pony quality-tag prefix is mandatory. Stack 5 LoRAs at strength 0.8 for the named ones, default 1.0 for unnamed. Use `(weight:value)` parenthesized boost for individual tags ("`(blush:1.1)`"). Subject as comma-tagged list. SDXL-style negative.

### #2 — Flux portrait (id=64399178, 15,864 likes, by L10n_H34r7)

```
prompt:    "A close-up of a face adorned with intricate black and blue patterns.
            The left side of the face is predominantly yellow, with symbols and
            doodles, while the right side is dark, featuring mechanical elements.
            The eye on the left is a striking shade of [...]"
size:      832x1216
steps:     30
cfg:       2.5  (low FluxGuidance — natural realism path)
sampler:   Undefined (Flux uses model-internal sampling)
```

**What this teaches:** Flux dev wants **natural language paragraphs**, not comma-tagged lists. Detailed scene description with spatial relationships. **cfg=2.5 is below the canonical 3.5 — for natural realism you go LOW**. The 832x1216 portrait is the Flux community canonical.

### #5 — Anthropomorphic samurai (id=60535375, 10,395 likes — DIRECT relevance to Luis's NPC roster)

```
prompt:    "A humanoid (black cat) wearing red samurai armor. He is wearing a
            white headband with the Japanese rising sun on it. Holding a katana
            He is in a field. Full body Cinematic lighting, volumetric lighting,
            8k quality"
base:      Flux.1 D
size:      832x1216
steps:     20
cfg:       7  (HIGH FluxGuidance — for stylized/dramatic look)
```

**What this teaches:** **High cfg (7) on Flux** for stylized character work. Note the `(black cat)` parenthesization — that's Flux's way to emphasize a key phrase. Cinematic vocabulary ("Cinematic lighting, volumetric lighting, 8k quality") is the Flux quality-prompt convention. **Direct template Luis can clone for anthropomorphic NPC characters** — substitute `(red fox)` / `(green frog)` / etc. for the species.

### #6 — Demon woman portrait (id=56975911, 8,723 likes, by tent44)

```
prompt:    "A close-up portrait of a demon woman with molten lava-like cracks
            on her skin, her fiery eyes glowing intensely. Her horns are jagged
            and sharp, resembling molten stone, and her expression is one of
            wrath and destruction, with flames flickering aroun[d her]"
base:      Flux.1 D
size:      832x1216
steps:     38  (HIGH — quality-max)
cfg:       4.5  (mid FluxGuidance)
```

**What this teaches:** **38 steps is unusually high** — used for max-quality dramatic character output. Detailed material description ("molten lava-like cracks", "molten stone horns", "fiery eyes"). For Luis's enemy variants (boss tier), high-step + mid-cfg is the production-quality template.

### #7 — Neon samurai (id=69643023, 8,513 likes, by AIDigitalMediaAgency)

```
prompt:    "A neon samurai, his body adorned with holographic armor that shifts
            in color with every step, walks through the neon-drenched streets
            of a cybernetic Tokyo. His katana, humming with digitized energy,
            slices through the rain, leaving a trail of flicker[ing light]"
base:      Flux.1 D
size:      832x1216
steps:     24
cfg:       3.5  (canonical FluxGuidance default)
```

**What this teaches:** **Canonical Flux setup** — 832x1216 + 24 steps + cfg 3.5. Action-rich verb-driven prompt ("walks through", "slices through", "leaving a trail"). Uses brand-vocabulary ("cybernetic", "digitized", "flickering") for cohesive aesthetic.

### #8 — Gabriel Picolo style (id=87488990, 8,132 likes — SDXL with detailed negative)

```
prompt:    "illustrated by Gabriel Picolo, (resplendent highlighting) in the
            style of casual line and wash sketch, hauntingly beautiful,
            violento colorido, influenced by Bernard Buffet, a contemporary
            watercolor painting, tightly framed, close-up portrait of a [...]"
negative:  "watermark, cloned face, same face, nsfw, nipples, elongated,
            long neck makeup, face paint, weapons, sticks, holding objects,
            long forearms, duplicate"
base:      SDXL 1.0
size:      832x1216
steps:     21
cfg:       6
sampler:   Euler a
```

**What this teaches:** **Artist-name attribution** ("illustrated by Gabriel Picolo") triggers style transfer in SDXL. Mix multiple artist references ("influenced by Bernard Buffet") for hybrid styles. **The detailed negative prompt is THE signature of SDXL/Pony work** — Flux doesn't need this verbose negative because it ignores most of it. For SDXL you list specific anti-features (cloned-face, elongated neck, weapons, holding objects, duplicate) to anchor against common artifacts.

### #10 — Misty fantasy valley (id=64621413, 7,554 likes — Flux landscape with DPM++)

```
prompt:    "A golden road winds through a misty valley towards towering
            mountains. The rising sun peeks over the horizon, painting the sky
            in vivid hues of pink, orange, and gold. Ancient white cherry trees
            line the path, their blossoms awakening to the dawn's f[irst light]"
base:      Flux.1 D
steps:     30
cfg:       3.5
sampler:   DPM++ 2M  (NICHE — not Euler!)
```

**What this teaches:** **DPM++ 2M shows up for landscapes** — the niche choice when you want softer atmospheric output. For your `runners/biome_painterly.py` painterly biomes, this sampler may produce better atmospheric depth than Euler. Long verb-driven scene description with color callouts ("vivid hues of pink, orange, gold"). **Direct template for biome generation.**

---

## 7. Prompt grammar conventions per base model

### Pony Diffusion XL grammar

```
[QUALITY PREFIX] [SUBJECT TAGS] [SCENE TAGS] [LORA INVOCATIONS]
score_9, score_8_up, score_7_up, [comma-tagged subject], [comma-tagged scene], <lora:path/name:strength> ...
```

- **Quality prefix is mandatory.** `score_9, score_8_up, score_7_up` — without it output is washed out.
- **Negative is short and tag-only:** `score_6, score_5, score_4`.
- **Tag-driven, not natural language.** `1girl, short hair, brown hair, gray eyes, white sleeveless top` — not "a girl with short brown hair wearing a white top".
- **LoRA invocations end the prompt** with `<lora:path/name:strength>` syntax. Strengths cluster around 0.7-0.9.
- **Parenthesized weights** for individual emphasis: `(blush:1.1)` boosts that tag's weight.

### Illustrious grammar (post-Pony era, 2024-2025)

```
masterpiece, best quality, very aesthetic, [tag list]
```

- **Quality prefix:** `masterpiece, best quality, very aesthetic` (instead of Pony's score system)
- **Same tag-driven approach** as Pony
- **Mandatory companions:** Stabilizer (id=971952) + Aesthetic Quality Modifiers (id=929497) LoRAs
- **Often dropped** the `_up` modifier patterns from Pony — Illustrious doesn't recognize them

### Flux dev grammar

```
A [subject], [detailed scene description with spatial relationships and material descriptions],
[atmospheric/lighting vocabulary], [quality vocabulary like "8k quality, cinematic"]
```

- **Natural language paragraphs**, NOT comma-tagged lists
- **Scene-based** — describe the spatial setup ("close-up of", "walks through", "leans against")
- **Material specificity** is rewarded — "molten lava-like cracks", "holographic armor that shifts in color"
- **Cinematic vocabulary** as quality tags — "Cinematic lighting, volumetric lighting, 8k quality"
- **`(parenthesized phrase)`** for emphasis (NOT for weighting like SDXL — Flux just treats parens as natural emphasis)
- **No score_9-style prefix** — Flux doesn't use them
- **LoRAs are NOT inline in prompt** — they go in `LoraLoaderModelOnly` workflow nodes
- **cfg/FluxGuidance ranges 2.5 (natural) → 3.5 (canonical) → 7 (stylized)**

### SDXL 1.0 grammar (when used directly, not via Pony/Illustrious)

```
[artist attribution], [(parenthesized weighted tag)], [style descriptors],
[material descriptors], [composition descriptors], [subject]
```

- **Artist attribution** triggers style: "illustrated by [artist name]", "influenced by [artist name]"
- **Mix multiple artists** for hybrid styles
- **Verbose negative prompts** with specific anti-features (cloned-face, watermark, NSFW, elongated, duplicate)
- **Parenthesized weights:** `(resplendent highlighting:1.2)` — pure A1111 syntax
- **Mid-range cfg (5-7)** typical
- **Euler a** is the canonical sampler

### OpenAI / GPT-Image grammar (NOT a ComfyUI workflow but appears in feed)

- **Pure natural language**, often poetic or minimalistic
- "Dead can dance, misty morning, unreal shapes emerge from the fog, photo realism."
- No tags, no LoRAs, no parenthesized weights
- Civitai surfaces these as if they're samplers (`GoogleNanoBanana2`, `GPT-Image-2`, `Grok`) but the underlying generation isn't ComfyUI

---

## 8. Implications for Luis's runners and POP house style

### Add 832×1216 to runner aspect-ratio options

Three of the top community Flux workflows use 832×1216. My `runners/character_cel_shaded.py` defaults to 3:4 (1024×1536-ish) which is similar but not identical. Worth adding `--aspect 832x1216` as the community-canonical preset.

### Update prompt-construction patterns based on base model

The runners currently use the same prompt structure regardless of which Nano Banana / Qwen / Z-Image / Flux backend they target. Each backend prefers a different prompt grammar:

- **Nano Banana** = Flux-style natural language
- **Qwen-Image** = handles both styles, prefers natural language
- **Z-Image** = handles both styles
- **Flux 2 Klein** = Flux-style natural language
- **Pony / Illustrious (if you ever use)** = quality-tag prefix + comma-tagged subject

For free-local runners that target Z-Image or Qwen, the existing natural-language prompts are correct. For any future Pony/Illustrious runner, add the quality-tag prefix template.

### POP house-style LoRA training: trigger word recommendation

Use **leetspeak pattern** for your trigger token:
- `pop_h5tyle` (good — rare, no collisions, readable)
- `popstyle` (bad — collides with Pop Art descriptions)
- `POP_houseSTYLE` (mediocre — CamelCase + composite, harder to remember)

Train against either Flux.1 D or Qwen-Image-2512 as base. After training, the LoRA loads in your runners by inserting `LoraLoaderModelOnly` between `model_loader` and `shift`, with `lora_name="pop_h5tyle.safetensors"`, strength 0.7-0.85 to start.

### When you bridge with civitai LoRAs (before your own POP LoRA exists)

Drop these into Flux runners with these strengths (community-validated):

| LoRA ID | Name | Recommended strength |
|---|---|---|
| 599757 | Velvet's Mythic Fantasy Styles | 0.8 (multi-base, stack-friendly) |
| 800718 | Anthropomorphic Fantasy DnD | 0.85 (key trigger required: `In the style of anthr0dnd`) |
| 100435 | Character Design Sheet HELPER | 0.7 (helper LoRAs apply lighter) |
| 308147 | Fantasy Wizard & Witches | 0.85 (concept LoRA) |
| 1890368 | Crystal Plague World Morph | 0.7 (style LoRAs on the lighter end) |
| 1063807 | F1 Isometric 3D medieval | 1.0 (full strength — concept-heavy) |

For multi-LoRA stacking (the community's actual pattern), chain 2-3 LoraLoaderModelOnly nodes in a row. Total combined strength typically caps at ~2.0 — beyond that, output gets weird.

---

## 9. Patterns I extracted that surprised me

1. **Of 56 top-engagement workflow records, only 1 has inline `<lora:...>` syntax in prompt.** The other 55 use proper LoraLoaderModelOnly nodes (or are API-call images). The community has moved away from A1111-style inline LoRA invocation toward node-based stacking. **The hashes field is more reliable than prompt text for identifying which LoRAs were used.**

2. **OpenAI / GPT-Image API calls dominate the "top this week" sort.** Free local generation is the norm in `top_alltime`, but recent feeds tilt toward paid API services. Civitai has become a hybrid showcase, not just ComfyUI.

3. **Pony Diffusion XL is fading.** Only 1 of 56 top records used it. Five years ago Pony was THE leader. The community has moved to Illustrious for anime/cel-shaded and Z-Image-Turbo for fast quality.

4. **`Klein-consistency` and `riftGATE__9b__epoch_10` LoRAs surfaced in workflow hashes.** These are Flux 2 Klein 9B LoRAs that I haven't catalogued elsewhere — community has started training Klein-specific LoRAs which suggests the model is gaining traction beyond Comfy-Org's official examples.

5. **A `zimage/painting_zimage_v1` LoRA exists.** Z-Image also has community-trained LoRAs being used in production work. The Z-Image LoRA ecosystem is technically empty per civitai's search (as I documented in ref 49), but in workflow hashes I can see they DO exist and ARE being used. They're just not surfaced via the public model-search API.

6. **`LORA:lighting` appears 2x.** A LoRA literally named "lighting" is being used in top workflows. Likely a generic light-direction control — would be useful to surface and add to runner toolkit.

---

## What's still NOT in the data we pulled

- **Actual workflow JSON** (only embedded in PNG EXIF — would need pull_civitai_workflow.py to extract per-image)
- **Article content** (`/api/v1/articles` returns 404 — would need to scrape browser side)
- **Specific LoRA strength recommendations from civitai's UI** (not exposed via API)
- **Comments section content** (which often has technique discussions — would need separate endpoint)
- **The full meta of images sorted by less-popular criteria** (we only sampled top reactions / comments / newest)

If any of these become important later, separate API endpoints exist for posts and comments — `/api/v1/posts` and the comment thread endpoints. The articles endpoint returning 404 is the only confirmed dead path.
