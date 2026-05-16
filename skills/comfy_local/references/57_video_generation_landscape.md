---
name: Video generation landscape — what Luis has, what ComfyUI supports, what's possible
description: Beyond Wan 2.1 t2v. Full video model coverage in ComfyUI core (Hunyuan / Mochi / LTX / SVD / Cosmos / WanMove), what's installed locally vs what's downloadable, frame interpolation (RIFE/FILM), output pipeline (VHS_VideoCombine, SaveVideo, SaveWEBM), seedvr2 video upscaler, and the practical gap-list of what Luis could enable next.
type: reference
---

# Video generation in ComfyUI

Reference 07 covers Wan 2.1 specifically. This reference covers the broader video landscape — what's possible, what Luis already has, what's a one-download-away from being usable.

**Read date:** 2026-05-09

---

## 1. What Luis has installed RIGHT NOW

**Video DiTs on disk:**
```
G:\models\diffusion_models\
└── wan2.1_t2v_14B_fp8_scaled.safetensors    (14.3 GB — ONLY video DiT installed)
```

**Video VAE / encoders:**
```
G:\models\vae\wan_2.1_vae.safetensors                           (243 MB)
G:\models\text_encoders\umt5_xxl_fp16.safetensors                (11.4 GB)
G:\models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors   (6.7 GB)
```

**Video custom nodes:**
- `ComfyUI-WanVideoWrapper` (kijai) — comprehensive Wan pipeline, 80+ Wan-specific nodes
- `ComfyUI-WanAnimatePreprocess` (kijai) — face/pose extraction for Wan-Animate
- `comfyui-videohelpersuite` (VHS) — `VHS_VideoCombine` for assembling images into video files
- `seedvr2_videoupscaler` — SeedVR2 video upscaler (separate from image upscalers)

**Video runner:**
- `runners/wan_t2v.py` — submits a Wan 2.1 14B text-to-video job. 832×480 / 49 frames @ 16fps default.

**Net capability today:** text → 49-frame 832×480 video via Wan, then optional upscale via SeedVR2.

---

## 2. What ComfyUI core supports (no extra packs needed) but Luis hasn't downloaded weights for

ComfyUI core has built-in nodes for SEVEN distinct video model families. Luis has weights for ONE (Wan 2.1 t2v).

### a) Wan 2.1 / 2.2 — what's downloadable beyond t2v

Wan-Video and kijai publish many variants on HF. Luis has ONLY t2v 14B fp8_scaled. Other Wan variants:

