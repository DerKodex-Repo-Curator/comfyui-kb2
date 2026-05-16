---
name: NanoBanana2Direct — proven workflow patterns and full schema
description: Reverse-engineered from PNG metadata of Luis's actual ComfyUI outputs. Definitive widget list + two canonical workflow patterns he uses.
type: reference
---

**Source:** PNG metadata extracted from `ComfyUI/output/nano_banana_pro_00001_.png`, `ComfyUI_00001_.png`, etc. on 2026-05-09. These are real outputs from Luis's working pipeline, so the schemas and patterns below are battle-tested.

## NanoBanana2Direct full input schema

```python
{
    "prompt":              str,        # positive prompt (or wired from a String node)
    "model":               str,        # always: "Nano Banana 2 (Gemini 3.1 Flash Image)"
    "seed":                int,        # 32-bit; oversized seeds auto-normalized by node
    "aspect_ratio":        str,        # "auto" | "1:1" | "16:9" | "9:16" | "4:3" | "3:4" | etc.
    "resolution":          str,        # "512" | "1K" | "2K" | "4K"  (token cost scales)
    "response_modalities": str,        # "IMAGE+TEXT" | "IMAGE"
    "thinking_level":      str,        # "LOW" | "MEDIUM" | "HIGH"  (Luis uses HIGH)
    "system_prompt":       str,        # default works well — see below
    "api_key":             str,        # empty string falls back to GEMINI_API_KEY env var
    "images":              optional,   # IMAGE input from another node (reference images batched)
}
```

