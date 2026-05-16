---
name: Runners catalog — what each `runners/*.py` script does, when to reach for it
description: Index of headless runner scripts that wrap canonical templates. Each entry covers problem, CLI signature, the template(s) it clones, quirks, and cost.
type: reference
---

`runners/` holds Tier-1 one-shot orchestration scripts. They:
1. Build an API-format workflow dict
2. (Optional) Save the graph-format counterpart for canvas drag-drop
3. POST to `/prompt` and exit on `prompt_id` — never poll (the watcher daemon handles output download)
4. (Optional) POST the saved graph to `/open_workflow` so it auto-displays on Luis's active ComfyUI canvas

When adding a new runner, add an entry here. Each entry should answer: what problem does it solve, what's the CLI, what templates does it clone, what quirks did the build surface, and what does each invocation cost.

---

## `runners/icon_cel_shaded.py` — Cel-shaded UI icon runner (NanoBanana2Direct)

**Problem solved:** generates UI icons for the studio matching Luis's house style for icons (verbatim style lock from `references/18_example_house_style.md` § 1, plus the canonical "Avoid …" line). Supports four output shapes (single icon, 2×4 contact sheet, 4×5 contact sheet, chonkify proportion sheet) and two reference modes (text-only vs style-anchor-matched), composable with N-parallel variations.

**CLI signature:**

```
python runners/icon_cel_shaded.py
    --subject "<icon concept>"          (required)
    [--mode {single,2x4,4x5,chonk}]    (default: single)
    [--reference <abs path>]            (optional → switches to Pattern A and uploads via /upload/image)
    [--variations N]                    (default: 1; N>1 fans out to N parallel calls; cost is N × ~$0.10)
    [--seed <int>]                      (random if omitted; with --variations N, becomes S, S+1, …, S+N-1)
    [--resolution {1K,2K}]              (default: 2K; --mode chonk forces 4K regardless)
    [--no-display]                      (skip auto-display via /open_workflow)
```

**Examples:**

| Use case | Command | Cost |
|---|---|---|
| Fresh single icon, no reference | `--subject "treasure chest"` | ~$0.10 |
| Match an existing set | `--subject "magic rune" --reference G:\path\anchor.png` | ~$0.10 |
| Comparison sheet — 4 versions, no reference | `--subject "scroll" --variations 4` | ~$0.40 |
| Comparison sheet — 4 versions matching anchor | `--subject "scroll" --reference anchor.png --variations 4` | ~$0.40 |
| Chonkify proportion variations | `--subject "shield" --mode chonk --reference shield.png` | ~$0.10 (4K) |
| 2×4 grid, no reference | `--subject "loot icons" --mode 2x4` | ~$0.10 |

**Modes vs patterns matrix:**

| Mode | Pattern C (no `--reference`) | Pattern A (with `--reference`) |
|---|---|---|
| `single` | Verbatim icon style lock + Avoid line | Adapted Pattern A canonical wording + style lock + Avoid line |
| `2x4` / `4x5` | Style lock + grid clause | Style lock + grid clause + "match reference's exact line weight, palette, cel-shading, outline" addendum |
| `chonk` | **Not allowed** (errors out — chonkify needs an `image1`) | Verbatim CHONKIFY MASTER PROMPT (no icon style lock injected — chonkify is self-contained); forces 4K + aspect "auto" |

**Templates cloned:**

- `workflows/nano_banana_templates/pattern_a_style_transfer_workflow.json` — for the LoadImage→NanoBanana2Direct→SaveImage shape (Pattern A single).
- `workflows/user_canonical_templates/generate multiple cel sahded images.json` — for the N-parallel fan-out shape. Important substitution: the canonical uses `GeminiNanoBanana2`; we substitute `NanoBanana2Direct` per ref 20 § "USER PREFERENCE".
- `workflows/user_canonical_templates/chonkify.json` — for the chonk mode. Same substitution as above (`GeminiNanoBanana2` → `NanoBanana2Direct`). The MASTER PROMPT widget value is included **verbatim** in the runner as `CHONKIFY_MASTER_PROMPT` — do not paraphrase if updating.

**Quirks discovered while building this:**

- `NanoBanana2Direct.thinking_level` enum is `["MINIMAL", "HIGH"]` only. Earlier docs claimed `LOW | MEDIUM | HIGH`; those values are rejected by `/prompt`. Confirmed against live `/object_info/NanoBanana2Direct` on 2026-05-09. Also written into ref 20 § "Discovered quirks".
- Default node settings (1K / MINIMAL / IMAGE) are *cheaper* than Luis's house defaults (2K / HIGH / IMAGE+TEXT). Runners must set the house values explicitly or quality drops silently.
- The `images` and `files` inputs are both **optional** — no `ImageBatch` node needed when there's only one reference image. Wire the LoadImage directly into `images`.
- For Pattern A with `--variations N`, **all N calls share** the same uploaded reference and the same shared `PrimitiveStringMultiline` prompt node. Editing the String node in the canvas changes all N at once on next queue.
- `--variations` > 1 with grid mode is unusual and is allowed but warns: each variation is its own grid (so `--variations 3 --mode 2x4` produces 3 separate 8-icon contact sheets, total 24 icons, cost ~$0.30).
- The chonkify MASTER PROMPT references both `image1` and `image2`, but the canonical `chonkify.json` only ever wires one image. The runner mirrors that — pass a single `--reference`. If the reference image is itself a multi-icon contact sheet, Gemini will anchor on whichever icon matches `--subject`.
- **Workflow filenames have a `_pattern{C|A}` suffix and, when `--variations N>1`, an `_xN` suffix** — so different patterns/scales don't clobber each other on disk: e.g., `icon_cel_shaded_treasure_chest_single_patternA_x4_workflow.json`.

