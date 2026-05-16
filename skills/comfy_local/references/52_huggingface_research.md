---
name: huggingface.co — model hub research and how it complements civitai
description: Site structure, key orgs publishing models Luis uses (Comfy-Org, black-forest-labs, kijai, city96, Alibaba-PAI, lightx2v, etc.), filter/search system, programmatic API surface, Spaces, Datasets, Inference Providers, the huggingface_hub Python library. How HF differs from civitai (authoritative vs remix culture).
type: reference
---

# huggingface.co — research

**Read date:** 2026-05-09. Verified content from live fetches; deeper API specifics and org details synthesized from prior knowledge.

## What HF is vs what civitai is

| Aspect | Hugging Face | civitai |
|---|---|---|
| Identity | Authoritative model home + ML platform | Community model marketplace |
| Who publishes | Research labs, model authors, foundation model teams | Mostly community remixes / fine-tunes |
| Content type | Models (any modality), datasets, Spaces (apps), evals | Models (image gen focus), images, posts |
| New model launches | **Here first** — Black Forest Labs, Alibaba, kijai, etc. publish weights here on day 0 | Days/weeks later, after community packages |
| Quality remixes | Sparse | Dense — civitai's specialty |
| API for programmatic access | Excellent (`huggingface_hub` Python library, OpenAPI) | Decent but undocumented; some endpoints 404 |
| LoRA hosting | Possible but less common | Primary use case |
| Datasets | Massive (500K+ datasets), public + gated | None |
| Inference Providers | 45,000+ models served via paid API | Buzz-system on-site generation |

**Mental model:** HF is "where the math papers go," civitai is "where the artists riff." Use HF to grab official weights and find new model releases the day they drop. Use civitai to find community LoRAs that remix those weights.

## Site sections (verified)

| Section | URL | What lives there |
|---|---|---|
| **Models** | `/models` | 2.8M+ models (multimodal — text/image/video/audio/3D) |
| **Datasets** | `/datasets` | 500K+ datasets (for training, eval, fine-tuning) |
| **Spaces** | `/spaces` | 1M+ hosted demos / apps (try-before-download) |
| **Buckets** | `/storage` | Newer object storage for ML pipelines |
| **Docs** | `/docs` | All HF library docs + tutorials |
| **Enterprise** | `/enterprise` | $20/user/month tier with SSO, regions, audit |
| **Pricing** | `/pricing` | Pro accounts, GPU compute |
| **Inference** | `/inference/models` | 45,000+ models served by 18+ providers (Groq, Novita, Cerebras, fal, Hyperbolic, Together, etc.) |

## Trending models (snapshot 2026-05-09)

Top trending was LLM-dominant: `Qwen/Qwen3.6-35B-A3B`, `moonshotai/Kimi-K2.6`, `tencent/HY-Embodied-0.5`, `google/gemma-4-31B-it`, `MiniMaxAI/MiniMax-M2.7`, `zai-org/GLM-5.1`. These don't directly affect Luis's image-gen work but signal where infrastructure attention flows.

**Image-gen models in trending:**
- `baidu/ERNIE-Image` and `baidu/ERNIE-Image-Turbo` — NEW image gen from Baidu (post-cutoff for me, surfaced in fetch)
- `NucleusAI/Nucleus-Image` — another new image gen
- `Comfy-Org/ERNIE-Image` — Comfy-Org's repackaging for ComfyUI consumption

**Video / 3D in trending Spaces:**
- `r3gm/wan2-2-fp8da-aoti-preview` — Wan2.2 14B Preview Space (try-before-download)
- `microsoft/TRELLIS.2` — High-fidelity 3D Generation from images (relevant for game asset prototyping)
- `prithivMLmods/FireRed-Image-Edit-1.0-Fast` — Image editor demo

**Implication for Luis:** ERNIE-Image and Nucleus-Image are image-gen models I had no prior knowledge of. Worth checking if they offer anything compelling for game art before they (probably) propagate to civitai.

## Key orgs publishing models Luis uses

