---
name: ComfyUI official docs + Comfy-Org template authoring + key external resources
description: Findings from web research of docs.comfy.org, Comfy-Org/workflow_templates GitHub repo, and official model HuggingFace pages. Subgraph blueprint feature, template authoring workflow, model card facts.
type: reference
---

**Source:** Web fetched 2026-05-09 from `docs.comfy.org`, `github.com/Comfy-Org/workflow_templates`, official HF model cards.

## docs.comfy.org structure (what's actually there)

The docs site is built with Mintlify and has these sections relevant to Luis's work:

**Get Started:** Introduction, Install locally, Install Custom Nodes, First Generation
**Basic Concepts:** Workflow, Nodes, Custom Nodes, Properties, Links, Models, Dependencies
**Interface Guide:** Interface Overview, APP mode, Nodes 2.0, Mask Editor, Workflow Templates, **Subgraph**, Partial Execution, Node docs, Settings
**Tutorials:**
- Basic Examples
- ControlNet
- **Image** (this is the deep one):
  - Flux (subsection)
  - Qwen (Qwen-Image, Qwen-Image-2512, Qwen-Image-Edit, Qwen-Image-Edit-2511, Qwen-Image-Layered)
  - Z-Image, HiDream, Ovis, NewBie-image, ERNIE-Image, Cosmos-Predict2, OmniGen2
- 3D, Video, Audio, Utility, Partner Nodes
**Development:** Custom Nodes guide, Local API, Cloud API
**Registry/Cloud API Reference:** for programmatic access

**Key URL for AI agents:** `https://docs.comfy.org/llms.txt` — full documentation index designed for LLM consumption. (Note: the one I tried to fetch was 99K characters, exceeded my context limit. If you ever want me to read specific docs pages, paste the URLs directly.)

## Subgraph feature (canonical info from docs)

**Requires frontend version 1.24.3+.** Luis is on 1.42.14, so subgraphs work natively.

**What subgraphs are:**
- A "folder" for grouped nodes — package complex workflows into a single reusable subgraph node
- Use to: simplify complex workflows, reuse common node combinations, build modular components

**How to create:**
1. Select nodes you want to group
2. Click the subgraph icon in toolbar
3. ComfyUI auto-creates a subgraph based on inputs/outputs
4. Edit/customize via "Editing Subgraphs" mode

**Editing:**
- Double-click empty area inside subgraph (NOT on widgets) OR click subgraph edit button to enter edit mode
- Inside: navigation bar (exit), input slots (right-click to rename/delete), output slots
- Right-click connection points to manage exposed slots
- Default slot (labeled 1) is for adding new connections

**Parameters Panel** (v0.3.66+): edit subgraph widgets directly without entering. Right-click "Edit Subgraph Widgets" → reorder/visibility controls.

**Nested subgraphs:** can put subgraphs inside subgraphs. Navigation bar shows current level.

**Exit subgraph:** click navigation bar OR press Esc.

**Unpack subgraph to nodes:** right-click → "Unpack subgraph". Reverses the grouping.

### Subgraph Blueprint (v1.27.7+) — REUSABLE subgraphs

Lets you publish a subgraph to the node library so it appears in the node palette like a normal node.

**Publish:**
1. Select subgraph → click "book(publish)" icon in selection toolbox, OR
2. Open selection toolbox menu → "Add Subgraph to Library"
3. Name dialog appears → save

After publishing, the subgraph appears in the node library. Drag/search like any node. **Each instance is isolated** — instances added from blueprints can be edited independently without affecting other instances.

**Edit a published blueprint:** click the edit button → enables editing mode → make changes → save (Ctrl+S) to update the blueprint definition.

**Implications for runner authoring:**
- Subgraphs are pure UI organization. The execution engine flattens them at runtime.
- For headless API-format workflows (what runners build), subgraphs don't apply. Keep workflows flat.
- For graph-format JSONs we save alongside, optionally use subgraphs to match modern Comfy-Org templates' visual style — but this adds JSON complexity (the `definitions.subgraphs` array). Skip unless explicitly wanted.

## Comfy-Org/workflow_templates repo — how official templates are made

**Repo:** `https://github.com/Comfy-Org/workflow_templates` (388 stars, MIT licensed).

**Structure:**
- `templates/` — the actual workflow JSON files + thumbnails (.webp/.png)
- `blueprints/` — reusable subgraph blueprints
- `packages/core` — manifest + loader helpers (Python: `comfyui-workflow-templates-core`)
- `packages/media_*` — workflow templates split by media type (Python: `comfyui-workflow-templates-{api,image,video,other}`)
- `packages/blueprints` — subgraph blueprints package
- `packages/meta` — meta package
- `site/` — Astro static site at `templates.comfy.org`

**Each template needs:**
1. JSON workflow file (with embedded model metadata — see below)
2. Thumbnail file (webp/png/animated webp). Same name as JSON + counter suffix: `name-1.webp`, `name-2.webp`
3. Bundle assignment in `bundles.json`
4. Entry in `templates/index.json` with: `name`, `description`, `mediaType`, `mediaSubtype`, optional `tutorialUrl`, optional `thumbnailVariant`
5. Compressed assets (webp at 65% quality is recommended)

**Embedded model metadata in template JSONs:**

