---
name: Custom node authoring patterns (legacy + v3 API)
description: How to write a ComfyUI custom node. Legacy class-attribute pattern (used by 99% of installed nodes) and the new io.ComfyNode pattern. Image tensor shape, custom socket types, REST routes, JS frontend extensions, common quirks.
type: reference
---

# Custom node authoring patterns

Luis's project goal includes building custom nodes. This reference covers the two API styles, the conventions every node must follow, and patterns from real installed nodes worth copying.

**Sources read:**
- `ComfyUI/custom_nodes/example_node.py.example` (official ComfyUI v3 API example, 130 lines)
- `ComfyUI/custom_nodes/comfy_load_workflow_endpoint/__init__.py` (endpoint-only node, 73 lines)
- `ComfyUI/custom_nodes/nano_banana_direct_pkg/nano_banana_direct.py` (real legacy-style node Luis uses, 608 lines)

## The two API styles

There are two coexisting custom node APIs in ComfyUI right now:

### Legacy API (class attributes) — used by 99% of installed nodes

```python
class MyNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": { ... },
            "optional": { ... },
            "hidden":   { ... },   # uncommonly used
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "summary")   # optional, defaults to lowercased types
    FUNCTION = "execute"                   # name of the method to call
    CATEGORY = "Mygroup/Subgroup"          # menu placement
    OUTPUT_NODE = False                    # True = node has side effects, runs even with no consumers

    def execute(self, **kwargs):
        return (image_tensor, "summary text")
```

Then at module level:

```python
NODE_CLASS_MAPPINGS = {
    "MyNode": MyNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MyNode": "My Node (display name)",
}
```

This is what you'll see in `nano_banana_direct.py`, KJNodes, rgthree, comfyui_essentials — basically every installed package.

### New v3 API (io.ComfyNode) — official as of late 2025

```python
from comfy_api.latest import ComfyExtension, io

class MyNode(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="MyNode",
            display_name="My Node",
            category="Mygroup/Subgroup",
            inputs=[
                io.Image.Input("image"),
                io.Int.Input("count", min=1, max=64, default=1),
                io.String.Input("text", multiline=True, default=""),
                io.Combo.Input("mode", options=["a", "b", "c"]),
            ],
            outputs=[io.Image.Output()],
        )

    @classmethod
    def execute(cls, image, count, text, mode) -> io.NodeOutput:
        return io.NodeOutput(image)

class MyExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [MyNode]

async def comfy_entrypoint() -> MyExtension:
    return MyExtension()
```

Strengths: typed schema, lazy inputs declared inline, no string magic, explicit extension class. Weaknesses: most reference material online still uses legacy; tutorials lag behind.

**Recommendation for Luis:** when authoring NEW nodes, prefer the v3 API — it's cleaner and the typed schema catches mistakes. When reading or modifying existing custom nodes, expect legacy.

## INPUT_TYPES schema (legacy)

The dict has up to three sections:

| Section | Meaning |
|---|---|
| `required` | Inputs the user MUST supply. Workflow fails to validate if missing. |
| `optional` | Inputs that can be left disconnected. Receive `None` if so. |
| `hidden` | Inputs supplied by ComfyUI itself, not the user. Common: `"unique_id": "UNIQUE_ID"`, `"prompt": "PROMPT"`, `"extra_pnginfo": "EXTRA_PNGINFO"`. |

Each entry is `(type_or_options, options_dict)`:

```python
"prompt": ("STRING", {"multiline": True, "default": "", "tooltip": "..."}),
"seed": ("INT", {"default": 0, "min": 0, "max": 2**31 - 1, "control_after_generate": True}),
"strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
"mode": (["one", "two", "three"], {"default": "one"}),  # COMBO — pass a list directly
"image": ("IMAGE",),  # connectable socket, no widget
```

### Common widget options

| Option | Type | Purpose |
|---|---|---|
| `default` | any | Initial value |
| `min` / `max` | number | Numeric clamping |
| `step` | number | Slider/spinner increment |
| `round` | number/False | Round numeric to N decimals; `False` disables |
| `multiline` | bool | STRING textarea instead of single-line |
| `tooltip` | str | Hover help in UI |
| `control_after_generate` | bool | INT only — adds the magic "fixed/increment/decrement/randomize" dropdown next to seed widgets |
| `forceInput` | bool | Hide the widget, force the input to be wired only |
| `dynamicPrompts` | bool | STRING — enable wildcards like `{a\|b\|c}` |
| `lazy` | bool | Don't evaluate this input until `check_lazy_status()` requests it (v3 API style) |

## Built-in type names

These are the wire types ComfyUI knows about. Match them across nodes to allow connections.

`STRING`, `INT`, `FLOAT`, `BOOLEAN`, `IMAGE`, `MASK`, `LATENT`, `MODEL`, `CLIP`, `VAE`, `CONDITIONING`, `CONTROL_NET`, `STYLE_MODEL`, `CLIP_VISION`, `CLIP_VISION_OUTPUT`, `UPSCALE_MODEL`, `SAMPLER`, `SIGMAS`, `GLIGEN`, `AUDIO`, `VIDEO`, `NOISE`, `GUIDER`.

