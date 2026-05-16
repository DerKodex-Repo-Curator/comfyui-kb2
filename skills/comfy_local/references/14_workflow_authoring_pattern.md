---
name: How to author a new ComfyUI workflow — Maciej Dziuba's adapted-Purz pattern
description: The "give Claude a proven skill + explicit install-state constraints + canonical templates repo" prompt pattern from Maciej's YouTube setup. Adapt as a checklist for any new workflow.
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
Maciej Dziuba (YouTube: "Claude Code just made ComfyUI 10x more powerful", April 2026) demonstrated a clean prompt pattern for getting Claude to author working ComfyUI workflows. Compress the pattern to its essentials:

## The four-part prompt

1. **Anchor to a proven skill** — point Claude at a known-good ComfyUI skill (Purz's `lora_tester/.claude/skills/comfy_local/skill.md` is canonical) and say "use this as the basis."
2. **Adapt paths to the user's environment** — explicit OS / install path remapping. (For Luis: `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\ComfyUI\` and `G:\models\` — already in `reference_paths.md`.)
3. **Declare install state explicitly** — "I HAVE these models installed. I do NOT have X." Prevents Claude from hallucinating filenames or recommending downloads.
4. **Reference the canonical workflow source** — `https://github.com/Comfy-Org/workflow_templates/tree/main/templates` — for new pipeline shapes. Mix-and-match templates rather than authoring from scratch.

Plus the **single most important guardrail**: "Do NOT download any new models. Only use what I already have installed."

## Translation to my standard process for Luis

Whenever Luis asks for a new workflow:

1. **Determine the target model family.** Read the corresponding `reference_<family>.md` memory file for encoder/VAE pairings. Verify against `G:\models\` via bash that the files exist.
2. **Query the live ComfyUI API at `localhost:8188`** before authoring — `curl http://localhost:8188/object_info/UNETLoader` etc. — to confirm ComfyUI sees the file. (Better than disk-walk because it reflects extra_model_paths.yaml resolution.) See `reference_comfyui_api.md`.
3. **If the workflow shape is novel** (e.g., first time wiring up Wan VACE), pull a reference JSON from `Comfy-Org/workflow_templates` and adapt rather than inventing.
4. **Author both formats:** `name_workflow.json` (graph) and `name_workflow-api.json` (API).
5. **Validate via the API** by submitting to `/prompt` and checking the `node_errors` field. (Cancel before it actually runs if you only want to validate.) Optional: queue it and let it run for full end-to-end verification.
6. **Run the verification checklist** in `feedback_workflow_verification_checklist.md` before delivery.

## What this guards against

- Hallucinating filenames Claude has seen elsewhere but Luis doesn't have
- Pairing the wrong encoder with the wrong DiT (the Klein/Mistral incident)
- Recommending Wan workflows when Wan DiTs aren't actually downloaded
- Authoring workflows that look fine in JSON but fail at runtime
- Re-discovering things every conversation (memory + API queries replace re-research)

## When something new appears

If Luis names a model I don't have a memory file for (e.g., he asks for "Wan 2.2 i2v" when I only know Wan 2.1), the flow is:
1. Verify the file exists in `G:\models\`. If not — STOP and tell Luis it's not installed.
2. Query `localhost:8188/object_info/<Loader>` to see what ComfyUI sees.
3. If install state is fine, look for the pipeline shape in `Comfy-Org/workflow_templates`.
4. After the workflow works, **save what was learned to a new `reference_*.md` memory file** so the second time is fast.