**Output naming:** `ComfyUI/output/icons/<subject_slug>_<mode>_pattern{C|A}[_vNN]_NNNNN_.png`. `_v01..vNN` only when `--variations > 1`; otherwise no `_v` infix.

**Cost summary:** `N × $0.10` for 2K, slightly more for 4K (chonk mode). Single calls bill against `GEMINI_API_KEY` env var (or `GOOGLE_API_KEY`); the empty `api_key` widget triggers env-var fallback.

---

## `runners/wan_t2v.py` — Wan 2.1 14B text-to-video (kijai's WanVideoWrapper)

**Problem solved:** local text-to-video on the RTX 5090. No API cost, no provider dependency. Uses Wan 2.1 14B fp8_scaled — Comfy-Org's recommended quantized variant for 32 GB VRAM.

**CLI signature:**

```
python runners/wan_t2v.py "<prompt>"
    [--negative "..."]                  (default: Wan canonical anti-artifact list)
    [--prefix Wan/<YYYYMMDD>_wan_t2v]
    [--seed <int>]
    [--width 832] [--height 480]        (Wan 2.1 480p canonical)
    [--length 49]                       (num_frames; (4n+1) values: 17, 33, 49, 65, 81)
    [--steps 30]
    [--cfg 6.0]
    [--shift 5.0]
    [--fps 16]                          (Wan native 16 fps)
    [--block-swap 0]                    (reserved; not yet wired — see quirks)
    [--no-display]
```

**Examples:**

| Use case | Command | Wall-time (5090, fp8) |
|---|---|---|
| Quick 3s test | `"shiba running across meadow"` (defaults) | ~60-90s |
| Long-ish 5s clip | `--length 81` | ~120-180s |
| Higher-res 720p | `--width 1280 --height 720` | ~200-300s, possible OOM (see BlockSwap quirk below) |

