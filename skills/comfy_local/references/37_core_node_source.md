---
name: ComfyUI core node source — exact behavior of canonical nodes
description: Truth (not paraphrase) of what KSampler, CLIPTextEncode, VAEDecode, SaveImage, ConditioningZeroOut, LoraLoader, EmptyLatentImage, EmptyFlux2LatentImage, ModelSamplingAuraFlow, FluxGuidance, UNETLoader, CLIPLoader, DualCLIPLoader actually do. Source: ComfyUI/nodes.py (2527 lines) + comfy_extras/nodes_flux.py + nodes_model_advanced.py.
type: reference
---

# Core node source — exact behavior

**Why this exists:** working from API behavior risks paraphrasing. This reference captures what the canonical core nodes literally do, copied from the source.

**Sources:** `ComfyUI/nodes.py` (2527 lines), `ComfyUI/comfy_extras/nodes_flux.py`, `ComfyUI/comfy_extras/nodes_model_advanced.py`. Read date: 2026-05-09.

## CLIPTextEncode

```python
def encode(self, clip, text):
    if clip is None:
        raise RuntimeError("ERROR: clip input is invalid: None\n\n...")
    tokens = clip.tokenize(text)
    return (clip.encode_from_tokens_scheduled(tokens), )
```

- Inputs: `text` (STRING, multiline=True, dynamicPrompts=True), `clip` (CLIP)
- Output: `CONDITIONING`
- The "scheduled" in `encode_from_tokens_scheduled` is what supports BREAK syntax and weight syntax `(thing:1.3)`. dynamicPrompts=True enables wildcard expansion `{a|b|c}`.
- Pure pass-through — no model loaded here, just tokenization + embedding.

## ConditioningZeroOut (the `negative = zero(positive)` distilled-model trick)

```python
def zero_out(self, conditioning):
    c = []
    for t in conditioning:
        d = t[1].copy()
        pooled_output = d.get("pooled_output", None)
        if pooled_output is not None:
            d["pooled_output"] = torch.zeros_like(pooled_output)
        conditioning_lyrics = d.get("conditioning_lyrics", None)
        if conditioning_lyrics is not None:
            d["conditioning_lyrics"] = torch.zeros_like(conditioning_lyrics)
        n = [torch.zeros_like(t[0]), d]
        c.append(n)
    return (c, )
```

- Replaces the embedding tensor with zeros AND zeros the pooled output too (so SDXL/Flux pooled paths also get zeroed).
- Preserves dict metadata (cross-attention keys, masks, etc.) — only the tensor values get zeroed.
- This is THE node to use for distilled models (Flux 2, Klein, schnell, Kontext, Krea, Fill, Lightning Qwen, Z-Image turbo) where the negative is internally ignored. Wire `CLIPTextEncode("")` → `ConditioningZeroOut` → KSampler.negative.

## VAEDecode

```python
def decode(self, vae, samples):
    latent = samples["samples"]
    if latent.is_nested:
        latent = latent.unbind()[0]
    images = vae.decode(latent)
    if len(images.shape) == 5:  # Combine batches (video)
        images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])
    return (images, )
```

- LATENT is a dict `{"samples": tensor, ...}` — not the bare tensor.
- For video VAEs the output is 5D `[B, F, H, W, C]`; this node reshapes to 4D `[B*F, H, W, C]` so downstream image nodes can handle the per-frame view.

## ConditioningCombine vs ConditioningConcat vs ConditioningAverage

| Node | What it does |
|---|---|
| `ConditioningCombine` | `return (conditioning_1 + conditioning_2, )` — Python list concatenation. Both conds apply additively at sampling time. |
| `ConditioningConcat` | Concatenates the embedding tensors along the token dimension (`torch.cat([t1, t0], dim=1)`). Useful for SDXL where you want long prompts. |
| `ConditioningAverage` | Weighted blend of two conds. `tw = t1 * strength + t0 * (1-strength)`. The "from" tensor gets cropped/padded to the "to" length first. |

Combine is the multi-prompt-region pattern; Concat is the "make one long prompt" pattern; Average is the "interpolate styles" pattern.

