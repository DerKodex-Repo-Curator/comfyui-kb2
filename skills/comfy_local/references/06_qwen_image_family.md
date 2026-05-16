---
name: Qwen-Image family compatibility
description: Qwen-Image text-to-image and Edit variants (2509, 2511, 2512, Layered) — encoders, VAEs, Lightning low-step LoRAs, Nunchaku SVDQ
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
Luis has an extensive Qwen-Image collection. Three product lines:
1. **Qwen-Image** (text-to-image, multilingual, very strong typography)
2. **Qwen-Image Edit** (instruction-based image editing)
3. **Qwen-Image Layered** (separated layer outputs)

Plus dated revisions: 2509 (Sept 2025), 2511 (Nov 2025), 2512 (Dec 2025).

## Encoder + VAE pairing

| Component | File |
|---|---|
| Text encoder (full bf16) | `clip/qwen_2.5_vl_7b.safetensors` (16 GB) — Qwen2.5-VL 7B |
| Text encoder (fp8) | `clip/qwen_2.5_vl_7b_fp8_scaled.safetensors` (8.8 GB) — practical pick |
| CLIPLoader type | `qwen_image` |
| VAE | `vae/qwen_image_vae.safetensors` (243 MB) for normal models |
| Layered VAE | `vae/qwen_image_layered_vae.safetensors` (243 MB) for `qwen_image_layered_*` only |
| Latent | EmptySD3LatentImage works (model accepts via fix_empty_latent_channels) |

**ComfyUI-QwenVL** custom node provides extra QwenVL utility nodes for prompt enhancement.

## Qwen-Image (T2I) variants

| File | Format | Size | Recommended for |
|---|---|---|---|
| `qwenImage_qwenImageFullBF16.safetensors` | bf16 | 39 GB | best quality, tight on 32 GB |
| `qwen_image_2512_bf16.safetensors` | bf16 (Dec 2025) | 39 GB | newest, best quality |
| `qwen_image_fp8_e4m3fn.safetensors` | fp8 | 20 GB | daily driver |
| `qwen_image_2512_fp8_e4m3fn.safetensors` | fp8 (Dec 2025) | 20 GB | newest fp8 |
| `qwen-image-Q4_0.gguf` / `Q8_0.gguf` (in unet/) | GGUF | 12 / 21 GB | low/mid VRAM |
| `unet/qwen-image-2512-Q8_0.gguf` | GGUF Dec 2025 | 21 GB | |
| `Qwen-Rapid-AIO-NSFW-v9.safetensors` / `LiteNSFW-v9` | finetune | 27 GB | |
| `unet/qwen-rapid-nsfw-v5.3-Q8_0.gguf` | finetune GGUF | 21 GB | |

## Qwen-Image Edit variants (instruction-based image editing)

| File | Format | Size | Notes |
|---|---|---|---|
| `qwen_image_edit_bf16.safetensors` | bf16 | 39 GB | original Edit |
| `qwen_image_edit_fp8_e4m3fn.safetensors` | fp8 | 20 GB | original fp8 |
| `qwen_image_edit_2509_bf16.safetensors` | bf16 (Sept 2025) | 39 GB | |
| `qwen_image_edit_2509_fp8_e4m3fn.safetensors` | fp8 (Sept 2025) | 20 GB | |
| `qwen_image_edit_2511_bf16.safetensors` | bf16 (Nov 2025) | 39 GB | newer |
| `unet/Qwen-Image-Edit-2509-Q3_K_M.gguf` ... `Q8_0.gguf` | full GGUF range | 9-21 GB | Q3-Q8 all available |
| `unet/qwen-image-edit-2511-Q8_0.gguf` | GGUF Nov 2025 | 21 GB | |

Edit workflow shape: load image with `LoadImage` → `VAEEncode` → `ReferenceLatent` (from kjnodes or core) → conditioning input. Pattern matches the existing `GGUG_Flux2.json` in user's workflows folder which is actually a Qwen-Edit-style two-image workflow.

## Qwen-Image Layered

`qwen_image_layered_bf16.safetensors` (39 GB) + `unet/Qwen_Image_Layered-Q8_0.gguf` (21 GB) — outputs separated layers (foreground/background/alpha). Pair with `qwen_image_layered_vae.safetensors` (NOT the regular Qwen VAE).

## Nunchaku SVDQ Qwen-Image (FP4/INT4 quantization)

Loads via `NunchakuQwenImageDiTLoader` from ComfyUI-nunchaku, NOT UNETLoader.

### Lightning variants (4-step / 8-step distilled)

| File | Quant | Steps | Size |
|---|---|---|---|
| `svdq-fp4_r32-qwen-image-lightningv1.0-4steps.safetensors` | FP4 r32 | 4 | 12 GB |
| `svdq-fp4_r32-qwen-image-lightningv1.1-8steps.safetensors` | FP4 r32 | 8 | 12 GB |
| `svdq-fp4_r128-qwen-image-lightningv1.1-8steps.safetensors` | FP4 r128 | 8 | 13 GB |
| `svdq-int4_r32-qwen-image-lightningv1.0-4steps.safetensors` | INT4 r32 | 4 | 11 GB |

### Edit-2509 SVDQ Lightning variants

| File | Quant | Steps |
|---|---|---|
| `svdq-fp4_r128-qwen-image-edit-2509-lightningv2.0-4steps.safetensors` | FP4 r128 | 4 |
| `svdq-fp4_r128-qwen-image-edit-2509-lightningv2.0-8steps.safetensors` | FP4 r128 | 8 |
| `svdq-fp4_r32-qwen-image-edit-2509-lightningv2.0-4steps.safetensors` | FP4 r32 | 4 |
| `svdq-fp4_r32-qwen-image-edit-2509-lightningv2.0-8steps.safetensors` | FP4 r32 | 8 |
| `svdq-int4_r128-qwen-image-edit-2509-lightningv2.0-4steps.safetensors` | INT4 r128 | 4 |
| `svdq-int4_r32-qwen-image-edit-lightningv1.0-4steps.safetensors` | INT4 r32 | 4 |

**Lightning LoRA usage:** the model is the base Qwen-Image bundled with a Lightning low-step LoRA already merged. Use the matching step count in KSampler. cfg≈1 for distilled output.

**FP4 vs INT4 on Luis's 5090:** FP4 needs cu130 to actually accelerate (currently on cu128). Until upgrade, INT4 r32 is the practical choice on Blackwell.

## Qwen-Image ControlNets

| File | Type |
|---|---|
| `controlnet/Qwen-Image-InstantX-ControlNet-Union.safetensors` (3.3 GB) | Union (multi-mode) |
| `controlnet/Qwen-Image-InstantX-ControlNet-Inpainting.safetensors` (4.0 GB) | Inpainting |

## ComfyUI-QwenMultiAngle custom node

Custom node `comfyui-qwenmultiangle` provides Qwen-VL-based multi-angle generation utilities. Workflow `Qwen_MultiAngle_image_edit (1).json` already in user's library uses these nodes.

## Verification

1. Filename in `G:\models\diffusion_models\` or `unet\`
2. Encoder = `qwen_2.5_vl_7b.safetensors` (or fp8) with type `qwen_image`
3. VAE = `qwen_image_vae.safetensors` (or `qwen_image_layered_vae` for layered)
4. For Lightning variants: KSampler steps match the filename suffix (4steps → 4 steps, etc.); cfg=1
5. For SVDQ variants: use `NunchakuQwenImageDiTLoader` not UNETLoader
