---
name: ComfyUI REST API and headless workflow submission
description: ComfyUI runs a REST API on localhost:8188. Use it to query node schemas, list available models/loras, submit workflows headlessly, and verify execution. Massive verification upgrade over disk-walk-only.
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
ComfyUI exposes a full REST API on `http://localhost:8188` whenever it's running. This is a much better source of truth than `ls G:\models\<dir>` because it reflects what ComfyUI actually sees (extra_model_paths.yaml resolved, custom node loaders' file lists, etc).

**Source of this knowledge:** purzbeats's `comfy_local` skill at https://github.com/purzbeats/lora_tester/blob/master/.claude/skills/comfy_local/skill.md

## Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/prompt` | POST | Submit a workflow in API format (`{"prompt": {...}}`). Returns `{prompt_id, number, node_errors}`. |
| `/queue` | GET | Current queue status. |
| `/history/{prompt_id}` | GET | Get job result/status. Returns `{outputs, status, error}` once done. |
| `/object_info` | GET | List all available node types. |
| `/object_info/{NodeType}` | GET | Get a node's INPUT_TYPES, returns the live list of available checkpoints/loras/vaes/etc. |
| `/view?filename=X&type=output` | GET | Download an output file. Type can be `output`, `input`, `temp`. |
| `/upload/image` | POST | Upload an input image (multipart/form-data). |
| `/system_stats` | GET | GPU, VRAM, ComfyUI version, frontend version. |
| `/embeddings` | GET | List installed embeddings. |
| `/extensions` | GET | Frontend extension list. |

## Discovering models/loras live (preferred over disk walk)

```bash
# Available diffusion_models (UNETLoader)
curl -s http://localhost:8188/object_info/UNETLoader | python -c "
import json,sys; d=json.load(sys.stdin)
for m in d['UNETLoader']['input']['required']['unet_name'][0]: print(m)"

# Available checkpoints
curl -s http://localhost:8188/object_info/CheckpointLoaderSimple | python -c "
import json,sys; d=json.load(sys.stdin)
for m in d['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]: print(m)"

# Available loras (with subfolder paths)
curl -s http://localhost:8188/object_info/LoraLoader | python -c "
import json,sys; d=json.load(sys.stdin)
for l in d['LoraLoader']['input']['required']['lora_name'][0]: print(l)"

# Available CLIP/text encoders
curl -s http://localhost:8188/object_info/CLIPLoader | python -c "
import json,sys; d=json.load(sys.stdin)
for c in d['CLIPLoader']['input']['required']['clip_name'][0]: print(c)"

# Available VAEs
curl -s http://localhost:8188/object_info/VAELoader | python -c "
import json,sys; d=json.load(sys.stdin)
for v in d['VAELoader']['input']['required']['vae_name'][0]: print(v)"
```

Same pattern for `ControlNetLoader`, `LatentUpscaleModelLoader`, `UpscaleModelLoader`, `StyleModelLoader`, `NunchakuFluxDiTLoader`, `UnetLoaderGGUF`, etc. Custom node loaders show up too.

## API format (different from graph/frontend format)

API format is what `/prompt` accepts. Flat dict keyed by string node ID. Each node has `class_type` and `inputs`. References to other nodes use `["node_id_string", output_index]`.

```json
{
  "prompt": {
    "1": {
      "class_type": "UNETLoader",
      "inputs": {
        "unet_name": "flux2_dev_fp8mixed.safetensors",
        "weight_dtype": "default"
      }
    },
    "2": {
      "class_type": "CLIPLoader",
      "inputs": {
        "clip_name": "mistral_3_small_flux2_fp8.safetensors",
        "type": "flux2",
        "device": "default"
      }
    },
    "9": {
      "class_type": "KSampler",
      "inputs": {
        "model": ["1", 0],
        "positive": ["5", 0],
        "negative": ["7", 0],
        "latent_image": ["8", 0],
        "seed": 42,
        "steps": 20,
        "cfg": 1.0,
        "sampler_name": "euler",
        "scheduler": "simple",
        "denoise": 1.0
      }
    }
  }
}
```

**Differences from graph format:**
- Flat dict keyed by string ID (not array of node objects)
- `inputs` is a dict (not separate inputs array + widgets_values)
- All inputs (widget values AND node references) are mixed into the same `inputs` dict — the format figures out which is which
- Node references are 2-tuples `[node_id_string, slot_index]`
- No `pos`, `size`, `links`, `groups` — that's all UI metadata

