---
name: APP Mode + Custom Node management + final docs synthesis
description: ComfyUI APP Mode (turn workflows into apps without scripts!) + Custom Node install/dependency/version-control workflows + final consolidated findings from web research round.
type: reference
---

**Source:** Web fetched 2026-05-09 from `docs.comfy.org/interface/app-mode`, `docs.comfy.org/development/core-concepts/custom-nodes`, `docs.comfy.org/development/core-concepts/models`, plus Lightning LoRA model cards and Qwen tutorial pages.

This consolidates the final batch of docs into actionable knowledge.

## APP Mode — turn workflows into apps without writing scripts

**This is huge for Luis's workflow distribution.** APP Mode lets you take any complex workflow and expose it as a simple form — pick inputs to expose, pick outputs to display, save, share via link. Recipients run it via a clean UI without ever seeing the node graph.

**Available from:** ComfyUI frontend version 1.41.13+ (Luis is on 1.42.14 ✓).

**How to enter APP mode:**
1. Click the top-left icon → dropdown → "Enter app mode", OR
2. Use the breadcrumb navigation dropdown at the top

**4-step builder:**

1. **Select Inputs** — click nodes on the canvas to expose them as user-controllable inputs. Image upload nodes, prompt text fields, model selectors, etc.
2. **Select Outputs** — choose which output nodes (Preview Image, Save Image, etc.) to display in the app
3. **Preview** — review the layout before committing
4. **Set default view** — choose whether the workflow opens in App mode or Node Graph mode by default

**Use:**
- Right panel = adjustable inputs
- Click Run to execute
- Cancel button appears during runs
- Mobile/narrow-screen layout: tab-based (inputs / outputs / Media Assets)
- Left sidebar: rebuild app, view assets, open workflow panel

**Save:** `Ctrl+S` / `Cmd+S` for local save. Workflows show in left sidebar saved-workflows panel.

**Share** (Comfy Cloud ONLY):
- Click Share in left sidebar → save workflow if unsaved → "Create a link" → copy
- Recipients open the link, run the workflow directly. **Full configuration is included.**

**For Luis specifically:**
- Take `runners/icon_cel_shaded.py` workflow (or any other) → convert to APP mode → expose `--subject` and `--mode` as inputs, SaveImage as output → save with name "POP Icon Generator"
- Now anyone on his team (or even Luis himself in a different context) can use the workflow with a clean UI, no Python invocation needed
- Significantly lowers the bar for non-technical collaborators
- **Local APP mode** works without Cloud — Cloud is only required for share links

**Trade-off vs runner scripts:**
- APP Mode: clean UI, no Python knowledge needed, but tied to ComfyUI
- Runner scripts: scriptable, batch-able, integrate with watchers, can hit /api directly without UI

**Recommendation:** for one-off recurring tasks (a specific icon generator, a biome generator), build APP Mode versions of the runner workflows. For batch jobs and the "Maciej runner+watcher" pattern, keep the Python scripts.

## Custom Node management — official guide

The official docs document the install/dependency/update/disable/uninstall workflow. Summary:

**Three install methods (recommended order):**

