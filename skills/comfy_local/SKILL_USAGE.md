# comfy_local skill

Headless ComfyUI driver for Luis's RTX 5090 Windows install. Both Claude Code (CLI, run from this folder) and Claude in Cowork mode (via the workspace mount) read this skill and the references in `references/`.

## Architecture

**Tier 1 — Runner script (one-shot):** `runners/<name>.py` builds an API-format workflow dict and POSTs it to `http://localhost:8188/prompt`. Prints `prompt_id` and exits.

**Tier 2 — Watcher daemon (persistent):** `watcher.py` holds a WebSocket to `ws://localhost:8188/ws`, listens for `executed` events, downloads outputs to `../../outputs_watched/`, dedupes via `state/downloaded.txt`.

```
.claude\skills\comfy_local\
├── skill.md                       # Entry point — both Claudes read this first
├── README.md                      # This file
├── watcher.py                     # The persistent WebSocket daemon
├── runner_template.py             # Boilerplate for new runners
├── start_watcher.bat              # Launch the watcher in background
├── stop_watcher.bat               # Stop it
├── runners/
│   └── flux2_t2i.py               # First concrete runner: Flux 2 dev text-to-image
├── workflows/                     # Saved workflow JSONs (graph + API formats)
├── state/                         # Watcher PID, log, dedupe ledger
└── references/                    # 17 model/family/pattern docs
```

Outputs land in: `..\..\outputs_watched\` (two levels up from this skill — i.e., `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\outputs_watched\`).

## First-time setup

### 1. Install Claude Code (if you want full Maciej-style autonomy)

```powershell
# Install Node.js first (https://nodejs.org), then:
npm install -g @anthropic-ai/claude-code

# Open a terminal in the ComfyUI-Easy-Install folder:
cd G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install
claude
```

Claude Code will read `CLAUDE.md` (project root) and discover `.claude\skills\comfy_local\skill.md` as the active skill.

### 2. Install websocket-client into the portable Python

The watcher needs it. `start_watcher.bat` will auto-install it on first run, but you can also do it manually:

```powershell
.\python_embeded\python.exe -m pip install websocket-client
```

### 3. Start ComfyUI

Use the desktop shortcut, or `Start ComfyUI.bat` (which already launches with `--use-sage-attention`).

### 4. Start the watcher

Double-click `start_watcher.bat` — runs in the background, writes PID to `state\watcher.pid`. Verify it connected by tailing `state\watcher.log`.

## Daily use

### From Claude Code (full autonomy)

Tell Claude what you want. It writes a runner (or reuses `runners/flux2_t2i.py`), invokes it via Bash, and lets the watcher do the rest. You'll see PNGs / MP4s appear in `outputs_watched/`.

### From Cowork (split responsibility)

I (Claude in Cowork) author the runner. You run it from PowerShell:

```powershell
.\python_embeded\python.exe .\.claude\skills\comfy_local\runners\flux2_t2i.py "your prompt here"
```

Outputs land in `outputs_watched/` and I can read them via the workspace mount.

## Adding a new runner

1. Copy `runner_template.py` to `runners/<your_name>.py`
2. Replace the `build_workflow(...)` function with your specific node graph (in API format — see `references/12_comfyui_api.md` for the format)
3. Verify all referenced files exist in `G:\models\<subfolder>\` (or via `curl localhost:8188/object_info/<Loader>`)
4. Cross-check encoder/VAE pairings — see `references/16_flux2_encoder_pairing.md` and `references/15_verification_checklist.md`
5. Test with a tiny step-count first (`steps=2`) to validate the graph before doing a full run

## Stopping cleanly

Double-click `stop_watcher.bat`. It reads `state\watcher.pid`, kills the process, removes the PID file.

## When something breaks

- **Watcher not connecting** → check ComfyUI is running on `localhost:8188` (open `http://localhost:8188` in browser), check `state\watcher.log` for connection errors
- **`/prompt` rejected** → response includes `node_errors` dict telling you which node + which input failed validation. Most common cause: filename in a loader that doesn't exist on disk.
- **`mat1/mat2 shape mismatch` at sampling time** → encoder/DiT mismatch. See `references/16_flux2_encoder_pairing.md`.
- **Output is incoherent / washed out** → cfg too high for a distilled model (Flux 2, Klein, schnell, Lightning, Z-Image turbo all need cfg=1).

## Reference docs

See `references/` for the full knowledge base. Start with `01_workstation.md` and `02_paths.md` for context, then dive into the model family doc relevant to your task.
