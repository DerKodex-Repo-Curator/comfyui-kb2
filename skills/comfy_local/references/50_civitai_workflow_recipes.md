---
name: civitai workflow recipes — what top community workflows actually use
description: Verified findings from real /api/v1/images browse against Luis's account 2026-05-09. The actual prompt + sampler + cfg + steps + LoRA stack patterns that win likes on civitai. The API does NOT expose workflow JSON — only the recipe — but the recipe is the actual learning value.
type: reference
---

# civitai workflow recipes

**Method:** Ran `civitai_workflows_v3.py` against Luis's API key on 2026-05-09. Pulled 500 community-engaging images across 5 sort buckets (top all-time / month / week / most-commented-month / newest), filtered to ~194 with ComfyUI workflow markers, then deep-fetched 56 with full metadata for analysis.

**Important caveat about civitai's API and workflows:**

> The civitai API does NOT serve the actual workflow JSON. The `meta.workflow` field is just a marker that civitai's UI uses to know whether to render a "Workflow" tab on the image page. The real workflow JSON is embedded only in the original PNG's EXIF metadata, which the API doesn't expose.

To study an actual workflow node-graph from civitai:
1. Open the image page in browser (`https://civitai.com/images/<id>`)
2. Right-click the image → **Save image as** to download the original PNG with EXIF intact
3. Drag the PNG onto your ComfyUI canvas — Comfy auto-extracts the embedded workflow JSON

