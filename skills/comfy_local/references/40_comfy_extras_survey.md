---
name: comfy_extras coverage — newer / specialized core nodes
description: Survey of comfy_extras files I hadn't read. APG, CFG variants, attention multiply, EasyCache, AYS scheduler, custom sampler tree, differential diffusion, context windows, post-processing, Porter-Duff compositing, canny, controlnet helpers.
type: reference
---

# comfy_extras survey

Reference 37 covered the workhorse nodes in `nodes.py`. This one walks through `comfy_extras/` which hosts newer, specialized, or experimental nodes — many tagged `is_experimental=True` or in `_for_testing` category but already useful in production.

**Read date:** 2026-05-09. Files surveyed: 13 (~3500 lines).

## nodes_apg.py — Adaptive Projected Guidance

`APG` (display: "Adaptive Projected Guidance"). Category: `sampling/custom_sampling`.

A newer alternative to plain CFG. Instead of scaling the unconditional/conditional gradient straight, it projects the guidance to remove the parallel-to-prediction component, then scales. Often gets sharper images at lower nominal cfg. Takes a Model in, returns the patched Model.

Pair with regular KSampler downstream. Useful when you want Flux-quality guidance behavior on non-Flux models.

## nodes_cfg.py — CFG variants

| Node | Category | What it does |
|---|---|---|
| `CFGZeroStar` | `advanced/guidance` | Zero-out the unconditional path — degenerate CFG case used in some research. Patches MODEL. |
| `CFGNorm` | `advanced/guidance` | Normalize CFG by the conditional norm. `strength` parameter (default 1.0). Reduces oversaturation at high cfg. Patches MODEL. |

Both produce a patched MODEL — wire upstream of KSampler.

## nodes_attention_multiply.py — attention scaling tricks

| Node | What it does |
|---|---|
| `UNetSelfAttentionMultiply` | Scale self-attention activations in the U-Net. Heuristic detail/contrast knob. |
| `UNetCrossAttentionMultiply` | Scale cross-attention (text-to-image) activations. Tighter or looser prompt adherence. |
| `CLIPAttentionMultiply` | Scale CLIP-side attention. |
| `UNetTemporalAttentionMultiply` | Scale temporal attention (video models). Motion intensity knob. |

These are scratch-card knobs for fine-tuning a generation when normal cfg/sampler tuning has plateaued. Strength 1.0 = identity; 1.1 / 0.9 are typical first nudges.

## nodes_easycache.py — caching wrapper for inference speedup

`EasyCacheNode` (display: "EasyCache"). Category: `advanced/debug/model`. Experimental.

```
reuse_threshold  default 0.2   (lower = more aggressive caching)
start_percent    default 0.15
end_percent      default 0.95
```

Patches the MODEL with `easycache` wrappers in `transformer_options`. Skips redundant transformer block computations when activations are similar enough between adjacent steps. Speedups can be 1.5×–2× at minimal quality loss for the 0.15–0.95 step range.

`LazyCacheNode` is the related "even more aggressive" variant. Both stash a `EasyCacheHolder` / `LazyCacheHolder` in `model.model_options['transformer_options']`. Compatible with most models.

For Wan video, prefer the dedicated `WanVideoSampler` cache_args (TeaCache) — see ref 07 — because Wan needs its own cache logic.

## nodes_align_your_steps.py — AYS scheduler

`AlignYourStepsScheduler` (alias: `AYS scheduler`). Category: `sampling/custom_sampling/schedulers`.

Inputs: `model_type` (combo: SD1, SDXL, SVD), `steps`, `denoise`. Outputs: `SIGMAS`.

Produces tuned sigma curves for low step counts (typically 10) on SD1.5 / SDXL / SVD. Wire its SIGMAS output into `SamplerCustomAdvanced`. Often noticeably better than karras at 10 steps.

For Flux/Qwen/Z-Image, AYS doesn't apply — use the appropriate `simple` / `beta` / `linear_quadratic` scheduler instead.

## nodes_custom_sampler.py — the full decomposed sampling tree (1095 lines)

This file decomposes the `KSampler` monolith into individually-wireable components, letting you mix-and-match:

**Schedulers (each outputs SIGMAS):**
- `BasicScheduler` (combo of all SCHEDULER_NAMES)
- `KarrasScheduler`, `ExponentialScheduler`, `PolyexponentialScheduler`, `LaplaceScheduler`, `SDTurboScheduler`, `BetaSamplingScheduler`, `VPScheduler` (each with their parameters exposed)

