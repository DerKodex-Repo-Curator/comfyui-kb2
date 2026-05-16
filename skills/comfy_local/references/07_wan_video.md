---
name: Wan video model family compatibility
description: Wan 2.1 video DiT family — t2v / i2v / vace / camera / animate / s2v / humo / scail variants, encoder, VAE, ComfyUI-WanVideoWrapper nodes
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
Wan 2.1 is the dominant open-weight video DiT (text-to-video, image-to-video, control variants) circa late 2025. ComfyUI core supports it via standard loaders OR via the much-richer **ComfyUI-WanVideoWrapper** custom node (kijai's wrapper, installed in Luis's setup).

## ComfyUI core's Wan support — model_type variants auto-detected

From `comfy/model_detection.py` (Wan 2.1 branch), the following sub-types are detected from state-dict keys:

| sub-type | Detected by key | Use case |
|---|---|---|
| `t2v` | (default Wan) | Text → video |
| `i2v` | `img_emb.proj.0.bias` | Image-conditioned → video |
| `vace` | `vace_patch_embedding.weight` | VACE — masked editing on video |
| `camera` / `camera_2.2` | `control_adapter.conv.weight` | Camera-control |
| `s2v` | `casual_audio_encoder.encoder.final_linear.weight` | Sound → video |
| `humo` | `audio_proj.audio_proj_glob_1.layer.bias` | Multimodal humans |
| `animate` | `face_adapter.fuser_blocks.0.k_norm.weight` | Face-swap / character animate |
| `scail` | `patch_embedding_pose.weight` | SCAIL pose-driven (custom node `ComfyUI-SCAIL-Pose` present) |

Plus first/last-frame mode detected via `flf_pos_embed_token_number`.

## Encoder + VAE

| Component | File |
|---|---|
| Text encoder | `text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors` (6.3 GB) | UMT5-XXL — Wan-specific, NOT regular T5 |
| CLIPLoader type | `wan` |
| VAE | `vae/wan_2.1_vae.safetensors` (243 MB) |

## ComfyUI-WanVideoWrapper (kijai's wrapper) — what it adds