For lists (combos), pass a Python list as the type field directly:

```python
"sampler_name": (comfy.samplers.KSampler.SAMPLERS, ),
"scheduler": (comfy.samplers.KSampler.SCHEDULERS, ),
```

## Custom socket types (extending the type system)

You can invent new socket types just by using a string. Example from `nano_banana_direct.py`:

```python
RETURN_TYPES = ("GEMINI_DIRECT_FILES",)
```

…and another node:

```python
"files": ("GEMINI_DIRECT_FILES",),
```

Now those two nodes can be wired together. The string is opaque — ComfyUI doesn't validate the runtime payload. Whatever Python object the upstream node returns is passed verbatim. Convention: `UPPER_SNAKE_CASE`.

## Image tensor convention (CRITICAL)

ComfyUI images are PyTorch tensors with a specific shape that breaks if you forget:

- Shape: `[B, H, W, C]` — batch, height, width, channels
- Dtype: `float32`
- Range: `0.0` to `1.0` (NOT 0-255)
- Channel order: `RGB` (3 channels) or `RGBA` (4 channels for masks/transparency)
- Single-image case: `[1, H, W, C]`. Don't squeeze the batch dim — downstream nodes expect it.

PIL conversion helpers (lifted from `nano_banana_direct.py`):

```python
def _tensor_to_pil(image_tensor: torch.Tensor) -> Image.Image:
    if image_tensor.ndim == 4:
        image_tensor = image_tensor[0]
    arr = image_tensor.detach().cpu().numpy()
    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(arr[:, :, :3], "RGB")

def _pil_to_tensor(pil_image) -> torch.Tensor:
    rgb = pil_image.convert("RGB")
    arr = np.array(rgb).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None, ...]   # add batch dim
```

For masks, shape is `[B, H, W]` (no channel dim), `float32`, 0..1 where 1 = white = unmasked area.

## Returning multiple images / batched output

`torch.cat([tensor1, tensor2, ...], dim=0)` along the batch axis. Downstream `SaveImage` will save them separately. ComfyUI also accepts a list of tensors in some places, but the canonical form is one batched tensor.

## Returning a `dict` instead of a tuple — the `ui` channel

The cleanest pattern for a node that wants to BOTH return downstream wiring data AND show something in the canvas (text, preview image, status) is:

```python
return {
    "ui": {"text": [summary_string]},          # rendered as text below the node
    "result": (image_tensor, summary_string),  # actual return values matching RETURN_TYPES
}
```

Other `ui` keys: `images` (list of `{"filename": ..., "subfolder": ..., "type": "temp"}` dicts to render preview thumbnails). This is how `PreviewImage` and Cost-tracking nodes display info inline.

## OUTPUT_NODE = True

Set when the node has side effects and should run even if nothing reads its outputs. `SaveImage`, `PreviewImage`, the watcher endpoint, anything that writes a file or pings an external service.

## Custom REST endpoints (no UI node, just a route)

`comfy_load_workflow_endpoint` is the canonical example: zero UI nodes, just a REST POST handler. Pattern:

```python
from aiohttp import web
from server import PromptServer

NODE_CLASS_MAPPINGS = {}        # required to be defined, even if empty
NODE_DISPLAY_NAME_MAPPINGS = {}

@PromptServer.instance.routes.post("/my_endpoint")
async def my_handler(request: web.Request) -> web.Response:
    data = await request.json()
    # ...do stuff...
    return web.json_response({"ok": True})
```

The route is automatically registered when the package's `__init__.py` is imported. Common verbs: `routes.get`, `routes.post`, `routes.put`, `routes.delete`. The handler is `async`.

To push events to all connected frontend clients over the WebSocket:

```python
PromptServer.instance.send_sync("event_name", {"key": "value"})
```

The frontend JS extension subscribes via `api.addEventListener("event_name", handler)`.

## JS frontend extensions

Set `WEB_DIRECTORY = "./web"` in `__init__.py` and put `.js` files in that subdirectory. ComfyUI auto-loads them and exposes them via the `app` object (`window.app` / `app.registerExtension({...})`).

Used for: custom node UIs, modal dialogs, listening for backend events, swapping the canvas (as in `comfy_load_workflow_endpoint/web/open_workflow.js`).

## Reading ComfyUI's filesystem locations

```python
import folder_paths

folder_paths.get_input_directory()     # ComfyUI/input/
folder_paths.get_output_directory()    # ComfyUI/output/
folder_paths.get_temp_directory()      # ComfyUI/temp/
folder_paths.get_filename_list("checkpoints")     # all checkpoint files (resolved against extra_model_paths.yaml)
folder_paths.get_filename_list("loras")
folder_paths.get_filename_list("vae")
folder_paths.get_filename_list("diffusion_models")
folder_paths.get_filename_list("text_encoders")
folder_paths.get_filename_list("controlnet")
folder_paths.get_full_path("checkpoints", "sd_xl_base_1.0.safetensors")  # absolute path resolution
```

