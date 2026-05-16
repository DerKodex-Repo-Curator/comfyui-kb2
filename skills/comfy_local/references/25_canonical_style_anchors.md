---
name: Canonical style anchor library — Luis's reference image organization
description: Where Luis's style anchor / reference images live. ComfyUI/input/ has ~700 named anchors plus 1014 pasted images. Catalog of the most-referenced ones from production workflows.
type: reference
---

**Source:** Inspected `ComfyUI/input/` on 2026-05-09. 1741 total image files in input directory.

When building Pattern A (style transfer) runners, the `--reference` argument should typically point into `ComfyUI/input/` since these anchors are already in the right place for ComfyUI's `LoadImage` node (the node lists this folder in its dropdown).

## Structure

```
ComfyUI/input/
├── (~700 named anchor images at root level)
├── pasted/         — 1014 ad-hoc clipboard pastes (temporary refs)
├── 3d/             — empty currently
└── clipspace/      — ComfyUI clipspace cache
```

## Confirmed canonical anchors (from PNG metadata of saved workflows)

These are the references Luis's actual production workflows use:

### Cel-shaded character style transfer
| File | Used in | Role |
|---|---|---|
| `npc_Nekomata.png` | (base reference) | Original Nekomata character design |
| `npc_Nekomata_Still_2.png` | `nano_banana_pro_*.png` workflow | Subject reference (image1) — the character to transform |
| `npc_Nekomata_Cel_Shaded.png` | `nano_banana_pro_*.png` workflow | Style anchor (image2) — the cel-shaded look to apply |

### Character batch conversion
| File | Used in | Role |
|---|---|---|
| `Frame 1000003534 (1).png` | `generate multiple cel sahded images.json`, `chibi_character_convert.json` | Style anchor / cel-shaded reference frame |
| `Asset 3@4x.png` | `chibi_character_convert.json` | Subject reference |

### Editing / surgical changes
| File | Used in | Role |
|---|---|---|
| `ComfyUI_10035_.png` | `ComfyUI_00001_.png` (the leaf-creature edit) | Subject — original character to edit |

## Style anchors by use case (named groups)

### NPC / character references (anthropomorphic, frog/fox/snake style)
- `npc_Nekomata.png`, `npc_Nekomata_Cel_Shaded.png`, `npc_Nekomata_Still_2.png` — Nekomata (mythical cat NPC)
- `BallerinaBunny.png`, `BunnyExplorer.png`, `DancersBunny.png` — bunny NPCs
- `Mole_lean.png` — anthropomorphic mole
- `mouse_.png` — anthropomorphic mouse
- `CatVector.png`, `Geisha.png` — additional character anchors

### Biome / environment templates
- `Forest_Test.png`, `Forest_base.png`, `Location_Forest_Fin.png`, `Location_Forest_Fin2.png`, `forest_biome_EXYZ.png` — forest biome
- `Bone_Arena_template.png` — bone arena biome
- `Brown ogre tower base.png`, `brown_ogre_arena_base.png`, `brown_ogre_arena_template.png` — ogre arena
- `Observatory_Tower_base.png`, `Observatory_Tower_template.png`, `arena_observatory_background.png` — observatory
- `Owl Clock tower_base.png`, `Owl Clock tower_template.png`, `arena_owl_background.png` — owl clock tower
- `Red dungeon environment_base.png`, `Red dungeon environment_template.png`, `Red dungeon environment_template2.png` — red dungeon
- `Hedge_Maze_Base.png` and 8 variants — hedge maze biome
- `biome_01_rough.png`, `biome_rough.png`, `biome_abandonedVillageDay_final_Extended.png` — generic biome roughs
- `codex_biome_full.png`, `codex_cherry_biome_full.png` — codex biome reference (canonical?)

### Icon / UI references
- `Buttons.png` — UI button samples
- `Frame_Base.png`, `Frame_Base (1).png`, `Frame_Base2.png` — frame templates (cel-shaded UI frames — same family as `Frame 1000003534 (1).png`?)
- `Rune_Base.png` — runestone base
- Many `ComfyUI_NNNNN_.png` files — saved ComfyUI outputs reused as anchors

