---
name: ostris/ai-toolkit — LoRA / fine-tuning training framework
description: Practical reference for training LoRAs and fine-tuning diffusion models with ostris/ai-toolkit. CLI + GUI workflow, supported model families, dataset format, config structure, fit for Luis's RTX 5090 + 64 GB. Notes plan for a POP house-style LoRA. Verified intro from README, deeper details from prior knowledge — verify specifics against the current repo.
type: reference
---

# ostris/ai-toolkit — diffusion model training

**Repo:** https://github.com/ostris/ai-toolkit
**Author:** Ostris (Jaret Burkett — also behind IPAdapters and several Flux ControlNets)
**Read date:** 2026-05-09 (README intro fetched; deeper details synthesized from prior knowledge — verify against current repo state before relying on exact CLI syntax)

> Verified from README intro: "AI Toolkit is an all in one training suite for diffusion models. I try to support all the latest models on consumer grade hardware. Image and video models. It can be run as a GUI or CLI."

## What it is

A training framework that wraps `diffusers` and adds the bookkeeping, dataset handling, sample generation, and optimizer setup you'd otherwise have to write yourself. The two output types it produces:

- **LoRAs** — small adapter weights (10-300 MB depending on rank) you load on top of a base checkpoint
- **Full fine-tunes** — a full new checkpoint (multi-GB), more expensive, larger output

Both consumable in ComfyUI via standard loaders — LoRAs go in `G:\models\loras\` and load via `LoraLoader`, full fine-tunes go in `G:\models\diffusion_models\` and load via `UNETLoader`.

## CLI vs GUI

**CLI:** edit a YAML config file in `config/your_job.yaml`, then run `python run.py config/your_job.yaml`. Better for scripted/repeatable training, version-controllable configs.

**GUI:** web app launches with `python ui.py` (or similar — verify), runs at `localhost:8675` by default. Better for interactive iteration, no YAML editing. Lets you upload datasets, watch samples, manage multiple jobs.

## Models supported (verify current state — this list grows)

Image models known to be supported (as of mid-2025):
- **SD 1.5 / SDXL** — classic LoRA training
- **Flux.1 dev** — the most-used path; LoRA training fits a 24 GB card with rank ~16-32
- **Flux.1 schnell** — distilled training is more sensitive but supported
- **Flux 2** — newer; should work given the framework's pace, but verify the current repo
- **Qwen-Image** — added in 2025
- **Lumina2 / Z-Image** — added in 2025
- **HiDream** — supported

Video models:
- **Wan 2.1 / 2.2** — video LoRA training, requires block-swap on 32 GB cards for full-frame training

Verify by checking `config/examples/` in the repo — every supported model has an example config there.

## Dataset format

Convention is a folder of paired image + caption files:

```
dataset/
  001.png      002.txt has the caption "a forest shrine in autumn..."
  001.txt
  002.png
  002.txt
  ...
```

For multi-resolution training, ai-toolkit handles bucketing automatically based on image dimensions. You don't need to pre-resize — it groups images of similar aspect ratios into batches.

**Auto-captioning:** ai-toolkit can run BLIP / WD-Tagger / similar to generate captions if you don't have them.

**Regularization images:** for full fine-tunes, you can supply unrelated reference images so the model doesn't catastrophically forget its base knowledge. Less critical for LoRA training.

## Config structure (high-level YAML schema)

A typical Flux LoRA config looks roughly like:

```yaml
job: extension
config:
  name: my_pop_house_style_v1
  process:
    - type: sd_trainer
      training_folder: output/
      device: cuda:0
      network:
        type: lora
        linear: 16          # rank
        linear_alpha: 16
      save:
        dtype: float16
        save_every: 250
        max_step_saves_to_keep: 4
      datasets:
        - folder_path: G:/datasets/pop_style
          caption_ext: txt
          caption_dropout_rate: 0.05
          shuffle_tokens: false
          cache_latents_to_disk: true
          resolution: [512, 768, 1024]   # multi-res
      train:
        batch_size: 1
        steps: 2000
        gradient_accumulation_steps: 1
        train_unet: true
        train_text_encoder: false
        gradient_checkpointing: true
        noise_scheduler: flowmatch
        optimizer: adamw8bit
        lr: 4e-4
      model:
        name_or_path: black-forest-labs/FLUX.1-dev
        is_flux: true
        quantize: true             # 8-bit base for VRAM savings
      sample:
        sampler: flowmatch
        sample_every: 250
        width: 1024
        height: 1024
        prompts:
          - "a forest shrine in pop house style, painterly"
          - "a shiba warrior in pop house style, cel-shaded"
        seed: 42
        guidance_scale: 4
        sample_steps: 20
