---
name: Comfy Cloud + Partner Nodes + Registry API + Cloud API + Utility tutorials
description: The four docs.comfy.org sections we skipped earlier. Comfy Cloud (managed offering, 5-tier pricing, 96GB Blackwell GPUs). Partner Nodes (closed-source model integration via credits — alternative to NanoBanana2Direct path). Cloud API (~30 REST endpoints for programmatic Cloud workflows). Registry API (~50 REST endpoints for custom node publishing). Utility tutorials (frame interpolation + video upscale empirical numbers).
type: reference
---

# Comfy Cloud + Partner Nodes + Registry API + Cloud API

Compact umbrella covering four sections of `docs.comfy.org` skipped earlier — for completeness, not because Luis urgently needs any of them. Each section is brief; expand if a specific use case emerges.

**Read date:** 2026-05-09

---

## 1. Comfy Cloud — managed ComfyUI hosting

Source: `docs.comfy.org/get_started/cloud` + `comfy.org/cloud/pricing`

### What it is

Same ComfyUI Luis runs locally, hosted on Comfy-Org's infrastructure. **All models + custom nodes pre-installed.** Web UI, no installation. Powered by **Blackwell RTX 6000 Pro** GPUs with **96 GB VRAM** (vs Luis's 5090 32 GB — fits Flux 2 dev 24B without offloading).

### Pricing tiers (verified 2026-05-09)

| Tier | $/mo | Credits | Approx output | Runtime cap | Concurrent jobs | Custom LoRA import |
|---|---|---|---|---|---|---|
| **FREE** | $0 | 400 | ~35 5s videos | 10 min | 1 | No |
| **STANDARD** | $20 | 4,200 | ~380 5s videos | 30 min | 1 | No |
| **CREATOR** *(most popular)* | $35 | 7,400 | ~670 5s videos | 30 min | **3** | **Yes (civitai + HF)** |
| **PRO** | $100 | 21,100 | ~1,915 5s videos | 60 min | 5 | Yes |
| **ENTERPRISE** | contact | — | — | — | — | — |

Credit math: ~12 credits per 5-second Wan 2.2 i2v video at default settings (81 frames, 18fps, 640×640, 4-step sampler). Cost scales with model + steps + resolution + frames.

### Key facts

- **Only billed for active GPU time.** Idle workflow-building is free.
- **Top-up credits** can be added anytime, **roll over for 1 year**.
- **900+ pre-installed models** (no manual downloads).
- **Job queue: up to 100 workflows** at once.
- **Custom node support is limited** to a curated set (expanding) — not arbitrary like local.
- **Custom LoRA import** is Creator tier or higher (civitai now, HF coming soon).
- **Partner Nodes** (paid model APIs) consume the same credits as workflow runtime.

### When Luis would want Comfy Cloud

Honestly — **rarely.** With a 5090 + 64 GB RAM at home:
- Local is free
- Local has all 50+ custom nodes (not just the curated subset)
- Local datasets stay private
- Local has full control

Comfy Cloud only makes sense if:
1. **Traveling** without the workstation
2. **Short-term scale need** (one-off batch of 100+ generations for a deadline) where parallel cloud GPUs beat single 5090
3. **Onboarding teammates** who don't have GPUs — let them work alongside without buying hardware
4. **Testing on a 96 GB GPU** for full Flux 2 dev fine-tunes that won't fit locally

For everything else, local wins. The Free tier (400 credits) is fine for sporadic remote use.

---

## 2. Partner Nodes — ComfyUI's official paid-API integration

Source: `docs.comfy.org/tutorials/partner-nodes/overview`

### What they are

Built-in nodes that call closed-source/paid models (Black Forest Labs, ByteDance, Google, OpenAI, Recraft, Kling, Runway, Hunyuan 3D, Meshy, Tripo, Rodin, Wan, Bria, Reve, Luma, Moonvalley, Stability AI, Ideogram, HappyHorse, Sonilo, etc.) directly from the ComfyUI canvas. **20+ partner integrations.**

