---
name: kijai (Jukka Seppänen) — repo catalog and notable works
description: Verified status of kijai's pinned repos in Luis's install (all 4 present), notable other repos from kijai's 106-repo catalog worth considering, his HF account for quantized model weights, and how to follow his work.
type: reference
---

# kijai (Jukka Seppänen) repos

**About:** Jukka Seppänen, Finland-based developer. 106 repos on GitHub, 6.1k followers. The single most prolific author of ComfyUI custom nodes. Maintains wrappers for almost every video model that exists, plus the ubiquitous KJNodes utility pack.

**Verified from fetch (2026-05-09):** kijai's GitHub overview shows **4 pinned repos**, **all 4 already installed** in Luis's ComfyUI. He has more in his catalog (106 total) but not all are equally maintained or relevant.

## Installed in Luis's ComfyUI (verified)

| Pack | Stars | What it does | Relevance |
|---|---|---|---|
| **ComfyUI-WanVideoWrapper** | 6.4k | Comprehensive Wan 2.1/2.2 video pipeline. Adds 80+ Wan-specific nodes. Updates faster than core ComfyUI's Wan support. | Core dependency of `runners/wan_t2v.py` (ref 07, 28) |
| **ComfyUI-KJNodes** | 2.6k | Utility node pack — `Set/Get` (named variables for graph cleanup), `ImageBatchMulti`, `ModelSamplingAuraFlow` was originally here, `WidgetToString`, `Mathematical Eval`, `Noise Generators`, etc. | Used in many runner workflows for the Set/Get pattern |
| **ComfyUI-WanAnimatePreprocess** | 512 | Preprocessing for Wan-Animate (face/pose extraction for character animation) | Specific to Wan-Animate workflow |
| **ComfyUI-SCAIL-Pose** | 309 | SCAIL pose driving for Wan video | Specific to SCAIL pose-driven Wan |

**Practical note:** kijai's WanVideoWrapper is updated multiple times per week. When new Wan-related models or features land (RealisDance, Stand-In, WanAnimate, MTV, FantasyTalking, etc.), they appear here within hours-days. This is the fastest-moving repo in the ecosystem Luis depends on.

## Notable other kijai repos worth considering (from prior knowledge, not all live-verified)

These are kijai's repos I know of from prior knowledge of the ComfyUI ecosystem. Verify availability and current state at `github.com/kijai?tab=repositories` before relying on any specific one — kijai sometimes archives older wrappers when their model has been integrated into ComfyUI core.

### Vision / understanding (useful for LoRA training data prep)

| Repo | Purpose | Relevance for Luis |
|---|---|---|
| **ComfyUI-Florence2** | Microsoft Florence-2 vision-language wrapper. Image captioning / object detection / segmentation. | **HIGH — for LoRA training.** When you train POP house-style LoRA, you'll want auto-captions on your dataset (per ai-toolkit's caption requirements). Florence-2 is a top-tier captioner. |
| **ComfyUI-DepthAnythingV2** | DepthAnything V2 wrapper (depth estimation) | Possibly redundant with `comfyui_controlnet_aux`'s `DepthAnythingV2Preprocessor` — verify which one Luis's `runners/zimage_controlnet.py --mode depth` is hitting. |
| **ComfyUI-Marigold** | Marigold depth estimator (older, more atmospheric) | Alternative depth source. Lower priority than DAv2. |
| **ComfyUI-segment-anything-2** | SAM2 (Segment Anything 2) wrapper | Useful for masking workflows. Drops into ImpactPack-style detail-on-region pipelines. |
| **ComfyUI-MoGe** | MoGe depth model | Another depth alternative. |
| **ComfyUI-Geowizard** | Geowizard depth + normal estimator | Niche alternative. |

### Video models (alternatives / complements to Wan)

| Repo | Purpose | Relevance for Luis |
|---|---|---|
| **ComfyUI-HunyuanVideoWrapper** | Tencent's Hunyuan Video wrapper | Alternative to Wan for video. Hunyuan Video is a competing video model; ComfyUI core has basic support, kijai's wrapper has the rich feature set. |
| **ComfyUI-CogVideoXWrapper** | CogVideoX wrapper | Another video model alternative. Older, smaller community. |
| **ComfyUI-MochiWrapper** | Mochi-1 wrapper | Older video model. Mostly historical interest. |
| **ComfyUI-HunyuanVideoMultiLora** | Multi-LoRA support for Hunyuan Video | If Luis pivots to Hunyuan video, useful for stacking multiple LoRAs. |
| **ComfyUI-LivePortraitKJ** | LivePortrait — animate still portraits with reference video driving | Could animate cel-shaded character art into talking-head shots. Niche but creative. |

### Audio / multi-modal

| Repo | Purpose | Relevance for Luis |
|---|---|---|
| **ComfyUI-StableAudioOpen** | Stable Audio Open wrapper | Audio generation. Out of Luis's current scope. |
| **ComfyUI-GLM-4-Voice** | GLM-4 voice model | Speech synthesis / voice cloning. Out of scope. |

### Image enhancement / restoration

