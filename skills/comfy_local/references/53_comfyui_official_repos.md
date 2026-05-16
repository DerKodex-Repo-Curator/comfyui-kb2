---
name: comfyanonymous/ComfyUI + Comfy-Org/workflow_templates — official repos
description: The two key GitHub repos that drive the platform. ComfyUI core release cycle (weekly), three-repo split (core/desktop/frontend), Luis's installed version 0.19.3, recent commits already merged, full model coverage list, complete 42-template inventory with NEW templates flagged, frontend keyboard shortcuts.
type: reference
---

# Official ComfyUI repositories

The two repos that define the platform's official surface.

**Read date:** 2026-05-09. Most data verified from local clones (Luis's `ComfyUI/` install + cloned `workflow_templates/` package). Recent commits read directly from `git log` on the local install.

## The three interconnected repos (per ComfyUI README)

| Repo | URL | Cadence | What it is |
|---|---|---|---|
| **ComfyUI Core** | `github.com/comfyanonymous/ComfyUI` | Weekly stable releases (target: Mondays). Patch versions for fixes backported onto current stable. | Source of truth — Python algorithm code, the executor, the API server, all `comfy_extras/` nodes |
| **ComfyUI Desktop** | `github.com/Comfy-Org/desktop` | Builds new release using latest stable core | Electron-wrapped distribution (Windows + macOS). What end users install instead of running Python locally. |
| **ComfyUI Frontend** | `github.com/Comfy-Org/ComfyUI_frontend` | Frontend updates merged into core every 2+ weeks. Features frozen before each core release. | The TypeScript/Vue web UI. Distributed as the `comfyui-frontend-package` PyPI package. |

For Luis's portable install (`G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\ComfyUI\`), only **Core** matters operationally — the Desktop wrapper is for users who don't want to manage Python. The Frontend is bundled inside Core's release.

## Luis's current install: ComfyUI 0.19.3

Per `pyproject.toml`:
```toml
[project]
name = "ComfyUI"
version = "0.19.3"
requires-python = ">=3.10"
```

Frontend bundled: `comfyui-frontend-package` 1.42.14 (latest as of 2026-05-09 per the `Bump comfyui-frontend-package` commit on the install).

## Recent commits already in Luis's install (last 30 affecting `comfy/` algorithm core)

These are NEW capabilities Luis already has, sorted newest first:

| Commit | What it adds |
|---|---|
| RIFE and FILM frame interpolation (CORE-29) | Frame-interpolation models for smoothing video output |
| LTXV audio VAEs (standalone + native) | LTX-Video audio VAE support |
| Ernie inference optimizations | Faster ERNIE-Image |
| **SUPIR model support (CORE-17)** | Image upscaling/restoration via SUPIR |
| ErnieTEModel class refactor | ERNIE text encoder cleanup |
| OOM regression fix for quantized models | Memory fix |
| Ernie fp64 device compat | ERNIE on hardware without fp64 |
| Ministral text generation | Ministral LLM support |
| **Implement Ernie Image model** | ERNIE-Image baseline |
| `supports_fp64` function | Hardware capability check |
| **SDPose: resize input always** | Pose detector input handling fix |
| **Small Flux 2 decoder** | Flux 2 lighter decoder variant |
| **Ace Step 1.5 XL** | ACE Step audio model |
| RAM cache integration with model RAM management | Memory optimization |
| Flux conditioning without pooled output | Flux flexibility |
| LTX2 reference audio (ID-LoRA) | LTX2 voice/identity LoRA |
| **LongCat-Image edit** | LongCat image edit support |
| Wan VAE light/color fix | Wan output color accuracy |
| FP16 intermediates fix | Numerical fix |

And recent `comfy_extras/` (newer specialized nodes):

| Commit | What it adds |
|---|---|
| `JsonExtractString` node | Pull a string field out of JSON in workflow |
| `ImageUpscaleWithModel` intermediate dtype fix | Upscale plays nice with bf16 |
| Image histogram node | Histogram visualization |
| CURVE node | Curve adjustment node (animation/interp) |
| Painter node | Inline drawing/painting node |
| Number Convert node | Type conversion utility |
| Train LoRA bfloat16 fix | LoRA training stability |
| `slice_cond` + per-model context window cond resizing | Conditioning handling |
| `essentials_category` flag for Essentials tab | UI organization |

**Practical implication:** Luis's install is bleeding-edge. RIFE/FILM frame interpolation, SUPIR upscaling, Ace Step 1.5 XL audio, LongCat-Image edit, and Capybara model are all ALREADY in his install but not yet documented in his existing reference files. If he wants to use them, the `comfy_extras` survey (ref 40) would benefit from a refresh.

## Models officially supported (per README — the complete list)

### Image generation
- SD 1.x, SD 2.x (with unCLIP)
- SDXL, SDXL Turbo
- Stable Cascade
- SD3, SD3.5
- Pixart Alpha, Pixart Sigma
- AuraFlow
- HunyuanDiT
- **Flux** (dev / schnell)
- Lumina Image 2.0
- **HiDream**
- **Qwen Image**
- Hunyuan Image 2.1
- **Flux 2**
- **Z Image**

### Image editing
- Omnigen 2
- Flux Kontext
- HiDream E1.1
- Qwen Image Edit

### Video
- Stable Video Diffusion
- Mochi
- LTX-Video (LTX, LTX2)
- Hunyuan Video, Hunyuan Video 1.5
- **Wan 2.1, Wan 2.2**

### Audio
- Stable Audio
- ACE Step (1.5 XL is now in Luis's install)

### 3D
- Hunyuan3D 2.0

**Bold = primary models in Luis's runner suite.** The list also implicitly covers ERNIE Image, Capybara, LongCat-Image, RT-DETRv4 (detection), SUPIR (upscale), and others added via recent commits but not yet reflected in the README's curated list.

## Workflow templates — full 42-template inventory

The `Comfy-Org/workflow_templates` package (currently pinned to `v0.9.59`) bundles 42 templates split across categories. Local clone is at `.claude/skills/comfy_local/workflows/comfy_org_canonical_templates/`.

### Image generation / editing (24 templates — `image_*` prefix)

```
image_flux2.json                              Flux 2 dev T2I
image_flux2_fp8.json                          Flux 2 dev T2I (fp8 variant)
image_flux2_text_to_image.json                Flux 2 T2I default
image_flux2_text_to_image_9b.json             Flux 2 9B T2I

image_flux2_klein_text_to_image.json          Klein T2I
image_flux2_klein_image_edit_4b_base.json     Klein 4B base edit
image_flux2_klein_image_edit_4b_distilled.json Klein 4B distilled edit
image_flux2_klein_image_edit_9b_base.json     Klein 9B base edit
image_flux2_klein_image_edit_9b_distilled.json Klein 9B distilled edit (used by enemy_biome_themed.py)
image_flux2_klein_9b_kv_image_edit.json       Klein 9B KV-cache image edit (NEW — KV optimization)

image_qwen_image.json                         Qwen-Image base T2I
image_qwen_image_2512_with_2steps_lora.json   Qwen 2512 + Wuli 2-step Lightning
image_qwen_Image_2512_controlnet.json         Qwen 2512 ControlNet
image_qwen_image_controlnet_patch.json        Qwen ControlNet via model patch
image_qwen_image_edit.json                    Qwen-Image-Edit base
image_qwen_image_edit_2509.json               Qwen-Image-Edit 2509 (used by qwen_edit_lightning.py)
image_qwen_image_edit_2509_relight.json       Qwen 2509 with relighting variant
image_qwen_image_edit_2511.json               Qwen-Image-Edit 2511 (NEWER than 2509)
image_qwen_image_layered.json                 Qwen-Image-Layered (RGBA decomposition)
image_qwen_image_layered_control.json         Qwen-Image-Layered + ControlNet
image_qwen_image_instantx_controlnet.json     InstantX ControlNet for Qwen
image_qwen_image_instantx_inpainting_controlnet.json InstantX Inpainting ControlNet
image_qwen_image_union_control_lora.json      Union ControlNet via LoRA

image_chrono_edit_14B.json                    ChronoEdit 14B
```

### API-call templates (8 templates — `api_*` prefix)

These hit paid external APIs (BFL, Google, Recraft, ByteDance) instead of local generation. Drop-in proof-of-concept for any of these services:

```
api_flux2.json                                BFL Flux 2 API
api_bfl_flux2_max_sofa_swap.json              BFL Flux 2 Max — image edit
api_bfl_flux_1_kontext_max_image.json         BFL Flux Kontext Max
api_bfl_flux_1_kontext_pro_image.json         BFL Flux Kontext Pro
api_bfl_flux_1_kontext_multiple_images_input.json Kontext multi-image input
api_google_nano_banana2_image_edit.json       Nano Banana 2 (Gemini) image edit
api_nano_banana_pro.json                      Nano Banana Pro variant
api_recraft_style_reference.json              Recraft style reference
```

### Tutorial templates (2 templates — `template_*` prefix)

```
template_qwen_image_illustration_lora.json    LoRA training tutorial workflow
template_sugar_coated_gummy_style_qwen.json   Specific style demonstration
```

### NEW model templates (Capybara — added recently)

```
Image_capybara_v0_1_text_to_image.json        Capybara v0.1 T2I
Image_capybara_v0_1_image_edit.json           Capybara v0.1 image edit
```

Capybara is a NEWLY supported image gen model (post-cutoff for me, surfaced via recent commits). Worth a look if Luis wants to test something fresh.

### 3D (2 templates — `3d_*` prefix)

```
3d_hunyuan3d_multiview_to_model.json          Hunyuan3D 2.0 multiview → 3D model
3d_hunyuan3d_multiview_to_model_turbo.json    Turbo variant
```

Both are "give me 4-6 views of an object → get a textured 3D mesh." Direct potential application to Luis's game work — generate cel-shaded character art, then turn into a 3D model.

### Misc / legacy (4 templates)

```
01_get_started_text_to_image.json             SD 1.5 hello-world starter
02_qwen_Image_edit_subgraphed.json            Qwen edit demonstrating subgraph pattern
flux_kontext_dev_basic.json                   Flux Kontext basic
flux1_dev_uso_reference_image_gen.json        Flux 1 dev + USO (Unified Style Object) reference
```

### NEW templates worth flagging since reference 27 was written

| Template | What's new |
|---|---|
| `Image_capybara_v0_1_*` | Capybara — new image gen model |
| `image_flux2_klein_9b_kv_image_edit.json` | KV-cache optimization for Klein 9B edit |
| `image_qwen_image_edit_2511.json` | Qwen-Image-Edit 2511 (replaces 2509 for newest work) |
| `image_qwen_image_layered_control.json` | Layered + ControlNet combo |
| `image_qwen_image_union_control_lora.json` | Union ControlNet expressed as a LoRA |
| `image_chrono_edit_14B.json` | ChronoEdit 14B |
| `flux1_dev_uso_reference_image_gen.json` | USO reference-style generation |
| `template_qwen_image_illustration_lora.json` | Tutorial template — illustration LoRA |
| `template_sugar_coated_gummy_style_qwen.json` | Tutorial template — specific style |

## ComfyUI release cycle

Per the README: **Weekly stable releases targeting Mondays.** Patch versions for fixes backported onto current stable.

Version scheme:
- `0.19.3` — current stable on Luis's install
- Minor bump (`0.20.0`) — features merged from master
- Patch bump (`0.19.4`) — fixes backported to current stable

**For Luis's update strategy:** the project root has `Update ComfyUI*.bat` files that pull master. Per CLAUDE.md rule #6: don't recommend running these without explicit approval — master commits "may be very unstable and break many custom nodes" per the README. Wait for stable releases or read the recent commits before pulling.

## ComfyUI keyboard shortcuts (from README)

| Shortcut | Action |
|---|---|
| `Ctrl+Enter` | Queue current graph |
| `Ctrl+Shift+Enter` | Queue as FIRST in line (jump queue) |
| `Ctrl+Alt+Enter` | Cancel current generation |
| `Ctrl+Z` / `Ctrl+Y` | Undo / Redo |
| `Ctrl+S` / `Ctrl+O` | Save / Load workflow |
| `Ctrl+A` | Select all nodes |
| `Alt+C` | Collapse/uncollapse selected |
| `Ctrl+M` | **Mute** selected (mode 2 — disables node entirely, breaks downstream) |
| `Ctrl+B` | **Bypass** selected (mode 4 — passes data through unprocessed, downstream still runs) |
| `Delete`/`Backspace` | Delete selected nodes |
| `Ctrl+Backspace` | Delete entire graph |
| `Space` (held) | Pan the canvas |
| `Ctrl/Shift+Click` | Add to selection |
| `Ctrl+C/V` | Copy/paste (no connections) |
| `Ctrl+C/Ctrl+Shift+V` | Copy/paste WITH connections from upstream |
| `Shift+Drag` | Move multiple selected nodes simultaneously |
| `Ctrl+D` | Load default graph |
| `Alt + +/-` | Canvas zoom in/out |
| `Ctrl+Shift+LMB+drag vertical` | Canvas zoom |
| `P` | Pin/unpin selected nodes |
| `Ctrl+G` | Group selected nodes |
| `Q` | Toggle queue visibility |
| `H` | Toggle history visibility |
| `R` | Refresh graph (re-read models from disk — important after adding new files!) |
| `F` | Show/hide menu |
| `.` | Fit view to selection (or whole graph if nothing selected) |
| Double-click LMB | Open node quick-search palette |
| `Shift+Drag` (on wires) | Move multiple wires at once |
| `Ctrl+Alt+LMB` (on slot) | Disconnect ALL wires from clicked slot |

`Ctrl` → `Cmd` on macOS.

**Key shortcut to remember:** `R` to refresh after dropping a new model file in `G:\models\` — without it, ComfyUI doesn't see the new file in dropdowns.

**Mute (Ctrl+M) vs Bypass (Ctrl+B) distinction matters** (per ref 33): mute disables the node and breaks downstream; bypass passes data through unprocessed, downstream still runs. For LoRA loaders specifically, bypass is the right toggle because the model still flows through; mute would break the chain.

## Where to track new releases

For Luis's "stay current" workflow:

- **Releases page:** `github.com/comfyanonymous/ComfyUI/releases` — weekly tags with notes
- **Master branch commits:** `github.com/comfyanonymous/ComfyUI/commits/master` — leading-edge but unstable
- **comfy_extras commits** specifically: `github.com/comfyanonymous/ComfyUI/commits/master/comfy_extras` — new node types appear here first
- **workflow_templates releases:** `github.com/Comfy-Org/workflow_templates/releases` — new template additions
- **Frontend changelog:** `github.com/Comfy-Org/ComfyUI_frontend/releases` — UI/UX changes
- **Comfy-Org docs:** `docs.comfy.org` — tutorials and how-to guides

**Recommendation for Luis:** rather than constantly polling, watch the workflow_templates repo specifically. New templates land there only after the underlying model has been merged into core, so a new template = "the model is now stable enough to package as a recommended workflow." That's the strongest signal that a model is production-ready.

## How the official repos relate to the rest of Luis's stack

```
github.com/comfyanonymous/ComfyUI (Core)
   ↓ ships as
ComfyUI 0.19.3 in G:\...\ComfyUI-Easy-Install\ComfyUI\
   ↓ provides
nodes.py + comfy/ + comfy_extras/ + execution.py + folder_paths.py
   ↓ called by
runners/*.py via /prompt API submissions

github.com/Comfy-Org/workflow_templates (Templates)
   ↓ ships as
comfyui-workflow-templates PyPI package (pinned to v0.9.59)
   ↓ accessible via
Templates browser in the ComfyUI UI
   ↓ also cloned to
.claude/skills/comfy_local/workflows/comfy_org_canonical_templates/

github.com/Comfy-Org/ComfyUI_frontend (Frontend)
   ↓ ships as
comfyui-frontend-package PyPI 1.42.14
   ↓ embedded inside
ComfyUI core release
   ↓ provides
The web UI at localhost:8188
```

## Practical takeaways

1. **Luis's install is current.** 0.19.3 + Frontend 1.42.14 + templates v0.9.59 are all latest stable as of 2026-05-09.

2. **He has features his existing references don't yet document.** RIFE/FILM frame interpolation, SUPIR, ACE Step 1.5 XL, ERNIE Image, LongCat-Image, Capybara are all merged but not yet in references 40 / 11 / 33 / etc. Worth a refresh pass on those references later.

3. **The Capybara templates are interesting unexplored territory.** Capybara v0.1 has both T2I and image-edit templates. Could test against existing runners to see if it's worth adding to the runner suite.

4. **The `image_flux2_klein_9b_kv_image_edit.json` template** is a NEW Klein 9B variant using KV-cache optimization. Faster than the regular Klein 9B image-edit pipeline. Worth comparing against `enemy_biome_themed.py` to see if Claude Code should switch to the KV variant.

5. **Three GitHub repos to watch for new functionality**, ranked by signal-to-noise: workflow_templates > Core > Frontend.
