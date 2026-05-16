---
name: ComfyUI key paths and shared models folder
description: Where Luis's ComfyUI install, launcher, workflows, and shared models live on disk
type: reference
---
Luis runs a portable ComfyUI install. Key paths:

- **ComfyUI root:** `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\ComfyUI\`
- **Launcher:** `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\Start ComfyUI.bat` (currently launches with `--use-sage-attention`)
- **Embedded Python:** `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\python_embeded\python.exe`
- **User workflows folder:** `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\ComfyUI\user\default\workflows\` — save new workflow JSONs here so they show up in the ComfyUI workflow browser.
- **Shared models folder:** `G:\models\` — used across multiple ComfyUI versions (wired up via `extra_model_paths.yaml` with `base_path: G:\`). Always verify model filenames against `G:\models\<subfolder>\` rather than `ComfyUI\models\<subfolder>\` (which only has placeholder files).
- **Startup log:** `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\ComfyUI\user\comfyui.log` — read this to confirm GPU, VRAM, attention backend, and import errors.
- **API:** `http://localhost:8188` REST + `ws://localhost:8188/ws` WebSocket
- **Skill canonical location:** `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\.claude\skills\comfy_local\`
