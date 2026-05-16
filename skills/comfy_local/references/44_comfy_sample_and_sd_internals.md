---
name: comfy/sample.py + comfy/sd.py — algorithm-layer internals
description: What's underneath KSampler and the loader nodes. comfy/sample.py (73 lines, noise prep + sample()) and comfy/sd.py (1887 lines, load_diffusion_model + load_clip + TEModel enum + LoRA application). Encoder auto-detection, model auto-detection, the relationship between user-facing nodes and the algorithm code.
type: reference
---

# comfy/sample.py + comfy/sd.py internals

Reference 37 covered the user-facing core node CLASSES (KSampler, CLIPTextEncode, etc.). This one goes one layer deeper — the actual algorithm code those nodes call.

**Sources:** `comfy/sample.py` (73 lines), `comfy/sd.py` (1887 lines). Read date: 2026-05-09.

---

## comfy/sample.py — the entire file is this short

It's 73 lines with 5 public functions. KSampler delegates almost everything here.

### `prepare_noise(latent_image, seed, noise_inds=None)`

```python
def prepare_noise(latent_image, seed, noise_inds=None):
    generator = torch.manual_seed(seed)
    # ... handles is_nested case (latent batches) ...
    return prepare_noise_inner(latent_image, generator, noise_inds)
```

Deterministic noise from a seed. **Critical detail**: noise is generated on CPU (`device="cpu"` in `torch.randn`), THEN cast to the latent's device. This matters because:
- Same seed = same noise across different GPU models (RTX 4090 and RTX 5090 produce identical noise from the same seed)
- The seed is global (`torch.manual_seed`), not per-tensor
- `noise_inds` lets you skip-and-discard noise samples for partial batches

### `fix_empty_latent_channels(model, latent_image, downscale_ratio_spacial=None)`

This is what makes `EmptyLatentImage` work across ALL model families even though it always produces 4-channel `[B,4,H/8,W/8]` latents:

```python
latent_format = model.get_model_object("latent_format")
if torch.count_nonzero(latent_image) == 0:    # only reshape EMPTY (zero) latents
    if latent_format.latent_channels != latent_image.shape[1]:
        latent_image = comfy.utils.repeat_to_batch_size(
            latent_image, latent_format.latent_channels, dim=1)
    if downscale_ratio_spacial is not None:
        if downscale_ratio_spacial != latent_format.spacial_downscale_ratio:
            ratio = downscale_ratio_spacial / latent_format.spacial_downscale_ratio
            latent_image = comfy.utils.common_upscale(...)
```

So:
- Wired `EmptyLatentImage(1024, 1024)` → produces `[1, 4, 128, 128]` with `downscale_ratio_spacial=8`
- KSampler with a Flux 2 model calls `fix_empty_latent_channels` → reshapes to `[1, 128, 64, 64]` (Flux 2 has 128 channels and /16 spatial)
- KSampler with SDXL → leaves as `[1, 4, 128, 128]`

`latent_format` lives on the model and exposes `latent_channels` + `spacial_downscale_ratio`. This is also why `EmptyFlux2LatentImage` (ref 37) directly produces `[B, 128, H/16, W/16]` — for clarity, but `EmptyLatentImage + Flux 2` would also work (the auto-fix kicks in).

NON-empty latents (img2img path) are NOT reshaped — they're passed through. This is correct because img2img latents are already in the model's native shape from VAEEncode.

### `sample(model, noise, steps, cfg, sampler_name, scheduler, positive, negative, latent_image, ...)`

```python
def sample(model, noise, steps, cfg, sampler_name, scheduler, positive, negative,
           latent_image, denoise=1.0, ...):
    sampler = comfy.samplers.KSampler(
        model, steps=steps, device=model.load_device,
        sampler=sampler_name, scheduler=scheduler,
        denoise=denoise, model_options=model.model_options
    )
    samples = sampler.sample(noise, positive, negative, cfg=cfg, latent_image=latent_image,
                             start_step=start_step, last_step=last_step,
                             force_full_denoise=force_full_denoise,
                             denoise_mask=noise_mask, sigmas=sigmas,
                             callback=callback, disable_pbar=disable_pbar, seed=seed)
    samples = samples.to(device=comfy.model_management.intermediate_device(),
                         dtype=comfy.model_management.intermediate_dtype())
    return samples
```

The function is a 3-line wrapper:
1. Instantiate `KSampler` from `comfy.samplers` with the chosen sampler+scheduler combo
2. Call `.sample()` with the prepared inputs
3. Move output to intermediate device/dtype (so VRAM frees, downstream node can pick up)