**Pipeline (8 nodes, all from kijai's `ComfyUI-WanVideoWrapper` + `comfyui-videohelpersuite`):**

```
WanVideoModelLoader   ─→ WanVideoSampler ─→ WanVideoDecode ─→ VHS_VideoCombine
WanVideoVAELoader   ──┐    ▲       ▲           ▲
LoadWanVideoT5Text    │    │       │           │
   Encoder ─→ WanVideoTextEncode  │           (VAE input)
                                  │
                  WanVideoEmptyEmbeds (width/height/num_frames)
```

**Templates:** none — authored from scratch. `references/07_wan_video.md` was the structural reference. No Wan template exists in `workflows/comfy_org_canonical_templates/` or `user_canonical_templates/`. Once the runner is exercised more, consider extracting the saved graph format as a "user canonical template" and indexing it in ref 21.

**Verified config (live `/object_info` queries on 2026-05-09):**
- `WanVideoModelLoader`: `model = "wan2.1_t2v_14B_fp8_scaled.safetensors"`, `base_precision = "bf16"`, `quantization = "fp8_e4m3fn_scaled"` (matches the file's fp8_scaled nature), `load_device = "main_device"`.
- `WanVideoVAELoader`: `model_name = "wan_2.1_vae.safetensors"`, `precision = "bf16"`.
- `LoadWanVideoT5TextEncoder`: `model_name = "umt5_xxl_fp16.safetensors"`, `precision = "bf16"`, `quantization = "fp8_e4m3fn"`. (UMT5-XXL — Wan-specific, NOT regular T5; see ref 07. **The fp8_scaled variant is REJECTED — see quirks below.**)
- `WanVideoSampler`: `scheduler = "unipc"` (Wan canonical; 21 schedulers offered, but unipc is the default), `cfg = 6.0`, `shift = 5.0`, `riflex_freq_index = 0`, `force_offload = True`.
- `WanVideoDecode`: `enable_vae_tiling = True` with `tile_x/tile_y = 272`, `tile_stride_x = 144`, `tile_stride_y = 128` — keeps decode VRAM bounded for long clips.
- `VHS_VideoCombine`: `format = "video/h264-mp4"`, `frame_rate = 16` (Wan native).

**Output:** `ComfyUI/output/Wan/<prefix>_NN.mp4` (VHS auto-numbers).

**Cost:** $0 — fully local.

**Quirks discovered while building:**

- **`WanVideoTextEncoder` (the obvious-looking name) is NOT registered.** The actual UMT5 loader is `LoadWanVideoT5TextEncoder` — different naming convention from the rest of the wrapper's nodes. Confirmed via `/object_info`.
- **`LoadWanVideoT5TextEncoder` REJECTS `_scaled` fp8 encoder files at runtime.** First execution of the runner failed with `ValueError: Invalid T5 text encoder model, fp8 scaled is not supported by this node` raised at `custom_nodes\ComfyUI-WanVideoWrapper\nodes_model_loading.py:1992`. The pre-staged `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (already on disk) does **not** work with this wrapper. Fix: download `umt5_xxl_fp16.safetensors` (~11.4 GB from `Comfy-Org/Wan_2.1_ComfyUI_repackaged/split_files/text_encoders/`) and set `quantization = "fp8_e4m3fn"` on the loader for runtime VRAM savings. The runner's `UMT5_ENCODER` constant points at the fp16 file. Schema gotcha: `precision` enum only offers `fp32`/`bf16` (that's runtime precision, not file precision); `quantization` is a separate optional widget that handles the fp8 conversion at load time.
- **`quantization` enum on `WanVideoModelLoader` is the runtime quant, separate from the file's pre-quantization.** The `fp8_scaled` file pairs with `quantization = "fp8_e4m3fn_scaled"` — there's also `_fast` variants (faster but more aggressive), and `disabled` (load as bf16 — uses more VRAM). The naming "scaled" matches between file and quant option.
- **`force_offload = True` on `WanVideoSampler`** — wraps each step's VRAM usage so the 14B model can stay in VRAM only when actively sampling. Don't disable unless you know your VRAM headroom.
- **BlockSwap is NOT yet wired** in the scaffold. The CLI accepts `--block-swap N` but it's currently a no-op — wiring it requires a `WanVideoBlockSwap` args-builder node first, then the result piped into `WanVideoModelLoader.block_swap_args`. The fp8_scaled 14B fits a 32 GB 5090 cleanly for clips up to ~80 frames at 480p without offloading. If you push to 720p or 100+ frames, this needs to be turned on or you'll OOM.
- **Latent shape:** `WanVideoEmptyEmbeds` takes width/height/num_frames directly — no separate `EmptyLatentImage`-style node. Wan's text-to-video path produces the latent shape internally.
- **Frame count convention:** Wan likes `(4n+1)` values (17, 33, 49, 65, 81) because its temporal patch encoding is /4. Other counts work but may show seams.
- **Wan needs the canonical negative prompt.** The default in the runner is the Wan model card's recommended anti-artifact list (gray, JPEG, deformed, walking backwards, etc.). Don't strip it — the model is sensitive to negative guidance for motion and quality.

---

## `runners/flux2_t2i.py` — Flux 2 dev text-to-image (with auto-display upgrade)

**Problem solved:** quick local Flux 2 dev text-to-image — no API cost, full prompt freedom (no house style locks injected). For when Luis wants to test a prompt or generate non-Proof-of-Play content fast.

**CLI signature:**

```
python runners/flux2_t2i.py "<prompt>"
    [--prefix NAME]                     (filename prefix; default: <YYYYMMDD>_flux2_t2i)
    [--seed <int>]                      (random 32-bit if omitted)
    [--steps 20]                        (KSampler steps)
    [--guidance 4.0]                    (FluxGuidance value)
    [--width 1024] [--height 1024]
    [--no-display]                      (skip auto-display via /open_workflow)
```

**Example:** `python runners/flux2_t2i.py "a cozy medieval village at golden hour, painterly fantasy game illustration"`

**Templates / models:**

- Built from scratch (no template clone) — pattern matches `workflows/comfy_org_canonical_templates/flux2_t2i.json` if you want the canvas equivalent.
- Models (verified live via `/object_info/UNETLoader`):
  - `diffusion_models/flux2_dev_fp8mixed.safetensors`
  - `text_encoders/mistral_3_small_flux2_fp8.safetensors` (`type=flux2` — Mistral 3 Small encoder)
  - `vae/flux2-vae.safetensors`
- Sampling: KSampler euler/simple, 20 steps, `cfg=1`, `FluxGuidance=4.0`. ConditioningZeroOut on the negative branch.

**Quirks:**

- Flux 2 dev uses `EmptyFlux2LatentImage` (128-ch /16 spatial), NOT `EmptySD3LatentImage`. Mismatched latent shape is the most common Flux 2 build error.
- `flux2_dev_fp8mixed` requires the **Mistral 3 Small** encoder (`type=flux2`). Pairing it with Flux.1's CLIP-L+T5-XXL pipeline causes `mat1/mat2 shape` errors at `txt = self.txt_in(txt)`. See `references/16_flux2_encoder_pairing.md`.
- Distilled model — keep `cfg=1.0`. Higher cfg washes out output.
- After submission, the runner uses `_api_to_graph.py` to also produce a graph-format file with section-grouped colored layout (Loaders/Conditioning/Sampling/Decode), then POSTs that file to `/open_workflow` so the canvas auto-updates. Total saved files per run: `<prefix>_workflow-api.json` + `<prefix>_workflow.json` (11 nodes).

**Cost:** zero — fully local on the RTX 5090. Wall-time is typically 30-90s per 1024×1024 / 20-step run after the first (UNET cache).

---

## `ComfyUI/custom_nodes/comfy_load_workflow_endpoint/` — Canvas auto-display infrastructure

**Problem solved:** ComfyUI's REST API has no endpoint to "load this workflow into the active canvas" — the canvas state lives in the browser. This custom node bridges that gap so headless runners can surface their generated graphs without Luis having to drag-drop the saved `.json` file each time.

**Endpoint:**

```
POST /open_workflow
body: {"path": "<absolute path to a graph-format _workflow.json>"}
returns: 200 {ok, path, node_count}  on success
         400 if missing path / not absolute / not graph format
         404 if file doesn't exist
         500 if read/parse fails
```

The handler reads the file, validates it has a top-level `nodes` key (so accidentally pointing at a `_workflow-api.json` returns a clear error), and broadcasts via the existing ComfyUI WebSocket as a custom event named `open_workflow`.

**Frontend extension** (`web/open_workflow.js`): registers a Comfy app extension that listens for the `open_workflow` event on the api event emitter and calls `app.loadGraphData(workflow)` to swap the canvas. Logs `[load_workflow_endpoint]` lines in the browser dev console for both successful loads and failures.

**Setup:** drop the folder into `ComfyUI/custom_nodes/`, restart ComfyUI. Boot log shows `[comfy_load_workflow_endpoint] registered POST /open_workflow`.

**When to use it from a runner:** after `/prompt` accepts a workflow, POST the saved graph file's absolute path to `/open_workflow` with a 5-second timeout. Tolerate 404/405 (custom node not loaded) and connection errors silently — never let display failure break the run. See `runners/icon_cel_shaded.py:request_display()` for the canonical pattern.

**Quirks:**

- The endpoint is local-single-user. No auth. Don't expose ComfyUI to the internet without adding a layer on top.
- It accepts any absolute path, not just paths under `workflows/`. This was a deliberate policy choice for daily-use friction reduction; can be tightened to a directory whitelist by adding a check in `__init__.py` if multi-user.
- The frontend listener relies on `api.addEventListener` from `scripts/api.js`. If ComfyUI's frontend ever changes its WebSocket event dispatch, the listener will silently stop working — the custom node logs will still show "broadcast workflow" but the canvas won't update. Verify by checking the browser console for `[load_workflow_endpoint] loaded workflow`.
- Auto-display is **opt-out** by default for all runners I build for Luis (per memory `runners_auto_display.md`).

## `runners/character_cel_shaded.py` - Cel-shaded character runner (NanoBanana2Direct)

**Added 2026-05-09.** Mirrors `icon_cel_shaded.py` structure but assembles category-specific prompts for the three character types Luis works with.

CLI:
```
python3 runners/character_cel_shaded.py --category {hero,enemy,npc} --subject "<concept>" \
    [--mode {single,sheet}] [--reference <path>] [--seed N] \
    [--resolution {1K,2K}] [--variations N] [--no-display]
```

Categories pull verbatim style locks from:
- `--category hero` → ref 19 (Shiba protagonist, anthropomorphic)
- `--category enemy` → ref 22 (magical monsters, NOT anthropomorphic, single-gimmick design budget)
- `--category npc` → ref 24 (anthropomorphic frog/fox/snake roster, friendly)

Universal rules baked in: face LEFT, white background, 3-fingers+thumb hand rule,
cel-shaded 2-tone with thick black outlines, saturated shadows, NO 3D/photorealism/futuristic.

Default aspect ratio: `3:4` for `single`, `1:1` for `sheet` (2x2 multi-pose grid reads square).
Default resolution: `2K`. Default backend: `NanoBanana2Direct` (per ref 20 user preference).

Output prefix: `characters/<category>/<subject_slug>_<mode>_pattern<A|C>[_vNN]` -
lands under `ComfyUI/output/characters/<category>/`.

Same dual JSON emission (`_workflow.json` graph + `_workflow-api.json` API) and
canvas-display push via `/open_workflow` as the icon runner.

Patterns: A (with `--reference` style anchor) or C (text-only). Same N-parallel
variations fan-out. Cost: N x ~$0.10 per variation.

Compiles clean (`py_compile`). Submit-and-exit pattern. The watcher daemon picks
up outputs from `ComfyUI/output/characters/...`.

## `runners/biome_painterly.py` - V11 painterly biome runner (NanoBanana2Direct)

**Added 2026-05-09.** V11 biome framework (ref 23) implemented as a runner. Locks
in 3:4 portrait, gouache painterly with NO outlines, playfield-centered composition,
anthropomorphic-statue-only rule, mandatory final saturation line.

CLI:
```
python3 runners/biome_painterly.py --biome "<concept>" \
    [--mode {standard,chonk,description_only}] [--reference <path>] \
    [--seed N] [--resolution {1K,2K}] [--variations N] [--no-display]
```

Modes:
- `standard` - default V11 prompt assembly
- `chonk` - appends V11 chonk rules block (extreme massing on selective forms)
- `description_only` - includes the verbatim "This is a new image based on the
  written description below. Do not copy any exact layout from any reference."
  line; useful when supplying a reference for STYLE only, not layout

Pattern A (with `--reference`) opens with the verbatim PATTERN_A_OPENING line
("Using the uploaded reference images only as strict references, ...") and
includes the REFERENCE_ROLES_BLOCK (design blueprint vs style bible separation).
Pattern C is text-only.

Aspect ratio is hard-locked at `3:4` per V11 mandate. Default resolution: 2K.

Output prefix: `biomes/<biome_slug>_<mode>_pattern<A|C>[_vNN]` -
lands under `ComfyUI/output/biomes/`.

Every prompt ends with the mandatory line:
> Maintain vibrant color saturation throughout including shadows.

Same dual JSON emission, /open_workflow display push, and N-parallel-variations
fan-out as the icon and character runners.

Compiles clean. The runner suite now covers the three asset types:
- `runners/icon_cel_shaded.py` - icons (1:1, cel-shaded with outlines)
- `runners/character_cel_shaded.py` - characters (3:4, cel-shaded with outlines)
- `runners/biome_painterly.py` - biomes (3:4, painterly NO outlines, V11)

## `runners/enemy_variant.py` - V4 enemy variant runner (NanoBanana2Direct paired output)

**Added 2026-05-09.** Specialized for the V4 framework (ref 22) where every call
emits TWO prompts as a pair: SIMPLIFIED (production variant) and CHIBI-INFLUENCED
(slightly stylized but still hostile). This is V4's mandatory output format.

CLI:
```
python3 runners/enemy_variant.py --subject "<name>" --reference <path> \
    [--biome forest|swamp|volcanic|desert|crystal|shrine|abyssal|<custom>] \
    [--escalation {standard,elemental,elite,corrupted,boss}] \
    [--seed N] [--resolution {1K,2K}] [--variations N] [--no-display]
```

`--reference` is REQUIRED (V4 is variant-of-existing - never text-only). The
50%-faithful rule is baked into the OPENING_LINE_PATTERN_A: preserve core
identity + base anatomy + primary silhouette + weapon type, modify armor +
materials + magical features + danger accents + biome influence + colors.

Each `--variations N` gives N PAIRS (2N total NanoBanana2Direct calls). Workflow
shape: shared LoadImage + 2 shared PrimitiveStringMultiline (simplified prompt,
chibi prompt) fanning out to N pairs of (simplified Gemini+SaveImage, chibi
Gemini+SaveImage). Seeds increment so both prompts in a pair get independent
seeds (seed, seed+1, seed+2, seed+3, ...).

Biomes use the verbatim ref 22 mutation matrix (forest=bark/moss, swamp=algae/
fungal, volcanic=obsidian/magma, desert=sandstone/bone, crystal=growths/shards,
shrine=ritual collars, abyssal=void seams). Custom biome names get a generic
adaptation block.

Escalations:
- `standard` - stronger anchor, slight armor up
- `elemental` - element transformation (fire/ice/electric/gloom/holy/fungal/stone)
- `elite` - heavier mid-tier boss read
- `corrupted` - external hostile force has altered anatomy/silhouette/eyes
- `boss` - end-of-act intensity, larger silhouette, multiple danger accents

Output prefix: `enemies/<subject_slug>[_<biome>]_<escalation>_{simplified|chibi}_vNN`.
Lands under `ComfyUI/output/enemies/`.

Aspect ratio hard-locked at `3:4` (characters/enemies are taller). Compiles clean.

---

## `runners/enemy_biome_themed.py` — Local-only biome-themed enemy generator (Flux 2 Klein 9B image-edit)

**Added 2026-05-09.** Local alternative to `enemy_variant.py` for when API cost
must be zero. Same enemy framework rules (ref 22) but uses Flux 2 Klein 9B
image-edit pipeline instead of NanoBanana2Direct. Single call per run, single
reference image (style anchor), biome described in text via `--biome-name`.

**Why a separate runner from `enemy_variant.py`:** different backend (Flux 2
Klein vs Nano Banana), different I/O shape (single ref vs paired outputs). The
two coexist — pick by cost preference and whether you want SIMPLIFIED+CHIBI
paired output (use `enemy_variant.py`) or just one image (this).

**CLI signature:**

```
python runners/enemy_biome_themed.py
    --style-anchor <path-or-input-name>          required: existing character image
    [--subject "<concept hint>"]                  e.g. "shrine bell beast"
    [--biome-name forest|swamp|volcanic|desert|crystal]
    [--prefix NAME]
    [--seed <int>] [--steps 4] [--cfg 1.0]
    [--width 1024] [--height 1024]
    [--megapixels 1.0]                            ImageScaleToTotalPixels target
    [--no-display]
```

**Templates / models:**

- Mirrors `workflows/comfy_org_canonical_templates/image_flux2_klein_image_edit_9b_distilled.json`
  (the single-ref subgraph variant). 18 nodes, no LoRA.
- `diffusion_models/flux-2-klein-9b-fp8.safetensors` — Klein 9B distilled
- `text_encoders/qwen_3_8b_fp8mixed.safetensors` (CLIPLoader `type=flux2`,
  Klein 9B's encoder — NOT Mistral)
- `vae/flux2-vae.safetensors` — substitutes for the canonical
  `full_encoder_small_decoder.safetensors` which is NOT installed; the full
  Flux 2 VAE works fine in its place.

**Pipeline shape:**

```
LoadImage(anchor) -> ImageScaleToTotalPixels(lanczos, 1MP) -> VAEEncode -+
                                                                          |
CLIPTextEncode(positive) ----------+                                      |
                                   v                                      v
                          ReferenceLatent ---+               ReferenceLatent --+
                                              |                                  |
ConditioningZeroOut -> ReferenceLatent --+    +-> CFGGuider(model, pos, neg, 1) -|-> SamplerCustomAdvanced
                                                                                  |
EmptyFlux2LatentImage(W, H, 1) ---------------------------------------------------+
RandomNoise(seed) -> SamplerCustomAdvanced.noise
KSamplerSelect("euler") -> SamplerCustomAdvanced.sampler
Flux2Scheduler(steps, W, H) -> SamplerCustomAdvanced.sigmas
SamplerCustomAdvanced -> VAEDecode -> SaveImage("Enemies/<prefix>")
```

Notable: positive AND negative conditioning BOTH pass through their own
ReferenceLatent on the same encoded reference image — this is what makes the
output respect the reference's render style without copying its identity.

**Biome adaptation rules** (verbatim from ref 22, injected when
`--biome-name` is set):

| `--biome-name` | Injected materials/palette |
|---|---|
| `forest` | bark armor, moss growth, leaf mantles, seed/root magic, deep greens + warm browns |
| `swamp` | algae growth, fungal patches, lantern organs, toxic slime, murky teal + bile yellow |
| `volcanic` | obsidian armor, magma cracks, furnace hearts, ash cloth, charcoal + ember orange |
| `desert` | sandstone armor, bone relics, dried wraps, sun-baked shell, ochre + bleached bone |
| `crystal` | crystal growths, reflective shards, glowing crystal cores, prismatic energy, jewel tones |

Without `--biome-name`, the prompt has no biome clause and the model relies
entirely on `--subject` for thematic context.

**Quirks discovered while building:**

- **Qwen-Image-Edit 2509 was the original target — switched after debugging
  hell.** Tried 7 permutations of Qwen pipelines (fp8 + Lightning LoRA +
  CFGNorm canonical, bf16 variant, ConditioningZeroOut neg, Qwen-Rapid-AIO
  with sa_solver/beta/0.3-shift, both `EmptyLatentImage` and
  `EmptySD3LatentImage`). All produced all-zero PNGs with
  `RuntimeWarning: invalid value encountered in cast` from VAE decode. Root
  cause never isolated — could be a numerical instability specific to this
  install's version of one of the Qwen-stack nodes. Klein 9B image-edit
  worked first try once `resolution_steps=1` was added to
  `ImageScaleToTotalPixels`.
- **`ImageScaleToTotalPixels` requires `resolution_steps`** even though the
  schema marks it `advanced: true`. Omitting it triggers
  `required_input_missing` from `/prompt` validation. Default `1` works.
- **Klein 9B uses the Qwen3-8B text encoder, NOT Mistral.** Pairing wrong:
  `mat1/mat2 shape` errors at `txt = self.txt_in(txt)`. See ref 16.
- **Latent shape comes from `EmptyFlux2LatentImage(W, H, 1)`, NOT from
  VAEEncode.** The VAEEncoded image goes into `ReferenceLatent` only — to
  modulate conditioning, not to set the sampler's latent shape. Using
  `EmptySD3LatentImage` here would produce a 16-ch latent which Klein
  doesn't understand (Klein wants 128-ch /16-spatial).
- **`flux2-vae.safetensors` is fine in place of the canonical
  `full_encoder_small_decoder.safetensors`** (which isn't installed). The
  decoder is slower but produces equivalent quality.
- **Output silhouettes can lean "beastly" despite the negative rules** —
  `--subject` phrasing matters a lot. "Lantern parasite with fungal antlers"
  produced an antlered quadruped that reads close to a familiar animal
  silhouette. "Floating shrine bell with jagged maw" or "cursed candle
  with melted face" produces non-anthropomorphic object-creatures more
  reliably. When in doubt, lean object-creature.
- **Subject phrasing: noun = body shape.** Confirmed 2026-05-09. The
  noun in `--subject` becomes the silhouette regardless of the negative
  rules. `"lantern parasite"` → quadruped beast carrying a lantern.
  `"shrine bell creature"` or `"mossy stone slime"` → actual object-creature.
  Lead with a non-creature noun (slime, bell, candle, mask, mound, lantern)
  to avoid humanoid/quadruped silhouettes leaking from the style anchor.
- **Multi-character roster sheets work BETTER than single-character anchors.**
  Confirmed 2026-05-09. Initial runs used `npc_Nekomata_Cel_Shaded.png`
  (single bipedal humanoid) — outputs leaked the bipedal silhouette into
  every result regardless of subject. Switching to
  `base_character_ref.png` (a 3-character contact sheet of frog merchant
  + fox ranger + orange snake) gave the model a menu of silhouettes to
  pick from per subject, producing more varied and on-brief outputs. The
  bell-shaped subject got an actual bell-creature, the mask subject got
  a floating mask, the slime got a slime. **`base_character_ref.png` is
  now the runner default for `--style-anchor`.**
- **Prompt density tuning** ("too detailed" / "too simple" / middle).
  Confirmed 2026-05-09 through three iterations:
    * Original verbose prompt (30+ lines, mystical anchor + danger
      accent + biome materials + framework rules) → outputs were busy
      quadruped warriors with crystal spines, leaf armor, multiple
      textures. Too much detail.
    * Stripped-down prompt ("match the reference's exact simplicity",
      "2 to 4 large flat shapes only", "ONE defining feature only") →
      outputs collapsed to generic blobs that lost the gimmick (lantern
      subject got a lantern-less lump). Too simple.
    * Middle-density prompt ("match the reference's visual density --
      not simpler, not busier", "ONE clear defining feature: a lantern,
      a bell, a mask, a single horn, a glowing core...", drop the
      "no extra ornament" prohibition) → designs preserve the gimmick
      AND match the reference's level of restraint. Right balance.
  This is what's currently in `build_prompt()`. If outputs ever drift
  busy or sparse again, adjust THIS clause first.
- **Biome adaptation is palette-only by default**, NOT materials. The
  original prompt injected `"bark armor, moss growth, leaf mantles, seed
  and root magic"` for forest, which forced the model to add all those
  features as visible details. Reduced to palette only
  (`"deep greens, warm browns, soft moss tones"`); materials are
  implied by the style anchor's render approach.

**Output naming:** `ComfyUI/output/Enemies/<prefix>_NNNNN_.png`

**Cost:** $0 — fully local on the 5090. Wall-time ~30s per 1024×1024 / 4-step
run after the UNET is cached (first run ~90s).

The runner suite now covers all four asset categories:

| Asset | Runner | Aspect | Style | Pattern |
|---|---|---|---|---|
| Icons | `icon_cel_shaded.py` | 1:1/auto | cel-shaded outlines | A or C |
| Characters | `character_cel_shaded.py` | 3:4/1:1 | cel-shaded outlines | A or C |
| Biomes | `biome_painterly.py` | 3:4 (locked) | painterly NO outlines | A or C |
| Enemy variants (paid, paired) | `enemy_variant.py` | 3:4 (locked) | cel-shaded outlines | A required, paired output |
| Enemy variants (local, single) | `enemy_biome_themed.py` | 1:1 (default) | cel-shaded outlines | Klein 9B image-edit, single ref |

## `runners/qwen_edit_lightning.py` - Free local Qwen-Image-Edit-2509 4-step Lightning

**Added 2026-05-09.** The free alternative to NanoBanana2Direct for image-edit tasks.
$0 cost per call (fully local on the RTX 5090). Cloned directly from Comfy-Org's
canonical `image_qwen_image_edit_2509.json` template.

CLI:
```
python3 runners/qwen_edit_lightning.py --image <path> --prompt "<edit instruction>" \
    [--seed N] [--steps {4,8}] [--variations N] [--no-display]
```

Pipeline (14 nodes):
```
UNETLoader (qwen_image_edit_2509_fp8_e4m3fn.safetensors)
   -> LoraLoaderModelOnly (Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors)
   -> ModelSamplingAuraFlow (shift=3)
   -> CFGNorm (strength=1)
                                                                               +--> KSampler v01 -> VAEDecode -> SaveImage
LoadImage -> FluxKontextImageScale -> VAEEncode (init latent)                  |
                                  \-> TextEncodeQwenImageEditPlus (positive)   +--> KSampler v02 -> VAEDecode -> SaveImage
                                  \-> TextEncodeQwenImageEditPlus (negative)   |
CLIPLoader (qwen_2.5_vl_7b_fp8_scaled.safetensors, type=qwen_image)            +--> ...
VAELoader (qwen_image_vae.safetensors)
```

KSampler config: 4 steps, cfg=1.0, sampler=euler, scheduler=simple, denoise=1.0.
ModelSamplingAuraFlow shift=3 (matches the canonical Comfy-Org subgraph, NOT
the 0.3 I noted earlier in ref 11 - the canonical 2509 template uses 3).

Variations: N>1 shares ALL loaders + clip + vae + image conditioning, fans out
to N parallel (KSampler, VAEDecode, SaveImage) triplets with different seeds.
Cost stays $0 because nothing leaves the GPU.

Output prefix: `qwen_edits/<input_stem>__<prompt_slug>[_vNN]`.
Lands under `ComfyUI/output/qwen_edits/`.

**Setup gotcha: encoder location.** The runner expects `qwen_2.5_vl_7b_fp8_scaled.safetensors`
in `G:\models\text_encoders\`. Luis has it in `G:\models\clip\` (per ref 43).
First-run will reject with a clean node_errors response from /prompt and the
runner prints fix instructions to stderr — copy or symlink the file to
text_encoders\ to resolve.

Compiles clean. Only emits API-format JSON (no graph format / no /open_workflow
display push) to keep the file focused — Luis can still drag the saved
`*_workflow-api.json` into the canvas if he wants to inspect the graph.

The runner suite for image generation now covers:

| Backend | Cost | Speed | Quality | When to use |
|---|---|---|---|---|
| `icon_cel_shaded.py` (NB2Direct) | ~$0.10 | ~30s | best | Hard-to-render icons, contact sheets |
| `character_cel_shaded.py` (NB2Direct) | ~$0.10 | ~30s | best | Character portraits, multi-pose sheets |
| `biome_painterly.py` (NB2Direct) | ~$0.10 | ~30s | best | Painterly biomes |
| `enemy_variant.py` (NB2Direct paired) | ~$0.20 | ~60s | best | V4 enemy variants (Simplified + Chibi) |
| `qwen_edit_lightning.py` (local Qwen) | **$0** | ~5-10s | very good | Image edits, iterations, quick A/B |

## `runners/zimage_t2i.py` - Z-Image-Turbo text-to-image (free local) — REWRITTEN 2026-05-09

**Updated 2026-05-09.** Replaced the older positional-arg version with a clean
argparse-driven runner that mirrors the qwen_edit_lightning.py / character_cel_shaded.py
pattern. The previous version had a stale `control_after_generate` key inside
KSampler inputs (which is widget metadata, not a real input — could trip
validation). Fixed and modernized.

CLI:
```
python3 runners/zimage_t2i.py --prompt "<positive>" \
    [--width 1024] [--height 1024] [--seed N] [--steps 8] \
    [--variations N] [--no-display]
```

Pipeline (10 nodes for single, scales linearly with --variations):
- UNETLoader (z-image-turbo-fp8-e4m3fn.safetensors)
- ModelSamplingAuraFlow shift=3
- CLIPLoader (qwen_3_4b.safetensors, type=lumina2 — NOT flux2)
- VAELoader (ae.safetensors — Flux.1 / Z-Image shared VAE)
- CLIPTextEncode positive + CLIPTextEncode("") + ConditioningZeroOut for negative
- EmptySD3LatentImage 16-ch latent
- KSampler (steps=8 default, cfg=1.0, sampler=res_multistep, scheduler=simple, denoise=1.0)
- VAEDecode -> SaveImage

Variations: shared loaders + clip + vae + conditioning + latent fan out to N
parallel (KSampler, VAEDecode, SaveImage) triplets. Cost stays $0.

Output prefix: `zimage/<prompt_slug>[_vNN]`. Lands under `ComfyUI/output/zimage/`.

The free-local image generation set is now complete:

| Task | Runner | Cost | Speed |
|---|---|---|---|
| Text → image | `zimage_t2i.py` | **$0** | ~3-5s |
| Image edit | `qwen_edit_lightning.py` | **$0** | ~5-10s |
| Premium icons / characters / biomes | NB2Direct runners | ~$0.10 | ~30s |
| Premium enemy variants (paired) | `enemy_variant.py` | ~$0.20 | ~60s |
| Video generation | `wan_t2v.py` | $0 | 60-180s |

## `runners/zimage_controlnet.py` - Z-Image-Turbo ControlNet (free local)

**Added 2026-05-09.** Uses the Z-Image-Turbo-Fun-Controlnet-Union model patch
(in G:\models\model_patches\) to control Z-Image-Turbo output via canny / depth
/ pose. Cost: $0 per call. Pipeline cloned from Comfy-Org's "Canny / Depth /
Pose to Image (Z-Image-Turbo)" blueprint subgraphs.

CLI:
```
python3 runners/zimage_controlnet.py --mode {canny,depth,pose} \
    --image <control_image_path> --prompt "<what to generate>" \
    [--width 1024] [--height 1024] [--seed N] [--steps 9] \
    [--strength 1.0] [--low-threshold 0.3] [--high-threshold 0.4] \
    [--variations N] [--no-display]
```

Mode -> preprocessor mapping:
- `canny` -> built-in `Canny` node (low_threshold + high_threshold)
- `depth` -> `DepthAnythingV2Preprocessor` (comfyui_controlnet_aux)
- `pose` -> `DWPreprocessor` (DWPose, comfyui_controlnet_aux)

Pipeline (12-13 nodes):
- UNETLoader (z_image_turbo_bf16.safetensors) -> ModelSamplingAuraFlow(shift=3) -> [model]
- ModelPatchLoader (Z-Image-Turbo-Fun-Controlnet-Union.safetensors) -> [patch]
- LoadImage -> ImageScaleToTotalPixels(1MP, lanczos) -> [Canny | DepthAnythingV2Preprocessor | DWPreprocessor] -> [control image]
- QwenImageDiffsynthControlnet(model, model_patch, vae, image=control, strength) -> [patched_model]
  (despite the "Qwen" name, this routes to ZImageControlPatch when patch is Z-Image)
- CLIPLoader (qwen_3_4b, lumina2) -> CLIPTextEncode(prompt) [positive]
                                  -> CLIPTextEncode("") -> ConditioningZeroOut [negative]
- VAELoader (ae.safetensors)
- EmptySD3LatentImage(W, H, 1)
- KSampler (steps=9, cfg=1, sampler=res_multistep, scheduler=simple, denoise=1)
- VAEDecode -> SaveImage

Variations: shared loaders + clip + vae + control chain + latent fan out to N
parallel (KSampler, VAEDecode, SaveImage) triplets.

Output prefix: `zimage_cn/<mode>_<input_stem>__<prompt_slug>[_vNN]`. Lands under
`ComfyUI/output/zimage_cn/`.

First-run gotcha: depth/pose modes require auxiliary models (depth_anything_v2_vitb.pth
for depth; yolox_l.onnx + dw-ll_ucoco_384.onnx for pose). comfyui_controlnet_aux
auto-downloads these to G:\models\controlnet_aux_models\... on first use. The
runner prints clear stderr instructions if /prompt rejects on missing models.

The runner suite for free local generation now covers:

| Task | Runner | Cost | Speed |
|---|---|---|---|
| Text -> image (no control) | `zimage_t2i.py` | $0 | ~3-5s |
| Text -> image (controlled by canny/depth/pose) | `zimage_controlnet.py` | $0 | ~5-10s |
| Image edit (text + ref image) | `qwen_edit_lightning.py` | $0 | ~5-10s |
| Video (Wan 2.1 t2v) | `wan_t2v.py` | $0 | 60-180s |

## `runners/qwen_t2i_lightning.py` - Qwen-Image-2512 Lightning text-to-image (free local)

**Added 2026-05-09.** Premium-quality free-local text-to-image. Higher-fidelity
than zimage_t2i.py (~10-15s vs 3-5s, but better adherence + higher detail).
Cloned from Comfy-Org's `image_qwen_image_2512_with_2steps_lora.json` template.

CLI:
```
python3 runners/qwen_t2i_lightning.py --prompt "<positive>" \
    [--width 1328] [--height 1328] [--seed N] \
    [--speed {standard,fast}] [--variations N] [--no-display]
```

`--speed standard` (default): 4 steps, Qwen-Image-2512-Lightning-4steps-V1.0-bf16.safetensors
`--speed fast`: 2 steps, Wuli-Qwen-Image-2512-Turbo-LoRA-4steps-V1.0-bf16.safetensors

Pipeline:
- UNETLoader (qwen_image_2512_fp8_e4m3fn.safetensors)
- LoraLoaderModelOnly (Lightning, strength=1.0)
- ModelSamplingAuraFlow shift=3 (verified canonical)
- CLIPLoader (qwen_2.5_vl_7b_fp8_scaled, type=qwen_image)
- VAELoader (qwen_image_vae.safetensors)
- CLIPTextEncode positive + ConditioningZeroOut on negative (cfg=1)
- EmptySD3LatentImage(W, H, 1)
- KSampler (steps=4 or 2, cfg=1, sampler=euler, scheduler=simple)
- VAEDecode -> SaveImage

Canonical aspect-ratio dimensions (from the template's MarkdownNote):
- 1:1   1328x1328  (default)
- 16:9  1664x928
- 9:16  928x1664
- 4:3   1472x1104
- 3:4   1104x1472
- 3:2   1584x1056
- 2:3   1056x1584

Same encoder-location gotcha as qwen_edit_lightning.py: needs
qwen_2.5_vl_7b_fp8_scaled.safetensors in text_encoders\ (not clip\).

Output prefix: `qwen_t2i/<prompt_slug>[_vNN]`. Lands under `ComfyUI/output/qwen_t2i/`.

---

## Final runner suite summary (2026-05-09)

The shared runner directory now contains **9 runners** covering the full asset pipeline:

| Runner | Asset type | Backend | Cost | Speed |
|---|---|---|---|---|
| `icon_cel_shaded.py` | Cel-shaded icons (1:1, contact sheets) | NB2Direct | ~$0.10 | 30s |
| `character_cel_shaded.py` | Hero / enemy / NPC characters (3:4) | NB2Direct | ~$0.10 | 30s |
| `biome_painterly.py` | V11 painterly biomes (3:4 portrait) | NB2Direct | ~$0.10 | 30s |
| `enemy_variant.py` | V4 enemy variants (paired Simplified+Chibi) | NB2Direct | ~$0.20 | 60s |
| `qwen_edit_lightning.py` | Image edits (Qwen-Image-Edit 2509 4-step) | local Qwen | $0 | 5-10s |
| `qwen_t2i_lightning.py` | Premium T2I (Qwen-Image 2512 4-step Lightning) | local Qwen | $0 | 10-15s |
| `zimage_t2i.py` | Fast T2I (Z-Image-Turbo 8-NFE) | local Z-Image | $0 | 3-5s |
| `zimage_controlnet.py` | Controlled T2I (canny/depth/pose) | local Z-Image | $0 | 5-10s |
| `wan_t2v.py` | Text-to-video (Wan 2.1 14B) | local Wan | $0 | 60-180s |
| `flux2_t2i.py` | Flux 2 dev T2I | local Flux 2 | $0 | 20-30s |
| `multi_model_t2i.py` | Multi-backend test runner | local | $0 | varies |

Decision matrix:
- **Free fast iteration** -> `zimage_t2i.py`
- **Free quality T2I** -> `qwen_t2i_lightning.py`
- **Free image edit** -> `qwen_edit_lightning.py`
- **Free pose/canny/depth controlled gen** -> `zimage_controlnet.py`
- **Free video** -> `wan_t2v.py`
- **Premium icons / characters / biomes / enemies** -> NB2Direct runners
