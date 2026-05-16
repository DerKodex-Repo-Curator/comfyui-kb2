---
name: Flux 2 family encoder pairings
description: Which text encoder file pairs with which Flux 2 diffusion model — mismatching them causes a mat1/mat2 shape error
type: reference
---
Flux 2 dev and Flux 2 Klein use DIFFERENT text encoders, even though both use CLIPLoader type `flux2`. ComfyUI auto-detects the encoder arch from the file content and routes to either `flux2_te` (Mistral) or `klein_te` (Qwen3) — but you have to give it the correct file.

| Diffusion model | Required text encoder | Encoder arch | Conditioning dim |
|---|---|---|---|
| `flux2-dev.safetensors`, `flux2_dev_fp8mixed.safetensors` | `mistral_3_small_flux2_fp8.safetensors` or `_bf16.safetensors` | Mistral 3 (pruned to 30 layers) | 15360 (5120 × 3) |
| `flux-2-klein-4b-*.safetensors` | `qwen_3_4b.safetensors` | Qwen3-4B | 7680 |
| `flux-2-klein-9b-*.safetensors`, `flux-2-klein-base-9b-*.safetensors` | `qwen_3_8b_fp8mixed.safetensors` | Qwen3-8B | larger |

**Symptom of mismatch:** `RuntimeError: mat1 and mat2 shapes cannot be multiplied (Bx15360 and 7680xH)` (or the inverse). The traceback ends in `comfy/ldm/flux/model.py: txt = self.txt_in(txt)`.

**Source:** `comfy/text_encoders/flux.py` (Flux2TEModel, KleinTokenizer, klein_te factory) and `comfy/sd.py` around line 1456-1472 where TEModel detection routes to the right encoder loader.