1. **ComfyUI Manager (recommended)** — Manager has joined Comfy Org as a core dependency. Maintained by [@Dr.Lt.Data](https://github.com/ltdrdata). Search → install → restart → done. Auto-installs dependencies.
2. **Git clone** — `cd custom_nodes`, `git clone <repo>`. Then manually install dependencies.
3. **Manual ZIP** — last resort. Loses git version history. Can't version-manage afterwards.

**Dependency install for Luis's portable setup:**

```powershell
cd G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install
.\python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\<package_name>\requirements.txt
```

**Important:** do NOT use system `pip install -r requirements.txt` — that installs into system Python, NOT the embedded Python ComfyUI uses. Use the embedded Python explicitly. (Luis already does this — confirmed in the install_optimizations.bat we wrote earlier.)

**Version control via git:**
```bash
cd custom_nodes/<package_name>
git tag                              # list available versions
git checkout <tag_or_commit_hash>    # switch
# then re-install dependencies if they changed
```

**Manager-based version control:**
- Open Manager → filter installed packages → switch version
- Manager handles dependency updates automatically
- Restart ComfyUI for changes to take effect

**Source:** `https://github.com/Comfy-Org/ComfyUI-Manager` (official Comfy-Org owned, blog post: "ComfyUI Manager joins Comfy Org").

**Developing your own custom node:** 
- Official guide at `https://docs.comfy.org/custom-nodes/walkthrough` (linked from "Start Developing Custom Nodes" in the docs)
- Custom node = Python file + (optional) JS file + `__init__.py` exporting `NODE_CLASS_MAPPINGS`
- Each node = Python class with `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, optional `CATEGORY`
- This matches Luis's stated project goal of "workflows + custom nodes"

## Lightning LoRA — official scheduler config (confirmed)

From the `lightx2v/Qwen-Image-Lightning` model card, the **Diffusers scheduler config** (used in distillation):

```python
scheduler_config = {
    "base_image_seq_len": 256,
    "base_shift": math.log(3),       # SHIFT=3 IN DISTILLATION
    "invert_sigmas": False,
    "max_image_seq_len": 8192,
    "max_shift": math.log(3),        # Same shift
    "num_train_timesteps": 1000,
    "shift": 1.0,
    "shift_terminal": None,
    "stochastic_sampling": False,
    "time_shift_type": "exponential",
    "use_beta_sigmas": False,
    "use_dynamic_shifting": True,
    "use_exponential_sigmas": False,
    "use_karras_sigmas": False,
}
```

**ComfyUI translation:** `ModelSamplingAuraFlow shift=3` is the correct ComfyUI equivalent.

**Diffusers usage example:**
```python
pipe.load_lora_weights(
    "lightx2v/Qwen-Image-Lightning",
    weight_name="Qwen-Image-Lightning-8steps-V1.0.safetensors"
)
# Then: 8 steps, true_cfg_scale=1.0, no other changes
```

**Confirmed downloads:** 474k last month for the LoRA — high adoption.

## Models concept page — extra_model_paths.yaml deep dive

Confirmed details:

**Multi-section format** (the `extra_model_paths.yaml.example` template):

```yaml
# config for a1111 ui
a111:
    base_path: path/to/stable-diffusion-webui/
    checkpoints: models/Stable-diffusion
    configs: models/Stable-diffusion
    vae: models/VAE
    loras: |
         models/Lora
         models/LyCORIS
    upscale_models: |
                  models/ESRGAN
                  models/RealESRGAN
                  models/SwinIR
    embeddings: embeddings
    hypernetworks: models/hypernetworks
    controlnet: models/ControlNet

# config for additional comfyui paths
comfyui:
    base_path: path/to/comfyui/
    is_default: true                  # default for downloads
    checkpoints: models/checkpoints/
    diffusion_models: |
                  models/diffusion_models
                  models/unet
    # ... etc
```

**Key facts:**
- Multiple sections under different `base_path` entries
- `is_default: true` — section gets used for downloads
- Pipe `|` for multi-path keys (joins multiple folders for one model type)
- Restart ComfyUI after editing
- `custom_nodes:` key adds extra custom node search paths
- Linux/Mac: `~/Library/Application Support/ComfyUI/extra_models_config.yaml` (Desktop)
- Windows: `C:\Users\<user>\AppData\Roaming\ComfyUI\extra_models_config.yaml` (Desktop)
- Portable: `ComfyUI/extra_model_paths.yaml` (root) — note SINGULAR "model_paths" (Portable) vs PLURAL "models_config" (Desktop)

**Common issues from the docs:**

> **GGUF support:** ComfyUI does NOT natively support GGUF. Need `ComfyUI-GGUF` custom node. (Luis already has this.)

> **Can't find my model:** Press `r` to refresh node definitions. For Desktop, check **Help → Open Folder → Open Model Folder** to verify path.

## Updated runner authoring rules (from final synthesis)

1. **For Lightning workflows:** always use `ModelSamplingAuraFlow shift=3` between UNETLoader and KSampler. Confirmed by lightx2v's official scheduler config. (Already documented; this is final confirmation.)

2. **For dependency installs in custom node troubleshooting:** the canonical command for Luis's portable install is:
   ```
   .\python_embeded\python.exe -m pip install -r ComfyUI\custom_nodes\<package>\requirements.txt
   ```
   Don't use `pip install` from system Python.

3. **For the next runner iteration — consider APP Mode wrappers:** every runner Luis uses regularly could have a companion APP Mode workflow saved under `ComfyUI/user/apps/` (or wherever Luis prefers). Same workflow JSON; APP mode adds a UI layer on top.

4. **For non-technical collaborators:** if Luis ever wants to share workflows with team members who aren't comfortable with ComfyUI's node graph, APP Mode is the path. Create app, save with descriptive name, share via Comfy Cloud link if cloud-deployed (or just send the JSON file for local use).

## Strategic implications for Luis's pipeline

**1. Two complementary distribution paths:**
- **Headless / batch / automated:** runner scripts + watcher daemon (the Maciej pattern we built)
- **Interactive / one-off / shareable:** APP Mode workflows

Both use the same underlying workflow JSONs. Just different "skins" on top.

**2. Custom node development is well-trodden:**
- Manager handles dependency installs, version control, missing-node detection
- Luis's stated goal of "build custom nodes" is supported by clear docs
- When the time comes, Custom Node Walkthrough in `https://docs.comfy.org/custom-nodes/walkthrough` is the entry point

**3. Lightning LoRA is the standard fast path:**
- Base Qwen → 8-step Lightning at cfg=1
- 2512 → 4-step Lightning at cfg=1
- Edit-2511 → 4-step Lightning at cfg=1 (separate LoRA, or fused FP8 single-file model)
- All use `ModelSamplingAuraFlow shift=3`
- All from `lightx2v/` HuggingFace org

**4. Multi-person consistency is real and shipping:**
- Qwen-Image-Edit-2511 has it baked in
- Roster work (multiple NPCs in one scene) becomes a single workflow input
- Fits Luis's frog/fox/snake roster style natively

**5. Layered decomposition is real and shipping:**
- Qwen-Image-Layered for biome parallax slicing, character-with-clothing separation, icon-element separation
- Recursive (any layer can be re-decomposed)
- Variable count (3, 4, 8+ as needed)
- Replaces manual Photoshop layer separation work

The shared knowledge base is now substantial enough that any new workflow Luis wants — characters, biomes, props, icons, edits, multi-angle, multi-person, layered, ControlNet'd, LoRA'd — has a documented canonical path.
