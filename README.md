# comfyui-kb

A working knowledge base for **ComfyUI workflows and custom nodes**, optimized for AI coding agents (Codex, Claude Code, Cursor, Windsurf) but also useful as a human reference.

Covers the full surface of modern ComfyUI as of 2026: Flux.1 dev/schnell/Kontext/Krea/Fill/Redux, Flux 2 dev, Flux 2 Klein (4B and 9B variants), Qwen-Image (original / 2509 / 2511 / 2512 / Layered + Edit variants + Lightning low-step LoRAs), Wan 2.1 video (t2v / i2v / VACE / Animate / Camera / S2V / HuMo / SCAIL), Z-Image, ChronoEdit, Chroma, Ovis, LTX-Video, plus the SDXL/SD1.5 lineage.

## What's inside

- **59 reference docs** covering every model family with encoder/VAE/sampler pairings, every installed custom-node package, the ComfyUI workflow JSON format, the REST API endpoints, sampler/scheduler personalities, GGUF and Nunchaku quantization, Civitai/Hugging Face ecosystem maps, Wan video model landscape, and the Comfy Org canonical template catalog.
- **15 Python runners** that build API-format workflows headlessly and POST them to `localhost:8188/prompt`.
- **A WebSocket watcher daemon** that listens to ComfyUI's `/ws` endpoint and auto-downloads completed outputs.
- **9 canonical workflow JSONs** (one per model family) from the upstream Comfy Org templates, vendor-neutral and ready to drag-drop into the ComfyUI UI.

## Reference workstation

Everything is written against this hardware. Adapt paths for your own install:

| Component | Spec |
|---|---|
| GPU | NVIDIA RTX 5090 (Blackwell, 32 GB VRAM) |
| CPU | AMD Ryzen 9 9950X3D |
| RAM | 64 GB |
| OS | Windows 11 |
| Python | 3.12 (portable embedded) |
| PyTorch | 2.8.0 + cu128 |
| ComfyUI | 0.19.x (frontend 1.42.x) |
| Attention | SageAttention 1.0.6 + triton-windows 3.6.0 |

## Quick start — for AI agents

Point your agent at `AGENTS.md` (Codex, generic OpenAI agents) or `CLAUDE.md` (Claude Code). Both files are identical and serve as the entry point. From there the agent will discover `skills/comfy_local/skill.md` and the 59 numbered reference docs.

Cursor and Windsurf already read `.cursorrules` and `.windsurfrules` from the repo root, both of which point at `AGENTS.md`.

## Quick start — for humans

1. Browse `skills/comfy_local/skill.md` for the full topic index.
2. Pick a model family doc (e.g. `skills/comfy_local/references/05_flux_family.md`).
3. Or grab a workflow JSON from `workflows/` and drag-drop it into the ComfyUI canvas.

## Running headless workflows

If you want to author runners that fire workflows at ComfyUI without touching the UI:

```powershell
# 1. Install the websocket-client into your portable Python
.\python_embeded\python.exe -m pip install websocket-client

# 2. Start ComfyUI as normal (with --use-sage-attention for Blackwell)

# 3. Start the watcher daemon
.\skills\comfy_local\start_watcher.bat

# 4. Run a runner
.\python_embeded\python.exe .\skills\comfy_local\runners\flux2_t2i.py "your prompt here"
```

Outputs land in `outputs_watched/` two folders up from the skill.

See `skills/comfy_local/SKILL_USAGE.md` for the full daemon walkthrough.

## Reference index

The `skills/comfy_local/references/` folder contains 59 numbered docs. The full table with descriptions is in `skills/comfy_local/skill.md`. Quick map:

| Range | Topic |
|---|---|
| 01–04 | Workstation, paths, model inventory |
| 05–08 | Flux / Qwen-Image / Wan video / other model families |
| 09–13 | Custom nodes, workflow JSON format, samplers, API, runner architecture |
| 14–17 | Authoring patterns, verification checklist, encoder pairings, compatibility |
| 18–25 | Example house-style framework (substitute your own) |
| 26–33 | Custom-node deep dives, Comfy Org templates, foundational concepts |
| 34–47 | Prompt templates, group conventions, runner catalog, internals, training |
| 48–58 | Civitai, Hugging Face, official repos, Kijai's repos, Pixaroma, video landscape, fal.ai |
| 59 | Comfy Cloud, Partner Nodes, Cloud API, Registry API |

## A note on the "example house-style" content

References 18 and 19 document a specific game-project visual style (chibi medieval fantasy with anthropomorphic animal characters, side-scrolling 2D, cel-shaded UI + painterly biomes). These are kept as concrete examples of how to encode a project's visual rules into reusable references that AI agents can read. **Substitute your own house style** when adapting this repo for your own work.

The runners under `skills/comfy_local/runners/` follow the same pattern — they bake the example house style into the prompts. Edit the prompt strings to match your project.

## License

This knowledge base is released under the MIT License (see `LICENSE`). The workflow JSONs in `workflows/` are unmodified content from the [Comfy Org canonical templates](https://github.com/Comfy-Org/workflow_templates) and remain under their original license.

## Contributing

This is a personal reference repo, but PRs that add new model families, fix factual errors, or extend the runner library are welcome. New reference docs should:

- Sit in `skills/comfy_local/references/` with a number prefix
- Use the existing frontmatter format (`name`, `description`, `type`)
- Be added to the master table in `skills/comfy_local/skill.md`