`intermediate_device()` is typically CPU when using `--cpu-offload` style settings; `intermediate_dtype()` is bfloat16 by default.

### `sample_custom(model, noise, cfg, sampler, sigmas, ...)`

The SamplerCustomAdvanced path. Takes pre-built `sampler` and `sigmas` objects directly (skipping the sampler_name + scheduler + steps + denoise → sampler instantiation). Used by AYS, custom sigma curves, two-stage sampling.

```python
samples = comfy.samplers.sample(model, noise, positive, negative, cfg, model.load_device,
                                sampler, sigmas, model_options=model.model_options, ...)
```

This calls a different entry point in `comfy.samplers` — module-level `sample()` rather than `KSampler.sample()`.

### `prepare_sampling()` and `cleanup_additional_models()` — both deprecated

Both emit warnings and return immediately. Kept for backward compatibility with custom nodes that haven't migrated yet.

---

## comfy/sd.py — the 1887-line model-loading library

This file is what every loader node calls into. Public functions:

| Function | What user-facing node uses it |
|---|---|
| `load_checkpoint_guess_config(ckpt_path, ...)` | `CheckpointLoaderSimple` |
| `load_diffusion_model(unet_path, model_options)` | `UNETLoader` |
| `load_clip(ckpt_paths, embedding_directory, clip_type, model_options)` | `CLIPLoader`, `DualCLIPLoader` |
| `load_text_encoder_state_dicts(state_dicts, ...)` | Used internally by load_clip + GGUF custom node |
| `load_diffusion_model_state_dict(sd, model_options, metadata)` | Used by GGUF/Nunchaku custom nodes when they have a state_dict already |
| `load_lora_for_models(model, clip, lora, strength_model, strength_clip)` | `LoraLoader` |
| `load_style_model(ckpt_path)` | `StyleModelLoader` |
| `load_gligen(ckpt_path)` | `GLIGENLoader` |

Plus `class CLIP`, `class VAE`, `class StyleModel` — the actual model wrapper classes.

### CLIPType enum — the `type` field on CLIPLoader

```python
class CLIPType(Enum):
    STABLE_DIFFUSION = 1
    FLUX = 2
    SD3 = 3
    HUNYUAN_VIDEO = 4
    HIDREAM = 5
    HUNYUAN_IMAGE = 6
    KANDINSKY5 = 7
    KANDINSKY5_IMAGE = 8
    LTXV = 9
    NEWBIE = 10
    ACE = 11
    STABLE_CASCADE = 12
    STABLE_AUDIO = 13
    MOCHI = 14
    PIXART = 15
    COSMOS = 16
    LUMINA2 = 17       # Z-Image, AuraFlow
    WAN = 18
    CHROMA = 19
    OMNIGEN2 = 20
    QWEN_IMAGE = 21
    FLUX2 = 22
    OVIS = 23
    LONGCAT_IMAGE = 24
    HUNYUAN_VIDEO_15 = 25
    OMNIGEN3 = 26
    HUNYUAN_TINKER = 27
    ...
```

When you set `CLIPLoader.type = "lumina2"`, it converts via `getattr(comfy.sd.CLIPType, type.upper())` into the int value above and routes to the right tokenizer + embedding pipeline.

### TEModel enum — what files actually contain

```python
class TEModel(Enum):
    CLIP_L = 1
    CLIP_H = 2
    CLIP_G = 3
    T5_XXL = 4
    T5_XL = 5
    T5_BASE = 6
    LLAMA3_8 = 7
    T5_XXL_OLD = 8
    GEMMA_2_2B = 9
    QWEN25_3B = 10        # OmniGen2
    QWEN25_7B = 11        # Qwen-Image, Qwen-Image-Edit
    BYT5_SMALL_GLYPH = 12
    GEMMA_3_4B = 13
    MISTRAL3_24B = 14
    MISTRAL3_24B_PRUNED_FLUX2 = 15  # Flux 2 dev encoder
    QWEN3_4B = 16         # Z-Image, Klein-4B
    QWEN3_2B = 17
    GEMMA_3_12B = 18
    JINA_CLIP_2 = 19
    QWEN3_8B = 20         # Klein-9B
    QWEN3_06B = 21
    GEMMA_3_4B_VISION = 22
    QWEN35_08B/2B/4B/9B/27B = 23-27
    MINISTRAL_3_3B = 28
```

### `detect_te_model(sd)` — encoder auto-identification

When you load an encoder file, `detect_te_model` introspects the state_dict to identify which architecture it is by looking at signature weights:

