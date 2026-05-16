---
name: Always verify workflow compatibility against the actual install
description: Before delivering ComfyUI workflows, verify model filenames exist in G:\models and that nodes match what's installed
type: feedback
---
When building ComfyUI workflows for Luis, **always verify against his actual install before claiming a workflow will work**.

**Why:** he runs a shared `G:\models` folder across multiple ComfyUI versions and explicitly asked for compatibility checks. Workflow JSONs that reference filenames that don't exist on his disk are wasted work.

**How to apply:**

1. Confirm every `widgets_values` filename for UNETLoader / CLIPLoader / VAELoader / LoraLoader exists in the corresponding `G:\models\<subfolder>\` (request the directory if not already mounted).
2. Confirm node `type` strings exist either in core ComfyUI (`comfy_extras/nodes_*.py`) or in his installed `custom_nodes/` directories — don't assume a node exists just because it's standard elsewhere.
3. Cross-check capability constraints from his startup log: VRAM ceiling, attention backend, missing optimizations (Triton/SageAttn/FlashAttn), CUDA version mismatches that disable backends like comfy_kitchen.
4. Validate the JSON parses and link IDs are bidirectionally consistent (link recorded on both source `output.links` array AND target `input.link` field) before declaring it done. Use a Python validator script.

**Known write quirk:** the Write/Edit tools sometimes truncate large JSON files when writing through the Windows path. If validation fails with unterminated string / EOF, rewrite the file via `python3 -c` in bash through the `/sessions/.../mnt/...` path instead.