```

The exact keys evolve — always copy from a current `config/examples/<model>_lora.yaml` as a starting template.

## Fit for Luis's RTX 5090 + 64 GB RAM

The 5090's 32 GB VRAM is comfortable for:
- **Flux.1 dev LoRA** at rank 16-32, bf16 base, batch_size 1, gradient checkpointing on. ~30-60 minutes for 2000 steps on a small (~50 image) dataset.
- **Flux.1 dev FULL fine-tune**: tight at 32 GB. Need bf16 + grad checkpointing + maybe layer freezing. Possible but you'll feel it.
- **Qwen-Image / Z-Image LoRA**: similar to Flux — comfortable.
- **Wan 2.1 video LoRA**: needs block-swap (offload N transformer blocks to RAM during training, similar to how kijai's WanVideoWrapper does it for inference). 64 GB system RAM is plenty for this.
- **Flux 2 Klein-4B LoRA**: should be very comfortable (small model).
- **Flux 2 dev LoRA**: ~24B params — likely needs full block-swap or quantization tricks.

The 64 GB system RAM matters here. Block-swap during training trades VRAM for RAM; Luis has plenty.

## Fit into Luis's existing pipeline

```
[Source images]
   ↓
[Caption with BLIP or hand-write captions]
   ↓
[ai-toolkit training run, ~30-60 min for 2000 steps]
   ↓
[output/my_pop_house_style_v1/my_pop_house_style_v1.safetensors]
   ↓
[Copy to G:\models\loras\]
   ↓
