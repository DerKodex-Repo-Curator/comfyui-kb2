---
name: Runner + watcher daemon architecture for headless ComfyUI
description: Maciej Dziuba's two-tier setup — orchestrator script + persistent WebSocket watcher daemon — that turns Claude into a fully autonomous ComfyUI driver. Directly portable to localhost:8188.
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
Maciej Dziuba's video setup demonstrates a clean two-tier architecture for headless ComfyUI work. Authoring (one-shot per request) is separate from runtime (persistent background daemon).

## Tier 1: Runner script (one per use case)

A Python orchestrator that runs once per user request. Example: `shortfilm_run.py` is ~116 lines and does:

1. **Upload inputs** — POST reference images to `/api/upload/image`, get back server-side filenames
2. **Expand prompt** — if `ANTHROPIC_API_KEY` is set, call Claude API to expand the user's one-line prompt into N scene prompts using a 4-beat template (`establishing → confrontation → reflection → resolution`); else use the template directly
3. **Build big JSON workflow** — programmatically construct the multi-node API-format dict (the Maciej short-film one is 86 nodes), substituting the prompt, scene texts, uploaded filenames, and style LoRAs into the right slots
4. **Submit** — POST to `/api/prompt`, get back `prompt_id`
5. **Print post-processing command** — e.g., an `ffmpeg concat` one-liner that stitches the 4 mp4s the watcher will eventually drop

The script's job ends after step 5. It does NOT poll for completion — that's the watcher's job.

## Tier 2: Watcher daemon (one per environment, runs forever)

A Python script that runs as a persistent background process. Holds a WebSocket connection to ComfyUI's `/ws` endpoint, listens for events, auto-downloads completed outputs.

```
- Output folder: ~/ComfyCloudOutputs/  (or any user-chosen sink)
- Script: ~/.claude/skills/<skill_name>/watcher.py
- State: ~/.claude/skills/<skill_name>/<skill_name>_state/
  - watcher.log
  - watcher.pid
  - downloaded.txt  (dedupe ledger)
- Mechanism: persistent WebSocket; listens for "executed" events;
  auto-downloads via /api/view; dedupes via downloaded.txt;
  auto-reconnects with backoff on drop.
```

**Lifecycle commands** (Mac/Linux pattern; adjust for Windows):
- Stop: `kill $(cat ~/.claude/skills/<skill>/<skill>_state/watcher.pid)`
- Restart: `nohup python3 ~/.claude/skills/<skill>/watcher.py >/dev/null 2>&1 & disown`

For Luis on Windows, the equivalent would be a PowerShell `Start-Process -WindowStyle Hidden` or a scheduled task — or just a regular cmd window left running.

## Architecture in one sentence

> Your machine uploads + orchestrates; ComfyUI runs the models; watcher pulls results back. The UI workflow JSON is just a visualization of step 3 of the runner.

## ComfyUI WebSocket endpoint reference

For Luis's localhost setup, the watcher would connect to `ws://localhost:8188/ws`. Events to listen for:

| Event type | When fired | Useful fields |
|---|---|---|
| `status` | Queue size changed | `data.status.exec_info.queue_remaining` |
| `executing` | Node started | `data.node`, `data.prompt_id` |
| `progress` | KSampler step progress | `data.value`, `data.max`, `data.prompt_id` |
| `executed` | Node completed (this fires for SaveImage etc.) | `data.node`, `data.output.images[]`, `data.prompt_id` |
| `execution_success` | Whole prompt done | `data.prompt_id` |
| `execution_error` | Failure | `data.exception_message`, `data.traceback`, `data.prompt_id` |
| `execution_cached` | Skipped via cache | `data.nodes`, `data.prompt_id` |

For an `executed` event with `data.output.images`, each image has `{filename, subfolder, type}`. Build the download URL: `http://localhost:8188/view?filename=<filename>&subfolder=<subfolder>&type=<type>`.

## Skill folder layout (Maciej's pattern, adapted for Luis)

For Luis on Windows, suggested layout when we build this:

```
G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\skills\
├── comfy_local\
│   ├── skill.md                 # the skill / instruction file (adapted from Purz)
│   ├── runner.py                # one-shot orchestrator template
│   ├── watcher.py               # persistent WebSocket daemon
│   ├── watcher_state\
│   │   ├── watcher.log
│   │   ├── watcher.pid
│   │   └── downloaded.txt
│   ├── workflows\
│   │   ├── flux2_basic_t2i_workflow.json         # graph format
│   │   ├── flux2_basic_t2i_workflow-api.json     # API format
│   │   ├── flux2_4model_parallel_workflow.json
│   │   ├── flux2_4model_parallel_workflow-api.json
│   │   └── ...
│   └── .env                     # ANTHROPIC_API_KEY, etc.
└── outputs\                     # where the watcher drops everything
```

## The 4-beat scene expansion template

Used by Maciej to convert one user-provided story prompt into 4 scene prompts. Generalizes to any narrative-style multi-shot workflow.

```
Scene 1 — establishing
Scene 2 — confrontation
Scene 3 — reflection
Scene 4 — resolution
```

Implementation: the runner either calls Anthropic's API to author each scene (if `ANTHROPIC_API_KEY` is set) or substitutes the user's prompt into a fixed template. Same shape applies to non-narrative use cases too — e.g., 4 angles of one subject (front / 3-quarter / profile / back).

## Multi-model parallel sub-graph pattern

One workflow JSON containing N independent sub-graphs. Each sub-graph: own checkpoint loader, encoders, sampler, save node. ALL sub-graphs share only the prompt text (via a `PrimitiveStringMultiline` node fanned out). Per-model filename suffixes (`_qwen`, `_flux`, `_sdxl`, `_sd35`) prevent output collisions.

For Luis's install, candidates for a 4-model T2I parallel test:
- A) Flux 2 dev fp8mixed
- B) Flux.1 dev fp8 or Krea
- C) SDXL Juggernaut XI / RealVis V5
- D) Qwen-Image 2512 fp8 OR Z-Image turbo

Each gets its own UNETLoader / DualCLIPLoader / VAELoader / KSampler / SaveImage chain, all fed by one shared CLIPTextEncode-per-model that pulls from the same shared prompt primitive.

## Why save BOTH workflow formats

Maciej confirms (and Purz earlier said the same): the **API format** is what `/api/prompt` accepts; the **graph format** is what the UI loads on drag-drop. Neither environment auto-converts. There's also no server-side endpoint to persist workflows in the Cloud UI.

Convention: save as `<name>_workflow.json` (graph) and `<name>_workflow-api.json` (API).

## When to apply this for Luis

- **One-shot generation requests** ("generate me an image of X") — don't need this; just author and run.
- **Multi-stage pipelines** (story → 4 scenes → 4 videos → stitched final) — runner script is the right tool.
- **Comparison runs** (one prompt across N models or N LoRA strengths) — runner + parallel sub-graph workflow.
- **Long-running batch work** (evaluate a LoRA across 50 prompts) — runner + watcher is exactly the right architecture; Maciej's pattern + Purz's batch loop combined.

For a one-off "give me a Flux 2 image" we just author a workflow JSON and the user drag-drops it. For anything more complex, build the runner.
