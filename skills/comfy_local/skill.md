---
name: comfy_local
description: Generate images, edit images, and (eventually) video via the local ComfyUI server at http://localhost:8188 on Luis's RTX 5090 Windows install. Use when the user wants to create, render, or generate using ComfyUI, diffusion models, LoRAs, ControlNets, or AI image generation workflows.
argument-hint: prompt or description of what to generate
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# ComfyUI Local Server Skill

You drive Luis's local ComfyUI server at `http://localhost:8188` to author workflows, submit jobs headlessly, and verify outputs. The full architecture is **Tier 1: runner script** (one-shot orchestrator) plus **Tier 2: watcher daemon** (persistent WebSocket subscriber that auto-downloads outputs).

## Before any workflow request — ALWAYS

1. **Read the relevant reference doc.** Reference docs are in `references/` and indexed below.
2. **Verify model files actually exist on disk.** Use `Glob` against `G:\models\<subfolder>\<filename>` OR query the live API: `curl http://localhost:8188/object_info/<LoaderName>`. Don't trust your memory — verify.
3. **Verify the encoder ↔ DiT pairing.** This is the #1 source of past errors. See `references/05_flux_family.md` and `references/16_flux2_encoder_pairing.md`.
4. **Run the verification checklist** before declaring a workflow done. See `references/15_verification_checklist.md`.

## Reference docs (in `references/`)