**Sigma manipulation:**
- `SplitSigmas` — split a SIGMAS at a step index (for two-stage sampling)
- `SplitSigmasDenoise` — split based on denoise %
- `FlipSigmas` — reverse (for img2img-style continue from existing)
- `SetFirstSigma`, `ExtendIntermediateSigmas`, `SamplingPercentToSigma`
- `ManualSigmas` — author a sigma curve by hand

**Sampler selectors (each outputs SAMPLER):**
- `KSamplerSelect` (combo of all SAMPLER_NAMES)
- Specific advanced ones with their tunable knobs: `SamplerDPMPP_3M_SDE`, `SamplerDPMPP_2M_SDE`, `SamplerDPMPP_SDE`, `SamplerDPMPP_2S_Ancestral`, `SamplerEulerAncestral`, `SamplerEulerAncestralCFGPP`, `SamplerLMS`, `SamplerDPMAdaptative`, `SamplerER_SDE`, `SamplerSASolver`, `SamplerSEEDS2`

**Noise (NOISE wire):**
- `RandomNoise` — random noise from seed
- `DisableNoise` — zero noise (for continuing from existing latent)
- Internal: `Noise_EmptyNoise`, `Noise_RandomNoise`

**Guiders (CFG-like wrappers, GUIDER wire):**
- `BasicGuider` — wraps positive conditioning, no negative (for distilled models)
- `CFGGuider` — full positive/negative + cfg
- `DualCFGGuider` — two parallel cfg passes (for SD3-style)

**The actual samplers:**
- `SamplerCustom` — older, takes (model, positive, negative, sampler, sigmas, latent, noise_seed, cfg, add_noise)
- `SamplerCustomAdvanced` — modern, takes (noise, guider, sampler, sigmas, latent_image). Cleaner.

`AddNoise` — add noise to a latent (for img2img continuation).

### Why this matters

Workflows using `SamplerCustomAdvanced` (the modern advanced sampling pipeline) wire:

```
RandomNoise → SamplerCustomAdvanced.noise
BasicGuider (positive only) → SamplerCustomAdvanced.guider
KSamplerSelect (e.g. "euler") → SamplerCustomAdvanced.sampler
KarrasScheduler (or AYS, or BasicScheduler) → SamplerCustomAdvanced.sigmas
EmptyLatentImage → SamplerCustomAdvanced.latent_image
```

This is the "decomposed KSampler" pattern. It's required for AYS, custom sigma curves, Wan-like long-form video, and anywhere you need finer control than KSampler/KSamplerAdvanced expose.

## nodes_advanced_samplers.py — niche samplers

| Node | What it does |
|---|---|
| `SamplerLCMUpscale` | LCM sampler tuned for upscale passes |
| `SamplerEulerCFGpp` | euler with CFG pre-projection variants (`regular` or `alternative`). Outputs SAMPLER. |

## nodes_canny.py — built-in Canny edge detector

`Canny` node. Inputs: image, low_threshold, high_threshold (both 0..1). Returns the binary edge image. No GPU model — pure OpenCV-style canny. For ControlNet-canny pipelines.

## nodes_compositing.py — Porter-Duff compositing + alpha tools

| Node | What it does |
|---|---|
| `PorterDuffImageComposite` | Composite two RGBA images using a Porter-Duff mode (18 modes — ADD, CLEAR, DARKEN, DST_OVER, LIGHTEN, MULTIPLY, OVERLAY, SCREEN, SRC, SRC_ATOP, SRC_IN, SRC_OUT, SRC_OVER, XOR, plus the matching DST_* variants). |
| `SplitImageWithAlpha` | Split RGBA → (RGB image, alpha mask). |
| `JoinImageWithAlpha` | Join (RGB image, alpha mask) → RGBA. |

For Qwen-Image-Layered output handling. Layered model emits RGBA per-element layers; `SplitImageWithAlpha` separates them.

## nodes_context_windows.py — sliding context window for long videos

`ContextWindowsManual` (display: "Context Windows (Manual)"). Subclass: `WanContextWindowsManualNode`.

Patches a video MODEL with sliding-window inference. Key params:
- `context_length` (default 16) — frames per window
- `context_overlap` (default 4) — overlap between adjacent windows
- `context_schedule` — STATIC_STANDARD / UNIFORM_STANDARD / UNIFORM_LOOPED / BATCHED
- `closed_loop` — whether the video loops (last connects back to first)
- `fuse_method` — PYRAMID (default) or others
- `freenoise` — apply FreeNoise shuffling for window blending
- `cond_retain_index_list` — keep specific latent indices in conditioning across windows (e.g. "0" keeps the start image)