Loader nodes (UNETLoader, CLIPLoader, VAELoader, LoRA loaders) get a `models` property in their `properties` dict:

```json
"properties": {
  "Node name for S&R": "UNETLoader",
  "models": [
    {
      "name": "wan2.1_t2v_1.3B_bf16.safetensors",
      "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_t2v_1.3B_bf16.safetensors?download=true",
      "hash": "6f999b0d6cb9a72b3d98ac386ed96f57f8cecae13994a69232514ea4974ad5fd",
      "hash_type": "SHA256",
      "directory": "diffusion_models"
    }
  ]
}
```

This is **how ComfyUI auto-downloads missing models** when a user loads a template — the model is fetched from the embedded URL into the right folder.

**Embedded node version requirements** (optional):
```json
"properties": {
  "Node name for S&R": "SaveWEBM",
  "cnr_id": "comfy-core",
  "ver": "0.3.26"
}
```

This declares "this node requires ComfyUI v0.3.26+". Helps diagnose mismatches.

**Embedded MarkdownNote** with documentation links is encouraged.

**Translations:** templates support i18n via `scripts/sync_data.py --templates-dir templates` and `scripts/i18n.json`. 11 languages.

**Validation:** CI auto-validates JSON syntax, schema, bundle consistency, manifest sync, thumbnails. Run locally: `python scripts/sync_bundles.py`.

**For Luis:** if he ever wanted to contribute a template upstream (or just author internal ones in the same shape), the embedded `models` metadata is the killer feature. Local Claude Code could embed download URLs for any LoRA the workflow uses, so Luis (or future-Luis) could load the template fresh and ComfyUI would download the missing models automatically.

## Model card findings

### Flux 2 dev (Comfy-Org/flux2-dev)
- Quantized weights — original is `black-forest-labs/FLUX.2-dev`
- Two notable LoRAs in repo: `Flux2TurboComfyv2.safetensors` and `Flux_2-Turbo-LoRA_comfyui.safetensors` by ByteZSzn
- Downloads: ~973k last month — high adoption
- License: flux-1-dev-non-commercial-license

### Flux 2 Klein 9B (black-forest-labs/FLUX.2-klein-9b-fp8)
- 9B parameter rectified flow transformer
- **VRAM requirement: ~29 GB** — fits on Luis's 32GB 5090 ✓ (matches my earlier estimate)
- Min RTX 4090 or above
- Multi-reference editing capability
- Non-commercial license
- Klein 4B is Apache 2.0 licensed (open commercial); Klein 9B is non-commercial only
- BFL maintains aggressive safety filtering (CSAM/NCII inference filters baked in)
- Repo includes pixel-layer watermarking for content provenance

### Qwen-Image (Qwen/Qwen-Image)
- 20B parameter model, Apache 2.0 license
- Released Aug 4, 2025
- Designed for **complex text rendering** — particularly Chinese (logographic) AND English
- Generation defaults: **50 steps**, **true_cfg_scale=4.0**
- Native aspect ratios:
  ```
  1:1 → 1328×1328
  16:9 → 1664×928 / 9:16 → 928×1664
  4:3 → 1472×1140 / 3:4 → 1140×1472
  3:2 → 1584×1056 / 2:3 → 1056×1584
  ```
  **Note slight discrepancy with embedded Qwen template:** Qwen template MarkdownNote says 4:3=1472×1104 (not 1140) and 3:4=1104×1472 (not 1140). Both are valid — Qwen handles slight variation. Use the template's values when in doubt.
- Beyond image gen, Qwen-Image does: object detection, semantic segmentation, depth/edge estimation, novel view synthesis, super-resolution. All via the same model.
- Qwen team magic positive prompt suffix: `", Ultra HD, 4K, cinematic composition."` (English) or `", 超清，4K，电影级构图."` (Chinese)
- 485 adapter models, 64 finetunes, 19 quantizations on HuggingFace
- Top spaces: `Qwen/Qwen-Image-2512`, `Qwen-Image-Fast`, `InstantX/Qwen-Image-ControlNet`, `InstantX/Qwen-Image-ControlNet-Inpainting`, `Z-Image-LORA`

## Key external resources to remember

- **Comfy-Org example workflows hub:** `https://github.com/Comfy-Org/example_workflows` (referenced in Qwen Edit doc) — preview images live at `https://raw.githubusercontent.com/Comfy-Org/example_workflows/refs/heads/main/image/qwen/qwen-image-edit/`
- **Workflow extraction tool:** `https://comfyui-embedded-workflow-editor.vercel.app/` — drag a generated image/video to extract embedded workflow JSON
- **Templates site:** `https://templates.comfy.org/` — browseable, searchable, AI-generated descriptions, 11 languages
- **HuggingFace `Comfy-Org/Qwen-Image_ComfyUI`** — official Comfy-Org repackaged Qwen models for ComfyUI (split files for diffusion_models, text_encoders, vae)
- **HuggingFace `Comfy-Org/Wan_2.1_ComfyUI_repackaged`** — same for Wan 2.1
- **HuggingFace `Kijai/WanVideo_comfy`** and `Kijai/WanVideo_comfy_fp8_scaled` — kijai's curated Wan models (FP8 scaled is recommended)