### How they differ from Luis's `NanoBanana2Direct` custom node

| Aspect | NanoBanana2Direct (Luis's runner uses this) | Partner Node (built-in Google) |
|---|---|---|
| Auth | Your own Google API key in the node | ComfyUI Account API Key |
| Billing | Direct from Google | ComfyUI credits (prepaid Stripe) |
| Setup | Paste API key once | Login to Comfy account, buy credits |
| Where credits come from | None — pay Google directly | Same credits as Comfy Cloud subscription |

**Economically:** Luis's path (direct Google API) is cheaper since he's not paying Comfy-Org's margin. Partner Nodes are convenient if you don't want to manage individual provider API keys, but cost more per call.

### Credits also work locally

Important: **Partner Node credits work both in Comfy Cloud AND in local ComfyUI** if you log in with your Comfy account on local. So a Comfy Cloud subscription gives you credits that can drive Partner Nodes in your local install too.

### Two distinct API key concepts (don't confuse)

1. **ComfyUI Account API Key** — for Partner Node calls in workflows. Generate at `platform.comfy.org/profile/api-keys`. Used in the `X-API-Key` header for both Cloud API and Partner Node auth.
2. **Registry Publishing API Key (PAT)** — for developers publishing custom node packs to the Registry. Generated separately. Used by `comfy-cli publish` etc.

### `--disable-api-nodes` flag

Adding this launch flag to ComfyUI:
- Disables ALL Partner Nodes
- Prevents the frontend from communicating with the internet
- Pure-local operation guarantee

For privacy-sensitive work, this is the lockdown switch. Luis's `Start ComfyUI.bat` doesn't have it — Partner Nodes ARE available in his install if he logs in.

### Network requirements

- Local network: only `127.0.0.1` or `localhost` allowed for direct browser login
- LAN or non-whitelisted: must use API Key login flow
- HTTPS required

### Whether Luis should use Partner Nodes

**Probably not** for current work. He has Google's API key direct, NanoBanana2Direct already in his runner suite. Adding Partner Nodes would be a parallel/duplicate path. Worth knowing the option exists if a specific provider's model isn't accessible directly (Tripo / Rodin / Meshy 3D model APIs, etc.).

---

## 3. Cloud API — programmatic access to Comfy Cloud

Source: `docs.comfy.org/api-reference/cloud/...`

Base URL: `https://cloud.comfy.org/api/`
Auth: `X-API-Key` header (ComfyUI Account API Key)

### Endpoint surface (~30 endpoints across 7 categories)

**workflow (5):**
- `GET /api/prompt` — current execution status
- `POST` submit a workflow for execution
- `GET` available workflow templates
- `GET` available subgraph blueprints
- `GET` specific subgraph blueprint by ID

**node (2):**
- `GET` all node info (mirrors local `/object_info`)
- `GET` server feature flags

**model (3):**
- `GET` available model folders
- `GET` models in a specific folder
- `GET` model preview image

**job (9):**
- `POST` manage execution history
- `GET` list jobs (paginated/filtered)
- `GET` full job details / job status / queue info
- `POST` interrupt running jobs
- `POST` manage queue operations
- (plus 2 deprecated history endpoints)

**file (4):**
- `GET` view a file
- `GET` related mask layer files
- `POST` upload image / mask

**asset (13):**
- LIST/GET/CREATE/UPDATE/DELETE for cloud-hosted assets (images, videos, generated content, custom LoRAs)
- Tag management (add/remove/list/histogram)
- Hash-based existence check (`HEAD`)
- Initiate background download for large files

**user (5):**
- List / get / upload / delete user data files
- Get current user info

**system (1):**
- Get system statistics

### When this matters for Luis

If he ever wants to:
- Submit workflows to Comfy Cloud from his local machine programmatically (alternative to fal.ai's API for hosted inference)
- Build a tool that lets external users trigger his workflows on cloud GPUs
- Bridge between his local runner suite and Comfy Cloud as a fallback when local hardware is busy

Otherwise, his existing local `/prompt` API submission path (per ref 12, 41) is what he uses daily.

---

## 4. Registry API — for publishing custom node packs

Source: `docs.comfy.org/api-reference/admin/...` + `/api-reference/registry/...`

Base URL: `https://api.comfy.org/`

### Endpoint surface (~50 endpoints)

**Admin (1):**
- `POST /admin/generate-token` — short-lived JWT (1-hour expiry) for browser-based admin operations. Requires Firebase auth + admin privileges.

**Registry — 4 conceptual layers:**

1. **Publishers** — your account / org on the registry
   - Create / get / update / delete publisher
   - Validate username availability
   - Permissions per publisher

2. **Nodes** — your node pack (pip-installable)
   - Create / retrieve / update / delete a node pack
   - Claim a nodeId for a publisher
   - List all packs

3. **Node Versions** — releases of a pack
   - List versions
   - Retrieve specific version
   - Publish new version (the actual `comfy node publish` action)
   - Update changelog / deprecation status
   - Unpublish a version

4. **comfy-nodes** — individual Python node classes within a pack
   - List / retrieve / create / update
   - Get by ComfyUI node name (e.g., "KSampler" or "WanVideoModelLoader")

**PAT (Personal Access Tokens):**
- Create / delete

**Reviews + Translations:**
- Add review to a node version
- Create node translations (multilingual node descriptions)

### Plus other API surface in the Registry docs:

**Freepik (~12 endpoints):** relight, style transfer, upscale (Magnific / Precision V2), skin enhancer (Creative / Faithful / Flexible). Comfy-Org integrated Freepik's image-editing services as Partner Node-style API calls.

**Vidu API Nodes (~7 endpoints):** Vidu video model proxying — img2video, ref2video, multi-frame, start-end-to-video, text2video.

**Releases (1):** Get release notes.

### When this matters for Luis

When he eventually publishes a custom node pack (the `[tool.comfy]` config from ref 56). Practical flow:

1. Sign up at `comfyregistry.org` → pick a `PublisherId` (one-time)
2. Add `[tool.comfy]` block to `pyproject.toml`:
   ```toml
   [tool.comfy]
   PublisherId = "luis-pop"
   DisplayName = "POP-Studio-Tools"
   Icon = "..."
   ```
3. Generate a Personal Access Token (PAT) at the Registry
4. Run `comfy node publish` from the pack directory — this hits `POST /api/v1/publishers/{id}/nodes/{node-id}/versions` with the PAT
5. Pack appears in ComfyUI Manager's install list

Until he publishes a pack, the Registry API is informational only.

---

## 5. Tutorials we skipped — what's actually there

### Utility tutorials (confirmed structure)

`docs.comfy.org/tutorials/utility/`:
- **Preprocessors** — image/data prep utilities (input pre-processing for ControlNet etc.)
- **Frame interpolation** — RIFE/FILM tutorials (this is the canonical entry point for ref 53's RIFE/FILM mention)
- **Image upscale** — local image upscaling models (ESRGAN variants)
- **Video upscale** — full benchmark-driven guide (covered below)

### Video upscale empirical findings (verbatim from the docs)

Comfy-Org published actual benchmark numbers for video upscaling. Bookmark-worthy:

**TL;DR per their guide:**
- **Quality mode:** SeedVR2 + HitPaw deliver most accurate temporal consistency
- **Speed mode:** FlashVSR + HitPaw fastest
- **AI video fix (cleaning up generated video):** Topaz Astra Creative
- **Archival restoration:** SeedVR2 (preserves original structure)
- **CGI/3D render:** Topaz, SeedVR2, HitPaw all clean

**Speed comparison on 10-second 720p clips:**

| Model | Output res | Time |
|---|---|---|
| FlashVSR (local) | 1080p | ~41s |
| FlashVSR (local) | 4K | ~52s |
| HitPaw | 2K | ~80s |
| HitPaw | 4K | ~175s |
| **SeedVR2 (local, 5090)** | **1080p** | **~312s** |
| Topaz Astra (Partner) | 1080p | ~374s |
| Topaz Astra (Partner) | 4K | ~560s |

**SeedVR2 on 5090 = 312s** for 10s of 720p→1080p — Luis's exact hardware. Useful baseline. He has SeedVR2 installed (per ref 57); needs the weights.

### 3D tutorials structure (nav surfaced, contents not deeply fetched)

`docs.comfy.org/tutorials/3d/` contains tutorials for Hunyuan3D 2.0 (the "multiview to 3D mesh" pipeline you saw in ref 53 templates `3d_hunyuan3d_multiview_to_model.json` etc.). The canonical workflow: generate 4-6 views of an object via image gen → feed into Hunyuan3D → get a textured 3D mesh. Direct application for game asset prototyping.

### Audio tutorials structure (nav surfaced, contents not deeply fetched)

`docs.comfy.org/tutorials/audio/` covers Stable Audio + ACE Step (latest in core per ref 53 — "ACE Step 1.5 XL"). Out of Luis's current scope unless he eventually wants game music / SFX generation.

---

## 6. Comparison table — when to use which paid surface

For when Luis hits a need beyond his local 5090:

| Service | Best for | Cost model |
|---|---|---|
| **Comfy Cloud** | Same UI as local, just hosted. Travel, team onboarding, occasional 96GB-GPU need | Monthly subscription + credits |
| **Comfy Cloud Partner Nodes** | Quick API access to closed-source models without managing individual API keys | Credits per call |
| **Local ComfyUI + own provider API keys** (Luis's current path with NanoBanana2Direct) | Cost-optimal for high-volume single-provider use | Direct provider billing |
| **fal.ai Compute** (ref 58) | LoRA training, full fine-tunes, multi-GPU H100 | Per-hour |
| **fal.ai Model APIs** | Fallback hosted inference for hardware-busy days | Per-second |
| **Cloud API** (Comfy Cloud's REST surface) | Programmatic submission to Cloud from your local code | Same as Comfy Cloud |
| **Registry API** | Publishing your own node packs | Free (publisher account) |

**For Luis's current work:** local ComfyUI + own API keys + fal Compute when he ever needs training scale. The Comfy Cloud / Partner Nodes / Cloud API tier is currently overkill for solo work, becomes relevant if he ever onboards POP teammates onto the workflow infrastructure.

---

## 7. New URLs worth bookmarking

- `docs.comfy.org/llms.txt` — full documentation index optimized for LLM ingestion (programmatic access to all docs pages)
- `platform.comfy.org/profile/api-keys` — generate ComfyUI Account API Key
- `comfyregistry.org` — sign up as publisher
- `cloud.comfy.org` — Comfy Cloud web app

---

## What this reference adds

Closes four gaps left by earlier references:

| Gap | Now covered |
|---|---|
| Comfy Cloud pricing tiers | ref 59 §1 |
| Partner Nodes (paid API model integration) | ref 59 §2 |
| Cloud API surface (~30 REST endpoints) | ref 59 §3 |
| Registry API for publishing | ref 59 §4 |
| Utility tutorials structure + video upscale benchmarks | ref 59 §5 |
| Two distinct API key concepts (Account vs Registry PAT) | ref 59 §2 |

3D and Audio tutorials are flagged but not deep-dived — they're outside Luis's current scope. If Hunyuan3D becomes relevant for game asset generation (very plausible — generate 2D character → 4-view multi-perspective → Hunyuan3D mesh), the entry point is `docs.comfy.org/tutorials/3d/hunyuan3D-2`.
