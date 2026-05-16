---
name: Other model families — Z-Image, ChronoEdit, Chroma, Ovis, LTX-Video, Cascade-style
description: Compatibility notes for the smaller/specialty model families in Luis's library beyond Flux/Qwen/Wan
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
## Z-Image (Bytedance/community lightweight image DiT)

Compact image DiT with a turbo (distilled, low-step) variant. Detected as `image_model = "zimage_pixel"` (pixel-space variant) in ComfyUI core.

| Asset | File |
|---|---|
| DiT bf16 | `diffusion_models/z_image_bf16.safetensors` (12 GB) |
| DiT turbo bf16 | `diffusion_models/z_image_turbo_bf16.safetensors` (12 GB) — 4-step distilled |
| DiT turbo fp8 | `diffusion_models/z-image-turbo-fp8-e4m3fn.safetensors` (5.8 GB) |
| DiT turbo fp8 KJ | `diffusion_models/z-image-turbo_fp8_scaled_e5m2_KJ.safetensors` (5.8 GB) — kijai's quant |
| DiT GGUF | `unet/z_image-Q8_0.gguf` (6.8 GB), `unet/z_image_turbo-bf16.gguf` (12 GB) |
| Text encoder | `text_encoders/qwen_3_4b.safetensors` (7.5 GB) — Qwen3-4B |
| CLIPLoader type | **`lumina2`** (Z-Image is Lumina-derived; this is the verified working type from Purz's proven pipeline). DO NOT use `flux2` — that routes to `klein_te` which is wrong for Z-Image. |
| VAE | `vae/ae.safetensors` (Flux VAE) — verified working in Purz's pipeline. `qwen_image_vae.safetensors` may also work but `ae.safetensors` is the proven choice. |
| Sampler shift | `ModelSamplingAuraFlow` with `shift=3` between UNETLoader and KSampler — applies the Lumina/AuraFlow sigma shift Z-Image needs |
| Sampler | KSampler `res_multistep` / `simple`, **8 steps** for turbo at cfg=1 (Purz's proven setting). euler/simple at 4 also works. Non-turbo: 16-20 steps cfg=1. |
| Latent | `EmptySD3LatentImage` (16-ch) works |

**Existing user workflows** that use Z-Image: `Z-Image.json`, `Z-Image_Upscale_Image_Res.json`, `Z-Image_Upscale_Image_Res_2.json` in `user/default/workflows/` — read those before authoring a new Z-Image workflow to match user's preferred patterns.

`ComfyUI-nunchaku` provides `NunchakuQwenImageDiTLoader` and Z-Image-related Nunchaku examples (e.g., `nunchaku-z-image-turbo.json`, `-turbo-lora.json`, `-turbo-controlnet.json`).

## ChronoEdit (image editing, 14B)

Compact image-edit model.

| Asset | File |
|---|---|
| DiT bf16 | `diffusion_models/chrono_edit_14B_fp16.safetensors` (31 GB) — note `_fp16` in filename, but actually fp16/bf16 |
| DiT GGUF | `unet/ChronoEdit-14B-Q8_0.gguf` (17 GB) |
| Existing workflow | `user/default/workflows/Nvidia_chrono_edit_14B.json` — read before authoring |

ChronoEdit takes a reference image + edit instruction. Workflow shape: image input → VAE encode → ReferenceLatent → conditioning. ComfyUI core may auto-detect; if not, it routes through Wan-style code (similar arch). The Nvidia workflow JSON in user's library is canonical for them.

## Chroma (Chroma1-HD)

Minimalist diffusion model from a community team, detected as `image_model = "chroma"`.

| Asset | File |
|---|---|
| DiT bf16 | `diffusion_models/Chroma1-HD.safetensors` (17 GB) |
| DiT fp8mixed | `diffusion_models/Chroma1-HD-fp8mixed.safetensors` (8.6 GB) |
| Encoder | likely T5-XXL fp8 (Chroma is Flux-derived; check chroma.py for exact spec) |
| VAE | likely `ae.safetensors` (Flux VAE) — Chroma forks Flux schnell |

ComfyUI also has `chroma_radiance` variant detection.

## Ovis (image generation)

| Asset | File |
|---|---|
| DiT bf16 | `diffusion_models/ovis_image_bf16.safetensors` (14 GB) |
| Encoder | `text_encoders/ovis_2.5.safetensors` (4.8 GB) — Ovis 2.5 |
| VAE | `vae/ovis_ae.safetensors` (320 MB) |
| CLIPLoader type | `ovis` (per nodes.py CLIPLoader options) |

## LTX-Video (LTXV)

Lightricks' fast video model.

| Asset | File |
|---|---|
| Checkpoint | `checkpoints/ltx-2-19b-dev.safetensors` (41 GB), `ltx-2-19b-dev-fp8.safetensors` (26 GB) |
| Subfolder | `checkpoints/LTXV/` exists but is empty — placeholder |
| Loader | use `CheckpointLoaderSimple` for LTXV |
| CLIPLoader type | `ltxv` |

## Older / SD-family checkpoints (huge user library)

Luis has 124 checkpoint files. Categories:

### SDXL family (~25-30 files)
Juggernaut XI, X, v9, v8, v6, ragnarok, versionXInpaint; RealVisXL v4/v5 lightning; Pony Diffusion V6 XL; Dreamshaper XL Turbo; Dynavision XL; Stoiqo Afrodite Flux XL; THINKDIFFUSIONXL; ULTIMATEDIFFUSIONXL; UltriumV5; Wildcardx XL Fusion; Fenrisxl; sd_xl_base_1.0; sd_xl_turbo_1.0; ponyDiffusionV6XL; etc.

### SD 1.5 family (~30-40 files)
Realistic Vision V6.0, V60B1, V51 inpainting; Deliberate v5; epicrealism naturalSinRC1; majicmixFantasy; Dreamshaper 8; aiAngelMix v3; coloringBook; vector2_v1; vectorartzDiffusion; majicmixFantasy_v30Vae; v1-5-pruned-emaonly; babes_30; M4RV3LSDUNGEONS; copaxTimeless_xplus4; etc.

### SDXL Inpainting/Refiner
juggernautXL_versionXInpaint, realisticVisionV60B1_v51VAE-inpainting, epicrealism_pureEvolutionV5-inpainting

### Specialty
Florence-2 in `LLM/`; SUPIR-v0F (super-resolution helper)

### Legacy formats
- `.ckpt` files: vectorartzDiffusion_v1.ckpt, coloringBook.ckpt — older format, use CheckpointLoaderSimple

### NF4 / BNB (4-bit) Flux
- `flux1-dev-bnb-nf4.safetensors`, `flux1-schnell-bnb-nf4.safetensors`, `flux1DevHyperNF4Flux1DevBNB_flux1DevHyperNF4.safetensors` — for very low VRAM, requires bnb-aware loader

## Verification

For each family above:
1. Filename in correct subfolder
2. Encoder + VAE are paired with the right DiT family (CRITICAL — this is where most errors come from)
3. CLIPLoader `type` field is correct (visible in nodes.py CLIPLoader options list)
4. Sampler/scheduler/cfg are appropriate (distilled = cfg=1, low steps; non-distilled = cfg≥3, 20+ steps)