**Save BOTH formats:**
- `name_workflow.json` — graph format for UI (drag-and-drop)
- `name_workflow-api.json` — API format for headless submission

## Submitting a workflow

```python
import json, urllib.request

prompt = { ... }  # API format dict

payload = json.dumps({"prompt": prompt}).encode("utf-8")
req = urllib.request.Request("http://localhost:8188/prompt",
                              data=payload,
                              headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
# result = {"prompt_id": "...", "number": 1, "node_errors": {...}}
```

**bash heredoc gotcha:** avoid single quotes inside Python heredocs — break the heredoc. Write a `.py` file and run it instead.

## Polling for completion

```python
import time, urllib.request, json

prompt_id = result["prompt_id"]
deadline = time.time() + 240  # 4 min for images, 1800 for video
while time.time() < deadline:
    h = json.loads(urllib.request.urlopen(f"http://localhost:8188/history/{prompt_id}").read())
    if prompt_id in h:
        record = h[prompt_id]
        if record.get("status", {}).get("completed"):
            print("done. outputs:", record["outputs"])
            break
        if record.get("status", {}).get("status_str") == "error":
            print("error:", record["status"])
            break
    time.sleep(2)
```

## Batch generation pattern

For many prompts: submit all up front, then poll in a single loop. Models load once and stay cached.

```python
prompt_ids = []
for i, text in enumerate(prompts):
    wf = build_workflow(text=text, seed=42+i, prefix=f"{date}_{slug(text)}")
    r = submit(wf)
    prompt_ids.append((r["prompt_id"], slug(text)))

completed = set()
while len(completed) < len(prompt_ids):
    for pid, name in prompt_ids:
        if pid in completed: continue
        h = check_history(pid)
        if h.get("status", {}).get("completed"):
            completed.add(pid)
    time.sleep(3)
    if len(completed) % 20 == 0: print(f"  {len(completed)}/{len(prompt_ids)}")
```

Use `"control_after_generate": "fixed"` and pass explicit `seed` per prompt — NOT `"randomize"` — for reproducible batches.

## Verification upgrade — what to do BEFORE saying "done"

Old approach: validate JSON, check filenames on disk.
New approach: also submit the workflow to ComfyUI's `/prompt` endpoint with a 1-step KSampler test (or just submit and accept the "queued, no node errors" response as confirmation). The API will return `node_errors` immediately if anything's wrong with the workflow structure or referenced files.

```python
# Dry-run validation: submit and check immediate response
r = submit(workflow_api)
if r.get("node_errors"):
    print("BAD:", r["node_errors"])
else:
    print("Workflow accepted, prompt_id =", r["prompt_id"])
    # optionally cancel before it actually runs:
    urllib.request.Request("http://localhost:8188/queue",
                            data=json.dumps({"delete": [r["prompt_id"]]}).encode(),
                            method="POST")
```

## Common gotcha: API input names vs graph widget order

Graph format uses positional `widgets_values` arrays. API format uses named `inputs` dict. The names must match the node's `INPUT_TYPES` keys exactly — sometimes they differ from the visual labels in the UI. When in doubt, query `/object_info/{NodeType}` to see exact key names.

Examples Purz called out where template names ≠ API names:
- `ResizeImageMaskNode`: use `resize_type.crop` (not `crop`), `scale_method` (not `interpolation`)
- `LTXVPreprocess`: use `img_compression` (not `num_latent_frames`)
- `LTXVImgToVideoInplace`: use `strength` (not `image_denoise_strength`)

This is exactly the kind of thing `/object_info/{NodeType}` is for.

## Output file naming convention

Use `YYYYMMDD_descriptive-slug` for `filename_prefix` in SaveImage. ComfyUI auto-appends `_00001_` etc. For video: `video/YYYYMMDD_descriptive-slug` to nest in a video subfolder.

## Reference repos

- **Comfy-Org workflow templates:** https://github.com/Comfy-Org/workflow_templates/tree/main/templates — official source-of-truth workflow JSONs from the Comfy team. Mix and match for new workflow types.
- **Purz's lora_tester skill:** https://github.com/purzbeats/lora_tester/blob/master/.claude/skills/comfy_local/skill.md — the source of much of this doc.
