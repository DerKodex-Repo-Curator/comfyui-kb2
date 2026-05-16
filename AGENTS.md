# AGENTS.md — comfyui-kb

You are an AI coding agent (Codex, Claude Code, Cursor, Windsurf, etc.) working in a ComfyUI knowledge-base repo. This file is your entry point. Read it first.

## What this repo is

A working knowledge base for authoring **ComfyUI workflows and custom nodes**. The author runs an RTX 5090 portable Windows install and produces text-to-image, image-edit, and text-to-video workflows across the Flux, Flux 2, Klein, Qwen-Image, Wan, Z-Image, and ChronoEdit families.

The repo is organized as a single **skill** at `skills/comfy_local/`, with:

- `skills/comfy_local/skill.md` — the master index. Read this after this file.
- `skills/comfy_local/references/` — 59 markdown reference docs covering every model family, encoder pairing, sampler choice, custom-node package, ComfyUI API endpoint, and workflow JSON format detail.
- `skills/comfy_local/runners/` — 15 Python runner scripts that build API-format workflows and POST them to `http://localhost:8188/prompt`.
- `skills/comfy_local/watcher.py` — a WebSocket daemon that listens to ComfyUI's `/ws` endpoint and downloads outputs as they complete.
- `workflows/` — 9 vendor-neutral canonical workflows (one per model family) cherry-picked from the upstream Comfy Org templates.

## Critical operating rules

These are the "don't repeat past mistakes" rules. Read them before authoring any workflow.

1. **Verify every loader filename exists in the user's `models/<subfolder>/`** before declaring a workflow done. Either use shell `ls` against the real models folder, or query ComfyUI's `/object_info/<LoaderNodeName>` endpoint which returns the live list of available files.

2. **Encoder ↔ DiT pairing** is the #1 source of runtime errors. Flux 2 dev needs the Mistral encoder; Flux 2 Klein-4B needs Qwen3-4B; Flux 2 Klein-9B needs Qwen3-8B. Mismatches cause `RuntimeError: mat1 and mat2 shapes cannot be multiplied (Bx15360 and 7680xH)` at sampling time. See `skills/comfy_local/references/16_flux2_encoder_pairing.md` and `references/05_flux_family.md`.

3. **Distilled models use cfg=1.** Flux 2, Klein, schnell, Kontext, Krea, Fill, Lightning Qwen variants, and Z-Image turbo are all distilled. Negative prompt is internally zeroed; raising cfg breaks output coherence.

4. **Save workflows in BOTH formats:** `<name>_workflow.json` (graph format, for UI drag-drop) AND `<name>_workflow-api.json` (API format, for headless `/prompt` POST). Neither environment auto-converts.

5. **Don't recommend running `Update ComfyUI*.bat` without explicit user approval** — Comfy core updates can break custom nodes silently.

## Reference workstation profile

The reference docs are written against this hardware. Adapt paths and assumptions to your own install:

- GPU: NVIDIA RTX 5090 (Blackwell, sm_120, 32 GB VRAM)
- CPU: AMD Ryzen 9 9950X3D
- RAM: 64 GB (25 GB pinned for offload)
- OS: Windows 11
- Python: 3.12 (portable embedded at `python_embeded/python.exe`)
- PyTorch: 2.8.0 + cu128
- ComfyUI: 0.19.x (frontend 1.42.x)
- Attention: SageAttention 1.0.6 + triton-windows 3.6.0 via `--use-sage-attention`

## How to use this repo

### As a knowledge base (reading)

When you need to answer a ComfyUI question, read in this order:

1. This file (you've already done that).
2. `skills/comfy_local/skill.md` — the master index. It points at the right reference doc for every topic.
3. The specific reference doc(s) for the model family or topic you're working on.

The reference filenames are numbered for browsing order but topic-grouped. See `skill.md` for the full table.

### As an authoring toolkit (writing)

When the user asks you to author a new workflow:

1. Identify the target model family. Read the matching reference (e.g. `references/05_flux_family.md` for any Flux variant).
2. Confirm the encoder, VAE, and sampler pairings from that reference.
3. Check `references/15_verification_checklist.md` and run through every item before declaring the workflow done.
4. If the user is running headless, use `skills/comfy_local/runner_template.py` as the starting point and write the runner into `skills/comfy_local/runners/<your_name>.py`.
5. Save the resulting workflow JSON in BOTH formats (rule #4 above).

### As a runner library (running)

If the user has the watcher daemon running:

1. Author a runner in `skills/comfy_local/runners/` (or reuse an existing one).
2. The runner POSTs to `http://localhost:8188/prompt` and exits.
3. The watcher daemon sees the completion event over WebSocket and downloads outputs to `../../outputs_watched/`.
4. The user receives a PNG/MP4 with no further action needed.

See `skills/comfy_local/SKILL_USAGE.md` for the full daemon setup.

## Style conventions

- All reference docs use frontmatter (`name`, `description`, `type`) for discoverability.
- File numbering (`01_`, `02_`, etc.) is browsing order, not strict topic order — use the table in `skill.md` to find the right doc.
- The "house style" framework in `references/18_*` and the example world in `references/19_*` are templates — substitute your own style notes and project context when adapting.

## Repo layout

```
comfyui-kb/
├── README.md                          # Human-facing repo overview
├── AGENTS.md                          # This file (Codex / OpenAI agents)
├── CLAUDE.md                          # Mirror of this file (Claude Code convention)
├── .cursorrules                       # Pointer to AGENTS.md (Cursor convention)
├── .windsurfrules                     # Pointer to AGENTS.md (Windsurf convention)
├── .gitignore
├── LICENSE
├── skills/
│   └── comfy_local/
│       ├── skill.md                   # Master index
│       ├── SKILL_USAGE.md             # Daemon setup, daily-use guide
│       ├── watcher.py                 # WebSocket daemon
│       ├── runner_template.py         # Boilerplate for new runners
│       ├── start_watcher.bat
│       ├── stop_watcher.bat
│       ├── .env.example
│       ├── references/                # 59 numbered reference docs
│       └── runners/                   # 15 production runner scripts
└── workflows/                         # 9 vendor-neutral canonical workflows
```

## License

See `LICENSE`. The Comfy Org workflow JSONs in `workflows/` are upstream content from the Comfy Org canonical templates and remain under their original license.