| Variant | Purpose | HF location | Status |
|---|---|---|---|
| **Wan 2.1 i2v 14B** | image-to-video (animate a still) | `Wan-Video/Wan2.1-I2V-14B-720P` (or 480P) | **NOT downloaded** |
| **Wan 2.1 VACE** | masked editing on video (inpaint) | `Wan-Video/Wan2.1-VACE-14B` | NOT downloaded |
| **Wan 2.1 Camera** | camera-trajectory control | `Wan-Video/Wan2.1-Camera-...` | NOT downloaded |
| **Wan 2.1 Animate** | character animation | `Wan-Video/Wan2.1-Animate-...` | NOT downloaded |
| **Wan 2.1 S2V** | sound-to-video | NOT downloaded |
| **Wan 2.1 HuMo** | multimodal humans | NOT downloaded |
| **Wan 2.1 SCAIL** | pose-driven video (kijai's `ComfyUI-SCAIL-Pose` is INSTALLED but no weights) | NOT downloaded |
| **Wan 2.2** | Wan 2.2 family (2.2 t2v 14B, 2.2 i2v, 2.2 VACE) | `Wan-Video/Wan2.2-...` | NOT downloaded — newer than 2.1 |
| **Wan 1.3B / 5B** | smaller, faster Wan variants | `Wan-Video/Wan2.1-T2V-1.3B` etc. | NOT downloaded — useful for fast iteration |
| **WanMove** | trajectory/motion control (`comfy_extras/nodes_wanmove.py`) | github.com/ali-vilab/Wan-Move | NEW — added recently to core |

**Highest-value Wan additions for Luis's work:**
- **Wan 2.1 i2v 14B** — closes the loop on "animate Luis's static cel-shaded characters into action shots." Uses kijai's existing infrastructure. The 14 motion-effect LoRAs from civitai (ref 51) all require i2v.
- **Wan 1.3B t2v** — fast iteration variant. ~4× faster than 14B at lower quality. Useful for prompt testing before committing to a 14B run.

### b) Hunyuan Video — Tencent's competing video model

Core support: `comfy_extras/nodes_hunyuan.py` includes:
- `EmptyHunyuanLatentVideo` — Hunyuan video latent factory
- `EmptyHunyuanVideo15Latent` — Hunyuan Video 1.5 (newer, in Luis's install per ref 53 commits)
- `HunyuanVideo15ImageToVideo` — Hunyuan i2v
- `HunyuanVideo15SuperResolution` — built-in upscaler
- `HunyuanVideo15LatentUpscaleWithModel` — latent-space upscale
- `TextEncodeHunyuanVideo_ImageToVideo` — i2v conditioning
- `HunyuanRefinerLatent` — refiner stage

kijai also has `ComfyUI-HunyuanVideoWrapper` and `ComfyUI-HunyuanVideoMultiLora` packs (NOT installed).

Where to download: `tencent/HunyuanVideo` and `Kijai/HunyuanVideo_comfy` on HF.

**Why Hunyuan over Wan:** different model, sometimes wins on specific motion types. Lower priority than getting Wan i2v.

### c) LTX-Video — fast video model from Lightricks

Core support: implicit through standard nodes. Lots of references in commits — "LTXV audio VAEs (standalone + native)", "LTX2 reference audio (ID-LoRA)".

LTX is the fastest video model in the ecosystem — generates seconds of video in seconds (vs Wan's minutes). Quality is lower than Wan 14B but iterating is fast.

Where to download: `Lightricks/LTX-Video` and `Lightricks/LTX-Video-2` on HF.

**Use case:** rapid iteration / motion previz. Test a prompt with LTX in 10 seconds, then commit to Wan 14B for the final.

### d) Mochi — Genmo's video model

Core support: `comfy_extras/nodes_mochi.py` (`EmptyMochiLatentVideo`). Minimal but functional.

Where: `genmo/mochi-1-preview` on HF. Larger and slower than LTX, generally behind Wan now.

**Status:** mostly historical interest. Luis can skip unless researching.

### e) SVD (Stable Video Diffusion) — original i2v model

Core support: `comfy_extras/nodes_video_model.py`:
- `ImageOnlyCheckpointLoader` — SVD-style loader
- `SVD_img2vid_Conditioning` — SVD-specific conditioning
- `VideoLinearCFGGuidance` / `VideoTriangleCFGGuidance` — CFG guidance schedules

Where: `stabilityai/stable-video-diffusion-img2vid-xt`.

**Status:** older but still works. Lower-quality than Wan/Hunyuan but well-understood. Skip unless needed.

### f) Cosmos — NVIDIA's video model

Core support: `comfy_extras/nodes_cosmos.py`. Full pipeline.

Where: `nvidia/Cosmos-Predict2`.

**Status:** newer entrant, quality competitive with Wan. Heavy compute. Optional.

### g) Cosmos-Predict2 / Lumos / others

Several other video models have core support via comfy_extras but are niche. Don't worry about these.

---

## 3. Frame interpolation (NEW in core — RIFE / FILM)

Per ref 53, the recent commit `db85cf03 feat: RIFE and FILM frame interpolation model support (CORE-29)` added native frame-interpolation. This is HUGE for Wan output quality.

Wan generates at 16fps natively. Standard playback is 24-60fps. Interpolating 16→24 or 16→30 fps makes the output look way smoother without re-generating.

**Node:** `FrameInterpolationModelLoader` (loads RIFE or FILM weights), then a paired interpolation node that takes IMAGE (a video frame batch) and outputs more frames.

**Models go in:** `G:\models\frame_interpolation\`

**Status:** Luis does NOT have RIFE/FILM models downloaded yet (verified — `ls` returned nothing). Easy to add — small models (~100 MB each).

**HF locations (typical):**
- RIFE: `ai-forever/Real-ESRGAN-frame-interpolation` or various
- FILM: `lemonteaa/FILM-frame-interpolation` or similar (verify on HF)

**Use case:** wan_t2v.py output is 16fps. Pipe through RIFE x2 → 32fps. Pipe through RIFE x4 → 64fps. Smoother output, no extra Wan inference.

---

## 4. Output pipeline — VHS_VideoCombine and friends

The standard "combine generated frames into a video file" pattern uses **VHS_VideoCombine** from `comfyui-videohelpersuite`. Luis already has this installed and his `runners/wan_t2v.py` uses it.

```python
"video_combine": {
    "class_type": "VHS_VideoCombine",
    "inputs": {
        "images": ["vae_decode", 0],
        "frame_rate": 16,                  # Wan's native rate
        "loop_count": 0,                   # 0 = no loop, single play
        "filename_prefix": "Wan/output",
        "format": "video/h264-mp4",        # also: video/h265-mp4, video/webm, image/gif
        "pix_fmt": "yuv420p",
        "crf": 19,                         # quality — lower = better, higher = smaller file
        "save_metadata": True,
        "trim_to_audio": False,
        "pingpong": False,
    },
}
```

**Format options** (video formats supported by VHS):
- `video/h264-mp4` — most-compatible MP4 (default)
- `video/h265-mp4` — newer codec, smaller files, less compatible
- `video/webm` — WebM container (browser-friendly)
- `image/gif` — animated GIF (no audio, large files for high-quality video — fine for short loops)
- `image/apng` — animated PNG

**Other useful VHS nodes (not in current runner):**
- `VHS_LoadVideo` — load a video into a frame batch
- `VHS_LoadVideoPath` — same but from path
- `VHS_GetVideoComponents` — extract frames, audio, fps from existing video
- `VHS_VideoCombineByPath` — write to absolute path
- `VHS_SplitVideo` — split into segments

**ComfyUI core also added native video nodes** (`comfy_extras/nodes_video.py`):
- `SaveVideo`, `SaveWEBM` — newer alternatives to VHS_VideoCombine
- `LoadVideo`, `CreateVideo`, `GetVideoComponents`, `VideoSlice`

The core nodes are slightly less feature-rich than VHS but are first-party. For new workflows, VHS still has more options. Luis's `wan_t2v.py` correctly picks VHS.

---

## 5. SeedVR2 video upscaler (Luis already has it)

`seedvr2_videoupscaler` is installed in custom_nodes. SeedVR2 is a video super-resolution model — takes low-res video frames and upscales them while preserving temporal consistency (no flickering).

**Use case:** generate at Wan's native 832×480 (fast) → upscale to 1664×960 or 1920×1080 with SeedVR2 (slower but better quality than per-frame ESRGAN).

**Models go in:** check `seedvr2_videoupscaler/example_workflows/` for the canonical setup. Likely needs SeedVR2 weights downloaded from HF.

**Status:** node is installed but Luis hasn't run a pipeline through it. When he wants higher-than-480p output, this is the path.

---

## 6. The "longer video" problem — context windows

Wan 2.1 14B at 832×480 fits about 49-81 frames before VRAM saturates on a 32 GB card (per ref 07). For longer videos (>5 seconds), the canonical solution is **sliding context windows**:

- `WanContextWindowsManual` (kijai) — the WanVideoWrapper node
- `ContextWindowsManual` (core in `nodes_context_windows.py`)

These slide a window through the latent timeline, generating one window at a time with overlap, then fusing. Per ref 07's empirical data: 1025 frames @ window=81 / overlap=16 fits in <5 GB on a 5090 with the 1.3B model.

**For Luis's 14B at 32 GB:**
- 49 frames standalone — easy
- 81 frames standalone — fine
- 161 frames — needs `block_swap=20` (per ref 07)
- 481+ frames — needs context windows

`runners/wan_t2v.py` does NOT yet support context windows or block_swap. If Luis ever wants longer videos, the runner needs to grow those flags.

---

## 7. Animation LoRAs (the civitai motion-effect catalog from ref 51)

Reference 51 surfaced 14 Wan 2.1 I2V motion-effect LoRAs on civitai (Squish, Inflate, Deflate, Cakeify, Bullet Time, Super Saiyan, Strong Wind, etc.). **All require Wan i2v** which Luis doesn't have downloaded.

Once he downloads Wan i2v 14B (~14 GB, paired with the existing UMT5 encoder + Wan VAE he already has), these LoRAs become usable. The pattern:

```
LoadImage(static_character_art) -> WanVideoEncode(VAE, image) -> latent
WanVideoModelLoader(wan2.1_i2v_14B) -> model
LoraLoaderModelOnly(Wan2.1_Squish_Effect_I2V_LoRA, strength=0.85) -> patched_model
WanVideoTextEncode("the character squashes and bounces") -> conditioning
WanVideoSampler(patched_model, latent, conditioning, steps=30, cfg=6, shift=5) -> video latent
WanVideoDecode -> frames
VHS_VideoCombine -> mp4
```

**Use case for Luis:** generate his cel-shaded character art via existing runners → drop into i2v with a "squish" / "bullet-time" / "rotation" LoRA → static art becomes a 3-second action animation. Big creative leverage.

---

## 8. Practical gap-list — what to enable next

Ranked by leverage for Luis's specific work:

### Tier 1 — biggest unlock for current pipeline

1. **Wan 2.1 i2v 14B** — `Wan-Video/Wan2.1-I2V-14B-480P` or `720P` from HF. ~14 GB download. Pairs with existing UMT5 + Wan VAE. Unlocks animation of static character/biome art.

2. **RIFE frame-interpolation model** — `~100 MB` to `G:\models\frame_interpolation\`. Smooths Wan's 16fps output to 30-60fps without re-generation. Built-in core support (no new pack).

3. **SeedVR2 weights** — Luis has the node but no weights. Enables high-quality video upscaling. Find via `seedvr2_videoupscaler/example_workflows/` or HF.

### Tier 2 — alternative video models for variety

4. **LTX-Video 2 weights** — `Lightricks/LTX-Video-2`. Fast iteration model. Useful for prompt testing before committing to Wan 14B.

5. **Wan 2.2 14B t2v** — `Wan-Video/Wan2.2-T2V-14B`. Newer than 2.1, quality improvement. Drop-in upgrade path.

6. **Wan 1.3B t2v** — `Wan-Video/Wan2.1-T2V-1.3B`. Fast prompt-testing variant. Useful before 14B commits.

### Tier 3 — niche but available

7. **Hunyuan Video weights** — `tencent/HunyuanVideo` or kijai's quantized variant. Different model character; alternative to Wan when something doesn't work.

8. **Wan 2.1 VACE / Camera / Animate** — only download when a specific use case demands it (masked video editing, camera control, character animation).

### Tier 4 — skip

9. SVD, Mochi, Cosmos — older, slower, or niche. Skip unless researching.

---

## 9. Updates needed to existing references

The video landscape has evolved since I wrote ref 07. Specifically:

- **Ref 07 says Wan i2v / VACE / Camera / Animate / S2V / HuMo / SCAIL DiTs are NOT installed** — still true. But add: Wan 2.2 series exists and is newer than 2.1.
- **Ref 36 (runners catalog) says `wan_t2v.py` is 16-fps native** — still true. Add note that piping through frame interpolation is recommended.
- **CLAUDE.md rule #5** mentions Wan 2.1 t2v IS downloaded — still accurate.

No urgent updates needed; this reference (57) is the umbrella that consolidates the broader video picture.

---

## 10. What to write in `runners/` if Luis wants more video coverage

These are NOT yet built. Listing them as future runner candidates:

- **`runners/wan_i2v.py`** — Wan 2.1 i2v with optional motion-effect LoRA insertion (the 14 from ref 51). Requires the Wan i2v 14B download as prereq.
- **`runners/ltx_t2v.py`** — fast LTX-Video variant for iteration. Requires LTX weights.
- **`runners/video_upscale.py`** — wraps SeedVR2 with sane defaults. Takes an existing video file, upscales 2× or 4×.
- **`runners/frame_interp.py`** — wraps RIFE/FILM. Takes an existing video, increases fps via interpolation.
- **`runners/wan_long_t2v.py`** — context-window variant of `wan_t2v.py` for >5-second outputs. Needs WanVideoBlockSwap + ContextWindows wired in.

If Luis decides to expand his video runners, these are the obvious candidates. None blocks his current work — Wan 14B t2v is his only video model, and the existing runner handles it.

---

## Summary of knowledge gaps closed

This reference covers what was missing:
- **Full video model coverage** in ComfyUI core (Hunyuan, Mochi, LTX, SVD, Cosmos, WanMove)
- **Frame interpolation** (RIFE/FILM new in core)
- **Output codecs / formats** (VHS_VideoCombine options + native core video nodes)
- **SeedVR2 video upscaler** existence
- **Animation LoRA workflow shape** (when Luis gets Wan i2v)
- **Long-video context-window pattern**
- **What's installed vs what's downloadable** (the practical "what to grab next" list)

Reference 07 stays focused on Wan 2.1 specifics. Reference 57 (this one) is the broader video map.