This is what enables 1000+ frame video on a 32 GB card — the model only ever sees `context_length` frames at a time, but they slide through the full sequence with overlap-based fusing. Reference 07 mentions this in the "1025 frames in 5 GB" data point.

## nodes_controlnet.py — ControlNet helpers (newer)

| Node | What it does |
|---|---|
| `SetUnionControlNetType` | For Union-style ControlNets (one model that handles canny + depth + pose etc.), select which type to apply. Combo includes "auto" + UNION_CONTROLNET_TYPES.keys() (canny, tile, depth, blur, pose, gray, low_quality). |
| `ControlNetInpaintingAliMamaApply` | Apply AliMama's specialized inpainting ControlNet with mask input. |

The plain `ControlNetApply` and `ControlNetApplyAdvanced` live in `nodes.py` (ref 37) — these are extensions for the newer Union ControlNet and inpaint-specific variants.

## nodes_differential_diffusion.py — variable-strength masking

`DifferentialDiffusion` (alias: "inpaint gradient", "variable denoise strength"). Category: `_for_testing`. Experimental.

Patches the MODEL to interpret the noise_mask not as binary "noise here / don't here" but as a continuous strength map. White = full denoise, gray = partial, black = unchanged. Use for soft-edge inpaint, gradient style transfer to part of an image.

Single param: `strength` (0..1).

## nodes_post_processing.py — image fx and resizing utilities (904 lines)

| Node | What it does |
|---|---|
| `Blend` | Blend two images with mode + strength |
| `Blur` | Gaussian blur |
| `Quantize` | Quantize colors (color reduction) |
| `Sharpen` | Convolution sharpening |
| `ImageScaleToTotalPixels` | Resize to target pixel count instead of WxH |
| `ResizeImageMaskNode` | Resize with mask preservation |
| `BatchImagesNode`, `BatchMasksNode`, `BatchLatentsNode` | Concat batches |

These overlap with WAS Node Suite (reference 38); core versions are simpler but more reliable across ComfyUI versions.

## When to reach for which

| Goal | Reach for |
|---|---|
| Sharper images at lower cfg | `APG` (Adaptive Projected Guidance) wrapping the model |
| Fight oversaturation at high cfg | `CFGNorm` |
| Quick speedup on most models | `EasyCache` |
| Best 10-step SDXL/SD1.5 quality | `AlignYourStepsScheduler` → SamplerCustomAdvanced |
| Build a custom sigma curve / two-stage sampling | `SplitSigmas` + `KSamplerSelect` + `SamplerCustomAdvanced` |
| Long videos that fit in VRAM | `ContextWindowsManual` (or `WanContextWindowsManual`) patching the video MODEL |
| Soft-edge inpaint with continuous mask | `DifferentialDiffusion` |
| Fine-tune via attention strength | `UNetSelfAttentionMultiply` / `UNetCrossAttentionMultiply` |
| Composite RGBA layers from Qwen-Image-Layered | `SplitImageWithAlpha` + `PorterDuffImageComposite` + `JoinImageWithAlpha` |
| Union-style ControlNet (one model, multiple input types) | `SetUnionControlNetType` |
| Specialized inpainting ControlNet | `ControlNetInpaintingAliMamaApply` |
| Custom Canny edges (no extra model needed) | `Canny` |

## Typical SamplerCustomAdvanced recipe (modern, v3 io.ComfyNode style)

```
EmptyLatentImage(W,H,1) ─┐
                         │
RandomNoise(seed) ────────┐
                         │  ├──> SamplerCustomAdvanced ──> output_latent
CLIPTextEncode("...") ──> BasicGuider ──┤
                                        │
KSamplerSelect("euler") ───────────────┤
                                        │
KarrasScheduler(model, 25, 0..1) ──────┘
                                        │
                  (latent_image flows in too)
```

Same pattern with `CFGGuider` if you need negative+positive, `DualCFGGuider` for SD3-style dual-cfg models. Replace `KarrasScheduler` with `AlignYourStepsScheduler` or `BasicScheduler` or any sigma-producing source.

## Implication for runners

Most runners can stick with KSampler (simpler, fewer nodes). Switch to SamplerCustomAdvanced when:

- You need AYS sigmas (low-step SDXL with quality)
- You need split-sigma two-stage sampling
- You need a non-listed scheduler (Polyexponential, Laplace, VP)
- You need DualCFGGuider for SD3 / Cascade
- You need RandomNoise with a non-standard noise mode
