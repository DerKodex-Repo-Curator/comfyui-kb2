---
name: Flux family compatibility (Flux.1 + Flux 2 + Klein)
description: Encoders, VAEs, loaders, and quantization variants for every Flux model in Luis's library
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
## Flux 2 (newest — late 2025)

Flux 2 has **two distinct branches** with **different text encoders**. ComfyUI auto-detects from the encoder file content, but the CLIPLoader `type` is `flux2` for both.

### Flux 2 dev (Mistral branch)

| Asset | File | Notes |
|---|---|---|
| DiT | `flux2-dev.safetensors` (61 GB bf16) or `flux2_dev_fp8mixed.safetensors` (34 GB) | fp8mixed is the practical pick on 32 GB |
| Text encoder | `mistral_3_small_flux2_bf16.safetensors` (34 GB) or `_fp8.safetensors` (17 GB) | Mistral 3 24B pruned to 30 layers; conditioning dim = 15360 |
| VAE | `flux2-vae.safetensors` (321 MB) | |
| Latent | `EmptyFlux2LatentImage` (128-ch, /16 spatial) | DO NOT use EmptySD3LatentImage |
| Scheduler (recommended) | `Flux2Scheduler` (resolution-aware sigmas, 14-16 steps) | optional — KSampler/simple at 20 steps also works |
| Guidance | `FluxGuidance` 3.0-5.0 (default 4.0); cfg=1 in sampler | Distilled — negative prompt is ignored |
| GGUF variant | `unet/flux2-dev-Q4_K_S.gguf` (18 GB), `Q5_0` (22 GB), `Q6_K` (26 GB) | use `UnetLoaderGGUF` instead of UNETLoader |

### Flux 2 Klein (Qwen3 branch — different encoder!)

| Asset | File | Notes |
|---|---|---|
| Klein 4B DiT | `flux-2-klein-4b-fp8.safetensors` (3.8 GB) or `-nvfp4.safetensors` (2.3 GB) | NVFP4 needs cu130 to actually accelerate; on cu128 use fp8 |
| Klein 4B base DiT | `flux-2-klein-base-4b-fp8.safetensors` / `-nvfp4` | "base" = before instruction tuning |
| Klein 9B DiT | `flux-2-klein-9b-fp8.safetensors` (8.8 GB), `-kv-fp8.safetensors` (9.2 GB), `-kv.safetensors` bf16 (17 GB) | "kv" variant retains key/value caches |
| Klein 9B base DiT | `flux-2-klein-base-9b-fp8.safetensors` (9.0 GB), `-nvfp4.safetensors` (5.5 GB) | |
| Text encoder (Klein 4B) | `qwen_3_4b.safetensors` (7.5 GB) | conditioning dim ≈ 7680 |
| Text encoder (Klein 9B) | `qwen_3_8b_fp8mixed.safetensors` (8.1 GB) | larger conditioning dim |
| VAE | `flux2-vae.safetensors` | shared with dev |
| Latent | `EmptyFlux2LatentImage` (same as dev) | |
| Sampler | KSampler euler/simple, 12 steps for 4B, 14-16 for 9B | guidance-distilled, cfg=1 |

**Symptom of encoder mismatch:** `RuntimeError: mat1 and mat2 shapes cannot be multiplied (Bx15360 and 7680xH)` from `txt = self.txt_in(txt)` — means Mistral encoder fed to a Klein DiT, or vice versa.

## Flux.1 family

Single text encoder pattern: **CLIP-L + T5-XXL** via `DualCLIPLoader` with type `flux`.

### Common encoders for ALL Flux.1 models

| Asset | File |
|---|---|
| CLIP-L | `clip/clip_l.safetensors` (235 MB) — also `Flux_Kontext_clip_l.safetensors` |
| T5-XXL | `text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors` (4.9 GB) — fp8, fits anywhere |
| T5-XXL bf16 | `clip/t5xxl_fp16.safetensors` (9.2 GB) — higher quality, more VRAM |
| T5-XXL GGUF | `clip/t5-v1_1-xxl-encoder-Q3/Q6/Q8.gguf` — for `TripleCLIPLoaderGGUF` from ComfyUI-GGUF |
| Long CLIP-L | `text_encoders/long_clip/ViT-L-14-TEXT-detail-improved-hiT-GmP-TE-only-HF.safetensors` (309 MB) — extends 77 → 248 token context |

### Flux.1 model variants in install

