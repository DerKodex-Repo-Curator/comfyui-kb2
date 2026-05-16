---
name: Custom node authoring deep-dive — KJNodes patterns + JS extensions + Registry
description: Follow-up to ref 46. Real patterns from kijai's KJNodes (18K Python LOC + 14 JS files). Multi-file Python organization, NODE_CONFIG dict registration, JS-only nodes (Set/Get is pure JS, no Python class), ComfyUI Registry pyproject.toml [tool.comfy] config, hidden inputs, IO.ANY universal type, dynamic INPUT_TYPES, model patching patterns.
type: reference
---

# Custom node authoring — deep dive

Reference 46 covered the API basics. This one digs into real patterns from **kijai's KJNodes** — the most-installed utility pack in the ComfyUI ecosystem. KJNodes is 18,361 lines of Python across 11 files plus 14 JavaScript files, totaling ~150 nodes. It's the canonical "how to build a polished node pack" reference.

**Sources:** `custom_nodes/comfyui-kjnodes/` (Luis's installed copy).

---

## 1. Multi-file Python organization (large pack pattern)

For packs with more than ~10 nodes, splitting into separate files by category is the convention. KJNodes structure:

```
comfyui-kjnodes/
├── __init__.py                  ← imports all + NODE_CONFIG dict + registration
├── pyproject.toml               ← [tool.comfy] Registry config
├── requirements.txt             ← extra Python deps
├── nodes/
│   ├── nodes.py                 (3,406 LOC — main grab-bag)
│   ├── mask_nodes.py            (1,689 LOC)
│   ├── model_optimization_nodes.py (2,312 LOC)
│   ├── image_nodes.py
│   ├── image_transform_node.py
│   ├── batchcrop_nodes.py
│   ├── audioscheduler_nodes.py
│   ├── curve_nodes.py
│   ├── intrinsic_lora_nodes.py
│   ├── lora_nodes.py
│   ├── ltxv_nodes.py
│   └── sharpen_nodes.py
├── utility/                     ← shared helper modules
├── web/
│   └── js/                      ← 14 JS frontend extensions
├── docs/
└── example_workflows/           ← published example workflows
```

The `__init__.py` pattern:

```python
# Import all categories — wildcard imports surface every class
from .nodes.nodes import *
from .nodes.mask_nodes import *
from .nodes.model_optimization_nodes import *
from .nodes.image_nodes import *
from .nodes.lora_nodes import *
# ... etc

# Then a single NODE_CONFIG dict registers EVERYTHING with display names
NODE_CONFIG = {
    "BOOLConstant": {"class": BOOLConstant, "name": "BOOL Constant"},
    "INTConstant": {"class": INTConstant, "name": "INT Constant"},
    "FloatConstant": {"class": FloatConstant, "name": "Float Constant"},
    "StringConstant": {"class": StringConstant, "name": "String Constant"},
    "ConditioningMultiCombine": {"class": ConditioningMultiCombine, "name": "Conditioning Multi Combine"},
    "DrawMaskOnImage": {"class": DrawMaskOnImage, "name": "Draw Mask On Image"},
    # ... ~150 entries total
}

# Then expand to the canonical NODE_CLASS_MAPPINGS / NODE_DISPLAY_NAME_MAPPINGS
NODE_CLASS_MAPPINGS = {k: v["class"] for k, v in NODE_CONFIG.items()}
NODE_DISPLAY_NAME_MAPPINGS = {k: v.get("name", k) for k, v in NODE_CONFIG.items()}
```

Why this pattern:
- The single `NODE_CONFIG` dict is the audit-friendly source of truth — easy to grep / count / reorganize
- Wildcard imports keep the registration boilerplate minimal
- Each `nodes/X.py` file can be huge without making `__init__.py` unreadable

---

## 2. JS-only nodes (Set/Get is pure JavaScript — no Python class!)

The most consequential KJNodes pattern: **`SetNode` and `GetNode` are implemented entirely in `web/js/setgetnodes.js`**. There is NO Python class for them. The custom node infrastructure on the frontend (LiteGraph) lets you register node types from JavaScript directly.

Why this matters: nodes that only manipulate the workflow graph itself (don't compute on tensors, don't hit `/prompt`) can live entirely in JS. The Python side is unaware they exist. Set/Get is the canonical example — it's a graph-cleanup tool that tags a wire with a name and lets you retrieve by name across the canvas.

The JS file structure:

```javascript
// web/js/setgetnodes.js
const { app } = window.comfyAPI.app;

// Node-type color map (mirrors data-type colors from ref 33)
const _typeColorMap = {
    "DEFAULT":      LGraphCanvas.node_colors.gray,
    "MODEL":        LGraphCanvas.node_colors.blue,
    "LATENT":       LGraphCanvas.node_colors.purple,
    "VAE":          LGraphCanvas.node_colors.red,
    "CONDITIONING": LGraphCanvas.node_colors.brown,
    "IMAGE":        LGraphCanvas.node_colors.pale_blue,
    "CLIP":         LGraphCanvas.node_colors.yellow,
    "FLOAT":        LGraphCanvas.node_colors.green,
    "MASK":         { color: "#1c5715", bgcolor: "#1f401b" },
    "INT":          { color: "#1b4669", bgcolor: "#29699c" },
    // ...
};

// Define nodes via LiteGraph
class SetNode extends LiteGraph.LGraphNode {
    constructor() {
        super();
        // wire up properties, addInput / addOutput, etc.
    }
}

LiteGraph.registerNodeType("SetNode", SetNode);
```

Key insight from the actual source: KJNodes' Set/Get is **subgraph-aware**. The JS code includes "lexical scoping" for subgraphs — a Set node in a parent graph is visible to all descendant subgraphs, while a Get node searches up the chain (own graph → parent → grandparent → root). This is non-trivial graph-traversal logic that runs entirely client-side.

**When to use a JS-only node:** the work is graph manipulation (cleanup, naming, organization) and doesn't need execution backend. Examples: Set/Get, Reroute, Note, AnyType helpers, group-management nodes.

**When you still need Python:** anything that has to run during sampling, hit a model, or produce real data.

---

## 3. The 14 JS extension files KJNodes ships

| File | Adds |
|---|---|
| `setgetnodes.js` | Set/Get nodes (graph-cleanup, hide wires by name) |
| `contextmenu.js` | Right-click menu additions (add-node-to-cursor, etc.) |
| `appearance.js` | Visual customization for nodes |
| `canvas_background.js` | Custom canvas background patterns/grids |
| `fast_preview.js` | Faster image preview rendering |
| `fillconnect.js` | Auto-connect helper for selected nodes |
| `help_popup.js` | In-app help popup |
| `image_transform.js` | Drag-on-image transform widget |
| `jsnodes.js` | Generic helpers shared by other JS files |
| `nodeswap.js` | Replace one node type with another, preserving connections |
| `performance.js` | Performance monitoring overlay (FPS, memory) |
| `play_sound.js` | Completion sound on `executed` event |
| `screencap_stream.js` | Stream screen capture as IMAGE input |
| `utility.js` | Shared JS utilities |
| `editors/` | (subdirectory — JSON / curve editors) |

This is way more than just "register some nodes" — kijai uses JS extensions to fundamentally change the canvas UX. The pattern: register listeners via `app.registerExtension({...})`, hook into LiteGraph events, modify the node prototype dynamically.

Boilerplate for a JS extension:

```javascript
// web/js/my_extension.js
import { app } from "/scripts/app.js";

app.registerExtension({
    name: "kjnodes.my_extension",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Modify node behavior before registration
        if (nodeData.name === "MyNodeName") {
            const original = nodeType.prototype.onExecuted;
            nodeType.prototype.onExecuted = function(message) {
                original?.apply(this, arguments);
                // Custom behavior
            };
        }
    },
    async setup(app) {
        // Run once at app boot
    },
});
```

To wire JS into your custom node, set `WEB_DIRECTORY = "./web"` in `__init__.py`. ComfyUI auto-loads any `.js` file under that path on startup.

---

## 4. ComfyUI Registry — the `pyproject.toml [tool.comfy]` block

For a custom node pack to be discoverable by ComfyUI Manager and the Comfy Registry, add this section to `pyproject.toml`:

```toml
[project]
name = "comfyui-kjnodes"
description = "Various quality of life -nodes for ComfyUI..."
version = "1.3.8"
license = {file = "LICENSE"}
dependencies = ["pillow>=10.3.0", "color-matcher", "matplotlib"]

[project.urls]
Repository = "https://github.com/kijai/ComfyUI-KJNodes"

[tool.comfy]
PublisherId = "kijai"
DisplayName = "ComfyUI-KJNodes"
Icon = "https://avatars.githubusercontent.com/u/40791699"
```

The `[tool.comfy]` section is what `comfyregistry.org` reads:
- **`PublisherId`** — your registered publisher name on the registry (one-time signup)
- **`DisplayName`** — what shows in ComfyUI Manager's install list
- **`Icon`** — URL to display thumbnail (avatar / logo)

For Luis: when he eventually publishes a custom node, he'll need to:
1. Sign up at `comfyregistry.org` and pick a `PublisherId`
2. Add this `[tool.comfy]` block to his pack's `pyproject.toml`
3. Run `comfy-cli publish` (the official CLI) to push a new version
4. ComfyUI Manager users can then install via the Manager UI

The `version` in `[project]` controls Registry's version tracking.

---

## 5. Patterns from real KJNodes Python classes

### Hidden inputs unlock workflow context (ref 37 covered briefly, here in real use)

`WidgetToString` is the canonical example — it accesses the workflow's metadata via hidden inputs to read another node's widget value:

```python
class WidgetToString:
    @classmethod
    def IS_CHANGED(cls, *, id, node_title, any_input, **kwargs):
        # Force re-execution if upstream changed
        if any_input is not None and (id != 0 or node_title != ""):
            return float("NaN")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "id": ("INT", {"default": 0, "min": 0, "max": 100000, "step": 1}),
                "widget_name": ("STRING", {"multiline": False}),
                "return_all": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "any_input": (IO.ANY, ),                         # Universal-accept input
                "node_title": ("STRING", {"multiline": False}),
                "allowed_float_decimals": ("INT", {"default": 2, "min": 0, "max": 10}),
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO",                # Full graph format JSON
                "prompt": "PROMPT",                              # Full API format dict
                "unique_id": "UNIQUE_ID",                        # This node's runtime ID
            },
        }
    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_widget_value"
    CATEGORY = "KJNodes/text"

    def get_widget_value(self, id, widget_name, return_all, any_input=None, node_title=None,
                         extra_pnginfo=None, prompt=None, unique_id=None,
                         allowed_float_decimals=2):
        # Walk extra_pnginfo / prompt to find the target node by id or title,
        # then pull its widget value, format as string, return.
        ...
```

What this teaches:
- **`IO.ANY`** as input type accepts ANY data type (workaround for "I don't know what this will be")
- **`extra_pnginfo`** and **`prompt`** in hidden inputs give the node access to the FULL graph context — it can introspect other nodes' widgets, IDs, connections, etc.
- **`IS_CHANGED`** returning `float("NaN")` forces re-execution every run (cache-busting)
- **`unique_id`** lets the node know its own runtime ID for self-reference

### Dynamic INPUT_TYPES (filtered combo lists)

`DiffusionModelSelector` shows runtime-computed dropdown options:

```python
class DiffusionModelSelector():
    @classmethod
    def INPUT_TYPES(s):
        # Compute the list dynamically — filter by substring
        ltx2_connector_models = folder_paths.get_filename_list("text_encoders")
        ltx2_connector_models = [m for m in ltx2_connector_models if "connector" in m.lower()]
        return {
            "required": {
                "model_name": (
                    folder_paths.get_filename_list("diffusion_models") + ltx2_connector_models,
                    {"tooltip": "..."}
                ),
            },
        }
```

INPUT_TYPES is a `@classmethod` called every time the frontend asks `/object_info`. So you can compute the dropdown options at request-time. Useful for filtered lists, conditionally-available models, or merged paths.

### Model patching pattern (PatchSageAttentionKJ)

When you want to mutate a MODEL in place (apply an attention swap, add hooks, etc.):

```python
class PathchSageAttentionKJ():
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "model": ("MODEL",),
            "sage_attention": (sageattn_modes, {"default": False, "tooltip": "..."}),
        }}
    RETURN_TYPES = ("MODEL",)
    FUNCTION = "patch"
    CATEGORY = "KJNodes/experimental"

    def patch(self, model, sage_attention):
        m = model.clone()                                # Always clone before mutating!
        # Apply patches — set model_options, swap attention, install hooks
        m.model_options["transformer_options"]["sage_attention_mode"] = sage_attention
        return (m,)
```

Pattern: take MODEL in, `model.clone()` to avoid affecting the original, mutate the clone's `model_options`, return the clone. This is the same pattern `ModelSamplingAuraFlow`, `LoraLoaderModelOnly`, hooks etc. follow.

### Wrapping core nodes to add knobs

`CheckpointLoaderKJ` extends the core CheckpointLoader with extra options:

```python
class CheckpointLoaderKJ():
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "ckpt_name": (folder_paths.get_filename_list("checkpoints"), {"tooltip": "..."}),
            "weight_dtype": (["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2", "fp16", "bf16", "fp32"],),
            "compute_dtype": (["default", "fp16", "bf16", "fp32"], {"default": "default", "tooltip": "..."}),
            "patch_cublaslinear": ("BOOLEAN", {"default": False, "tooltip": "..."}),
            "sage_attention": (sageattn_modes, {"default": False, "tooltip": "..."}),
        }}
    # ... loads checkpoint, applies dtype/compute knobs, optional sage attention patch
```

When core's node almost-but-not-quite does what you want, wrapping it with extra inputs is cleaner than forking — your wrapper calls the core implementation internally and exposes additional options.

---

## 6. Practical templates Luis can use

### Template A — "Add a knob to an existing node"

Copy `CheckpointLoaderKJ` pattern. Take the core node's INPUT_TYPES, add your extra inputs to required/optional, call the core implementation in `FUNCTION`, layer your extra logic on top of the result.

### Template B — "JS-only graph utility"

For nodes that don't compute (organization, naming, group-management), implement entirely in `web/js/your_extension.js`. Set `WEB_DIRECTORY = "./web"` in `__init__.py` and otherwise leave Python empty (just empty `NODE_CLASS_MAPPINGS` dict). Frontend auto-loads.

### Template C — "Workflow-context-aware node"

Use hidden inputs `prompt`, `extra_pnginfo`, `unique_id` to introspect the graph at execution time. Useful for nodes that need to know about other nodes (lookups, validation, dependency tracking).

### Template D — "Dynamic input dropdown"

Compute INPUT_TYPES dynamically based on filesystem state, environment, or other runtime info. The classmethod runs every `/object_info` call.

### Template E — "Model patcher"

`model.clone()` → mutate `model.model_options["transformer_options"]` or call `model.add_wrapper_with_key(...)` → return the clone. Standard pattern for any model-side modification (attention swaps, sampling shifts, hooks).

---

## 7. Publishing-readiness checklist

Before publishing a custom node pack to the Comfy Registry:

1. **`pyproject.toml` with `[tool.comfy]` section** — PublisherId, DisplayName, Icon
2. **`requirements.txt`** — extra Python dependencies, pinned where critical
3. **`README.md`** — install instructions, example workflows, screenshots
4. **`LICENSE`** — pick one (MIT / Apache 2.0 / GPL-3.0 are common)
5. **`example_workflows/`** — at least 1-2 workflow JSONs demonstrating each major node
6. **`__init__.py` exports** — `NODE_CLASS_MAPPINGS`, `NODE_DISPLAY_NAME_MAPPINGS`, `WEB_DIRECTORY` (if you have JS)
7. **Version-tag git releases** — Registry tracks versions via git tags + pyproject version
8. **Test on a clean ComfyUI install** — your pack shouldn't have missing deps surprises
9. **`comfyui-frontend-package` compatibility** — declare a frontend min version if your JS uses newer APIs

For the actual publish step, the official CLI is `comfy-cli` (separate `pip install comfy-cli`). Run `comfy node publish` in the pack directory once configured.

---

## 8. When Luis would actually want to write a custom node

Reach for a custom node only when:

1. **You need a new wire type** that doesn't exist yet (like `GEMINI_DIRECT_FILES` in nano_banana_direct, ref 35)
2. **You need to hit an external service inline** (paid API, HTTP, gRPC) during workflow execution
3. **You need a UI affordance not expressible** via existing node palette (custom widget, file browser, drag-drop, color picker → JS extension)
4. **You need to push events back to the frontend** during execution (status updates, hint refreshes)
5. **You want to package your runner-emitted workflows as a reusable node pack** that other ComfyUI users can install

For pure prompt assembly, scene expansion, dual JSON emission — runner scripts (refs 13, 36) are simpler. Custom nodes are for things that have to live INSIDE the graph execution.

---

## What to read next when actually writing a node

- **Reference 46** — the API basics (INPUT_TYPES, RETURN_TYPES, FUNCTION, CATEGORY, NODE_CLASS_MAPPINGS, both v3 and legacy APIs)
- **Reference 37** — exact behavior of canonical core nodes (KSampler, CLIPTextEncode, etc.) — copy patterns from these
- **Reference 35** — `GEMINI_DIRECT_FILES` custom socket type example (real-world non-trivial node)
- **This reference (56)** — KJNodes patterns + JS extensions + Registry config

The recommended reading order if Luis writes his first node tomorrow: 46 (API mechanics) → 37 (core node behavior to mirror) → 56 (real-pack patterns + Registry) → 35 (a known-working real-world example to clone). Then pick a Template (A-E above) matching the use case.
