---
name: civitai.com — model marketplace, community, on-site generation + training
description: Practical reference for civitai.com. Site structure, content types, REST API, Civitai Link ComfyUI integration, AIR identifiers, Buzz currency, on-site LoRA trainer, education hub topics. What's most useful for Luis's POP house-style training and his existing inference pipeline.
type: reference
---

# civitai.com

## Curated findings from actual API browse (2026-05-09)

Ran `civitai_browse.py` against 10 curated queries with Luis's API key. **Most "obvious" queries returned 0 results** — civitai's text search matches model name/description literally, so phrases like "cel shaded" / "painterly" / "chibi" / "shiba" rarely appear in titles even when LoRAs of that style exist. Strategy lesson: prefer tag filtering, broad queries, and `Most Downloaded` sort over `Highest Rated`.

### Top picks for Luis's POP house style

| ID | Name | Base | Downloads | Trigger | Why it matters |
|---|---|---|---|---|---|
| **800718** | Anthropomorphic Fantasy DnD Illustrations [FLUX/Pony] | Flux.1 D | 1,511 | `In the style of anthr0dnd` | **Strongest match for the NPC roster.** Fantasy illustration style of furry/anthropomorphic characters. v2 supports Flux. By creator FlacFerret. |
| **2280495** | Flux_2D game UI Flat Vector style | Flux.1 D | 229 | (none — style activates from LoRA load) | **Direct match for icons.** Description literally says "geometric forms, circles, ovals, capsules, rounded rectangles, large-radius curves, soft friendly approachable proportions". Tagged `vector, style, flat ui`. By Belair. |
| **438813** | Flat Vector Art PDXL | Pony | 1,830 | `vztdzsxx, a flat style vector illustration, flat color, vector art, illustration, vector illustration, cel shading, simple coloring` | Highest-downloaded Pony LoRA in the cel-shaded space. Tags include `style, game character, male, man, video game`. By ktiseos_nyx. |
| **260449** | Drawn On | Pony | 1,693 | `Dr4wn0n, mixed media, cel shading clothing, slime, dripping` | Mixed-media cel-shaded look; clothing-focused. Recommended strength 0.75-0.9 per creator notes. By freckledvixon. |
| **429227** | SXZ Hades PDXL [Style] | Pony | 1,511 | `hds style, cel shading, linear hatching` | Hades-game-style cel-shaded. Creator's recommended settings: Clip Skip 2, Euler a or DPM++3M SDE (SGM Uniform), 30-40 steps, Hires.fix x1.5. By sadxzero. |
| **308147** | Fantasy Wizard & Witches | Flux.1 D | 21,414 | `hkmagic` | Highest-downloaded result of any query. Concept LoRA for wizards/witches/magic. Tags `concept, witch, magic, fantasy, wizard`. Could power NPC merchants / quest-givers with magical roles. By HailoKnight. |
| **2527237** | salpin (さるぴん/SALPIn02) Artist Style // Illustrious | Illustrious | 372 | `salpstyle, clean lineart, thin lines, cel shading, soft colors, flat colors, simple lighting` | Modern (2025) Illustrious LoRA with explicit cel-shading triggers. Pixiv artist salpin's style. By DarknessNOVA. |
| **2516970** | fukukucchi (フクッチ/エロッチ) Artist Style // Illustrious | Illustrious | 415 | `fukukstyle, monochrome, grayscale, flat shading` | Flat-shading focus; monochrome — could chain with color overlays. |

### Practical use

For Flux-based runners (qwen_t2i_lightning, qwen_edit_lightning), the directly-droppable picks are **800718** (anthropomorphic) and **2280495** (UI icon flat vector). For Pony pipelines, **438813** + **260449** + **429227** are all cel-shaded with strong download counts. For SDXL/Illustrious work, **2527237** is the modern cel-shaded artist style.