| File | Topic |
|---|---|
| `01_workstation.md` | Hardware, software stack, attention backend, what's enabled |
| `02_paths.md` | Filesystem layout, launcher, workflows folder, models folder |
| `03_user_role.md` | Luis's experience level and how to frame answers |
| `04_model_inventory.md` | High-level map of 2.4 TB of models in `G:\models\` |
| `05_flux_family.md` | Flux.1 (dev/schnell/Kontext/Krea/Fill/Redux) + Flux 2 (dev/Klein) — encoders, VAEs, GGUF/Nunchaku variants |
| `06_qwen_image_family.md` | Qwen-Image (orig/2509/2511/2512/Layered) + Edit + Lightning + Nunchaku SVDQ |
| `07_wan_video.md` | Wan 2.1 family (NOT installed yet). Custom node setup is ready, DiTs need download |
| `08_other_models.md` | Z-Image, ChronoEdit, Chroma, Ovis, LTX-Video + huge SDXL/SD1.5 catalog |
| `09_custom_nodes_catalog.md` | All 47 installed custom node packages, what each provides |
| `10_workflow_json_format.md` | Graph (UI) vs API formats; link consistency rules; widget value ordering |
| `11_samplers_schedulers.md` | Per-model defaults, sampler personalities, distilled vs non-distilled |
| `12_comfyui_api.md` | localhost:8188 REST API + WebSocket — endpoints, payloads, code patterns |
| `13_runner_watcher_architecture.md` | The two-tier autonomous setup; WS event types; folder layout |
| `14_workflow_authoring_pattern.md` | The "anchor → declare install state → query API → reference templates → validate" prompt pattern |
| `15_verification_checklist.md` | 10-section pre-delivery review |
| `16_flux2_encoder_pairing.md` | The Flux 2 dev/Klein encoder routing table — DO NOT mismatch |
| `17_workflow_compatibility.md` | The "always verify against the actual install" rule |
| `18_example_house_style.md` | **Luis's per-asset-type visual style rules — READ THIS BEFORE BUILDING ANY ASSET RUNNER** |
| `19_example_game_world.md` | Game setting, character roster, asset categories — anthropomorphic-only world, Shiba hero |
| `20_nano_banana_proven_workflows.md` | NanoBanana2Direct + GeminiNanoBanana2 + GeminiImage2Node schemas, N-parallel pattern, canonical templates |
| `21_user_canonical_workflows.md` | Catalog of Luis's saved workflows — clone these as templates instead of authoring from scratch |
| `22_enemy_monster_framework.md` | Enemy/monster variant generation rules (NOT anthropomorphic, magical horrors, faces LEFT) |
| `23_biome_creation_framework.md` | V11 biome rules — 3:4 portrait, gouache painterly, chonk rules, fix-locks |
| `24_roster_npc_framework.md` | NPC roster (frog/fox/snake style) — Animal/Hybrid/Creature variants, role-based expression, cuteness control |
| `25_canonical_style_anchors.md` | Reference image library in ComfyUI/input/ — proven style anchors per asset type |
| `26_custom_node_deep_dives.md` | Detailed schemas for production-critical custom nodes (Power Lora Loader, ModelSamplingAuraFlow, TextEncodeQwenImageEditPlus, ImageBatchMulti, etc.) |
| `27_comfy_org_canonical_templates.md` | 42 official Comfy-Org templates cloned to `workflows/comfy_org_canonical_templates/` — Flux 2/Klein, Qwen, ChronoEdit, multi-view 3D, Nano Banana, etc. Subgraph pattern explained. |
| `28_comfy_org_docs_and_official_resources.md` | docs.comfy.org structure, subgraph blueprints, Comfy-Org template repo authoring workflow, embedded model metadata, model card facts |
| `29_custom_node_ecosystem_expanded.md` | Deep dive on rgthree (Power Puter!), KJNodes (WidgetToString), WanVideoWrapper (20+ video models), Easy-Use (heavy integration), essentials (maintenance only) |
| `30_qwen_canonical_docs.md` | Official docs.comfy.org Qwen tutorials — base, 2512, Edit-2511 (multi-person!), Layered (RGBA decomposition!), 4 ControlNet paths, recommended settings |
| `31_comfyui_foundational_concepts.md` | Foundational facts: workflow=node graph, models folder layout, extra_model_paths.yaml multi-section format, Desktop vs Portable config paths, `r` key refresh, templates auto-download mechanism with embedded URLs, Partial Execution, Nodes 2.0, Lightning LoRA scheduler config, Qwen-Image-Layered pipeline args |
| `32_app_mode_and_workflow_distribution.md` | APP Mode (turn workflows into apps without scripts!) + Custom Node management (install/deps/version) + Lightning LoRA confirmed config + multi-section extra_model_paths.yaml |
| `33_comfyui_concepts_zimage_extras.md` | Node Modes (Never vs Bypass — KEY semantics), data type color coding, Mask Editor, in-app Node Docs, Z-Image complete family (Base/Turbo/Edit + Fun ControlNet) |
| `34_icon_prompt_templates.md` | **Verbatim icon prompt templates (single/2x4/4x5/ideas mode)** with the canonical avoid line. Source: BACKUP cel-shaded GPT compendium. Use when assembling icon prompts in any runner. |
| `35_workflow_group_convention.md` | Color-coded section groups (Loaders/Conditioning/Sampling/Decode) on every graph-format workflow |
| `36_runners_catalog.md` | **Index of `runners/*.py` scripts.** What each runner does, CLI signature, templates cloned, quirks, cost. Plus the `comfy_load_workflow_endpoint` custom node that powers canvas auto-display. Add an entry here whenever you build a new runner. |
| `37_core_node_source.md` | Truth (not paraphrase) of what KSampler, CLIPTextEncode, VAEDecode, SaveImage, ConditioningZeroOut, LoraLoader, EmptyLatentImage, EmptyFlux2LatentImage, ModelSamplingAuraFlow, FluxGuidance, UNETLoader, CLIPLoader, DualCLIPLoader actually do. Source: ComfyUI/nodes.py + comfy_extras |
| `38_impact_inspire_was_packs.md` | Headline nodes from comfyui-impact-pack (face detail, segmentation, region sampling), comfyui-inspire-pack (caching + LoRA block weight), was-node-suite (224 image utilities) — with reach-for-this-when guidance |
| `39_hooks_and_subgraphs.md` | Hooks = timestep-scheduled LoRAs / model patches. Subgraphs = reusable named subassemblies (38 official blueprints). Source: comfy_extras/nodes_hooks.py + app/subgraph_manager.py |
| `40_comfy_extras_survey.md` | Newer specialized core nodes — APG, CFG variants, attention multiply, EasyCache, AYS scheduler, custom sampler tree, differential diffusion, context windows, post-processing, Porter-Duff compositing |
| `41_execution_engine.md` | How `/prompt` becomes node executions. PromptExecutor, PromptQueue, CacheSet, validate_prompt, execute(). Caching, lazy inputs, async nodes, error propagation, full WS event timeline |
| `42_controlnet_aux_preprocessors.md` | comfyui_controlnet_aux preprocessor catalog (canny/depth/lineart/openpose-dwpose/normal/segmentation) paired with the canonical ControlNet model for each |
| `43_gguf_and_nunchaku_loaders.md` | ComfyUI-GGUF + ComfyUI-nunchaku loader signatures, supported model families, encoder pairings, full inventory of GGUF + SVDQ files on disk. The "use the quantized variant" path |
| `44_comfy_sample_and_sd_internals.md` | Algorithm-layer internals beneath KSampler/loaders. comfy/sample.py (noise + sample()) and comfy/sd.py (load_diffusion_model + load_clip + TEModel enum + LoRA application). Encoder/model auto-detection |
| `45_ai_toolkit_training.md` | **ostris/ai-toolkit LoRA training reference** — CLI + GUI flow, supported models, dataset format, full YAML schema, hardware fit for the 5090, and the POP house-style LoRA training plan (caption philosophy, trigger token rules, rank/steps starting points) |
| `46_custom_node_authoring.md` | How to write a ComfyUI custom node. Legacy class-attribute pattern (used by 99% of installed nodes) and the new io.ComfyNode pattern. Image tensor shape, custom socket types, REST routes, JS frontend extensions |
| `47_icon_runner_deep_read.md` | `icon_cel_shaded.py` runner — full code anatomy. Patterns and design choices in the 948-line icon runner. Reference template for runners that submit Nano Banana / image-gen jobs with optional reference upload, N-parallel variations, and dual JSON emission |
| `48_civitai_research.md` | **civitai.com reference** — site sections, REST API endpoints, AIR identifiers, Civitai Link ComfyUI integration, Buzz currency, on-site LoRA trainer vs ai-toolkit comparison, education hub topics, browsing patterns for finding style LoRAs |
| `49_civitai_lora_ecosystem_map.md` | **Curated LoRA findings from real API browse** — top picks per asset category (character sheets, anthropomorphic, biomes, isometric game assets, fantasy concept), Wan motion LoRAs, world-morph multi-base LoRAs, base-model culture differences, what civitai HAS vs DOESN'T for game art |
| `50_civitai_workflow_recipes.md` | **What top civitai community workflows actually use** — sampler/scheduler/cfg/steps distribution from 56 top-engagement workflow images, base-model dominance ranking (Z-Image-Turbo > Illustrious > Flux > others), recipe templates per model family, the LoRA stacking pattern at the top, civitai workflow culture observations. The API does NOT expose workflow JSON — only the recipe. |
| `51_civitai_deep_findings.md` | **Deep mining of pulled civitai data** — resolution canonicals (832×1216 dominates), creator portfolios worth following (Deformer_Toby, YeiYeiArt, Remade), multi-base + world-morph LoRAs (5-base in one file), trigger word naming patterns, prompt grammar conventions per base model, individual recipe study of top-12 workflows, Klein 9B + Z-Image community LoRAs surfacing in workflow hashes |
| `52_huggingface_research.md` | **huggingface.co reference** — site structure, key orgs publishing Luis's models (black-forest-labs / Comfy-Org / Kijai / city96 / lightx2v / Wan-Video / alibaba-pai / etc.), filter system, REST API + huggingface_hub Python library, Spaces try-before-download, how HF complements civitai (authoritative weights upstream of community remixes), watch-list pattern |
| `53_comfyui_official_repos.md` | **comfyanonymous/ComfyUI + Comfy-Org/workflow_templates** — three-repo split (Core/Desktop/Frontend), version 0.19.3 install state, recent commits already merged (RIFE/FILM, SUPIR, Capybara, ACE Step 1.5 XL, LongCat, ERNIE), full models list, complete 42-template inventory with NEW templates flagged, keyboard shortcuts, what to watch for new releases |
| `54_kijai_repos.md` | **kijai (Jukka Seppänen) repo catalog** — 106 repos total, 4 installed (WanVideoWrapper, KJNodes, WanAnimatePreprocess, SCAIL-Pose), notable others worth considering (Florence2 for LoRA captioning, FluxTrainer as ai-toolkit alternative, SAM2 for masking), relationship to Wan-Video team's HF releases, tracking pattern for staying current |
| `55_pixaroma_workflows.md` | **pixaroma-workflows** — small YouTube tutorial channel's workflow backups (6 episodes EP01-EP06 as of 2026-05-09). Distributed via Discord first + GitHub Releases backup. Tutorial-paced learning combo with the YouTube ComfyUI Free Course playlist |
| `56_custom_node_authoring_deep.md` | **Custom node authoring deep-dive** — KJNodes patterns (multi-file Python organization, NODE_CONFIG dict, ~150 nodes), JS-only nodes (Set/Get is pure JavaScript, no Python class!), 14 JS extension files KJNodes ships, ComfyUI Registry pyproject.toml [tool.comfy] config, hidden inputs, IO.ANY, dynamic INPUT_TYPES, model patching, 5 templates by use case, publishing-readiness checklist |
| `57_video_generation_landscape.md` | **Video generation umbrella** — full ComfyUI video model coverage (Wan / Hunyuan / Mochi / LTX / SVD / Cosmos / WanMove), what Luis has installed (Wan 2.1 t2v ONLY) vs what's a download away, frame interpolation (RIFE/FILM), VHS_VideoCombine output formats, SeedVR2 video upscaler, animation-LoRA workflow pattern (requires Wan i2v download), context-window long-video pattern, ranked gap-list of what to enable next |
| `58_fal_ai_research.md` | **fal.ai paid hosted compute** — three tiers (Model APIs, Serverless, Compute), Compute is the LoRA training path (H100 SXM single + 8x InfiniBand), honest comparison vs ai-toolkit local + civitai on-site trainer, when fal makes sense for Luis (concurrent runs, multi-GPU full fine-tunes), fal as fallback host for runner pipelines |
| `59_comfy_cloud_partner_apis.md` | **Comfy Cloud + Partner Nodes + Cloud API + Registry API + Utility tutorials** — managed offering 5-tier pricing (Blackwell RTX 6000 Pro 96GB), Partner Nodes (alternative to NanoBanana2Direct via credits), Cloud API ~30 endpoints, Registry API ~50 endpoints for publishing custom packs, video upscale empirical numbers (SeedVR2 5090 1080p = 312s) |

## Runtime architecture

### Tier 1: Runner scripts (one-shot)

Python scripts in `runners/` that orchestrate one user request. Pattern:

1. Load API key / config from `.env` (if needed)
2. (Optional) Upload reference images via POST `/upload/image`
3. (Optional) Expand a story prompt into N scene prompts
4. Build the API-format workflow dict (substituting prompt, filenames, LoRAs)
5. POST to `/prompt`, get back `prompt_id`
6. Print `prompt_id` and exit. Do NOT poll. The watcher downloads outputs.

`runner_template.py` in this folder is the boilerplate.

### Tier 2: Watcher daemon (persistent)

`watcher.py` is a long-running Python process that:

- Connects to `ws://localhost:8188/ws`
- Listens for `executed` events (which fire when SaveImage / SaveVideo nodes run)
- Auto-downloads outputs via `/view?filename=X&subfolder=Y&type=output` to `..\..\..\outputs_watched\`
- Dedupes via `state\downloaded.txt` (so re-running queued jobs doesn't re-download)
- Auto-reconnects with exponential backoff if the connection drops
- Logs to `state\watcher.log`
- Writes its PID to `state\watcher.pid`

Lifecycle: `start_watcher.bat` to launch (writes PID); `stop_watcher.bat` to terminate.

## Submitting a workflow (API format)

```python
import json, urllib.request

prompt = { ... }  # API format dict — flat dict keyed by string node ID

payload = json.dumps({"prompt": prompt}).encode("utf-8")
req = urllib.request.Request(
    "http://localhost:8188/prompt",
    data=payload,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
# result = {"prompt_id": "...", "number": N, "node_errors": {...}}
```

If `result["node_errors"]` is non-empty, the workflow was rejected. The dict tells you which nodes failed validation and why.

## Discovering live install state via API

Before authoring, query what ComfyUI sees:

```bash
# Available diffusion_models
curl -s http://localhost:8188/object_info/UNETLoader | python -c "
import json,sys; d=json.load(sys.stdin)
for m in d['UNETLoader']['input']['required']['unet_name'][0]: print(m)"

# Available loras (with subfolder paths)
curl -s http://localhost:8188/object_info/LoraLoader | python -c "
import json,sys; d=json.load(sys.stdin)
for l in d['LoraLoader']['input']['required']['lora_name'][0]: print(l)"
```

Same pattern for `CheckpointLoaderSimple`, `CLIPLoader`, `DualCLIPLoader`, `VAELoader`, `ControlNetLoader`, `LoraLoaderModelOnly`, `UpscaleModelLoader`, `LatentUpscaleModelLoader`, `StyleModelLoader`, `NunchakuFluxDiTLoader`, `UnetLoaderGGUF`.

This is more reliable than disk-walk because it reflects `extra_model_paths.yaml` resolution and custom node loader logic.

## Workflow output convention

For any new workflow, save BOTH formats in `workflows/`:

- `<name>_workflow.json` — graph format (drag-drop into ComfyUI UI)
- `<name>_workflow-api.json` — API format (headless `/prompt` submission)

Filename prefix in SaveImage nodes: `YYYYMMDD_descriptive-slug`. ComfyUI auto-appends `_00001_` etc.

## Common pitfalls (don't repeat past mistakes)

1. **Encoder ↔ DiT mismatch** → `mat1/mat2 shape` error at `txt = self.txt_in(txt)`. Flux 2 dev = Mistral encoder; Klein 4B = Qwen3-4B; Klein 9B = Qwen3-8B; Flux.1 = CLIP-L + T5-XXL.
2. **VAE mismatch** → wrong colors / garbled output. Each model family has its VAE.
3. **Latent shape wrong** → Flux 2 needs `EmptyFlux2LatentImage` (128-ch /16 spatial), NOT `EmptySD3LatentImage` (16-ch /8).
4. **Z-Image CLIPLoader type** → `lumina2`, NOT `flux2`. Wire `ModelSamplingAuraFlow(shift=3)` between UNETLoader and KSampler.
5. **Distilled model with cfg > 1** → washed-out / incoherent. Distilled = cfg=1.
6. **Lightning step count mismatch** → file says `4steps` → use 4 steps. `8steps` → 8.
7. **Large JSON write through Windows path may truncate** → if the saved file is missing trailing braces, rewrite via `python3 json.dump` in bash.
8. **Multi-fanout link missing in source `outputs.links`** → workflow loads but link is silently broken. The link ID must appear in BOTH the source's `outputs[i].links` array AND the target's `inputs[j].link` field.
9. **Wan workflows** → no Wan DiT installed yet. Don't propose Wan workflows without flagging the download requirement.

## When learning something new

Write a new `references/NN_<topic>.md` (or update an existing one). Update this skill.md's reference table. Both Claudes (Claude Code here, Cowork-mode Claude via mount) will read it.

## Reference repos

- **Comfy-Org workflow templates:** https://github.com/Comfy-Org/workflow_tem