### Style guides / training bases
- `BASE_TRAIN.png`, `BASE_TRAIN (1).png` — likely LoRA training base templates
- `Arna_Layout_Guide_2.png` — layout guide
- `Architecture.png` — architecture reference

### Recent ChatGPT image references (Mar 17-18, 2026)
- `ChatGPT Image Mar 17/18, 2026, *.png` — recent ChatGPT-generated references he's pulled in as style or composition anchors

## The `pasted/` subfolder

`input/pasted/` contains 1014 images named `image (1).png` through `image (1013).png`. These are ad-hoc clipboard pastes — temporary references used in workflows like `POP_Cel_Shaded_Nano_Banana_Pro.json` (which uses `pasted/image (543).png`).

**For runners:** if a user provides a path like `pasted/image (543).png`, it resolves to `input/pasted/image (543).png`. Don't refactor these paths — they're stable per-workflow.

**Cleanup note:** the pasted folder is large (~1000 ad-hoc files). If disk pressure ever becomes an issue, the pasted folder can probably be cleaned of older images, but cross-reference against any saved workflows that reference specific `pasted/image (NNN).png` files first.

## How runners should reference these

When building Pattern A or character-transfer runners, the `--reference` CLI argument should accept either:

1. A **bare filename** if the file lives at `input/<filename>` (most common case — ComfyUI's `LoadImage` node references files relative to `input/`)
2. A **`pasted/<filename>`** path if the reference is in the pasted subfolder
3. A **full absolute path** if the file is elsewhere — the runner should then upload it via `/upload/image` first (the API endpoint handles this automatically, copying the file into `input/` as part of the upload)

Reference path validation pattern in a runner:

```python
def resolve_reference(path_arg: str, input_dir: Path = Path("ComfyUI/input")) -> str:
    """Resolve a --reference argument to a string usable in LoadImage's image widget."""
    p = Path(path_arg)
    if p.is_absolute() and p.exists():
        # Need to upload via /upload/image first
        upload_to_comfy(p)
        return p.name
    elif (input_dir / path_arg).exists():
        return path_arg  # already in input/, just pass the relative path
    else:
        raise FileNotFoundError(f"Reference image not found: {path_arg}")
```

## Current convention (don't break this)

Luis's saved workflows reference these images by their **bare names** (no path prefix) when they live at `input/<name>`, and by `pasted/<name>` when in the subfolder. ComfyUI's `LoadImage` node resolves these correctly via its image widget.

When a runner needs to use a NEW reference image not already in `input/`, the proper flow is:
1. Upload via POST `/upload/image` (multipart form)
2. The API copies the file into `input/`
3. Then the workflow references it by the returned filename

This is the pattern `runners/icon_cel_shaded.py` already implements when `--reference` is supplied with a path outside `input/`.

## Style anchor recommendations per use case

When suggesting a default reference image for a runner, prefer:

| Asset type | Default style anchor |
|---|---|
| **Cel-shaded character** | `npc_Nekomata_Cel_Shaded.png` (proven in production) |
| **NPC roster member** | `npc_Nekomata_Cel_Shaded.png` or `Frame 1000003534 (1).png` |
| **Cel-shaded UI icon / frame** | `Frame_Base.png` or `Frame 1000003534 (1).png` |
| **Forest biome** | `Forest_base.png` or `Location_Forest_Fin.png` |
| **Tower biome** | `Owl Clock tower_template.png` or `Observatory_Tower_template.png` |
| **Dungeon biome** | `Red dungeon environment_template.png` |

If unsure, ask Luis to specify a reference rather than guessing. He has strong opinions about which anchor matches which use case.

## What's NOT here yet

- `image_03 (2).png` — referenced in `POP_Cel_Shaded_Nano_Banana_Pro.json` workflow but no longer present. Either renamed/moved, or the workflow file is older than the input folder cleanup.

If a runner attempts to load a missing reference, it should fail with a clear error mentioning the file is missing rather than silently substituting.