```python
if "text_model.encoder.layers.30.mlp.fc1.weight" in sd:
    return TEModel.CLIP_G
if "text_model.encoder.layers.22.mlp.fc1.weight" in sd:
    return TEModel.CLIP_H
if "text_model.encoder.layers.0.mlp.fc1.weight" in sd:
    return TEModel.CLIP_L
if "model.encoder.layers.0.mixer.Wqkv.weight" in sd:
    return TEModel.JINA_CLIP_2
if "encoder.block.23.layer.1.DenseReluDense.wi_1.weight" in sd:
    weight = sd["encoder.block.23.layer.1.DenseReluDense.wi_1.weight"]
    if weight.shape[0] == 10240:
        return TEModel.T5_XXL
    elif weight.shape[0] == 5120:
        return TEModel.T5_XL
# ...
```

This is what catches mismatches: load a Mistral file but pass `type="lumina2"` — `detect_te_model` returns `MISTRAL3_24B_PRUNED_FLUX2`, but the lumina2 path expects QWEN3_4B → mismatch error in `load_text_encoder_state_dicts`.

### `load_diffusion_model(unet_path)` — auto-detect model family

```python
def load_diffusion_model(unet_path, model_options={}):
    sd, metadata = comfy.utils.load_torch_file(unet_path, return_metadata=True)
    model = load_diffusion_model_state_dict(sd, model_options=model_options, metadata=metadata)
    if model is None:
        raise RuntimeError("ERROR: Could not detect model type of: ...")
    model.cached_patcher_init = (load_diffusion_model, (unet_path, model_options))
    return model
```

`load_diffusion_model_state_dict` calls into `comfy/model_detection.py` (ref 07 already showed the Wan branch) which scans state_dict keys to identify the model family. Same mechanism for Flux 2, Klein, Qwen-Image, Z-Image, etc.

`cached_patcher_init` lets the model patcher reload the same model later without going through detection again — important for `--lazy-load` and the cache providers.

### `load_lora_for_models(model, clip, lora, strength_model, strength_clip)`

LoRAs are dicts mapping target layer names to (UP, DOWN) weight tensors. This function:

1. Walks the lora dict
2. For each key, decides whether it targets the UNet (model) or CLIP based on the prefix
3. Calls `model.patch()` / `clip.patch()` with the (UP, DOWN, strength) tuples
4. Returns patched (model, clip)

`strength_model=0` AND `strength_clip=0` → returns originals unchanged (the LoraLoader short-circuit).

`load_bypass_lora_for_models` is a variant that bypasses the patcher cache — used when you need to apply different LoRA strengths to the same checkpoint repeatedly.

### `class CLIP` — what comes out of CLIPLoader

The CLIP class wraps:
- `self.tokenizer` — the encoder's tokenizer
- `self.cond_stage_model` — the actual encoder weights
- `self.patcher` — the ComfyUI ModelPatcher wrapper (for LoRA application)
- `self.layer_idx` — for `CLIPSetLastLayer` (clip skip)

Key methods:
- `tokenize(text)` — text → token IDs
- `encode_from_tokens_scheduled(tokens)` — token IDs → conditioning tensor (this is what CLIPTextEncode calls)

### `class VAE` — what comes out of VAELoader

VAE wraps:
- `self.first_stage_model` — the actual VAE weights
- `self.spacial_compression_decode()` / `self.spacial_compression_encode()` — returns the spatial scale (e.g. 8 for SDXL)
- `self.temporal_compression_decode()` — returns temporal scale (for video VAEs, None for image VAEs)
- `self.tiled_decode()` / `self.tiled_encode()` — for VAEDecodeTiled / VAEEncodeTiled

Key methods:
- `decode(latent)` — latent → image
- `encode(image)` — image → latent

### `load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, ...)`

The classic SD1.5 / SDXL / Pony / Illustrious checkpoint loader. Returns:
- `model` — the UNet
- `clip` — the text encoder(s) bundled into the checkpoint
- `vae` — the VAE bundled into the checkpoint
- `clipvision` — for IPAdapter etc. (optional)

This is what `CheckpointLoaderSimple` calls. Modern model families (Flux/Qwen/Z-Image/Wan) ship the components separately, so they use `UNETLoader + CLIPLoader + VAELoader` instead.

---

## How user-facing nodes map to library functions