[Use in ComfyUI: LoraLoader -> existing runner pipelines]
```

The trained LoRA can drop into any of Luis's runner pipelines that already use LoRAs:
- `runners/qwen_t2i_lightning.py` already loads Lightning LoRA — could chain a second LoraLoader for the POP style
- `runners/zimage_t2i.py` would need a LoraLoaderModelOnly inserted between UNETLoader and ModelSamplingAuraFlow
- `runners/wan_t2v.py` could load a Wan video LoRA via the WanVideoLoraSelect node

## POP house-style LoRA training plan (when Luis is ready)

The goal is a single LoRA that captures Luis's cel-shaded + painterly + UI-icon house style so prompts don't need the full verbatim style locks. Realistic plan:

1. **Curate a 30-100 image dataset** of Luis's existing cel-shaded characters / painterly biomes / UI icons. Higher quality > higher quantity. Mix all his asset types or train separate LoRAs per asset type.

2. **Caption each image** describing the *subject* but NOT the style (the style is what the LoRA learns implicitly). E.g., "a shiba warrior with a wooden shield, full body, white background" — NOT "in cel-shaded style with thick black outlines."

3. **Pick a base model.** For Luis's setup, two reasonable options:
   - Flux.1 dev — best general quality, well-supported
   - Qwen-Image-2512 — closer to what his runners already use, easier downstream integration

4. **Train at rank 16-32, ~2000 steps** to start. Watch the sample generations every 250 steps; stop when adherence is good but the LoRA hasn't memorized the dataset (overfitting shows as outputs that look like dataset images even with different prompts).

5. **Use a unique trigger token** in captions: e.g., "in pop_house_style art style". The LoRA learns to associate the trigger with the visual style. At inference time, include "pop_house_style" in your prompt.

6. **Test against Luis's existing GPT-prompt frameworks.** A successful LoRA reduces the prompt length needed (style locks become unnecessary because the LoRA enforces them).

7. **Iterate.** First LoRA usually needs adjustments — drop bad images, add more diverse poses, tweak rank, retrain.

## Other ai-toolkit features worth knowing

- **Layer-targeted training** — train only specific U-Net or transformer blocks (faster, smaller LoRA, less catastrophic forgetting)
- **Multi-resolution buckets** — automatic; just specify `resolution: [512, 768, 1024]` and ai-toolkit groups by aspect ratio
- **Captioning dropout** (`caption_dropout_rate: 0.05`) — randomly drops the caption for some training steps so the model learns the visual style independent of any specific caption
- **Sample generation during training** — every N steps, generate test images to monitor progress
- **Resume from checkpoint** — interrupted runs can resume from the last saved step
- **Multiple optimizers** — AdamW, AdamW 8-bit (less VRAM), Prodigy (auto-tuning LR), Adafactor (very memory-efficient)
- **DiffSynth-style training** for LoCon / LoHa / LoKr variants beyond plain LoRA

## Caveats / what could go wrong

1. **Setup friction.** Cloning + Python virtual env + `requirements.txt` install can take 30-60 minutes the first time. The portable Comfy install can't be reused — ai-toolkit needs its own venv.

2. **CUDA / torch version match.** ai-toolkit pulls a specific torch version; if your venv uses cu130 but the rest of your tooling is cu128, expect conflicts. Use a SEPARATE venv.

3. **OOM on first batch** — common. Reduce batch_size, enable gradient checkpointing, lower resolution, or use 8-bit quantized base.

4. **Captions matter a LOT.** Bad captions = bad LoRA. Spend the time captioning thoughtfully. WD-Tagger auto-tags work for general purposes; for stylistic LoRAs, hand-write or hand-edit.

5. **Trigger word collision.** If your trigger is a real English word, the model will activate the LoRA when ANYONE uses that word. Use deliberately rare or made-up tokens (e.g., "pop_hsstyle" not "popstyle").

6. **Overfitting vs underfitting.** Watch sample generations:
   - Underfitting: LoRA has no apparent effect even with trigger word. Train longer, increase rank, increase LR.
   - Overfitting: LoRA outputs look like dataset images. Train shorter, decrease rank, more caption dropout, more dataset diversity.

## When ai-toolkit is the right tool vs alternatives

- **Use ai-toolkit when:** you want LoRA training on Flux / Qwen / Z-Image / Wan / SDXL with sane defaults and active maintenance.
- **Use kohya_ss when:** you want SDXL / SD 1.5 LoRA training with the broadest community lore base. Better for older model families.
- **Use OneTrainer when:** you want a polished GUI with strong dataset prep features. Less cutting-edge model support.
- **Use diffusers' trainer scripts directly when:** you need custom modifications outside what ai-toolkit exposes.

## Caveat about this reference

This reference combines (a) the verified intro from the GitHub README and (b) my prior knowledge of ai-toolkit through mid-2025. The framework is actively maintained and the exact CLI syntax / config keys / supported models evolve. **Before training, verify against the CURRENT repo state**:
- Look at `config/examples/` for the most recent example configs per model
- Check `requirements.txt` for current torch / cuda compatibility
- Check the GitHub issues / discussions for known gotchas with your specific GPU + model combo

If Luis decides to train a POP house-style LoRA, the right next step is: (1) clone the repo into a separate folder (NOT inside ComfyUI-Easy-Install), (2) read the current README + a Flux-LoRA example config, (3) curate the dataset, (4) modify a copied example config, (5) test with a tiny dataset first to verify the pipeline works before doing a full training run.