**Default system_prompt** (Luis uses this verbatim — don't override unless you have a reason):

```
You are an expert image-generation engine. You must ALWAYS produce an image.
Interpret all user input—regardless of format, intent, or abstraction—as literal visual directives for image composition.
If a prompt is conversational or lacks specific visual details, you must creatively invent a concrete visual scenario that depicts the concept.
Prioritize generating the visual representation above any text, formatting, or conversational requests.
```

**RETURN_TYPES:** `(IMAGE, STRING, IMAGE)` — main image, response text, possibly preview/intermediate.

**Cost:** ~$0.10 per 2K image (Gemini 3.1 Flash Image pricing).

## Pattern A — Style transfer (his most common workflow)

**Use case:** "I have a character/icon/asset already. Apply this art style to it." Pulls from `nano_banana_pro_*.png` outputs.

**Graph (6 nodes):**
```
LoadImage(subject)  ─┐
                     ├→ ImageBatch ─→ NanoBanana2Direct ─→ SaveImage
LoadImage(style ref)─┘                       │
                                             └→ Image Comparer (rgthree)  ← image_b
```

**Canonical prompt text** (Luis uses this VERBATIM for style transfer — keep this exact wording in runners):
```
transform the style of the image1. maintain the composition, scale and proportions of the orginal image1. use the reference image2 for render style
```

**Default node settings he uses:**
- `model`: "Nano Banana 2 (Gemini 3.1 Flash Image)"
- `seed`: random 32-bit
- `aspect_ratio`: "auto"
- `resolution`: "2K"
- `response_modalities`: "IMAGE+TEXT"
- `thinking_level`: "HIGH"
- `system_prompt`: default (see above)
- `api_key`: ""  (env var fallback)

**Reference image convention:** image1 = subject (the thing you want to transform); image2 = style anchor (the look you want). The prompt explicitly references "image1" and "image2" — they're slots in the batched input.

**Image Comparer (rgthree)** is wired as a downstream A/B preview — not required for generation, but Luis includes it for visual comparison.

## Pattern B — Single-input edit / generation

**Use case:** "Edit this character: change X, keep Y" or "Generate something from a detailed text spec." Pulls from `ComfyUI_00001_.png` (13-node workflow).

**Graph (minimal — 4 nodes):**
```
String(prompt)  ─→ NanoBanana2Direct ─→ SaveImage
                          │
LoadImage      ─────────→ │
```

The prompt comes from a separate `String` node so the same prompt can fan out to multiple downstream nodes. The String node holds verbose text — Luis writes very detailed edit instructions with explicit "make these changes" / "keep and preserve" / "negative guidance" sections.

**Default node settings (he uses different from Pattern A here):**
- `aspect_ratio`: "1:1"
- `resolution`: "1K"  (cheaper for iterating)
- `response_modalities`: "IMAGE"  (skips text response when not needed)
- `thinking_level`: "HIGH"
- everything else as Pattern A

**Example prompt structure** he uses for character edits:

```
Edit the uploaded character image while preserving [the things to keep — style, identity markers, key visuals].

Make these specific changes:
- Change X
- Change Y
- Change Z

Keep and preserve:
- Visual element 1
- Visual element 2
- Visual element 3

Style rules:
- Rule 1
- Rule 2

Negative guidance:
- no X
- no Y
```

The 4-section structure (preserve / change / style rules / negative guidance) is Luis's house format for edits. Match it when building edit-mode runners.

## Pattern C — Pure text-to-image (no reference)

**Use case:** "Generate a brand-new icon/character/asset from a detailed prompt with style lock baked in."

**Graph (3 nodes minimum):**
```
String(verbose prompt with style lock) ─→ NanoBanana2Direct ─→ SaveImage
```

No LoadImage. The full style lock from `references/18_example_house_style.md` goes into the positive prompt. Use this pattern when you don't have a reference image but want a fresh generation in his house style.

## Patterns by asset type — what to reach for

| Asset type | Has reference? | Pattern |
|---|---|---|
| Icon — fresh design | No | Pattern C with full icon style lock |
| Icon — match existing set | Yes (style anchor) | Pattern A with image1 = blank/sketch, image2 = anchor |
| Character — new chibi | No | Pattern C with character style lock |
| Character — restyle existing | Yes (style anchor) | Pattern A |
| Character — surgical edit | Yes (the character itself) | Pattern B with detailed change list |
| Prop — new | No | Pattern C with painterly prop style lock |
| Biome — hero shot | Optional (design blueprint + style bible refs) | Pattern A with both refs in batch |

## Runners should accept these CLI args

- `--subject "<concept>"` (required for fresh generations)
- `--reference <path>` and/or `--style-anchor <path>` (optional, switches to Pattern A or B)
- `--mode {single, 2x4, 4x5}` (icons only)
- `--aspect-ratio {auto,1:1,16:9,9:16,4:3,3:4,21:9}` (default depends on asset type)
- `--resolution {512,1K,2K,4K}` (default 2K for hero shots, 1K for iteration)
- `--seed <int>` (random if omitted)
- `--style-lock` flag — if true, use Pattern C with full style lock; if false and no reference, fail with helpful message

## What NOT to do

- Don't override `system_prompt` unless you have a specific reason — Luis uses the default
- Don't pass an `api_key` value — leave it empty, the env var works
- Don't lower `thinking_level` to "LOW" — he uses HIGH consistently for quality
- Don't strip the verbatim style-transfer prompt wording in Pattern A — that exact phrasing is what works
- Don't forget to wire `Image Comparer (rgthree)` for style-transfer runs if Luis wants visual A/B (optional, but he uses it)

## Discovered quirks (verified against live `/object_info/NanoBanana2Direct` on 2026-05-09)

- **`thinking_level` enum is `["MINIMAL", "HIGH"]` — NOT `LOW | MEDIUM | HIGH`.** Section 1 of this doc lists three values; the live node only accepts two. "LOW" or "MEDIUM" will be rejected by /prompt validation. Use "HIGH" (Luis's choice) or "MINIMAL" (cheaper).
- **Default `resolution` is `"1K"`, default `thinking_level` is `"MINIMAL"`, default `response_modalities` is `"IMAGE"`.** Luis's house defaults (2K / HIGH / IMAGE+TEXT) are *not* the node defaults — runners must set them explicitly.
- **`aspect_ratio` enum (full list):** `"auto"`, `"1:1"`, `"1:4"`, `"1:8"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:1"`, `"4:3"`, `"4:5"`, `"5:4"`, `"8:1"`, `"9:16"`, `"16:9"`, `"21:9"`. No "1:2" or "2:1" — strange asymmetric values like "8:1" and "1:8" are present instead.
- **`images` and `files` are both `optional`** — pure text-to-image works with neither input wired. No need for an ImageBatch node when you only have one reference image; pass it directly to `images`.
- **No required widget for negative prompt** — there isn't one. Negative guidance must be folded into the positive `prompt` text (Luis's "Avoid …" sentence is exactly this convention).
- **`api_key` widget is `STRING` (single-line) not multiline.** Leaving it as `""` is the documented happy path; the env var fallback (`GEMINI_API_KEY` or `GOOGLE_API_KEY`) handles auth.

---

## CRITICAL ADDENDUM (added 2026-05-09 after reading user workflow library)

After inspecting Luis's `ComfyUI/user/default/workflows/` folder, three findings change the picture above:

### Three different Nano Banana / Gemini nodes, not one

| Node class | From package | Underlying model | When Luis uses it |
|---|---|---|---|
| `NanoBanana2Direct` | `nano_banana_direct_pkg` (woct0rdho-style direct) | Nano Banana 2 (Gemini 3.1 Flash Image) | Recent direct outputs (`nano_banana_pro_*.png` from Apr 27); the runner we built around this node |
| `GeminiNanoBanana2` | (built-in / API node) | Nano Banana 2 (Gemini 3.1 Flash Image) — same as Direct | His **default for most saved workflows** — `chibi_character_convert`, `chonkify`, `generate multiple cel sahded`, `POI generation`, `forest`, `frames`, `stone3` etc. |
| `GeminiImage2Node` | (built-in / API node) | **`gemini-3-pro-image-preview`** — different, stronger model | His character-quality workflow `POP_Cel_Shaded_Nano_Banana_Pro.json` and most "generate images from prompt and ref image" usage. ~$0.14/gen vs ~$0.10. |

**`GeminiNanoBanana2` is the canonical default for new runners** (matches his most-used pattern) unless the use case calls for the higher-tier Gemini 3 Pro model (cel-shaded character work, biome hero shots — see `POP_Cel_Shaded_Nano_Banana_Pro.json` and `forest.json`).

The widget orderings differ slightly between `NanoBanana2Direct` and `GeminiNanoBanana2`. Query `/object_info/GeminiNanoBanana2` to discover the exact schema before authoring with that node.

### The N-parallel-call pattern (Luis's actual variation strategy)

**Luis does NOT use Nano Banana's contact-sheet grid mode for variations.** He uses **N parallel calls in one workflow**, each with a different seed.

Example from `generate multiple cel sahded images.json`:
- One LoadImage(reference) → fed into 8 separate `GeminiNanoBanana2` nodes
- One String node (verbose character prompt) → fed into all 8 nodes
- Each `GeminiNanoBanana2` node has its own random seed (222, 230, 232, 234, 236, 238, 240, 242 in the file)
- Each has its own SaveImage downstream
- Result: 8 fully-formed character variations at 2K each, guaranteed unique because each is an independent API call

This costs **8× the API fee** ($0.80 instead of $0.10 for "8 variations") but each output is a complete, full-quality icon/character — not a cropped cell from a contact sheet that might look cramped.

**For grid/variation work in new runners, prefer the N-parallel pattern** unless cost is prohibitive. The grid mode (single API call asking for "exactly N icons") is unreliable: Nano Banana doesn't strictly enforce cell count, and individual icons in a grid are smaller / lower-detail than independent generations.

**Wall-clock timing** (verified 2026-05-09 with `runners/icon_cel_shaded.py --variations 4`): ComfyUI executes the N independent `NanoBanana2Direct` nodes **sequentially**, not in parallel — there's no intra-workflow concurrency in the executor. Total wall time ≈ N × single-call time (~30-45s per 2K HIGH-thinking call, so a `--variations 4` run takes 2-3 minutes). The KSampler-style progress indicator at the top of ComfyUI shows which Gemini node is currently running. If you genuinely need parallel API calls, submit N separate `/prompt` jobs from the runner instead of bundling them into one workflow.

### Image Comparer (rgthree) is part of his standard style-transfer setup

Luis includes `Image Comparer (rgthree)` in style-transfer workflows for visual A/B between the original and result. Optional but he uses it consistently. Not required for generation; purely UX.

### Pointer to canonical templates

Cloned copies of his actually-used workflows live at `workflows/user_canonical_templates/`:

- **`POP_Cel_Shaded_Nano_Banana_Pro.json`** — character cel-shading via `GeminiImage2Node` (Gemini 3 Pro). 9 nodes. Style anchor + composition reference + verbose character description in prompt widget. Image Comparer included.
- **`generate multiple cel sahded images.json`** — N-parallel pattern (8 variations) via `GeminiNanoBanana2` (Nano Banana 2). The reference template for any "give me N variations" runner.
- **`chibi_character_convert.json`** — character conversion via N-parallel `GeminiNanoBanana2` (8 variations). Same pattern as `generate multiple` but for chibi characters.
- **`chonkify.json`** — single `GeminiNanoBanana2` call at 4K resolution with a "MASTER PROMPT" structure asking for "6 variations on one contact sheet". Demonstrates the contact-sheet alternative with a more specific prompt structure.
- **`POI generation.json`** — biome/POI generation via `GeminiNanoBanana2` + `easy imageSwitch` for switching between style anchors.
- **`forest.json`** — biome with both `GeminiImage2Node` and `GeminiNanoBanana2` chained. The biome workflow.
- **`generate images from prompt and ref image.json`** — generic prompt+reference pattern (26 nodes, both Gemini node types in pipeline).
- **`stone3.json`** — `GeminiImage2Node` + `RecraftRemoveBackgroundNode` for asset+bgremoval pipeline.

For runner authoring, **clone one of these as a starting template** and substitute variable parts (subject text, reference filenames, seeds). Faster and more correct than authoring from scratch.

### Updated runner recommendation — STATUS as of 2026-05-09

Going forward, refactor `runners/icon_cel_shaded.py`:
1. ~~Switch from `NanoBanana2Direct` to `GeminiNanoBanana2` as the default node~~ — **REJECTED.** See § "USER PREFERENCE" below: Luis prefers `NanoBanana2Direct` for direct billing control. Don't switch back unless he asks.
2. ~~Add a `--variations N` mode that uses N-parallel calls~~ — **DONE.** `runners/icon_cel_shaded.py` now supports `--variations N` (orthogonal to mode and Pattern A/C). See `references/36_runners_catalog.md` for CLI signature and examples.
3. For character work specifically, build a separate `runners/character_cel_shaded.py` that clones `POP_Cel_Shaded_Nano_Banana_Pro.json`. — **PENDING.** The original recommendation said use `GeminiImage2Node` (Gemini 3 Pro); per USER PREFERENCE that should also use `NanoBanana2Direct` substituted in. Stay on Gemini 3 Pro IF Luis explicitly asks for the higher tier.

---

## USER PREFERENCE (confirmed 2026-05-09)

**Luis's preferred Nano Banana node going forward is `NanoBanana2Direct`** (from `nano_banana_direct_pkg`), NOT `GeminiNanoBanana2`.

**Why:** the README for `nano_banana_direct_pkg` is explicit — *"This is a normal local custom node, so it will not use Comfy's proxy credits system. This version keeps the visible api_key field for personal use."* Direct billing control via his own Google API key, no Comfy proxy / credit middleware. Cleaner cost picture per generation.

**The older `GeminiNanoBanana2` and `GeminiImage2Node` in his saved workflows** (e.g., `chibi_character_convert.json`, `generate multiple cel sahded images.json`) are historical — those workflows still demonstrate valuable patterns (N-parallel calls, character cel-shading, biome generation), but the **NODE used in those examples should be substituted with `NanoBanana2Direct` when adapting them**.

So the canonical pattern for new work:

| Pattern | Use this node |
|---|---|
| Single-call style transfer | `NanoBanana2Direct` |
| N-parallel variations (was: 8× `GeminiNanoBanana2`) | 8× `NanoBanana2Direct` |
| Character cel-shaded (was: `GeminiImage2Node` Gemini 3 Pro) | `NanoBanana2Direct` (Gemini 3.1 Flash Image) — or stay on Gemini Pro IF the user explicitly asks for the higher tier |
| Biome / forest / multi-call pipeline | `NanoBanana2Direct` |

**Don't switch back to `GeminiNanoBanana2` unless Luis asks.** If a new runner needs to clone a template from `workflows/user_canonical_templates/` that uses `GeminiNanoBanana2`, replace those nodes with `NanoBanana2Direct` and adapt widget names accordingly (the schemas differ slightly — see ref 20 § Discovered quirks for the live `NanoBanana2Direct` widget list).

**The icon runner currently in use (`runners/icon_cel_shaded.py`) is correct as built** — it uses `NanoBanana2Direct`. Don't refactor.