| User node | Library function called |
|---|---|
| `KSampler` | `comfy.sample.sample()` -> `comfy.samplers.KSampler.sample()` |
| `KSamplerAdvanced` | same with extra noise/step args |
| `SamplerCustomAdvanced` | `comfy.sample.sample_custom()` -> `comfy.samplers.sample()` |
| `EmptyLatentImage` | direct `torch.zeros(...)` (4-ch) — auto-reshaped by `fix_empty_latent_channels` |
| `EmptyFlux2LatentImage` | direct `torch.zeros(...)` (128-ch /16) — already correct shape |
| `UNETLoader` | `comfy.sd.load_diffusion_model()` |
| `CheckpointLoaderSimple` | `comfy.sd.load_checkpoint_guess_config()` |
| `CLIPLoader` / `DualCLIPLoader` | `comfy.sd.load_clip()` |
| `VAELoader` | `comfy.sd.VAE(...)` constructor |
| `LoraLoader` | `comfy.sd.load_lora_for_models()` |
| `CLIPTextEncode` | `clip.tokenize()` + `clip.encode_from_tokens_scheduled()` |
| `VAEDecode` | `vae.decode(latent)` |
| `VAEEncode` | `vae.encode(image)` |
| `ConditioningZeroOut` | `torch.zeros_like(t[0])` + `pooled_output` zeroing |

---

## Why this matters

Knowing the algorithm layer helps debug edge cases:

1. **"Why is my noise different on different seeds?"** — `prepare_noise` uses `torch.manual_seed(seed)` which sets the GLOBAL torch seed. If a custom node calls `torch.randn()` between your runs, it consumes random values from the same generator and shifts your output even if your seed is the same.

2. **"Why does my workflow break when I swap from SDXL to Flux 2?"** — `fix_empty_latent_channels` auto-reshapes from (4,/8) → (128,/16), but only for ZERO latents. If you're doing img2img, the latent already has SDXL's 4-channel shape and nothing reshapes — you get a shape mismatch in KSampler. Solution: re-encode with the new VAE.

3. **"Why does my LoRA seem to have no effect?"** — Two failure modes:
   - `strength_model=0 AND strength_clip=0` → silent early return
   - LoRA targets keys that don't exist in the loaded model (wrong family) → silent skip per-key. No error, just no effect.

4. **"Why does CLIPLoader fail with my GGUF encoder?"** — `detect_te_model` runs over the state_dict signature keys. GGUF tensors have different key names than safetensors. The GGUF custom node has its own `load_text_encoder_state_dicts` path that handles the rename — but core CLIPLoader doesn't.

5. **"My freshly trained LoRA isn't loading"** — `load_lora_for_models` expects standard LoRA key naming (`lora_unet_*`, `lora_te_*`). If your trainer used non-standard keys (e.g. `transformer_blocks.X.attn.to_q.lora_up`), it won't be detected. Either rename keys in the safetensors file or use `comfyui-lora-manager` which handles more naming conventions.

---

## CLIPType vs TEModel — the key distinction

- **CLIPType** = the FAMILY of MODEL the encoder is for (FLUX, QWEN_IMAGE, LUMINA2, WAN, etc.). Dictates the tokenizer config + how prompts get embedded.
- **TEModel** = the ARCHITECTURE of the encoder file itself (CLIP_L, T5_XXL, MISTRAL3_24B, QWEN3_4B, etc.). Dictated by the file's actual weights.

A CLIPType uses ONE OR MORE TEModels. Examples:
- CLIPType.STABLE_DIFFUSION → TEModel.CLIP_L
- CLIPType.FLUX → TEModel.CLIP_L + TEModel.T5_XXL (DualCLIPLoader)
- CLIPType.LUMINA2 → TEModel.QWEN3_4B (Z-Image)
- CLIPType.WAN → some-T5-variant (UMT5)
- CLIPType.QWEN_IMAGE → TEModel.QWEN25_7B (Qwen2.5-VL)
- CLIPType.FLUX2 → TEModel.MISTRAL3_24B_PRUNED_FLUX2 (Flux 2 dev) or TEModel.QWEN3_4B (Klein-4B) or TEModel.QWEN3_8B (Klein-9B)

This is why the encoder-mismatch error happens at `txt = self.txt_in(txt)` in the DiT — the tokenizer/encoder pair was wrong, so the embedding shape is wrong, so the DiT's projection matrix can't multiply.

The CLIPType → TEModel mapping is enforced inside `load_text_encoder_state_dicts(state_dicts, clip_type, ...)` — if you give it state_dicts that don't match what `clip_type` expects, you get an error before sampling even starts. (Sometimes. Other times the mismatch only shows up later. The errors haven't been uniform across the codebase historically.)