| File (in `diffusion_models/` or `unet/`) | Type | Loader |
|---|---|---|
| `flux1-dev.safetensors` (23 GB), `flux1-dev-fp8.safetensors` (17 GB), `flux1-dev-Q5_K_M.gguf` (7.9 GB), `flux1-dev-F16.gguf` (23 GB), `flux1-dev-Q8_0.gguf` (12 GB) | **dev** — main Flux.1 | UNETLoader / UnetLoaderGGUF |
| `FLUX1/flux1-schnell.safetensors`, `flux1-schnell-Q8_0.gguf` | **schnell** — distilled, 4-step | same |
| `flux1-kontext-dev.safetensors` (23 GB), `flux1-dev-kontext_fp8_scaled.safetensors` (12 GB), `flux1-kontext-dev-Q8_0.gguf` | **Kontext** — image editing model | same; needs ReferenceLatent / VAEEncode for input image |
| `flux1-krea-dev.safetensors` (23 GB), `flux1-krea-dev_fp8_scaled.safetensors` (12 GB) | **Krea** — Krea-trained variant | same |
| `flux1-fill-dev.safetensors` (23 GB), `flux1-fill-dev-fp16-Q8_0-GGUF.gguf`, `fluxFillFP8_v10.safetensors` | **Fill** — inpainting/outpainting | works with mask input on conditioning |
| `flux1DevHyperNF4Flux1DevBNB_flux1DevHyperNF4.safetensors` | NF4 quant for very low VRAM (4-bit) | needs bnb support |
| `style_models/flux1-redux-dev.safetensors` (124 MB) | **Redux** — image style transfer | `StyleModelLoader` + `StyleModelApply` |

### Nunchaku SVDQ variants (Flux.1 only)

Nunchaku is a SVD-quantized fp4/int4 format. Loads via `NunchakuFluxDiTLoader` from ComfyUI-nunchaku custom node, not UNETLoader.

| File | Notes |
|---|---|
| `svdq-fp4_r32-flux.1-dev.safetensors` (6.6 GB) | FP4 r32 dev — small, fast, requires Blackwell + cu130 for full speed |
| `svdq-int4_r32-flux.1-dev.safetensors` (6.4 GB) | INT4 r32 dev — works on older GPUs |
| `svdq-int4_r32-flux.1-kontext-dev.safetensors` (6.4 GB) | INT4 r32 Kontext |

**Caveat:** Nunchaku does NOT support Flux 2 / Klein yet (custom node only loads Flux.1, Qwen-Image, Z-Image as of install date).

### Flux ControlNets

| File | Type |
|---|---|
| `controlnet/flux-dev-controlnet-union.safetensors` (6.2 GB) | Union (multi-mode) |
| `controlnet/flux-cn-pro-2.safetensors.safetensors` (4.0 GB) | Pro v2 union |
| `controlnet/FLUX.1/flux_shakker_labs_union_pro-fp8_e4m3fn.safetensors` (3.1 GB) | fp8 Shakker-labs union |
| `controlnet/alimama-creativeFLUX.1-dev-Controlnet-Inpainting-Beta.safetensors` (4.0 GB) | Inpainting |
| `xlabs/controlnets/flux-canny-controlnet-v3.safetensors` (1.4 GB) | XLabs canny |
| `xlabs/controlnets/flux-depth-controlnet-v3.safetensors` (1.4 GB) | XLabs depth |

### Flux IP-Adapter / PuLID

| File | Notes |
|---|---|
| `ipadapter-flux/ip-adapter.bin` (5.0 GB) | XLabs IPAdapter for Flux.1 |
| `pulid/pulid_flux_v0.9.0.safetensors` / `_v0.9.1.safetensors` (1.1 GB) | Face identity transfer for Flux.1 |
| `clip_vision/sigclip_vision_patch14_384.safetensors` (817 MB) | Required vision encoder for PuLID Flux |

## Verification before delivering a Flux workflow

1. Filename exists in `G:\models\<subfolder>`
2. Encoder matches DiT family (Mistral ↔ flux2 dev; Qwen3-4B ↔ Klein-4B; Qwen3-8B ↔ Klein-9B; CLIP-L+T5 ↔ all Flux.1)
3. VAE matches DiT family (flux2-vae ↔ Flux 2; flux_kontext_ae or `ae.safetensors` ↔ Flux.1)
4. cfg=1 for distilled models (everything except CFGGuider use cases)
5. EmptyFlux2LatentImage (128-ch) for Flux 2; EmptyLatentImage or EmptySD3LatentImage (16-ch) for Flux.1
