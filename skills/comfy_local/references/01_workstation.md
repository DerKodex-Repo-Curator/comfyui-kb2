---
name: ComfyUI workstation specs
description: Hardware, software stack, and known compatibility constraints of Luis's ComfyUI rig — relevant when designing any workflow
type: project
---
Workstation profile (confirmed from ComfyUI startup log on 2026-05-08):

- **GPU:** NVIDIA RTX 5090 (Blackwell, sm_120, 32 GB VRAM, ~30 GB free at idle)
- **CPU:** AMD Ryzen 9 9950X3D (16-core)
- **RAM:** 64 GB (25 GB pinned for offload)
- **OS:** Windows 11, NVIDIA driver 596.36
- **Python:** 3.12.10 (portable embedded at `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\python_embeded\`)
- **PyTorch:** 2.8.0 + cu128 (NOT cu130 — `comfy_kitchen` CUDA backend is disabled as a result; NVFP4 models like `flux-2-klein-4b-nvfp4.safetensors` won't get FP4 acceleration until a cu130 upgrade)
- **ComfyUI:** 0.19.3 (frontend 1.42.14)
- **Attention:** SageAttention 1.0.6 + triton-windows 3.6.0 enabled via `--use-sage-attention` flag in `Start ComfyUI.bat` (confirmed working on 2026-05-08). FlashAttention NOT installed.
- **Nunchaku:** installed but only supports Flux.1 / Qwen-Image / Z-Image — NOT Flux 2.

**Why:** built up over multiple back-and-forths to verify what's actually present vs. what the install advertises.

**How to apply:** when designing workflows, prefer fp8 variants over nvfp4 (until cu130). For 32 GB VRAM, Flux 2 dev fp8mixed + mistral fp8 fits with offload. Klein-9B/4B is the speed/lightweight pick. Don't suggest Nunchaku DiT loaders for Flux 2.
