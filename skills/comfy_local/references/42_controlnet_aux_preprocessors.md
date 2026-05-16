---
name: ControlNet aux preprocessors — what each one detects and which ControlNet to pair
description: Catalog of comfyui_controlnet_aux preprocessors (canny, depth, lineart, openpose/dwpose, normal, segmentation, etc.) with the canonical ControlNet model each pairs with. Source: comfyui_controlnet_aux/README.md + node_wrappers/.
type: reference
---

# ControlNet aux preprocessors

The `comfyui_controlnet_aux` pack is the standard preprocessor library — it converts an input image into the conditioning map (edges, depth, pose, etc.) that a ControlNet model expects. This reference is a quick "which preprocessor for which ControlNet."

**Source:** `custom_nodes/comfyui_controlnet_aux/` (README + node_wrappers/).

## How preprocessing fits into a ControlNet workflow

```
Input image
   ↓
[ControlNet aux preprocessor]  ← e.g. CannyEdge, DepthAnythingV2, DWPose
   ↓
Hint image (a different visual representation: edges, depth map, pose skeleton, etc.)
   ↓
[ControlNetLoader] → [ControlNetApplyAdvanced(positive, negative, control_net, hint_image, strength, start, end)]
   ↓
Modified positive + negative conditioning → KSampler
```

The preprocessor node and the ControlNet model must match — Canny edges only work with a Canny-trained ControlNet, depth only with depth ControlNet, etc.

## Line extractors

| Preprocessor node | Output type | Pair with (ControlNet/T2I-Adapter) |
|---|---|---|
| `BinaryPreprocessor` | Binary edges | `control_scribble` |
| `CannyEdgePreprocessor` | Canny edges | `control_v11p_sd15_canny`, `control_canny`, `t2iadapter_canny` |
| `HEDPreprocessor` | Soft edges (HED) | `control_v11p_sd15_softedge`, `control_hed` |
| `LineartStandardPreprocessor` | Standard lineart | `control_v11p_sd15_lineart` |
| `LineArtPreprocessor` | Realistic lineart (or coarse mode) | `control_v11p_sd15_lineart` |
| `AnimeLineArtPreprocessor` | Anime lineart | `control_v11p_sd15s2_lineart_anime` |
| `Manga2Anime_LineArt_Preprocessor` | Manga lineart denoise | `control_v11p_sd15s2_lineart_anime` |
| `M-LSDPreprocessor` | M-LSD straight lines (architecture) | `control_v11p_sd15_mlsd`, `control_mlsd` |
| `PiDiNetPreprocessor` | PiDiNet soft edges | `control_v11p_sd15_softedge`, `control_scribble` |
| `ScribblePreprocessor` | Scribble lines | `control_v11p_sd15_scribble`, `control_scribble` |
| `ScribbleXDoG_Preprocessor` | Scribble XDoG | `control_v11p_sd15_scribble`, `control_scribble` |
| `Scribble_HED_Preprocessor` | Fake scribble (HED-based) | `control_v11p_sd15_scribble`, `control_scribble` |
| `TEED_Preprocessor` | TEED soft edges | SDXL: `controlnet-sd-xl-1.0-softedge-dexined`; SD1.5: `control_v11p_sd15_softedge` |
| `Scribble_PiDiNet_Preprocessor` | Scribble PiDiNet | `control_v11p_sd15_scribble`, `control_scribble` |
| `AnyLineArtPreprocessor_aux` | AnyLine | `mistoLine_fp16.safetensors`, `mistoLine_rank256`, `control_v11p_sd15s2_lineart_anime`, `control_v11p_sd15_lineart` |
| `PyraCannyPreprocessor` | Pyramid Canny (Fooocus-style) | Canny ControlNet variants |

**Practical defaults:** `CannyEdgePreprocessor` for hard structural lines (architecture, mechanical). `LineArtPreprocessor` for character/illustration. `AnimeLineArtPreprocessor` for Pony/anime checkpoints.

## Normal and depth estimators