| Repo | Purpose | Relevance for Luis |
|---|---|---|
| **ComfyUI-CCSR** | Content-Consistent Super-Resolution | Upscaling for image restoration. Possible alternative to SUPIR (which is now in core, ref 53). |
| **ComfyUI-DDColor** | Black-and-white colorization | Niche. |

### Lumina / older diffusion models

| Repo | Purpose | Relevance for Luis |
|---|---|---|
| **ComfyUI-LuminaWrapper** | Lumina model wrapper (pre-Lumina2) | Lumina2 is Z-Image's foundation. The wrapper is older but historical. Z-Image-Turbo is now in core, so this is mostly redundant. |
| **ComfyUI-DiffusersStableCascade** | Stable Cascade via diffusers | Stable Cascade is now in core. Historical. |
| **ComfyUI-DiffusersWuerstchenWrapper** | Würstchen via diffusers | Predecessor to Stable Cascade. Historical. |
| **ComfyUI-ELLA** | ELLA — Equip Large Language model with Diffusion | LLM-augmented prompting for SD. Niche. |

### Training (relevant when Luis builds his POP LoRA)

| Repo | Purpose | Relevance for Luis |
|---|---|---|
| **ComfyUI-FluxTrainer** | Train Flux LoRAs inside ComfyUI | **HIGH — alternative to ai-toolkit.** If you want to train without leaving ComfyUI, this packages the training pipeline as nodes. Trade-off: less control than ai-toolkit's YAML configs, but no separate venv to manage. |

### Misc

| Repo | Purpose |
|---|---|
| **ComfyUI-ModelDownloader** | Programmatic model download nodes |
| **ComfyUI_MagicClothing** | Garment-swap / virtual try-on |
| **Kijai/WanVideo_comfy** (HF — not GitHub) | Quantized Wan model weights (already in ref 52) |
| **Kijai/HunyuanVideo_comfy** (HF) | Quantized Hunyuan weights |
| **Kijai/WanVideo_comfy_fp8_scaled** (HF) | The fp8_scaled Wan models Luis uses |

## Most-relevant kijai repos NOT yet installed for Luis's specific work

If Luis wants to add to his stack from kijai's catalog:

**1. ComfyUI-Florence2** — Highest leverage. When you start LoRA training, Florence-2 auto-captioning is the canonical first step. Your dataset of 30-100 reference images each needs a caption file; Florence-2 generates them in seconds per image. Workflow: drag images → Florence-2 captioner → save text files → feed to ai-toolkit dataset folder.

**2. ComfyUI-FluxTrainer** — If you'd rather train inside ComfyUI than learn ai-toolkit's YAML configs. Less control, more convenient. Decision point: try ai-toolkit first (per ref 45 plan), fall back to FluxTrainer if config friction is too high.

**3. ComfyUI-segment-anything-2** — For mask-based workflows. Could pair with `comfyui-impact-pack`'s SEGS pipeline (ref 38) — Impact's `SAMDetectorCombined` already does this, but the standalone kijai wrapper might give you more direct control.

Everything else is either niche, redundant with core ComfyUI features that landed in 0.19.x, or out of scope for Luis's game art work.

## Tracking kijai's work

**Star/follow activity** (best signal-to-noise for new releases):

- `github.com/kijai?tab=repositories&sort=updated` — sorted by recent activity, surfaces new repos and major commits
- `github.com/kijai/ComfyUI-WanVideoWrapper/commits` — most-active repo, multiple commits per week, often introducing support for new Wan variants the day they release
- `github.com/sponsors/kijai` — sponsor him (he's open-sponsored, infrastructure-cost-funded)
- `huggingface.co/Kijai` — companion HF account where his quantized model weights live (ref 52)
- Twitter: `@kijaidesign`

**Practical "stay current" routine for Luis:**

1. **Weekly check** of `kijai/ComfyUI-WanVideoWrapper` recent commits — surfaces new Wan variants (ATI, RealisDance, Stand-In, FantasyTalking, MultiTalk, etc.) before they hit civitai
2. **Watch `kijai/ComfyUI-KJNodes`** for new utility nodes — Set/Get, batch operations, math nodes, sometimes new useful primitives
3. **Sponsor consideration** — if Luis's setup heavily depends on kijai's work (it does, via Wan), $5-10/month sponsorship is the polite "thanks for the labor" gesture

## Why kijai matters for Luis specifically

Luis's runner suite uses Wan video + kijai's WanVideoWrapper as a hard dependency. When Wan team publishes a new model variant on Hugging Face, the typical lag is:
- Day 0: `Wan-Video/...` repo on HF
- Day 0-1: `Kijai/WanVideo_comfy_fp8_scaled` quantized variant on HF
- Day 0-3: `kijai/ComfyUI-WanVideoWrapper` adds nodes for the new variant
- Day 3-7: Comfy-Org adds template if the variant is significant

Luis's `runners/wan_t2v.py` consumes #1+#2+#3 (Wan model + Kijai's quantized variant + WanVideoWrapper nodes). Watching kijai's commits = watching the leading edge of what's available before it propagates downstream.