Use `folder_paths.get_filename_list()` to populate combo widgets — that way the dropdown reflects whatever the user has installed, including extra_model_paths.yaml-mounted folders.

## Lazy inputs (v3 API)

```python
io.Int.Input("int_field", lazy=True),

@classmethod
def check_lazy_status(cls, image, int_field, ...):
    # return list of input names that need to be evaluated NOW
    if image is None:
        return ["image"]   # don't bother evaluating int_field until image is ready
    return []
```

ComfyUI calls `check_lazy_status()` first; only the requested inputs get computed before `execute()`. Useful for branching execution paths.

## fingerprint_inputs (re-execution control)

By default, a node re-runs only when one of its inputs changes. To force re-runs even on stable inputs (for, e.g., a LoadImage that should re-read disk if the file changed):

```python
@classmethod
def fingerprint_inputs(cls, *args, **kwargs):
    return some_string_or_number   # if different from last call, re-execute
```

Used heavily in core's LoadImage (returns the file hash).

## Module structure conventions

```
custom_nodes/my_pkg/
  __init__.py              # imports/exports NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
  my_nodes.py              # actual node classes
  requirements.txt         # pip deps; ComfyUI Manager auto-installs
  pyproject.toml           # optional, for proper packaging
  web/                     # optional JS extensions, declared via WEB_DIRECTORY
    my_extension.js
  README.md
```

Minimum viable `__init__.py`:

```python
from .my_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
```

Or if you want JS:

```python
from .my_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
```

## Common quirks (don't repeat past mistakes)

1. **Forgot batch dim** — returning `[H, W, C]` instead of `[1, H, W, C]` causes downstream type errors.
2. **Returned a single value, not a tuple** — `return image` instead of `return (image,)`. Always tuple, even for one output.
3. **Forgot `,)` on single-element type tuple** — `RETURN_TYPES = ("IMAGE")` is a string, not a tuple. Use `("IMAGE",)`.
4. **uint8 instead of float32** — model nodes will silently malfunction. Always normalize to 0..1 float32.
5. **PIL `convert("RGB")` strips alpha** — if you need transparency, branch on `mode == "RGBA"` first.
6. **Importing heavy deps at module load time** — ComfyUI imports every custom node at startup; slow imports delay boot. Defer to inside `execute()` when possible.
7. **`@PromptServer.instance.routes.post` registered at import time** — no opt-out. If your route is heavy or breaks under certain conditions, gate it inside the handler.
8. **Combo input that must reflect runtime state** — call `folder_paths.get_filename_list(...)` inside the `INPUT_TYPES` classmethod, NOT at module load. The classmethod is called every time the frontend asks for `/object_info`.

## Patterns worth copying from `nano_banana_direct.py`

- **Cost tracking with persistent JSON state file** — `_USAGE_LOCK`, `_load_usage_state`, `_save_usage_state`. Useful if you ever build a node that hits a paid API.
- **Helper functions outside the class** — `_tensor_to_pil`, `_pil_to_tensor`, `_safe_seed`, `_extract_parts` — keep node classes thin, business logic in module-level functions, easy to test in isolation.
- **Defensive image coercion** — `_coerce_to_pil_image` accepts PIL images, byte buffers, SDK wrapper objects, and numpy arrays. Real-world SDKs change return shapes between versions; this is what hardens against breakage.
- **Try/finally cleanup of remote resources** — uploaded files are deleted in `finally:` so a failed generation doesn't leak.
- **`{"ui": {...}, "result": (...)}` dict return** for in-canvas cost summary while still passing tensors downstream.

## Patterns worth copying from `comfy_load_workflow_endpoint`

- **Endpoint-only package** — zero NODE_CLASS_MAPPINGS, just a route + WEB_DIRECTORY. Useful pattern for "extension that adds a new capability to ComfyUI without cluttering the node menu."
- **Validation chain returning early with `web.json_response({"error": ...}, status=4xx)`** — clean error reporting.
- **`PromptServer.instance.send_sync(event_name, payload)`** to broadcast custom events to all connected frontends — lets a backend tool change UI state.

## When building a node for Luis

Most of his runner pipelines submit API-format JSON via `/prompt`. They DON'T need custom nodes — they just compose the existing core+installed nodes. Reach for a custom node only when:

- You need a new wire type (like `GEMINI_DIRECT_FILES`)
- You need to hit an external service inline (paid API, HTTP, gRPC)
- You need a UI affordance not expressible via the existing node palette (custom widget, file browser, drag-drop, color picker)
- You need to push events back to the frontend (status updates, file refresh hints)

For pure prompt assembly, scene expansion, or workflow generation, a runner script is simpler.
