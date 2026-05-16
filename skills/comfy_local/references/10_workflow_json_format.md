---
name: ComfyUI workflow JSON format (frontend save format)
description: Schema and conventions for the workflow JSON format ComfyUI saves and loads — what every field means, gotchas
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
ComfyUI has TWO JSON formats:
1. **Frontend / save format** — what gets saved when you press "Save (API Format)" → no, actually what gets saved on plain Save. This is what you drag-and-drop onto the canvas. THIS is what we author for Luis.
2. **API format** — flat dict keyed by node id, with `class_type` and `inputs` per node. Used by `/prompt` HTTP endpoint. Don't author this directly.

## Top-level frontend format

```json
{
  "id": "human-readable-id-or-uuid",
  "revision": 0,
  "last_node_id": <int>,    // must be >= max(node id)
  "last_link_id": <int>,    // must be >= max(link id)
  "nodes": [ ... array of node objects ... ],
  "links": [ [lid, src, sslot, tgt, tslot, "TYPE"], ... ],
  "groups": [ ... visual group rectangles ... ],
  "config": {},
  "extra": { "ds": { "scale": 0.85, "offset": [0, 0] } },
  "version": 0.4
}
```

## Node object schema

```json
{
  "id": <int>,
  "type": "ClassName",            // matches NODE_CLASS_MAPPINGS key
  "pos": [x, y],
  "size": [w, h],
  "flags": { "collapsed": true },  // optional
  "order": <int>,                  // execution-order hint, not strict
  "mode": 0,                       // 0=normal, 2=mute, 4=bypass
  "inputs": [
    { "name": "model", "type": "MODEL", "link": <lid or null> },
    { "name": "clip",  "type": "CLIP",  "link": <lid> }
  ],
  "outputs": [
    { "name": "MODEL", "type": "MODEL", "links": [<lid>, <lid>], "slot_index": 0 }
  ],
  "title": "Optional Custom Title",
  "properties": { "Node name for S&R": "ClassName" },
  "widgets_values": [ <ordered list of widget values matching INPUT_TYPES required + optional> ]
}
```

## Link list schema

Each link is a 6-tuple array (NOT object): `[lid, src_node_id, src_slot, tgt_node_id, tgt_slot, "TYPE"]`.

**CRITICAL bidirectional rule:** every link must be recorded BOTH:
- on the source node's `outputs[src_slot].links` array (which is a LIST — multiple consumers)
- AND on the target node's `inputs[tgt_slot].link` field (which is a SCALAR — single producer)

Forgetting to add to the source's `links` array is the #1 silent bug. If a node has multiple consumers of one output, the `links` array must list ALL of them.

## Widget values ordering

`widgets_values` is a positional array matching the order widgets appear in the node's INPUT_TYPES (required first, then optional). Get the order from the node's source code's `define_schema` or `INPUT_TYPES` method. Examples:

| Node | widgets_values |
|---|---|
| `UNETLoader` | `[unet_name, weight_dtype]` |
| `CLIPLoader` | `[clip_name, type, device]` (device usually "default") |
| `DualCLIPLoader` | `[clip_name1, clip_name2, type, device]` |
| `VAELoader` | `[vae_name]` |
| `CLIPTextEncode` | `[text]` |
| `EmptyLatentImage` | `[width, height, batch_size]` |
| `EmptyFlux2LatentImage` | `[width, height, batch_size]` |
| `KSampler` | `[seed, control_after_generate, steps, cfg, sampler_name, scheduler, denoise]` (control_after_generate is "fixed"/"increment"/"decrement"/"randomize") |
| `KSamplerSelect` | `[sampler_name]` |
| `RandomNoise` | `[noise_seed, control_after_generate]` |
| `Flux2Scheduler` | `[steps, width, height]` |
| `FluxGuidance` | `[guidance]` |
| `LoraLoader` | `[lora_name, strength_model, strength_clip]` |
| `ControlNetLoader` | `[control_net_name]` |
| `SaveImage` | `[filename_prefix]` |
| `LoadImage` | `[image_filename, "image"]` |
| `MarkdownNote` | `[markdown_text]` |
| `ImageScaleToTotalPixels` (kjnodes) | `[upscale_method, megapixels]` |

## Multi-output nodes

`SamplerCustomAdvanced` has TWO outputs: `output` (slot 0) and `denoised_output` (slot 1). Both must be present in the `outputs` array even if only slot 0 is wired. Set `links: null` on the unused one.

## Groups

```json
{
  "id": <int>,
  "title": "Group Name",
  "bounding": [x, y, w, h],
  "color": "#3f789e",
  "font_size": 24,
  "flags": {}
}
```

Groups are visual-only; they don't affect execution.

## extra.ds — viewport state

`{"scale": 0.85, "offset": [0, 0]}` — initial canvas zoom and pan. Set scale 0.7-0.9 for clean opens.

## Common pitfalls I've hit

1. **Truncated writes through Windows path** — Write/Edit tools occasionally cut off mid-file when saving JSON > 5KB to Windows-mounted paths. Workaround: write via `python3 json.dump` in bash through the `/sessions/.../mnt/...` path.
2. **Missing link in source `outputs.links`** — when a single node output fans out to two consumers, both link IDs must be in the source's `links` array.
3. **Stale `last_link_id` / `last_node_id`** — increment correctly when adding nodes/links or ComfyUI may renumber and break things.
4. **Wrong widget order** — values match the schema's INPUT_TYPES order, NOT alphabetical. When in doubt, read the node class.
5. **MarkdownNote text is one big string in widgets_values[0]** — newlines must be `\n` literal in JSON, escaped backslashes `\\\\` if you want a literal `\` in the rendered text.