Major node families (from the wrapper's NODE_CLASS_MAPPINGS):

- **Loading:** `WanVideoModelLoader`, `WanVideoVAELoader`, `WanVideoTextEncoder`
- **Encoding inputs:** `WanVideoEncode`, `WanVideoTextEncode`, `WanVideoTextEncodeCached`, `WanVideoTextEncodeSingle`, `WanVideoTextImageEncode`, `WanVideoImageToVideoEncode`, `WanVideoEncodeLatentBatch`, `WanVideoClipVisionEncode`
- **Embeds (model-specific add-ins):** `WanVideoAddBindweaveEmbeds`, `WanVideoAddControlEmbeds`, `WanVideoAddExtraLatent`, `WanVideoAddLucyEditLatents`, `WanVideoAddMTVMotion`, `WanVideoAddPusaNoise`, `WanVideoAddStandInLatent`, `WanVideoAddStoryMemLatents`, `WanVideoAddTTMLatents`, `WanVideoAnimateEmbeds`, `WanVideoApplyNAG`, `WanVideoControlEmbeds`, `WanVideoEmptyEmbeds`, `WanVideoMiniMaxRemoverEmbeds`, `WanVideoPhantomEmbeds`, `WanVideoRealisDanceLatents`, `WanVideoSVIProEmbeds`, `WanVideoUniLumosEmbeds`, `WanVideoVACEEncode`
- **Sampling and decoding:** `WanVideoSampler`, `WanVideoDecode`
- **Optimization:** `WanVideoSetBlockSwap` (offload blocks to CPU/RAM for huge models), `WanVideoSetRadialAttention`, `WanVideoEnhanceAVideo`, `WanVideoSLG`, `WanVideoFreeInitArgs`, `WanVideoLoopArgs`, `WanVideoExperimentalArgs`, `WanVideoBlockList`
- **Misc:** `TextImageEncodeQwenVL`, `WanVideoContextOptions`, `WanVideoRoPEFunction`

The wrapper also bundles support for related families: Ovi (`ovi.nodes_ovi`), HuMo, MTV, LongCat, FantasyPortrait, FantasyTalking, MultiTalk, RecamMaster, SkyReels, SteadyDancer, StandIn, Lynx, Mocha, Onetoall, Uni3C, UniAnimate, FlashVSR, ATI.

## Other companion custom nodes

- `ComfyUI-WanAnimatePreprocess` — preprocessing for Wan-Animate (face/pose extraction)
- `ComfyUI-SCAIL-Pose` — SCAIL pose driving for Wan
- `comfyui-videohelpersuite` — VHS for video I/O (`VHS_LoadVideo`, `VHS_VideoCombine`, `VHS_SplitImages`, etc.)
- `seedvr2_videoupscaler` — SeedVR2 video upscaling (uses sage attention; check status in startup log)

## VRAM strategy for Wan on a 32 GB 5090

Wan 2.1 14B at bf16 won't fit cleanly in 32 GB at long durations. Use `WanVideoSetBlockSwap` to offload N transformer blocks to CPU/RAM (Luis has 64 GB RAM with 25 GB pinned, plenty of headroom). Start with block_swap=20 and reduce if VRAM headroom allows.

## Models in Luis's install relevant to Wan

**Updated 2026-05-09:** Wan 2.1 t2v IS now downloaded.

| File | Path | Size |
|---|---|---|
| Wan 2.1 14B t2v fp8_scaled DiT | `G:\models\diffusion_models\wan2.1_t2v_14B_fp8_scaled.safetensors` | 14.3 GB |
| UMT5-XXL fp8 encoder | `G:\models\text_encoders\umt5_xxl_fp8_e4m3fn_scaled.safetensors` | 6.7 GB |
| UMT5-XXL fp16 encoder | `G:\models\text_encoders\umt5_xxl_fp16.safetensors` | 11.4 GB |
| Wan 2.1 VAE | `G:\models\vae\wan_2.1_vae.safetensors` | 243 MB |

A runner exists at `runners/wan_t2v.py` (kijai's WanVideoWrapper pipeline, 8 nodes). It defaults to 832x480 @ 49 frames, 30 steps, cfg=6.0, shift=5.0, scheduler=unipc, bf16+fp8_e4m3fn_scaled. Output goes to `ComfyUI/output/Wan/<prefix>_NN.mp4` via VHS_VideoCombine.

**Still NOT installed:** Wan 2.1 i2v / VACE / Camera / Animate / S2V / HuMo / SCAIL DiT files. These would need separate downloads if Luis wants them. Only the t2v base model is present.

## Verification before delivering a Wan workflow

1. Wan DiT exists in `G:\models\diffusion_models\` — currently NONE PRESENT, will need download
2. Encoder = `umt5_xxl_fp8_e4m3fn_scaled.safetensors` with type `wan`
3. VAE = `wan_2.1_vae.safetensors`
4. Use `ComfyUI-WanVideoWrapper` nodes (richer than core) unless user specifically wants core
5. Plan for block-swap on long durations
6. Frame count, fps, and resolution have hard VRAM costs — start low (e.g., 49 frames @ 480p) and scale up

---

## Real-world VRAM and tuning numbers (from kijai's README + node source, 2026-05-09)

### WanVideoSampler canonical defaults

```
steps        = 30
cfg          = 6.0
shift        = 5.0
scheduler    = unipc
seed         = 0..2^64-1
force_offload = True   (move model off GPU between samples — saves VRAM, costs time)
riflex_freq_index = 0  (disabled; set to 6 to allow new frames after looping)
```

Optional pipeline injection points: `feta_args`, `context_options` (for long videos via sliding window), `cache_args` (TeaCache), `slg_args`, `batched_cfg`, `rope_function` (`comfy` is faster, supports torch.compile; `chunked` reduces peak VRAM).

### WanVideoBlockSwap defaults

```
blocks_to_swap   = 20    # of 40 blocks for 14B (so half the model lives on CPU)
offload_img_emb  = False
offload_txt_emb  = False
vace_blocks_to_swap = 0  # only relevant for VACE variant (15 blocks total)
prefetch_blocks  = 0     # 1 is usually enough to offset speed loss; debug-confirm for your system
use_non_blocking = False # True is faster but uses more RAM
```

Block counts per model variant:
- **14B** = 40 blocks
- **1.3B / 5B** = 30 blocks
- **LongCat-Video** = 48 blocks

### Block-swap math (when adding LoRAs)

From kijai's README: "1GB unmerged LoRA, 20 blocks swapped on 14B model. We can divide the LoRA size by block count → single block grows by 25 MB → 20 blocks grow by 500 MB. So your VRAM usage would be 500 MB more than before. To compensate: swap 2 more blocks."

Formula: `extra_vram_used = (lora_size_GB * blocks_swapped) / total_blocks`
- 1 GB LoRA × 20 swapped / 40 total = 500 MB extra
- To recover those 500 MB: swap 2 more blocks (each block ≈ lora_size/40 = 25 MB × the blocks swapped delta)

### Empirical data points kijai posted

| Test | Resolution × Frames | VRAM | Time | Notes |
|---|---|---|---|---|
| First test | 512×512 × 81 frames | ~16 GB | — | 14B model with 20/40 blocks offloaded |
| Long video w/ context | 1025 frames @ window 81 / overlap 16 | <5 GB | 10 min | **1.3B** T2V model on a **5090** |

The second one is striking: 5090 + 1.3B + sliding context window = 1025 frames in 10 minutes for under 5 GB VRAM. The 14B at full quality is the slower / VRAM-heavier path.

### Recommended starting points for Luis's RTX 5090 (32 GB)

| Goal | Settings | Notes |
|---|---|---|
| Default short clip (3s) | 832×480 × 49f, 30 steps, cfg=6, shift=5, unipc | Fits without block_swap. Runner default. |
| Higher quality short | 1024×576 × 49f, 30 steps, fp8_scaled DiT, no block_swap | Should fit on 5090; if OOM, set block_swap=10 |
| Long clip (~10s) | 832×480 × 161f, 30 steps, **block_swap=20**, cache_args=TeaCache | The 14B + 161 frames pushes VRAM; offload half. |
| Very long via context | 832×480 × 481f+, **context_options** with window=81, overlap=16, block_swap=20 | Sliding window — stays VRAM-bounded. Add 1–2 blocks for prefetch trade. |
| Quick draft | 480×288 × 33f, 15 steps, cfg=4, shift=3 | Fast iteration / prompt testing |

Caveats:
- The fp8_scaled DiT Luis has (`wan2.1_t2v_14B_fp8_scaled.safetensors`) is the recommended quantization. Don't load bf16 unless you have specific reasons — it costs significantly more VRAM.
- TeaCache (`cache_args`) gives ~2× speedup at minor quality loss; thresholds 0.25–0.30 are good with the new coefficients (the README notes the new version's threshold is **10× higher** than the old WIP version).
- SageAttention is already on globally via the `--use-sage-attention` startup flag, which Wan benefits from. No need for `WanVideoSetRadialAttention` unless trying alternative modes.
- `rope_function=comfy` (the default) supports torch.compile if you enable it; `chunked` is the lower-peak-VRAM alternative.

### When to add WanVideoSetBlockSwap to a runner

The current `runners/wan_t2v.py` does NOT include block_swap (per its TODO comment). Add it when:
- Pushing past 49 frames at 832×480, OR
- Going to 1024+ resolution at any frame count, OR
- Stacking unmerged LoRAs that bloat the in-VRAM model

Pattern (API format):

```python
"blockswap": {
    "class_type": "WanVideoBlockSwap",
    "inputs": {"blocks_to_swap": 20, "offload_img_emb": False, "offload_txt_emb": False},
    "_meta": {"title": "Block Swap (20/40)"},
},
"blockswap_apply": {
    "class_type": "WanVideoSetBlockSwap",
    "inputs": {"model": ["model_loader_node_id", 0], "block_swap_args": ["blockswap", 0]},
    "_meta": {"title": "Apply Block Swap"},
},
# then route blockswap_apply.0 -> WanVideoSampler.model
```

### Triton-cache gotcha (Windows-specific)

After updating WanVideoWrapper or torch.compile-related deps, first run can OOM dramatically. Fix: clear Triton caches:
- `C:\Users\<username>\.triton`
- `C:\Users\<username>\AppData\Local\Temp\torchinductor_<username>`

Then re-run; once cached, the issue doesn't recur.

### Other patches available in WanVideoWrapper (not yet exercised)

- `WanVideoSetRadialAttention` — alternative attention modes (sdpa, flash_attn_2/3, sageattn, sparse_sage_attention) per-block.
- `WanVideoVRAMManagement` (`offload_percent`) — DiffSynth-Studio style aggressive offload, more memory savings but slower than block_swap.
- `WanVideoTorchCompileSettings` — enable `torch.compile` with mode (default / max-autotune / reduce-overhead). The 5090 + cu128 + Sage stack benefits significantly when first-run compile cost is amortized over many generations.