What the API DOES expose (and what's actually most useful for learning) is the **generation recipe** — the prompt, LoRA stack with strengths, sampler/scheduler/cfg/steps, base model, and seed. Recipes are arguably more valuable than node graphs because the graph is just visual placement; the recipe is the actual generation knowledge.

---

## Patterns observed in 56 top-engagement community workflows

### Sampler distribution (community-validated picks)

| Sampler | Count | Use signal |
|---|---|---|
| `Euler` | 16 | Safe-default for most models. Distilled-friendly. |
| `Euler a` | 12 | Ancestral variant — adds variation between same-seed runs. |
| `res_multistep` | 3 | Z-Image-Turbo canonical (matches your `runners/zimage_t2i.py`) |
| `DPM++ 2M SDE` | 2 | Old SDXL/Pony favorite — falling out of fashion |
| `er_sde_simple` | 1 | Newer experimental sampler |
| `Euler a Karras` | 1 | Niche — Euler ancestral with Karras schedule |
| `GoogleNanoBanana2` | 4 | API-call images (NOT a sampler — civitai surfaces these too) |
| `GPT-Image-2` | 2 | API-call images |
| `Undefined` | 4 | Workflow had no parsable sampler |

**Take-away:** Euler / Euler a dominate (28 of 56 = 50%). Specialty samplers (DPM++, sa_solver, dpmpp_3m_sde) are rare in top community work. Stick with Euler + simple as your default.

### Step count distribution

| Steps | Count | Likely model class |
|---|---|---|
| 30 | 13 | Non-distilled SDXL / Pony / Illustrious / Flux dev |
| 9 | 7 | **Z-Image-Turbo (8-NFE + 1)** — your canonical |
| 20 | 4 | Flux dev classic, mid-quality SDXL |
| 16 | 3 | Lightning step counts |
| 12 | 3 | Hyper-tuned distilled |
| 34 | 3 | Quality-max non-distilled |
| 25 | 2 | Mid-step Pony |

**Take-away:** Two clusters dominate — **30 steps for non-distilled** and **8-9 steps for Z-Image-Turbo**. Your runners hit both correctly.

### CFG distribution

| CFG | Count | Model class |
|---|---|---|
| 1 | **15** (highest) | Distilled — Z-Image-Turbo, Flux schnell, Lightning, Klein, Nunchaku Lightning |
| 7 | 9 | Classic SDXL / Pony / Illustrious non-distilled |
| 3.5 | 5 | Flux dev with FluxGuidance default |
| 4 | 3 | Flux dev with slightly higher guidance |
| 5 | 2 | Mid-cfg SDXL |
| 4.5 | 2 | Tweaked Flux dev |
| 1.2 | 2 | Slightly-above-1 distilled (uncommon — usually a mistake) |

**Take-away:** **cfg=1 is the single most common value** (15/56 = 27%). Distilled-model dominance in modern community work matches your runners' choices.

### Base model distribution (THE big finding)

| Base model | Count | Status |
|---|---|---|
| **ZImageTurbo** | **15** | Most-used base in top community workflows. Validates your Z-Image runners. |
| **Illustrious** | 10 | Modern anime / cel-shaded home. Has displaced Pony for new work. |
| **Flux.1 D** | 10 | Mainstream "quality" baseline |
| Nano Banana | 5 | API-call images (surface alongside ComfyUI on civitai) |
| OpenAI (GPT-Image) | 5 | API-call images |
| Grok | 2 | API-call images |
| SDXL 1.0 | 2 | Almost gone — community has moved to Illustrious |
| Pony | 1 | Almost gone in TOP images — Pony lives on but no longer dominates leaderboard |
| Anima | 1 | Niche |

**This is the single most important finding from this browse.** The community in 2025-2026 has converged on:
- **Z-Image-Turbo for fast quality T2I** (15/56 — top spot)
- **Illustrious for anime / cel-shaded** (10/56)
- **Flux.1 D for premium realism / general quality** (10/56)

Pony Diffusion XL is now a niche tool, not the leader. SDXL classic is barely represented. **Your runner choices match this exactly** — `zimage_t2i.py`, `qwen_t2i_lightning.py`, `flux2_t2i.py` cover the three dominant camps.

---

## Recipe templates from top images

These are real recipes pulled from actual top-liked civitai images.

### Z-Image-Turbo canonical

Multiple top-liked images use:
```
sampler:    Euler  (or res_multistep, or er_sde_simple)
scheduler:  simple
steps:      9
cfg:        1
base:       ZImageTurbo  (z_image_turbo_bf16 or z-image-turbo-fp8)
```

Matches your `runners/zimage_t2i.py` defaults. Confirmed canonical.

### Pony Diffusion classic (id=12097475, 15,363 likes — top all-time)

```
prompt:  "score_9, score_8_up, score_7_up, [subject], [pose], [details]
          <lora:pony/twilight_style:0.8> concept art, realistic,
          <lora:pony/expressiveh:0.8> expressiveh,
          <lora:pony/kenva:0.8> knva,
          <lora:pony/san_pony_v4>
          <lora:sdxl/sinfully_stylish_sdxl>"
negative: "score_6, score_5, score_4"
sampler:  Euler a Karras
cfg:      7
steps:    25
size:     896x1152
```

What this teaches:
- **Pony's quality-tag prefix** — `score_9, score_8_up, score_7_up` is mandatory for top output. `score_6, score_5, score_4` in negative is the canonical anti-low-quality block.
- **LoRA stacking is heavy** — 5 LoRAs at once, with strengths 0.8 for the named ones and unspecified (default 1.0) for the rest. Multiple style LoRAs cooperate.
- **`<lora:path/name:strength>` syntax** in the prompt is A1111-style. Civitai's web UI lets you stack these visually but stores them inline in the prompt for portability.
- **896x1152** is a Pony-canonical aspect ratio (~9:11.5).
- **Euler a + Karras** is an old-school SDXL combo that still wins for character art.

### Flux dev classic

Typical recipe pattern across the Flux.1 D entries in the dataset:
```
sampler:  Euler  (or DPM++ 2M SDE for premium)
scheduler: simple  (or beta for slightly better quality)
steps:    20-30
cfg:      3.5  (FluxGuidance internal — KSampler stays at 1)
size:     1024x1024 / 1024x1536 / 832x1216
```

Note: Flux dev's "cfg" in civitai's recipe field actually refers to FluxGuidance, not KSampler cfg. The KSampler cfg stays at 1.0 (distilled). When civitai surfaces `cfgScale: 3.5` for a Flux image, that's the FluxGuidance value.

### Illustrious classic (modern anime path)

```
prompt:  "masterpiece, best quality, very aesthetic, [subject details]"
sampler: Euler a  (or DPM++ 2M SDE)
scheduler: normal  (or simple)
steps:    25-30
cfg:      5-7
```

Illustrious adopted Pony's quality-tag culture but dropped the explicit `score_9` system. Top Illustrious images use `masterpiece, best quality, very aesthetic` as the universal quality prefix. Pair with the `Aesthetic Quality Modifiers` LoRA (id=929497) for an extra boost.

---

## What the data taught me about CIVITAI workflow culture

1. **Workflows are recipes more than graphs.** The community shares prompt + LoRA stack + sampler/steps/cfg, not necessarily the node placement. Two different visual graphs can produce the same recipe.

2. **LoRA stacking is HEAVY at the top.** Top images use 3-7 LoRAs simultaneously, with strengths in the 0.7-1.0 range. The "single style LoRA at strength 1.0" pattern is not how community winners actually operate.

3. **Quality-tag prompt prefixes are mandatory** for Pony/Illustrious base models. Skipping them = washed-out results.

4. **Distilled models have won.** cfg=1 is the most common value. Z-Image-Turbo is the most common base. Lightning LoRAs everywhere. The "20+ steps, cfg=7" old default is now niche.

5. **Civitai mixes API-call images with ComfyUI images** in the same feed. When you see `sampler: GoogleNanoBanana2` or `sampler: GPT-Image-2`, that's not ComfyUI — it's civitai's on-site generation calling out to a paid API service. The image is real, the workflow isn't.

6. **The `<lora:name:strength>` inline syntax** in prompts is the portable way to stack LoRAs. Civitai's web UI generates this format. Your runners use proper `LoraLoaderModelOnly` nodes which are equivalent at execution time.

---

## Practical learning plan for Luis

If you want to study top community workflows:

1. **Browse `https://civitai.com/images?sort=Most+Reactions&period=Week`** — these are the freshest community-validated outputs.

2. **For any image that interests you**, the page has a "Generation Data" section showing the recipe and (if a real ComfyUI workflow exists) a downloadable workflow.

3. **To get the actual node-graph workflow:**
   - Click the image to open its page
   - Look for a "Download Workflow" button (only present if the original PNG had EXIF workflow data)
   - OR right-click the image, Save As, then drag the PNG onto your ComfyUI canvas

4. **For learning purposes, focus on:**
   - Z-Image-Turbo workflows (15 in top dataset — most popular base)
   - Illustrious + LoRA-stack workflows (Pony-style quality tags + 3-5 LoRAs at 0.7-0.9)
   - Flux dev workflows that use FluxGuidance + custom samplers

5. **Specific image IDs worth opening from this browse:**

| ID | Likes | What to learn |
|---|---|---|
| 12097475 | 15,363 | Pony multi-LoRA stacking with score_9 quality tags |
| 64399178 | 15,058 | Top Flux work — close-up with intricate paint effects |
| 75799145 | 11,080 | Mood/atmosphere generation |
| 75749028 | 10,138 | "Cinematic photograph classil[ist]" — realism path |
| 60535375 | 9,919 | Anthropomorphic samurai — relevant for Luis's NPC roster aesthetic |
| 56975911 | 8,397 | Demon woman with molten lava — concept art techniques |
| 69643023 | 8,211 | Neon samurai with holographic armor — VFX-heavy character |
| 87488990 | 7,742 | Gabriel Picolo style — illustrator-style transfer |
| 77725327 | 7,476 | Egyptian warrior dynamic action shot |
| 64621413 | 7,345 | Misty valley fantasy landscape — biome inspiration |
| 74813012 | 6,925 | Cute magical hedgehog — chibi-friendly fantasy |
| 97017376 | 6,732 | 1800s masked hero — character-design vibe |

URLs follow pattern `https://civitai.com/images/<id>`.

---

## Refreshing the data

`civitai_workflows_v3.py` lives at the project root. Edit the `queries` list to add new sort/period combos. Re-run to refresh. Output goes to `.civitai_workflows_v3/` (gitignored).

If you ever want to extract actual workflow JSON from PNGs programmatically, the standard recipe is:

```python
from PIL import Image
img = Image.open("civitai_image.png")
workflow_json_string = img.info.get("workflow")  # ComfyUI metadata key
prompt_json_string = img.info.get("prompt")       # ComfyUI also stores API-format prompt
```

Both are JSON strings. Parse with `json.loads()` to get the workflow dict you can submit to `/prompt` directly.