## KSampler (the canonical sampler)

INPUT_TYPES (in order — these are the widget_values positions in graph format):

1. `model` — MODEL
2. `seed` — INT, range 0..2^64-1, **`control_after_generate: True`** (so the graph injects the "fixed/randomize/increment/decrement" widget here)
3. `steps` — INT, default 20, max 10000
4. `cfg` — FLOAT, default 8.0, max 100.0, step 0.1, **`round: 0.01`**
5. `sampler_name` — combo from `comfy.samplers.KSampler.SAMPLERS`
6. `scheduler` — combo from `comfy.samplers.KSampler.SCHEDULERS`
7. `positive` — CONDITIONING
8. `negative` — CONDITIONING
9. `latent_image` — LATENT
10. `denoise` — FLOAT, default 1.0, range 0..1

Returns `(LATENT,)`.

`common_ksampler()` is the workhorse — used by both KSampler and KSamplerAdvanced:

```python
def common_ksampler(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent,
                    denoise=1.0, disable_noise=False, start_step=None, last_step=None,
                    force_full_denoise=False):
    latent_image = latent["samples"]
    latent_image = comfy.sample.fix_empty_latent_channels(model, latent_image, latent.get("downscale_ratio_spacial", None))

    if disable_noise:
        noise = torch.zeros(latent_image.size(), ...)  # for "continue from leftover noise"
    else:
        batch_inds = latent.get("batch_index", None)
        noise = comfy.sample.prepare_noise(latent_image, seed, batch_inds)

    noise_mask = latent.get("noise_mask", None)

    callback = latent_preview.prepare_callback(model, steps)
    samples = comfy.sample.sample(model, noise, steps, cfg, sampler_name, scheduler,
                                  positive, negative, latent_image,
                                  denoise=denoise, disable_noise=disable_noise,
                                  start_step=start_step, last_step=last_step,
                                  force_full_denoise=force_full_denoise,
                                  noise_mask=noise_mask, callback=callback,
                                  disable_pbar=disable_pbar, seed=seed)
    out = latent.copy()
    out.pop("downscale_ratio_spacial", None)  # consumed once, removed from output
    out["samples"] = samples
    return (out, )
```

Things this clarifies:

- `noise` is generated once, deterministically from `(seed, batch_index)`. The same seed gives the same noise.
- `noise_mask` is read from the latent dict (set via `SetLatentNoiseMask`) — it's how inpaint masking flows into sampling.
- `downscale_ratio_spacial` is consumed by `fix_empty_latent_channels` and stripped from the output (so it doesn't propagate to downstream samplers).
- `force_full_denoise` is what KSamplerAdvanced toggles when `return_with_leftover_noise=disable`.

### KSamplerAdvanced extras

- `add_noise` enable/disable (start from a clean noisy latent vs continue from existing latent)
- `noise_seed` (separate from `seed` so you can reuse a layout's noise)
- `start_at_step` / `end_at_step` (partial-denoise range — useful for img2img and refiner pipelines)
- `return_with_leftover_noise` (controls `force_full_denoise`)

## SaveImage

```python
def __init__(self):
    self.output_dir = folder_paths.get_output_directory()
    self.type = "output"
    self.prefix_append = ""
    self.compress_level = 4

def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
    filename_prefix += self.prefix_append
    full_output_folder, filename, counter, subfolder, filename_prefix = \
        folder_paths.get_save_image_path(filename_prefix, self.output_dir,
                                        images[0].shape[1], images[0].shape[0])
    results = []
    for (batch_number, image) in enumerate(images):
        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        metadata = None
        if not args.disable_metadata:
            metadata = PngInfo()
            if prompt is not None:
                metadata.add_text("prompt", json.dumps(prompt))
            if extra_pnginfo is not None:
                for x in extra_pnginfo:
                    metadata.add_text(x, json.dumps(extra_pnginfo[x]))
        filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
        file = f"{filename_with_batch_num}_{counter:05}_.png"
        img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)
        results.append({"filename": file, "subfolder": subfolder, "type": self.type})
        counter += 1
    return {"ui": {"images": results}}
```

Truths buried here:

- `filename_prefix` supports format strings: `%date:yyyy-MM-dd%`, `%Empty Latent Image.width%` (lookup other node widget values), `%batch_num%` (per-image counter within the batch).
- `compress_level=4` for SaveImage, `compress_level=1` for PreviewImage (faster but bigger files for transient previews).
- The full prompt JSON gets embedded in the PNG metadata under the key `"prompt"` (ALL the workflow data — drag a saved PNG back into ComfyUI to recover the workflow).
- `extra_pnginfo` keys also get embedded — usually contains `"workflow"` (graph format) too.
- OUTPUT_NODE = True so it runs even if nothing reads its non-existent output.
- Returns `{"ui": {"images": [...]}}` — the `ui.images` channel is what shows the preview thumbnail in the canvas.

`PreviewImage` is `class PreviewImage(SaveImage)` with `output_dir=temp`, `type="temp"`, and `prefix_append` set to a random suffix so previews don't collide.

## LoraLoader

```python
def load_lora(self, model, clip, lora_name, strength_model, strength_clip):
    if strength_model == 0 and strength_clip == 0:
        return (model, clip)  # no-op early return

    lora_path = folder_paths.get_full_path_or_raise("loras", lora_name)
    lora = None
    if self.loaded_lora is not None:
        if self.loaded_lora[0] == lora_path:
            lora = self.loaded_lora[1]   # cache hit
        else:
            self.loaded_lora = None
    if lora is None:
        lora = comfy.utils.load_torch_file(lora_path, safe_load=True)
        self.loaded_lora = (lora_path, lora)

    model_lora, clip_lora = comfy.sd.load_lora_for_models(model, clip, lora, strength_model, strength_clip)
    return (model_lora, clip_lora)
```

- `__init__` sets `self.loaded_lora = None`. The instance caches the most-recent LoRA file content. Stacking LoRAs is multiple LoraLoader nodes chained — each instance has its own cache, the `comfy.sd.load_lora_for_models` call is what merges into the model+clip.
- `strength=0` short-circuits and returns the unmodified model+clip.
- Strength range `-100..+100` (negative LoRA inverts the direction).
- `LoraLoaderModelOnly` is a subclass that hides the clip path — used for distilled models that don't apply CLIP-side LoRAs (Flux UNET-only LoRAs).

## EmptyLatentImage (the SD 1.5 / SDXL latent generator)

```python
def generate(self, width, height, batch_size=1):
    latent = torch.zeros([batch_size, 4, height // 8, width // 8],
                         device=comfy.model_management.intermediate_device(),
                         dtype=comfy.model_management.intermediate_dtype())
    return ({"samples": latent, "downscale_ratio_spacial": 8}, )
```

- Latent shape: `[B, 4, H/8, W/8]`. Channel count = **4**.
- Spatial downsample = **8** (so 1024 px image → 128 px latent).
- The dict carries `downscale_ratio_spacial: 8` so KSampler can validate.

## EmptyFlux2LatentImage (the Flux 2 latent generator — different shape!)

```python
def execute(cls, width, height, batch_size=1) -> io.NodeOutput:
    latent = torch.zeros([batch_size, 128, height // 16, width // 16],
                        device=comfy.model_management.intermediate_device())
    return io.NodeOutput({"samples": latent})
```

- Latent shape: `[B, 128, H/16, W/16]`. Channel count = **128** (NOT 4). Spatial downsample = **16** (NOT 8).
- This is why mixing Flux 2 with the wrong latent generator produces shape errors — the channel count is 32× different.
- Note: written in v3 io.ComfyNode style.

## FluxGuidance (the distilled-CFG knob for Flux family)

```python
def execute(cls, conditioning, guidance) -> io.NodeOutput:
    c = node_helpers.conditioning_set_values(conditioning, {"guidance": guidance})
    return io.NodeOutput(c)
```

- Default: `guidance=3.5`.
- Doesn't change the embedding tensor — it ATTACHES `guidance` as a metadata field on the conditioning. The Flux DiT picks this up internally during sampling.
- This is why Flux uses `cfg=1` AND a separate FluxGuidance — the "real CFG" lives inside the model and is controlled by this guidance value.

## ModelSamplingAuraFlow (the Z-Image / AuraFlow / Lightning shift node)

```python
class ModelSamplingAuraFlow(ModelSamplingSD3):
    @classmethod
    def INPUT_TYPES(s):
        return {"required": { "model": ("MODEL",),
                              "shift": ("FLOAT", {"default": 1.73, "min": 0.0, "max": 100.0, "step":0.01}),
                              }}
    FUNCTION = "patch_aura"

    def patch_aura(self, model, shift):
        return self.patch(model, shift, multiplier=1.0)
```

- Inherits from `ModelSamplingSD3`. The `shift` parameter controls how the noise schedule's σ-curve gets shifted — high values push more noise into early steps, low values keep noise even.
- Default 1.73, but the model-family-correct values are:
  - Z-Image base / Z-Image-Turbo: shift=3
  - Qwen-Image-Edit / Qwen-Image-Edit-2511: shift=0.3
  - Lightning LoRAs (qwen): shift=3
- Returns the patched MODEL (the original is kept clean via `model.clone()` inside `patch`).

## ModelSamplingFlux (the Flux family equivalent)

Different shape — takes `max_shift`, `base_shift`, `width`, `height`. The shift is computed as a function of resolution rather than a single scalar. Default `max_shift=1.15, base_shift=0.5`. This is what AURA-flow and Flux model-sampling looks like in v1 widgets style.

## UNETLoader (the bare DiT loader)

```python
def load_unet(self, unet_name, weight_dtype):
    model_options = {}
    if weight_dtype == "fp8_e4m3fn":
        model_options["dtype"] = torch.float8_e4m3fn
    elif weight_dtype == "fp8_e4m3fn_fast":
        model_options["dtype"] = torch.float8_e4m3fn
        model_options["fp8_optimizations"] = True
    elif weight_dtype == "fp8_e5m2":
        model_options["dtype"] = torch.float8_e5m2
    unet_path = folder_paths.get_full_path_or_raise("diffusion_models", unet_name)
    model = comfy.sd.load_diffusion_model(unet_path, model_options=model_options)
    return (model,)
```

- `weight_dtype` choices: `default`, `fp8_e4m3fn`, `fp8_e4m3fn_fast`, `fp8_e5m2`. This is how you force fp8 quantization on a model that's stored as bf16 on disk.
- `default` lets ComfyUI auto-pick based on model state dict + GPU capability.
- Looks under the `diffusion_models` folder (and whatever extra_model_paths.yaml routes there).

## CLIPLoader (the single-encoder loader, all model families)

```python
"type": (["stable_diffusion", "stable_cascade", "sd3", "stable_audio", "mochi", "ltxv",
          "pixart", "cosmos", "lumina2", "wan", "hidream", "chroma", "ace", "omnigen2",
          "qwen_image", "hunyuan_image", "flux2", "ovis", "longcat_image"], ),
```

The `type` parameter is critical — it tells ComfyUI which encoder architecture to expect. For Luis's install:

| type | Used for |
|---|---|
| `flux2` | Mistral encoder (Flux 2 dev) |
| `lumina2` | Qwen3-4B (Z-Image, Lumina2, Klein-4B) |
| `wan` | UMT5-XXL (Wan video) |
| `qwen_image` | Qwen2.5-VL (Qwen-Image, Qwen-Image-Edit) |

Wrong type → encoder loads but emits embeddings in the wrong layout → mat1/mat2 shape mismatch at sampling time. This is the canonical encoder-mismatch root cause.

The DESCRIPTION docstring on this node lists the recipes:

> stable_diffusion: clip-l
> stable_cascade: clip-g
> sd3: t5 xxl/ clip-g / clip-l
> stable_audio: t5 base
> mochi: t5 xxl
> cosmos: old t5 xxl
> lumina2: gemma 2 2B (Z-Image: Qwen3-4B)
> wan: umt5 xxl
> hidream: llama-3.1 (Recommend) or t5
> omnigen2: qwen vl 2.5 3B

(Note the docstring is a bit outdated for Z-Image — it says gemma but Luis's install actually uses Qwen3-4B with type=lumina2.)

## DualCLIPLoader (two-encoder pairs)

```python
"type": (["sdxl", "sd3", "flux", "hunyuan_video", "hidream", "hunyuan_image",
          "hunyuan_video_15", "kandinsky5", "kandinsky5_image", "ltxv", "newbie", "ace"], ),
```

Used when a model needs two text encoders fed in pair:

- `sdxl` → clip-L + clip-G
- `flux` → clip-L + T5-XXL
- `sd3` → various 2-of-3 combos
- `hidream` → T5 + llama-3.1

## Where the search aliases come from

Every node has an optional `SEARCH_ALIASES = [...]` list. This is what powers the node-search UI when you press `n` and type — those aliases are matched in addition to the class name and display name. Nodes with good aliases ("denoise", "diffuse", "sampler" all map to KSampler) appear faster in search.

## Where the tooltips come from

`OUTPUT_TOOLTIPS = (...)` (tuple of strings, one per output) shows hover-help on output sockets. Per-input tooltips go in the INPUT_TYPES options dict: `("STRING", {"tooltip": "..."})`.

## Hidden inputs (the ones the user doesn't see)

```python
"hidden": {
    "prompt": "PROMPT",                 # the entire workflow API JSON
    "extra_pnginfo": "EXTRA_PNGINFO",   # the graph-format JSON + workflow metadata
    "unique_id": "UNIQUE_ID",           # this node's runtime ID
    "dynprompt": "DYNPROMPT",           # parsed dynamic prompt info
    "auth_token_comfy_org": "AUTH_TOKEN_COMFY_ORG",  # for Comfy-Org-paid nodes
    "api_key_comfy_org": "API_KEY_COMFY_ORG",
}
```

These are populated automatically by the executor — don't try to wire them. Use them when your node needs to introspect its own context (e.g. to add metadata to the saved PNG, or to send a status update keyed to its node ID).

## Patterns that show up across many core nodes

1. **`return (single,)` not `return single`** — always tuple. The trailing comma matters.
2. **`samples = latent["samples"]`** then `out = latent.copy(); out["samples"] = new_samples; return (out,)` — preserve other dict keys when transforming a LATENT.
3. **Cache lifetime is per-instance** — `self.loaded_lora` survives between executions because the Python object isn't recreated. The executor reuses node instances when the graph is re-run.
4. **Tooltip strings are fairly long** — the canonical KSampler tooltip is two sentences explaining what cfg does. Aim for that level of detail.
5. **`OUTPUT_NODE = True`** is set ONLY where there's a side effect (SaveImage, PreviewImage, websocket push, file write).

## When this matters in runner / workflow authoring

- **Building API-format workflows by hand:** match the input order in `INPUT_TYPES` exactly (keys preserve insertion order in Python 3.7+, so the dict literal IS the order). Otherwise widget values get misaligned.
- **Picking a sampler:** the `SAMPLERS` and `SCHEDULERS` lists are where the combo options live — see `comfy/samplers.py` if you need to enumerate them programmatically (or query `/object_info/KSampler`).
- **Handling LATENTs:** they're dicts, not tensors. Preserve `samples`, `noise_mask`, `batch_index` when transforming.
- **Encoder pairing:** the `type` field in CLIPLoader / DualCLIPLoader is the ONE thing that has to match the DiT family. If the model is Flux 2 dev, type MUST be `flux2`. If Klein-4B, type MUST be `lumina2`. See reference 16.
- **Distilled models:** wire `CLIPTextEncode("")` → `ConditioningZeroOut` → KSampler.negative. Don't try to write a meaningful negative prompt — the model ignores it.
- **Flux family CFG:** KSampler cfg=1 + FluxGuidance(3.5) is the default for Flux 2 dev, Flux.1 dev, schnell, Krea, Kontext, Fill. Klein 4B/9B uses cfg=1, no FluxGuidance.
- **Z-Image:** ModelSamplingAuraFlow(shift=3) between UNETLoader and KSampler. CLIPLoader type=lumina2.