| Preprocessor | Output | Pair with |
|---|---|---|
| `MiDaS-DepthMapPreprocessor` | MiDaS depth | `control_v11f1p_sd15_depth`, `control_depth`, `t2iadapter_depth` |
| `LeReS-DepthMapPreprocessor` | LeReS depth (often more accurate than MiDaS for foreground) | same depth ControlNets |
| `Zoe-DepthMapPreprocessor` | Zoe depth (mid-quality, fast) | same |
| `Depth_Anything_Preprocessor` | Depth Anything (V1) | depth ControlNet |
| `DepthAnythingV2Preprocessor` | Depth Anything V2 (newer, recommended) | depth ControlNet |
| `Zoe_DepthAnythingPreprocessor` | Zoe + DepthAnything encoder hybrid | depth ControlNet |
| `Metric3D-DepthMapPreprocessor` | Metric3D depth (metric scale) | `control_v11f1p_sd15_depth`, `control_depth`, `t2iadapter_depth` |
| `MiDaS-NormalMapPreprocessor` | MiDaS normal map | `control_normal` |
| `BAE-NormalMapPreprocessor` | BAE normal (recommended) | `control_v11p_sd15_normalbae` |
| `DSINE-NormalMapPreprocessor` | DSINE normal | `control_normal`, `control_v11p_sd15_normalbae` |
| `Metric3D-NormalMapPreprocessor` | Metric3D normal | `control_v11p_sd15_normalbae` |
| `MeshGraphormer-DepthMapPreprocessor` | Hand-refined depth (HandRefinder) | `control_sd15_inpaint_depth_hand_fp16` (specialized for fixing broken hands) |

**Practical defaults:** `DepthAnythingV2Preprocessor` is the modern choice for general depth (single best preprocessor). `BAE-NormalMapPreprocessor` for normals. Use `MeshGraphormer-DepthMapPreprocessor` SPECIFICALLY for hand fix workflows paired with HandRefinder ControlNet.

## Faces and poses

| Preprocessor | Output | Pair with |
|---|---|---|
| `DWPreprocessor` | DWPose body+hand+face skeleton (recommended over OpenPose) | `control_v11p_sd15_openpose`, `control_openpose`, `t2iadapter_openpose` |
| `OpenposePreprocessor` | OpenPose skeleton (configurable: body / +hand / faceonly / full) | same OpenPose ControlNets |
| `MediaPipe-FaceMeshPreprocessor` | MediaPipe face mesh (468 landmarks) | `controlnet_sd21_laion_face_v2` |
| `AnimalPosePreprocessor` | Animal pose skeleton | `control_sd15_animal_openpose_fp16` |
| `DenseposePreprocessor` | Densepose (dense surface coords) | DensePose-trained ControlNets |

**Practical defaults:** `DWPreprocessor` (DWPose) is universally recommended over OpenPose — better quality, especially for hand keypoints. The OpenPose-format JSON output is also useful for animation rigging.

## Semantic segmentation

| Preprocessor | Output | Pair with |
|---|---|---|
| `OneFormer-ADE20K-SemSegPreprocessor` | ADE20K class segmentation | `control_v11p_sd15_seg` |
| `OneFormer-COCO-SemSegPreprocessor` | COCO class segmentation | `control_v11p_sd15_seg` |
| `UniFormer-SemSegPreprocessor` | UniFormer segmentation | `control_sd15_seg`, `control_v11p_sd15_seg` |
| `AnimeFace_SemSegPreprocessor` | Anime face segmentation (face / hair / clothes regions) | Specialized anime segmentation ControlNets |
| `SAMPreprocessor` (or via Segment Anything node) | SAM mask | Mask-based ControlNets / inpainting |

## T2IAdapter-only (older but still useful)

| Preprocessor | Output | Pair with |
|---|---|---|
| `ColorPreprocessor` | Color palette swatches | `t2iadapter_color` |
| `ShufflePreprocessor` | Content shuffle (for style transfer) | `t2iadapter_style` |

## Recolor

| Preprocessor | Output |
|---|---|
| `ImageLuminanceDetector` | Luminance/grayscale extraction (for recolor controlnets) |
| `ImageIntensityDetector` | Intensity (different formula) |

## Tile / utility