To download via ComfyUI:
1. Open `https://civitai.com/models/<ID>` in browser (e.g., `https://civitai.com/models/800718` for the anthropomorphic Flux LoRA)
2. Download the `.safetensors` to `G:\models\loras\`
3. Insert a `LoraLoaderModelOnly` node before `ModelSamplingAuraFlow` in the runner's workflow:

```python
"lora_pop_anthro": {
    "class_type": "LoraLoaderModelOnly",
    "inputs": {
        "model": ["model_loader", 0],
        "lora_name": "anthr0dnd_v2_flux.safetensors",  # whatever you save it as
        "strength_model": 0.8,
    },
},
"shift": {
    "class_type": "ModelSamplingAuraFlow",
    "inputs": {"model": ["lora_pop_anthro", 0], "shift": 3.0},   # was ["model_loader", 0]
},
```

Trigger word goes in the prompt: "In the style of anthr0dnd, a wise frog merchant in a leaf cloak ..."

### Search strategies that DIDN'T work

These returned 0 results — flagging here so I don't try them again:
- `query=cel shaded&baseModels=Flux.1 D` (LoRA creators don't title with "cel shaded")
- `query=painterly&baseModels=Flux.1 D`
- `query=chibi&baseModels=Flux.1 D`
- `query=cel shaded&baseModels=Qwen-Image` (Qwen-Image LoRA ecosystem too young)
- `query=shiba&baseModels=Flux.1 D` (no shiba-specific Flux LoRAs found via text search; might exist with different naming)

### Search strategies to TRY in v2

- Tag-only filter (`tag=style&types=LORA&baseModels=Flux.1 D&sort=Most+Downloaded`)
- Broad-text + sort (`query=anime&types=LORA&baseModels=Flux.1 D&sort=Highest+Rated`)
- Artist-name searches (`query=ghibli`, `query=arcane`, `query=hades`, `query=cuphead`)
- `query=2d game&types=LORA` (Belair's UI LoRA showed up here)
- Don't filter by base model initially; filter the response client-side

### Follow-up runs

`civitai_browse.py` lives at the project root. Re-run anytime to refresh. Edit the `QUERIES` list to add new searches as the model ecosystem evolves. Output goes to `.civitai_results/` (gitignored — keep it that way).

---


The dominant community-hosted model marketplace and gen-AI hub for SD-derivative diffusion models. Combines model hosting + image/video gallery + community + on-site generation + on-site LoRA trainer.

**Read date:** 2026-05-09. Site sections verified from fetches; deeper API + integration details synthesized from prior knowledge — verify against current docs at `developer.civitai.com` before relying on exact endpoints/parameters.

---

## Site sections (verified from fetch)

Top nav: `home / models / images / videos / posts / articles / challenges / events / updates / shop`. Plus `/pricing`, `/auctions`, `/leaderboard/overall`, `/collections/...`, `/creator-program`, `/education`.

**Education hub** lives at `education.civitai.com` (separate WordPress site). Categories include: Beginner's Guides (8 posts), Civitai (35 posts), Quickstart Guides (13), Glossary, Flux, SDXL, Prompting, Training (3 posts), Guides, Video, LLM, SD3.

**Wiki** at `wiki.civitai.com/wiki/Main_Page` (broader reference content).

**API docs** moved to `developer.civitai.com/site/reference/` (the old `civitai.com/github/wiki/REST-API-Reference` redirects there with a deprecation notice).

---

## Content types you can host or browse

| Type | Purpose | Relevant for Luis |
|---|---|---|
| **Checkpoint** | Full diffusion model | Pony Diffusion XL, Illustrious XL, NoobAI XL, Flux variants, custom merged SDXLs. Luis already has the major SDXL/Pony libraries downloaded — useful for browsing newer releases. |
| **LoRA** | Adapter for style/character/concept | THE primary use case. Style LoRAs Luis could use as inspiration or directly. Character LoRAs less relevant (he's building his own roster). |
| **LoCon / LoHa / LyCORIS / DoRA** | LoRA variants with different rank decomposition | Same use as LoRA, sometimes better quality at smaller size |
| **Embedding (Textual Inversion)** | Single-token concept | Quality-tag bundles for SDXL ("score_9, score_8_up...") — Pony-specific |
| **Hypernetwork** | Older adaptation method | Mostly obsolete; ignore |
| **VAE** | Decoder weights | Edge case; default VAEs work for almost everything Luis runs |
| **AestheticGradient** | Generation steering | Niche |
| **Controlnet** | ControlNet model | Look here for non-mainstream variants — e.g. specialized canny / depth ControlNets for Pony or Flux |
| **Poses** | OpenPose JSON files | Useful for the `--mode pose` path in `runners/zimage_controlnet.py` if you want a curated pose library instead of extracting from photos |
| **Wildcards** | Random-substitution prompt files | Used by some custom nodes; not directly relevant to Luis's runners |
| **Workflows** | ComfyUI / A1111 workflow JSON | Sometimes hidden under "posts" — search post tag "workflow" or look at ComfyUI-specific articles |

## Filtering / browsing for Luis's needs

When hunting for **style LoRAs** for cel-shaded / painterly / chibi inspiration:

- Filter by base model: `Flux.1 D` / `Pony Diffusion XL` / `SDXL 1.0` / `Illustrious XL` / `Qwen-Image` (newer)
- Sort by `Most Liked` or `Highest Rated` — new uploads churn fast; bookmarks are signal
- Look at the LoRA's preview images — if the style consistently shows up across different prompts, the LoRA generalizes well
- Check the model card for **trigger words** and **suggested settings** (CFG, steps, sampler/scheduler, recommended LoRA strength)
- Look at "Generation Data" on user-uploaded images using that LoRA — those are real production prompts

Use cases that are NOT a fit for civitai:
- Direct training (use `ai-toolkit` for serious training; civitai's on-site trainer is convenient but less powerful — see below)
- Hosting Luis's own internal POP house-style LoRA (you wouldn't publish that)

---

## REST API basics

Endpoints (verify against `developer.civitai.com` for current state):

```
GET https://civitai.com/api/v1/models                   List models with filters
GET https://civitai.com/api/v1/models/{modelId}         Single model details + all versions
GET https://civitai.com/api/v1/model-versions/{id}       One specific version
GET https://civitai.com/api/v1/images                   Browse community images
GET https://civitai.com/api/v1/creators                 List creators
GET https://civitai.com/api/v1/tags                     Browse tags
```

Common query parameters on `/models`:
- `query=` text search
- `tag=` filter by tag (e.g. `tag=style`, `tag=anime`, `tag=character`)
- `types=Checkpoint,LORA` filter by content type
- `sort=Highest+Rated` / `Most+Downloaded` / `Newest`
- `period=AllTime` / `Year` / `Month` / `Week` / `Day`
- `nsfw=true|false`
- `baseModels=Flux.1 D,Pony,SDXL 1.0,Illustrious`
- `limit=100` (max ~100, paginate via `cursor`)

Authentication: optional `Authorization: Bearer <api-key>` for higher rate limits. Generate at `civitai.com/user/account` -> API Keys.

Direct download URL pattern (for fetching model files programmatically):
```
https://civitai.com/api/download/models/{modelVersionId}
```

Often returns a 302 to the actual S3-hosted blob. May require an API key for some uploads.

## AIR — Uniform Resource Names

Civitai uses an internal naming scheme called **AIR** (Artifact Identifier Resource). Format:

```
urn:air:{ecosystem}:{type}:{source}:{model_id}@{version_id}
```

Examples:
```
urn:air:sd1:lora:civitai:1234@5678
urn:air:sdxl:checkpoint:civitai:9999@10000
urn:air:flux1:lora:civitai:50000@60000
```

- `ecosystem` — `sd1` (SD 1.5), `sdxl`, `sd3`, `flux1`, `pony`, `illustrious`, `qwen`, etc.
- `type` — `checkpoint`, `lora`, `embedding`, `controlnet`, `vae`, etc.
- `source` — usually `civitai` but some external integrations use other values
- `model_id` and `version_id` are the numeric IDs from civitai's URLs

Why this matters: ComfyUI integrations that do auto-resolve (like Civitai Link, see below) accept AIRs as opaque identifiers. The API endpoint `/api/v1/models/by-air/{air}` lets you look up metadata by AIR.

---

## Civitai Link — ComfyUI integration

A custom node + browser extension that pulls models from civitai directly into your ComfyUI install without manual download.

- **Browser extension**: adds an "Add to ComfyUI" button on civitai model pages
- **Custom node** (likely in Luis's manager listing as `Civitai Comfy Nodes` or similar): receives push from extension and downloads the file to the right folder (`models/checkpoints/`, `models/loras/`, etc.)
- Needs ComfyUI's API on a port the extension can reach. Default localhost works for desktop usage.

For Luis: this is convenient for one-off "saw a cool LoRA on civitai → want to try it" workflows. Less critical given he's building his own LoRAs and already has a curated model library.

---

## Buzz currency system

Civitai's internal currency. Used for:
- On-site image/video generation (each gen costs Buzz)
- On-site LoRA training jobs (substantial Buzz cost — hundreds to thousands per training)
- Tipping creators
- Bidding on auctioned features (model promotion, etc.)

Earning Buzz: free daily allowance, post engagement, creator tier, paid purchase, gift codes.

For Luis's purposes: not really relevant. He's running everything locally on his 5090. Buzz only matters if you use the on-site tools.

---

## On-site LoRA trainer vs ai-toolkit

Civitai has an on-site LoRA trainer (`civitai.com/models/train`-style flow). Compared to ai-toolkit (ref 45):

| Aspect | Civitai on-site trainer | ai-toolkit (local) |
|---|---|---|
| Cost | Buzz per job (~$1-10 USD-equivalent per LoRA) | $0 (local) |
| Hardware | Civitai's GPUs | Luis's 5090 |
| Model coverage | SDXL, Flux.1, Pony — limited list | Wider: Flux 2, Qwen, Z-Image, Wan, Lumina2, etc. |
| Hyperparameter control | Limited GUI options | Full YAML config, every knob |
| Privacy | Datasets uploaded to civitai (storage / TOS implications) | All local, never leaves your disk |
| Convenience | High — upload images, click train, wait | Moderate — venv setup + config writing first time |
| Output | Downloadable .safetensors | Local file in `output/` |
| Trigger | Web UI | CLI or web GUI |

**For Luis's POP house-style LoRA: ai-toolkit is the better choice.** Local control, no Buzz cost, your dataset stays private, supports the wider model families he'd want to train against (Qwen-Image, Z-Image, Flux 2 Klein).

---

## Article categories worth bookmarking

The civitai.com `/articles` feed (and the education hub) has community guides on specific training and prompting topics. From what I saw in the fetch:

- "Flux Style Captioning Differences - Training Diary" by mnemic (Aug 2024) — empirical findings on caption style for Flux LoRAs
- "Towards Pony Diffusion V7" by PurpleSmartAI — relevant for understanding Pony lineage
- "Model Merging: Crafting Conceptual Palettes" — checkpoint merge theory
- "What is score_9 and how to use it" (Pony) — Pony-specific quality tag handling

The education hub's `Training` category (3 posts) and `Flux` category (1 post) are smaller; the main content lives in user-authored articles, which the API can surface programmatically:

```
GET https://civitai.com/api/v1/articles?tag=training&sort=Most+Liked
```

---

## Practical patterns for Luis's workflow

### Discovering a style LoRA to bridge until your own POP LoRA is trained

1. Search civitai for `cel-shaded` + `Flux.1 D` + sort by `Highest Rated`
2. Open promising LoRAs, study preview images for tonal match to your house style
3. Note trigger words and recommended settings from the model card
4. Download via Civitai Link or manual to `G:\models\loras\`
5. Test in `runners/qwen_t2i_lightning.py` or `runners/zimage_t2i.py` by inserting a `LoraLoaderModelOnly` node before `ModelSamplingAuraFlow` (chain it in: shift's input is now `["lora_loader", 0]` instead of `["model_loader", 0]`)
6. If it works for inspiration but doesn't quite match, mark it as a future training reference

### Browsing community workflows

Civitai's "posts" section sometimes includes ComfyUI workflow JSON. Filter posts by tag `workflow` or search articles for "ComfyUI". Less canonical than Comfy-Org's official template repo (ref 27) but useful for novel patterns. When you find one, the workflow JSON is usually downloadable as a file or embedded in PNG metadata.

### Bookmarking via API for offline reference

If you want to track interesting LoRAs without manual bookmarking:

```python
import urllib.request, json
api_key = "..."
headers = {"Authorization": f"Bearer {api_key}"}
url = "https://civitai.com/api/v1/models?tag=cel-shaded&baseModels=Flux.1+D&sort=Highest+Rated&limit=20"
req = urllib.request.Request(url, headers=headers)
data = json.loads(urllib.request.urlopen(req).read())
for m in data["items"]:
    print(m["id"], m["name"], m.get("stats", {}).get("rating"))
