---
name: G:\models inventory and shape — what's actually installed
description: High-level map of Luis's 2.4 TB ComfyUI model library — folder layout, model families present, sizes, where to look for what
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
Luis has a 2.4 TB shared model library at `G:\models\` (mounted across multiple ComfyUI installs via `extra_model_paths.yaml` with `base_path: G:\`).

## Folder layout (sizes as of 2026-05-08)

| Folder | Items | Size | Contents |
|---|---|---|---|
| `diffusion_models/` | 115 | 963 GB | Modern DiT models (Flux.1/Flux 2/Klein, Qwen-Image variants, Z-Image, ChronoEdit, Chroma, Nunchaku SVDQ, etc.) |
| `unet/` | 69 | 518 GB | Same-class as diffusion_models but mostly **GGUF quantizations** (flux1-dev-Q5_K_M.gguf, flux2-dev-Q4_K_S.gguf, qwen-image-2512-Q8_0.gguf, ChronoEdit-14B-Q8_0.gguf, etc.) |
| `checkpoints/` | 124 | 447 GB | All-in-one checkpoints: SDXL family (Juggernaut, RealVis, Pony, Illustrious-style), SD 1.5 family, plus older Flux.1 fp8 checkpoints, LTX-Video |
| `loras/` | 966 | 135 GB | 349 actual safetensors LoRAs (rest = previews/json). Spread: ~33 SDXL, ~26 Flux.1, ~14 Kontext, ~12 Flux 2/Klein, ~68 Qwen-Image, ~19 Z-Image, ~9 Pony, ~9 Illustrious, ~3 AnimateDiff. Plus subfolders `HyperSD/`, `SD1.5/`, `lcm/`, `recipes/` |
| `text_encoders/` | 14 | 131 GB | Mistral 3 (fp8 + bf16), Qwen3-4B, Qwen3-8B, Gemma 3 12B, T5-XXL fp8, UMT5-XXL fp8 (Wan), Ovis 2.5, Qwen3-4B-abliterated |
| `clip/` | 16 | 85 GB | T5-XXL (fp16, fp8, GGUF Q3-Q8/F16/F32), CLIP-L variants, Qwen2.5-VL 7B, EVA02-CLIP-L, T5 awq-int4 |
| `controlnet/` | 25+nested | 63 GB | Mixed Flux/SDXL/SD1.5 ControlNets. Flux.1 union pro, alimama inpainting, SDXL tile, several SD1.5 (canny/depth/scribble/inpaint/lineart/tile) |
| `clip_vision/` | 3 | 2.0 GB | clip_vision_h, sigclip_vision_patch14_384, EVA02-CLIP-L |
| `vae/` | 10 | 2.8 GB | flux2-vae, flux_kontext_ae (= ae for Flux.1), wan_2.1_vae, qwen_image_vae, qwen_image_layered_vae, ovis_ae, vae-ft-mse (SD 1.5) |
| `ipadapter/` | 9 | 0.5 GB | SD 1.5 IPAdapter set (full-face, plus, plus-face, vit-G) |
| `ipadapter-flux/` | 1 | 5.0 GB | XLabs ip-adapter for Flux.1 |
| `pulid/` | 3 | 2.9 GB | PuLID Flux v0.9.0 + v0.9.1, plus PuLID-style SDXL adapter |
| `instantid/` | 1 | 1.6 GB | InstantID adapter (SDXL) |
| `xlabs/` | nested | 2.8 GB | xlabs/controlnets: flux-canny-controlnet-v3, flux-depth-controlnet-v3 |
| `style_models/` | 2 | 12 GB | flux1-redux-dev (style transfer for Flux.1), flux1-fill-dev GGUF |
| `embeddings/` | 22 | 85 MB | SK_3DRENDER/ANIME/CINEMATIC/COMIC/Cyberpunk/DIGITALART/Fantasy/VECTORART, ac_neg1, sxz-texture-sdxl, ziprealism |
| `upscale_models/` | 9 | 645 MB | 4x-UltraSharp, 4x-AnimeSharp, 4xNomos2_hq_dat2, 4x_NMKD-* (Siax, Superscale, UniversalUpscalerV2-Sharp), 4x_foolhardy_Remacri, 8xNMKDFaces |
| `LLM/` | 8 | 14 GB | Florence-2 (base, large, PromptGen variants, Flux-Large), Llama-3.2-3B-Instruct |

## Empty/unused folders (placeholder)

Empty: `CogVideo/`, `Joy_caption/`, `animatediff_models/`, `animatediff_motion_lora/`, `animatediff_video_formats/`, `configs/`, `gligen/`, `hypernetworks/`, `layerstyle/`, `liveportrait/`, `onnx/`, `photomaker/`. If user wants AnimateDiff or LivePortrait workflows, models would need to be downloaded first.

## How to apply

When designing a workflow, start by checking what model family the user wants, then look in the right folder above. Always verify the specific filename exists — Luis's collection is broad but not infinite, and quantization/version variants are easy to confuse (e.g., qwen_image_edit_2509_bf16 vs _fp8_e4m3fn vs Q4_K_M.gguf vs svdq-fp4_r128 — all valid choices, very different VRAM/quality tradeoffs). See the per-family memory files for which encoder/VAE pairs with which DiT.
