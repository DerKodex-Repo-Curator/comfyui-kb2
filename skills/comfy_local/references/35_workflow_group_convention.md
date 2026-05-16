---
name: Workflow group rectangle convention
description: Color-coded section rectangles (Loaders / Conditioning / Sampling / Decode) wrapped around every graph-format workflow we emit
type: reference
---
# Color-coded section groups on every graph-format workflow

User preference (2026-05-09): every `*_workflow.json` we emit should have four
color-coded group rectangles drawn around the standard sections of a T2I/I2I
graph. This is implemented in `runners/_api_to_graph.py` via `build_groups()`
and applied automatically every time the converter runs.

## Section -> color -> member node classes

| Section | Color | Class types in this section |
|---|---|---|
| **Loaders** | `#3f789e` (blue) | `UNETLoader`, `CLIPLoader`, `DualCLIPLoader`, `VAELoader`, `CheckpointLoaderSimple` |
| **Conditioning** | `#5e8d56` (green) | `CLIPTextEncode`, `ConditioningZeroOut`, `FluxGuidance` |
| **Sampling** | `#a1309b` (purple) | `EmptyLatentImage`, `EmptySD3LatentImage`, `EmptyFlux2LatentImage`, `ModelSamplingAuraFlow`, `KSampler`, `SamplerCustomAdvanced` |
| **Decode** | `#a59c4d` (olive) | `VAEDecode`, `SaveImage` |

Latent generators (`EmptyLatentImage` and friends) are intentionally Sampling,
not Loaders — they produce the latent the sampler operates on, and grouping
them with KSampler keeps the Sampling rect contiguous. `ModelSamplingAuraFlow`
is also Sampling because it's a sampler-side model shift.

## Layout discipline

The converter places nodes by `column = max(topo_depth, SECTION_MIN_COL[section])`,
where:

```
Loaders      -> col 0
Conditioning -> col 1
Sampling     -> col 3   (gap at col 2 is intentional)
Decode       -> col 5   (gap at col 4 is intentional)
```

The gaps guarantee section bounding rects don't horizontally overlap input-less
nodes that would otherwise sit in column 0. With this layout the four group
rectangles tile cleanly left-to-right with only the 20 px padding touching at
the boundaries.

## When you add a new node class

If you add a node class to a runner that isn't already in `SECTION_OF` inside
`_api_to_graph.py`, also add it here. Without an entry the node falls outside
all groups (no rectangle drawn around it). This is the canary: if a new graph
has nodes visually outside every colored rectangle, that class needs both
`SECTION_OF` and `NODE_META` entries.

## Group object schema (from `references/10_workflow_json_format.md`)

```json
{
  "id": <int, 1-based, unique within the workflow>,
  "title": "Loaders",
  "bounding": [x, y, w, h],
  "color": "#3f789e",
  "font_size": 24,
  "flags": {}
}
```

Groups are visual-only — they do not affect execution, so a missing or wrong
group is a UX issue, not a correctness one.