| Preprocessor | Output |
|---|---|
| `TilePreprocessor` | Tile preview (for tiled diffusion / tiled ControlNet) |
| `InpaintPreprocessor` | Inpaint mask preprocessing (for inpaint ControlNets) |

## Optical flow (video)

| Preprocessor | Output | Pair with |
|---|---|---|
| `Unimatch_OptFlowPreprocessor` | Optical flow between frames | DragNUWA-style video ControlNet |

## How to get pose-format JSON for animation use

When using `DWPreprocessor` or `OpenposePreprocessor`:
- Add the `Save Pose Keypoints` node downstream (saves JSON to ComfyUI/output)
- Or read `/history/<prompt_id>` and look in the node's `output.openpose_json` field
- Format matches CMU-OpenPose's standard JSON

This is what feeds animation pipelines (DWPose → JSON → re-render at higher res, or pose-edit then back into AnimateDiff).

## Resolution input

Almost all preprocessors take a `resolution` int input (default 512). This is the **internal processing resolution** — output is resized back to source dimensions. Increase to 768 or 1024 for sharper hint images on high-res inputs; doesn't affect VRAM much.

## When the preprocessor matters more than the ControlNet

For SD1.5/SDXL workflows, the preprocessor often matters more than which ControlNet variant you pick. Going from `MiDaS-DepthMapPreprocessor` to `DepthAnythingV2Preprocessor` while keeping the same SD1.5 depth ControlNet usually gives a bigger quality jump than swapping ControlNets at fixed preprocessor.

## ControlNets that need the same model for multiple input types

Newer "Union" ControlNets (e.g. Flux Union ControlNet, Z-Image-Turbo-Fun-Controlnet-Union) accept multiple hint types (canny, depth, pose, etc.) through a single model. Use `SetUnionControlNetType` (ref 40) downstream of `ControlNetLoader` to tell it which hint type the upcoming hint image represents.

## Quick reach-for-this guide

| Goal | Preprocessor + ControlNet |
|---|---|
| "Match composition exactly, free interpretation" | Canny + canny ControlNet |
| "Soft structure cue" | HED or PiDiNet + softedge ControlNet |
| "Match depth structure (foreground / midground / background)" | DepthAnythingV2 + depth ControlNet |
| "Match scene normals" | BAE + normalbae ControlNet |
| "Match pose / character action" | DWPose + openpose ControlNet |
| "Fix broken hand in img2img" | MeshGraphormer + HandRefinder ControlNet |
| "Match line drawing exactly" | LineArt or AnimeLineArt + lineart ControlNet |
| "Match architectural straight lines (rooms, exteriors)" | M-LSD + mlsd ControlNet |
| "Match color palette only" | ColorPreprocessor + t2iadapter_color |
| "Match scribble for sketch-to-image" | Scribble + scribble ControlNet |
| "Match face landmarks for portrait pose" | MediaPipe-FaceMesh + face ControlNet |
| "Match animal pose" | AnimalPose + animal_openpose ControlNet |
| "Match semantic regions (sky, building, person)" | OneFormer-ADE20K + seg ControlNet |
| "Tiled high-res with content preservation" | TilePreprocessor + tile ControlNet |

## Implication for runner authoring

For Luis's game art workflows (cel-shaded characters, painterly biomes), the most relevant preprocessors are:

- **DWPose** — nail down character poses in cel-shaded character runners
- **CannyEdge / LineArt** — preserve composition when iterating on style
- **DepthAnythingV2** — stable foreground/background separation in biome compositions
- **MeshGraphormer** — fix broken hands in any cel-shaded character output

When authoring a `runners/character_cel_shaded.py` with pose control, the canonical chain would be:

```
LoadImage(pose_reference) → DWPreprocessor → ControlNetApplyAdvanced
                                                ↓
                                            (positive, negative)
                                                ↓
                                            KSampler ...
```

For Z-Image-Turbo workflows specifically, the model patches in `model_patches/` (e.g. `Z-Image-Turbo-Fun-Controlnet-Union.safetensors`) take a hint image directly — different wiring, but the preprocessor stays the same (DWPose for pose, DepthAnythingV2 for depth, etc.).