| Org | URL pattern | What they publish | Relevance |
|---|---|---|---|
| **black-forest-labs** | `/black-forest-labs/FLUX.1-dev`, `/FLUX.1-schnell`, `/FLUX.1-Kontext-dev`, `/FLUX.2-dev`, `/FLUX.2-Klein-...` | Official Flux weights | Primary source for Flux models — civitai has remixes, HF has originals |
| **Comfy-Org** | `/Comfy-Org/Qwen-Image_ComfyUI`, `/Comfy-Org/Qwen-Image-Edit_ComfyUI`, `/Comfy-Org/Wan2.1`, `/Comfy-Org/ERNIE-Image` | Repackaged versions of new models split into ComfyUI-loadable parts (split_files/diffusion_models/, /text_encoders/, /vae/) | THE place to grab models in the right ComfyUI layout |
| **Kijai** | `/Kijai/WanVideo_comfy`, `/Kijai/WanVideo_comfy_fp8_scaled`, `/Kijai/HunyuanVideo_comfy`, etc. | His personal repository of quantized variants of video models | The only place to get fp8_scaled Wan + Hunyuan variants |
| **city96** | `/city96/FLUX.1-dev-gguf`, `/city96/...` | GGUF quantizations of major image/text models | Grab GGUF DiT files here (see ref 43) |
| **lightx2v** | `/lightx2v/Qwen-Image-Lightning`, `/lightx2v/Qwen-Image-Edit-2509-Lightning-4steps` | Lightning step-distilled LoRAs | Source of the Lightning LoRAs Luis already has |
| **mit-han-lab** + **nunchaku-tech** | `/mit-han-lab/svdq-...` | Nunchaku SVDQuant 4-bit models | Source of the int4_r32 / fp4_r128 SVDQ files |
| **Wan-Video** | `/Wan-Video/Wan2.1-T2V-14B`, `/Wan-Video/Wan2.1-I2V-14B-720P`, `/Wan-Video/Wan2.1-VACE`, etc. | Official Wan team uploads | Source of un-quantized Wan models (kijai's fp8 are derived from these) |
| **alibaba-pai** | `/alibaba-pai/Wan2.1-Fun-1.3B-Control`, etc. | Alibaba's experimental Wan variants | The "Fun" variants Luis has heard about (`Z-Image-Turbo-Fun-Controlnet-Union`) |
| **Tencent-Hunyuan** | `/tencent/HunyuanVideo`, `/tencent/HunyuanDiT`, `/tencent/HY-World-2.0` | Hunyuan family | Newer competitor to Flux/Qwen-Image lineage |
| **lodestones** | `/lodestones/Chroma` | Chroma model | Open-source SD3-style alternative |
| **HiDream-ai** | `/HiDream-ai/HiDream-I1-Full`, `/HiDream-I1-Dev`, `/HiDream-I1-Fast` | HiDream image gen | Another modern image model family |
| **THUDM** (Tsinghua) | `/THUDM/CogVideoX-2b`, `/THUDM/CogVideoX1.5-5B-I2V` | CogVideoX | Alternative video model lineage |
| **stabilityai** | `/stabilityai/stable-diffusion-xl-base-1.0`, etc. | Original SD weights | Historical / source-of-truth |
| **ostris** | `/ostris/...` | Ostris's released LoRAs and tools | Same person who wrote ai-toolkit |

**For tracking new releases relevant to Luis:** follow `black-forest-labs`, `Comfy-Org`, `Kijai`, `city96`, `lightx2v`. Those five accounts' release activity covers ~90% of what hits Luis's runner pipeline.

## File structure of a typical model repo

A Comfy-Org model repo (e.g., `Comfy-Org/Qwen-Image_ComfyUI`) is structured to drop into ComfyUI directly:

```
split_files/
├── diffusion_models/
│   └── qwen_image_2512_fp8_e4m3fn.safetensors    -> goes in G:\models\diffusion_models\
├── text_encoders/
│   └── qwen_2.5_vl_7b_fp8_scaled.safetensors      -> goes in G:\models\text_encoders\
└── vae/
    └── qwen_image_vae.safetensors                 -> goes in G:\models\vae\
```

The directory names match ComfyUI's folder convention exactly. Download just the files you need with `huggingface-cli download <repo-id> --include "split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors" --local-dir G:\models\`.

A standard non-Comfy-packaged repo (e.g. `black-forest-labs/FLUX.1-dev`) has the diffusers structure:

```
text_encoder/    text_encoder_2/   tokenizer/   tokenizer_2/
transformer/     vae/              scheduler/   model_index.json
```

This is the **diffusers** library layout. To use in ComfyUI you either grab the right `.safetensors` files manually or use Comfy-Org's repackaged version.

## Filter / search system

The model browse page (`/models`) supports filters via URL parameters:

```
https://huggingface.co/models?pipeline_tag=text-to-image
https://huggingface.co/models?pipeline_tag=text-to-video
https://huggingface.co/models?pipeline_tag=image-to-image
https://huggingface.co/models?library=diffusers
https://huggingface.co/models?library=gguf
https://huggingface.co/models?other=lora
https://huggingface.co/models?sort=trending  /  ?sort=downloads  /  ?sort=likes
https://huggingface.co/models?author=Kijai
```

Pipeline tags (the canonical "task" categorization):
- `text-generation` — LLMs
- `text-to-image` — image gen (THE one Luis cares about)
- `text-to-video` — video gen
- `image-to-image` — img2img / edit
- `image-to-text` — captioning
- `image-text-to-text` — multimodal LLMs (Qwen-VL, Gemma-4)
- `text-to-speech` / `automatic-speech-recognition`
- `any-to-any` — multimodal foundations

Library filter is gold for ComfyUI work:
- `library=diffusers` — diffusers-format models
- `library=gguf` — GGUF quantizations (city96's territory)
- `library=safetensors` — anything safetensors-backed
- `other=lora` — LoRA adapters specifically

## REST API for programmatic queries

HF has a documented REST API at `https://huggingface.co/api/`:

```
GET https://huggingface.co/api/models?search=flux&filter=text-to-image&limit=30&sort=downloads
GET https://huggingface.co/api/models/<id>                  # full model card data
GET https://huggingface.co/api/datasets?search=...
GET https://huggingface.co/api/spaces?search=...
```

Returns JSON. Authenticated requests get higher rate limits — generate a read-only token at `huggingface.co/settings/tokens`.

Equivalent in Python via `huggingface_hub` library:

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")  # optional

# list models
models = api.list_models(filter="text-to-image", sort="downloads", direction=-1, limit=50)
# get specific
info = api.model_info("Comfy-Org/Qwen-Image_ComfyUI")
# download a single file
from huggingface_hub import hf_hub_download
local = hf_hub_download(
    repo_id="Comfy-Org/Qwen-Image_ComfyUI",
    filename="split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors",
    local_dir="G:/models/diffusion_models/",
    local_dir_use_symlinks=False,
)
```

## CLI tool: `huggingface-cli`

Installed via `pip install huggingface_hub`, gives you:

```powershell
huggingface-cli login                           # auth from token file
huggingface-cli download <repo-id>              # download whole repo
huggingface-cli download <repo-id> --include "split_files/**"
huggingface-cli download <repo-id> file1 file2  # specific files
huggingface-cli upload <repo-id> file1 file2    # upload (publish your own)
huggingface-cli scan-cache                      # see what's cached locally
huggingface-cli delete-cache                    # interactive cache cleanup
```

For Luis: this is the canonical way to grab official model weights. Prefer over hand-clicking download buttons in the browser.

## Spaces — try-before-download

A Space is a hosted demo (Gradio / Streamlit / static HTML) running on HF infrastructure. Useful for:

- **Trying a new model** before downloading the full weights (`r3gm/wan2-2-fp8da-aoti-preview` lets you generate Wan2.2 video without local install)
- **Comparing models** side by side
- **Running models you can't fit locally** (massive LLMs, etc.)

Spaces use HF's compute (CPU / T4 / A10G / Zero-tier). Free tier has ~queues; Pro accounts get priority.

For Luis: not core workflow, but the "see what Wan 2.2 does before downloading 14 GB" path is worth knowing about.

## Datasets — for training

When training the POP house-style LoRA via ai-toolkit, datasets are key. HF datasets that may help:

- `Comfy-Org/...` — sometimes publish curated training datasets
- Search: `https://huggingface.co/datasets?search=fantasy+style` etc.
- General-purpose: ImageNet, LAION, COCO subsets — for testing pipelines, not actual style training
- Style-specific: smaller curated datasets exist for many art styles, license varies

The 500K+ dataset catalog is harder to navigate than civitai's curated LoRA scene. For LoRA training, **your own dataset of 30-100 images is more important than HF dataset hunting**.

## Inference Providers (paid alternative to local)

`/inference/models` lists 45,000+ models served via these providers:
- **Groq** — fast LLM inference
- **Novita**, **Cerebras**, **SambaNova**, **Hyperbolic**, **Together**, **fal**, **Nscale** — various
- **HF's own Inference Endpoints** — pay-as-you-go GPU compute

**Cost-tradeoff for Luis:** local on the 5090 is free for him. Inference Providers matter if he wants to run a 30B+ LLM that doesn't fit in 32 GB, or if he wants to generate at scale beyond the 5090's wall-clock. Otherwise, skip.

## How HF complements civitai (the practical workflow)

```
1. New model drops on HF
   ↓ (e.g., black-forest-labs/FLUX.2-Klein-9B-Instruct-2026-05)
2. kijai / city96 / Comfy-Org repackage for ComfyUI within hours-days
   ↓ (Kijai/FLUX.2-Klein_comfy, etc.)
3. Comfy-Org publishes a workflow template in their workflow_templates repo
   ↓ (image_flux2_klein_image_edit_9b_distilled.json)
4. Luis grabs the model via huggingface-cli + the template via git
5. (Sometime later) civitai community starts publishing LoRAs on top of it
```

For the "stay current" workflow, watching HF is upstream of watching civitai. By the time a model hits civitai's discovery surface, kijai's quantized variants and Comfy-Org's templates have been on HF for days/weeks.

## A practical "watch list" pattern

Bookmark these org pages and re-visit weekly to spot new releases:

```
https://huggingface.co/black-forest-labs    # Flux family
https://huggingface.co/Comfy-Org             # ComfyUI-packaged versions
https://huggingface.co/Kijai                 # quantized variants + WanVideoWrapper updates
https://huggingface.co/city96                # GGUF for everything
https://huggingface.co/lightx2v              # Lightning LoRAs
https://huggingface.co/Wan-Video             # official Wan team
https://huggingface.co/alibaba-pai           # Alibaba experimental ("Fun" variants)
```

Each org page shows their latest uploads with timestamps — easy to scan.

## Caveat about this reference

The fetched homepage and `/models` page are verified live (2026-05-09). Specific endpoint signatures, the `huggingface_hub` Python library API, the org descriptions, and the model layout details are synthesized from prior knowledge (accurate to mid-2025; HF evolves but core API has been stable for years).

If the API surface changes, the canonical docs are at `https://huggingface.co/docs/huggingface_hub` and `https://huggingface.co/docs/api-inference`. The Python library is open-source at `https://github.com/huggingface/huggingface_hub`.