```

---

## Red flags / cautions

- **NSFW content is rampant.** Many LoRAs and checkpoints are tuned for NSFW use cases. Filter `nsfw=false` in API calls and toggle the safe-mode setting in the UI for clean browsing.
- **Quality varies wildly.** A 5-star rating with 3 reviews tells you nothing. Look at download counts (signal) and actual generation samples (verify).
- **Trigger word collisions.** A LoRA with trigger `popstyle` will activate any time you use that word in a prompt. Audit triggers before stacking multiple LoRAs.
- **Model TOS / licensing.** Most civitai LoRAs are CC0 or permissive but some have commercial restrictions. If POP plans to monetize generated assets, audit licenses.
- **Civitai's discovery surface heavily favors anime / NSFW / character LoRAs.** Style LoRAs for "painterly biome game art" are rarer; expect to dig.

---

## When to reach for civitai vs alternatives

| Goal | Best resource |
|---|---|
| Find a specific style LoRA quickly | civitai |
| Find a checkpoint you don't already have | civitai (Pony, Illustrious, NoobAI variants) |
| Find official model weights from labs | Hugging Face (more authoritative, fewer NSFW remixes) |
| Find ComfyUI workflows | Comfy-Org templates (ref 27) > civitai posts > miscellaneous Discord |
| Train your own LoRA | ai-toolkit (ref 45) > civitai on-site trainer for casual use |
| Get prompt inspiration | civitai images sorted by quality |
| Get training advice | civitai education hub + community articles + ostris discord + r/StableDiffusion |
| Authoritative API docs | developer.civitai.com (the wiki redirect target) |

---

## Caveat about this reference

The fetched HTML pages from civitai.com are heavily JS-rendered — individual model pages don't surface meaningful content via plain HTTP fetch. The structure, education hub topics, and high-level API surface are verified; specific endpoint signatures and current API authentication flow should be verified at `developer.civitai.com/site/reference/` before relying on them in code.

If Luis decides to use civitai's API programmatically, the right next step is: generate an API key from his civitai account settings, test one `/api/v1/models` GET against the live endpoint with curl, then build out from there.
