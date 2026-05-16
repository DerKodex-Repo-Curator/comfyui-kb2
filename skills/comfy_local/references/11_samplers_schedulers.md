---
name: Sampler and scheduler choice guide
description: Which sampler/scheduler combinations work for which model families and step counts — practical defaults
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
ComfyUI's `comfy.samplers.SAMPLER_NAMES` provides ~25 samplers, plus several schedulers. Most workflows just need euler/dpmpp_2m with simple/normal/karras/beta. The model determines what's appropriate.

## Per model family — practical defaults

| Model | Sampler | Scheduler | Steps | cfg | Notes |
|---|---|---|---|---|---|
| **Flux 2 dev** | euler | simple | 20 | 1.0 (FluxGuidance 4) | Or `Flux2Scheduler` + `SamplerCustomAdvanced` for better quality at 14-16 steps |
| **Flux 2 Klein 4B/9B** | euler | simple | 12-16 | 1.0 | Klein converges fast |
| **Flux.1 dev** | euler / dpmpp_2m | simple / beta | 20-25 | 1.0 (FluxGuidance 3.5) | beta scheduler is often a touch better than simple |
| **Flux.1 schnell** | euler | simple | 4 | 1.0 | Distilled — strict 4 steps |
| **Flux.1 Kontext** | euler | simple | 20 | 1.0 (FluxGuidance 2.5) | Lower guidance for edits |
| **Flux.1 Fill** | euler | simple | 20-25 | 1.0 | Mask in conditioning |
| **Qwen-Image (full)** | euler | simple / beta | 20-30 | 4.0 | NOT distilled — uses real cfg |
| **Qwen-Image Lightning 4-step** | euler | simple | 4 | 1.0 | Step count matches filename |
| **Qwen-Image Lightning 8-step** | euler | simple | 8 | 1.0 | |
| **Qwen-Image Edit** | euler | simple | 20-25 | 4.0 | |
| **Z-Image turbo** | `res_multistep` or euler | simple | 8 (Purz's proven) or 4 | 1.0 | Distilled. Wire `ModelSamplingAuraFlow(shift=3)` between UNETLoader and KSampler. CLIPLoader type `lumina2`. |
| **Z-Image (non-turbo)** | euler / dpmpp_2m | beta | 16-20 | 4.0 | Same `ModelSamplingAuraFlow` + `lumina2` setup as turbo |
| **SDXL** | dpmpp_2m / dpmpp_2m_sde | karras / beta | 20-30 | 6-8 | dpmpp_2m_sde with karras is the legendary combo |
| **SDXL Lightning/Turbo** | euler_ancestral / lcm | sgm_uniform | 4-8 | 1.0-2.0 | |
| **SD 1.5** | dpmpp_2m / euler_ancestral | karras | 20-30 | 7 | |
| **Pony Diffusion XL** | dpmpp_2m_sde / euler_ancestral | karras | 25-30 | 7-8 | Quality scoring tags |
| **LCM** | lcm | sgm_uniform | 4-8 | 1.0-2.0 | |
| **HyperSD** | euler | sgm_uniform | 4-8 | 1.0 | |

## Sampler personalities (general intuition)

- **euler** — deterministic, fast, no surprises. Default for distilled models.
- **euler_ancestral (`euler_a`)** — adds noise each step → variation between seeds even with same params. Good for diversity.
- **dpmpp_2m** — quality go-to for non-distilled. Slightly slower than euler.
- **dpmpp_2m_sde** — stochastic version. Best detail on SDXL. Use with karras.
- **dpmpp_3m_sde** — 3rd-order stochastic. Top quality, expensive. Ada/Blackwell rewards this.
- **dpmpp_sde** — like dpmpp_2m_sde but 1st-order. Sometimes better on cartoon/anime.
- **lms** — older Linear Multistep. Mostly historical.
- **heun** — second-order Euler. Slow, sometimes cleaner edges.
- **lcm** — for LCM-distilled models only.
- **res_multistep** — multistep RES sampler. Used for Z-Image turbo (Purz's proven pipeline). Pairs with `ModelSamplingAuraFlow`.
- **euler_cfg_pp** / **euler_ancestral_cfg_pp** — Euler with classifier-free-guidance pre-projection (cfg++). Used in LTX-Video high-res passes (per Purz). Slightly better adherence at low cfg.
- **uni_pc / uni_pc_bh2** — unified predictor-corrector. Strong with high cfg.
- **deis** — deterministic. Less common.
- **ddim / ddpm / plms** — legacy SD samplers. Prefer dpmpp_2m or euler.

## Scheduler personalities

- **simple** — linear timestep schedule. Default, works everywhere, especially for distilled models.
- **normal** — DDPM normal. Slightly different sigma curve than simple.
- **karras** — Karras et al's curve, more steps spent at high noise. Great for non-distilled SDXL/SD1.5.
- **exponential** — exponential decay. Less common.
- **sgm_uniform** — uniform spacing in sigmas. Used for LCM/Lightning.
- **beta** — beta-distributed sigmas. Often a tiny win over simple on Flux/Qwen.
- **ddim_uniform** — uniform DDIM. Legacy SD.
- **kl_optimal** — KL-divergence-optimized. Newer, sometimes wins on Qwen.
- **align_your_steps** (and `_GITS`) — specific samplers' tuned schedules.

## Custom sampling (SamplerCustomAdvanced) when to use

Use when the model has a model-specific scheduler that gives better quality at fewer steps:
- **Flux 2 → Flux2Scheduler** (resolution-aware, 14-16 steps clean)
- **Wan video → WanVideoSampler from kijai's wrapper has its own scheduling**
- **Qwen-Image with custom sigmas → CustomSigmas (kjnodes) + KSamplerSelect → SamplerCustomAdvanced**

Workflow shape:
```
RandomNoise → noise
BasicGuider(model, conditioning) → guider
KSamplerSelect(sampler_name) → sampler
<Scheduler>(steps, ...) → sigmas
EmptyLatent → latent_image
```
All 5 feed into `SamplerCustomAdvanced` which outputs LATENT.

## Negative prompt: when does it matter?

It does NOT matter (and is internally zeroed or ignored) for:
- Flux 2 dev / Klein (distilled, cfg=1)
- Flux.1 schnell / Kontext / Krea / Fill (distilled, cfg=1)
- Qwen-Image Lightning variants (distilled)
- Z-Image turbo, hyperNF4, LCM, SDXL Turbo

It DOES matter for:
- Flux.1 dev (some control via cfg ≥ 1.5)
- Qwen-Image full (cfg ≥ 3)
- SDXL non-distilled (cfg 6-8)
- SD 1.5 (cfg 7)

For distilled models: wire negative as `ConditioningZeroOut` of the positive (collapsed in the canvas) — this saves one CLIPTextEncode call and makes intent clear.

## Typical workflow patterns

### Pattern A: Distilled model basic (cfg=1)
`KSampler(cfg=1, steps=4-20)` with positive cond + zeroed negative.

### Pattern B: Non-distilled model
`KSampler(cfg=6-8, steps=20-30)` with real positive + real negative.

### Pattern C: Custom sampling for distilled-with-quality
`SamplerCustomAdvanced` + `BasicGuider` + model-specific scheduler.

### Pattern D: Two-stage (base + refiner / hires)
- Stage 1: KSampler at low res with denoise=1
- Latent upscale (`LatentUpscaleBy` or model-based with `UltimateSDUpscale`)
- Stage 2: KSampler at hi res with denoise=0.4-0.6 (avoid drift)

---

## Canonical lists from source (verified 2026-05-09 from `comfy/samplers.py`)

### SAMPLER_NAMES — 43 total

```
KSAMPLER_NAMES (40):
  euler, euler_cfg_pp, euler_ancestral, euler_ancestral_cfg_pp,
  heun, heunpp2, exp_heun_2_x0, exp_heun_2_x0_sde,
  dpm_2, dpm_2_ancestral,
  lms, dpm_fast, dpm_adaptive,
  dpmpp_2s_ancestral, dpmpp_2s_ancestral_cfg_pp,
  dpmpp_sde, dpmpp_sde_gpu,
  dpmpp_2m, dpmpp_2m_cfg_pp, dpmpp_2m_sde, dpmpp_2m_sde_gpu,
  dpmpp_2m_sde_heun, dpmpp_2m_sde_heun_gpu,
  dpmpp_3m_sde, dpmpp_3m_sde_gpu,
  ddpm, lcm,
  ipndm, ipndm_v, deis,
  res_multistep, res_multistep_cfg_pp,
  res_multistep_ancestral, res_multistep_ancestral_cfg_pp,
  gradient_estimation, gradient_estimation_cfg_pp,
  er_sde, seeds_2, seeds_3,
  sa_solver, sa_solver_pece

Plus (3):
  ddim, uni_pc, uni_pc_bh2
```

### SCHEDULER_NAMES — 9 total

From `SCHEDULER_HANDLERS` dict in `comfy/samplers.py`:

```
simple, sgm_uniform, karras, exponential, ddim_uniform,
beta, normal, linear_quadratic, kl_optimal
```

**Note on naming inflation:** `linear_quadratic` is the newer addition (used by LTX-Video). `kl_optimal` is the KL-divergence-optimized scheduler that sometimes wins on Qwen. `align_your_steps` and its variants come from `comfy_extras/nodes_align_your_steps.py` — they're added separately as nodes that produce `SIGMAS` directly, NOT entries in SCHEDULER_NAMES. Use them via `SamplerCustomAdvanced` with the AYS-output sigmas.

### Newer samplers worth experimenting with on Luis's stack

These are newer and not yet in the practical-defaults table at the top — they exist in source but have little community-level guidance yet:

| Sampler | What's distinctive |
|---|---|
| `seeds_2` / `seeds_3` | SEEDS sampler (multi-step, adaptive). Newer than dpmpp_3m_sde, sometimes wins at high steps |
| `er_sde` | ER-SDE sampler. Stochastic, newer DPM++ variant |
| `sa_solver` / `sa_solver_pece` | Stochastic Adams solver. PECE = predictor-evaluator-corrector-evaluator |
| `gradient_estimation` / `_cfg_pp` | Gradient estimation sampler. Limited adoption; experimental |
| `exp_heun_2_x0` / `exp_heun_2_x0_sde` | Exponential Heun-2 with x0 prediction (vs eps prediction). Newer Heun variant |
| `dpmpp_2m_cfg_pp` | dpmpp_2m with classifier-free-guidance pre-projection. Lighter "cfg++" trick |
| `res_multistep_ancestral` / `_cfg_pp` | Ancestral / cfg-pp variants of res_multistep — alternatives for Z-Image turbo |

The `_cfg_pp` suffix everywhere means "CFG pre-projection" — typically wins +0.5 to +2 cfg of effective adherence at the same cfg setting. Try if base Euler/dpmpp adherence feels weak.

### Defaults inside SCHEDULERS

The 9 scheduler functions live in `comfy/samplers.py`. Notable internals:

- `simple` → linear sigma spacing through model timesteps
- `karras` → `k_diffusion_sampling.get_sigmas_karras` with `use_ms=False` (millisecond timing disabled)
- `exponential` → `k_diffusion_sampling.get_sigmas_exponential`
- `kl_optimal` → custom `kl_optimal_scheduler` (use_ms=False)
- `sgm_uniform` → `partial(normal_scheduler, sgm=True)` — uniform in sigma space
- `beta` → custom `beta_scheduler` — beta-distributed sigma curve
- `linear_quadratic` → `linear_quadratic_schedule` — linear early, quadratic late (LTX-Video pairing)

## Implication for runner authoring

When emitting workflow JSON with hardcoded sampler/scheduler names:
- The strings must match the canonical list above EXACTLY (no synonyms, no aliases).
- For Z-Image turbo's "Purz's proven" recipe: `sampler_name="res_multistep"`, `scheduler="simple"`, 8 steps, cfg=1.0, with ModelSamplingAuraFlow(shift=3) upstream of KSampler.
- For Lightning LoRAs (4-step Qwen, 8-step Qwen base): `sampler_name="euler"`, `scheduler="simple"`, steps match LoRA filename.
- For Flux.1/2 default: `sampler_name="euler"`, `scheduler="simple"` or `"beta"`, cfg=1.0, with FluxGuidance attached to positive conditioning.

---

## Correction — ModelSamplingAuraFlow shift values verified against canonical templates (2026-05-09)

The "Z-Image=3, Qwen-Edit=0.3, Lightning=3" memo I noted earlier was **partially wrong**. Verified against Comfy-Org's official `image_qwen_image_edit_2509.json` and `image_qwen_image_2512_with_2steps_lora.json` blueprint subgraphs:

| Model family | Canonical shift |
|---|---|
| Z-Image-Turbo (T2I + ControlNet) | **3** ✓ |
| Z-Image base | **3** |
| Qwen-Image-Edit-2509 (with or without Lightning LoRA) | **3** (NOT 0.3) |
| Qwen-Image-Edit-2511 | **3** (verified — ref 30 `image_qwen_image_edit_2511.json`) |
| Qwen-Image base 2512 + Lightning | **3** |
| Qwen-Image base 2512 + Wuli 2-step Lightning | **3** |

**The practical answer is: shift=3 for all Qwen / Z-Image variants.** I'd noted 0.3 for Qwen-Edit somewhere upstream — that figure does not appear in any canonical Comfy-Org template I can find. If it ever was correct, it isn't anymore.

This correction is reflected in:
- `runners/zimage_t2i.py` (always shift=3)
- `runners/zimage_controlnet.py` (always shift=3)
- `runners/qwen_edit_lightning.py` (shift=3, fixed from earlier 0.3 plan)

Other shift values that are NOT 3:
- ModelSamplingFlux (different node, different mechanism — uses `max_shift` / `base_shift` per resolution, NOT a scalar)
- AuraFlow proper (the original) — default 1.73
- SD3 (uses ModelSamplingSD3 directly) — varies
