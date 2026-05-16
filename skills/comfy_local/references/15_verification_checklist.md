---
name: Pre-delivery workflow verification checklist
description: Run through this checklist before declaring any ComfyUI workflow done. Catches the failure modes Luis has hit before.
type: feedback
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
Before saying "this workflow is ready" to Luis, run through every applicable item below. If any fails, fix and re-verify.

**Why:** Luis explicitly asked for compatibility-checked workflows. Past failures (e.g., Klein 4B + Mistral encoder mismatch causing `mat1 mat2 shape (15360 vs 7680)` error at sampling time) traced to skipping these checks.

## 1. JSON validity

- [ ] File parses with `json.load()` cleanly
- [ ] If writing through Windows path with Write/Edit tool truncated, rewrite via `python3 json.dump` in bash through `/sessions/.../mnt/...` path instead. (Past quirk: large JSON writes through host Write tool occasionally got cut mid-stream.)

## 2. Link consistency

For every link `[lid, src, sslot, tgt, tslot, type]`:
- [ ] `src` and `tgt` node ids exist
- [ ] `src` has output slot `sslot`; `tgt` has input slot `tslot`
- [ ] `outputs[sslot].type == inputs[tslot].type`
- [ ] `lid` appears in source's `outputs[sslot].links` array (NOT just the single-output case — multi-fanout requires explicit listing)
- [ ] `lid` equals target's `inputs[tslot].link` field
- [ ] `last_link_id >= max(lid)` and `last_node_id >= max(node_id)`

## 3. File existence on disk

For every loader node (UNETLoader / CheckpointLoaderSimple / CLIPLoader / DualCLIPLoader / VAELoader / LoraLoader / ControlNetLoader / UpscaleModelLoader / NunchakuFluxDiTLoader / etc.):
- [ ] The filename in `widgets_values` exists in the corresponding `G:\models\<subfolder>\` (use bash `/sessions/affectionate-happy-ritchie/mnt/models/...` to check)
- [ ] If a path-prefix is in the filename (e.g., `FLUX1/flux1-schnell.safetensors`), the nested file exists

## 4. Encoder ↔ DiT family pairing (the #1 source of runtime errors)

- [ ] **Flux 2 dev** ↔ `mistral_3_small_flux2_*.safetensors` (NOT Qwen3)
- [ ] **Flux 2 Klein 4B** ↔ `qwen_3_4b.safetensors` (NOT Mistral, NOT Qwen3-8B)
- [ ] **Flux 2 Klein 9B** ↔ `qwen_3_8b_fp8mixed.safetensors`
- [ ] **Flux.1 (any)** ↔ DualCLIPLoader with `clip_l.safetensors` + `t5xxl_*.safetensors`, type `flux`
- [ ] **Qwen-Image (any)** ↔ `qwen_2.5_vl_7b*.safetensors`, type `qwen_image`
- [ ] **Wan video** ↔ `umt5_xxl_fp8_e4m3fn_scaled.safetensors`, type `wan`
- [ ] **Z-Image** ↔ `qwen_3_4b.safetensors`
- [ ] **SDXL/SD1.5** ↔ encoders bundled in checkpoint (CheckpointLoaderSimple) OR explicit CLIP-L+CLIP-G/T5

Symptom of mismatch: `mat1 and mat2 shapes cannot be multiplied (Bx<TE_dim>x and <DiT_in_dim>xH)` at `forward_orig: txt = self.txt_in(txt)`.

## 5. VAE family pairing

- [ ] **Flux 2** → `flux2-vae.safetensors`
- [ ] **Flux.1** → `ae.safetensors` or `flux_kontext_ae.safetensors`
- [ ] **Qwen-Image** → `qwen_image_vae.safetensors`
- [ ] **Qwen-Image Layered** → `qwen_image_layered_vae.safetensors` (different!)
- [ ] **Wan** → `wan_2.1_vae.safetensors`
- [ ] **Z-Image** → `qwen_image_vae.safetensors` works
- [ ] **SDXL** → bundled in checkpoint OR `vae-ft-mse-840000-ema-pruned.safetensors`

## 6. Latent shape

- [ ] **Flux 2** → `EmptyFlux2LatentImage` (128-ch, /16 spatial). DO NOT use EmptySD3LatentImage.
- [ ] **Flux.1 / Qwen-Image** → `EmptyLatentImage` or `EmptySD3LatentImage` (16-ch)
- [ ] **SDXL/SD1.5** → `EmptyLatentImage` (4-ch, /8 spatial)
- [ ] Width/height multiples are valid (Flux: ≥256, /16; SDXL: /8)

## 7. Sampler / scheduler / cfg

- [ ] Distilled models (schnell, Krea, Kontext, Flux 2 dev, Klein, Lightning Qwen variants, Z-Image turbo, hyperNF4) → cfg=1
- [ ] Non-distilled → cfg 3-7 typical
- [ ] Steps match model: schnell/Lightning 4-step → 4 steps, 8-step → 8, distilled dev → 12-20, non-distilled → 20-30
- [ ] If using Flux2Scheduler, the width/height widgets must MATCH EmptyFlux2LatentImage's width/height
- [ ] Sampler choice exists in `comfy.samplers.SAMPLER_NAMES` (don't invent names)

## 8. Custom node availability

- [ ] If workflow uses non-core nodes, the package is in `G:\ComfyUI_Nunchaku_Portable_V3\ComfyUI-Easy-Install\ComfyUI\custom_nodes\` (don't reference nodes from packages not installed)
- [ ] Currently broken packages to avoid until fixed: `comfyui-easy-sam3` (Triton dep — may now work after the SageAttention install)

## 9. VRAM budget against Luis's 32 GB ceiling

Rough envelope (model + encoder + VAE + activations + gradient — but only forward at inference):
- DiT bf16 takes ≈ param count × 2 bytes
- DiT fp8 takes ≈ param count × 1 byte
- DiT GGUF Q8 ≈ × 1 byte; Q4 ≈ × 0.5 byte
- Encoder is offloaded after encoding (only resident during conditioning)
- Activations scale with batch size and resolution

If the resident model (DiT alone) exceeds ~28 GB, plan for `WanVideoSetBlockSwap` or recommend a smaller quant.

## 10. Workflow loads & runs in ComfyUI (final pre-flight)

If the user is about to actually run it (not just save it):
- [ ] No deprecated node types that ComfyUI 0.19.3 will warn or fail on (e.g., Nunchaku PuLID v1 → use V2)
- [ ] If any custom node has a known issue (rgthree-comfy says "incompatible with Node 2.0 rendering" — note this for the user)

## When in doubt

Run a Python validator over the JSON. The validator I've used:

```python
nodes = {n['id']: n for n in w['nodes']}
errs = []
for link in w['links']:
    lid, src, sslot, tgt, tslot, ltype = link
    so = nodes[src]['outputs'][sslot]
    ti = nodes[tgt]['inputs'][tslot]
    if so['type'] != ti['type']: errs.append(f"link {lid}: type mismatch")
    if lid not in (so.get('links') or []): errs.append(f"link {lid}: missing on src")
    if ti.get('link') != lid: errs.append(f"link {lid}: missing on tgt")
```

Plus an `os.path.exists` check on every loader filename.
