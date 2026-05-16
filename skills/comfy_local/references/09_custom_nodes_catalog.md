---
name: Custom node catalog — what each installed package provides
description: Index of Luis's 47 installed ComfyUI custom node packages, grouped by purpose. Reach-for-which-tool guide.
type: reference
originSessionId: 936ef488-094e-4ea2-a742-2e5e5977f157
---
Luis's `custom_nodes/` has ~47 installed packages. Below is grouped by purpose with the key node families each provides.

## Workflow utilities (USE FIRST — these have the most leverage)

### `comfyui-kjnodes` (kijai's swiss army — 232 nodes)
Math/state: `BOOLConstant`, `FloatConstant`, `INTConstant`, `CheckpointLoaderKJ`, `DiffusionModelLoaderKJ`, `GGUFLoaderKJ`, `DiffusionModelSelector`. Image ops: `GetImageSize*`, `GetImageRangeFromBatch`, `ColorMatch`, `ColorMatchV2`, `CreateGradientFromCoords`, `CreateShape*`, `CrossFadeImages`, `BatchCropFromMask*`, `BatchUncrop*`. Sampling: `CustomSigmas`, `FlipSigmasAdjusted`, `FloatToSigmas`, `EmptyLatentImagePresets`, `EmptyLatentImageCustomPresets`. Animation: `CreateFadeMask`, `CreateMagicMask`, `CreateShapeMaskOnPath`, `CreateTextOnPath`, `CutAndDragOnPath`, `GenerateNoise`, `RifleXRoPE`. Conditioning: `ConditioningSetMaskAndCombine{,3,4,5}`, `ConditioningMultiCombine`, `CFGZeroStarAndInit`, `DifferentialDiffusionAdvanced`. **Default reach for**: utility math, masks-on-path, sigma manipulation, batch image ops.

### `rgthree-comfy`
Reroute, fast bypass, Power LoRA Loader (multi-LoRA in one node), Image Comparer, Power Prompt, Context (state container), KSampler (rgthree variant), seed control. Reach for: visually clean workflows with shared state, Power LoRA Loader for stacking many LoRAs.

### `cg-use-everywhere`
The "Anything Everywhere" / "Use Everywhere" pattern — define once, reference everywhere without explicit links. Reduces visual link spaghetti. Reach for: large workflows where MODEL/CLIP/VAE need to fan out to many nodes.

### `comfyui_essentials` (cubiq — `+` suffix on every node)
~62 nodes. Image: `ImageCrop+`, `ImageResize+`, `ImageComposite+`, `ImageColorMatch+`, `ImageHistogramMatch+`, `ImageDesaturate+`, `ImageRemoveBackground+`, `ImageTile+/Untile+`, `DrawText+`, `ImagePosterize+`. Mask: `MaskBlur+`, `MaskExpandBatch+`, `MaskFromColor+`, `MaskFromSegmentation+`, `MaskBoundingBox+`. Sampling: `KSamplerVariationsStochastic+`, `KSamplerVariationsWithNoise+`, `FluxSamplerParams+`, `InjectLatentNoise+`. Bg removal: `RemBGSession+`, `TransparentBGSession+`. SD3/Flux helpers: `CLIPTextEncodeSDXL+`, `SD3NegativeConditioning+`, `SDXLEmptyLatentSizePicker+`. Reach for: reliable image utilities (sharper than was-ns).

### `was-node-suite-comfyui` (W.A.S. — 214 nodes)
Massive grab-bag. Image filters galore (`Image Bloom Filter`, `Image Chromatic Aberration`, `Image Dragan Photography Filter`, `Image Lucy Sharpen`, `Image Pixelate`, `Image Power Noise`, `Image Perlin Noise`), batch ops, BLIP analysis (`BLIP Analyze Image`, `BLIP Model Loader`), conditioning input switches, palette extraction, grid creation, video from path, history-based loaders. Reach for: legacy compatibility, BLIP captioning, advanced filters.

### `comfyui-inspire-pack`
Extensive: regional prompting (`RegionalSampler`), prompt scheduling, FaceID variants (Kolors FaceID Plus, SDXL FaceID, SDXL Plus Composition, ViT-H), wildcard / lora-tag inline expansion (`LoraTagLoader`), background removal, schedulers, sampler customization. Reach for: regional prompts, FaceID flows, wildcard processing.

### `comfyui-impact-pack` (~250+ nodes)
Detailers/segmentation: `FaceDetailer`, `MaskDetailerPipe`, `DetailerForEach{,Pipe,SDXL}`, `SAMLoader`, `SAMDetectorCombined`, `BboxDetectorSEGS`, `SegmDetectorSEGS`, `MediaPipeFaceMeshToSEGS`, `ImpactSAM2VideoDetectorSEGS`. SEGS pipeline (segment → filter → process → paste): `MaskToSEGS`, `SEGSDetailer`, `SEGSPaste`, `SEGSPicker`, `SEGSLabelFilter`, `ImpactSEGSNMSFilter`. Logic: `ImpactConditionalBranch`, `ImpactSwitch`, `ImpactInversedSwitch`, `ImpactQueueTrigger`, `ImpactValueSender/Receiver`. Sampling: `KSamplerProvider`, `TwoSamplersForMask`, `TiledKSamplerProvider`, `RegionalPrompt`, `RegionalSampler`. Hooks/wildcards: `ImpactWildcardEncode`, `ImpactWildcardProcessor`. Reach for: face/hand detail fixes, region-based sampling, complex pipeline logic.

### `ComfyUI-Easy-Use` (~200 nodes, all prefixed `easy `)
Loader simplifiers: `easy a1111Loader`, `easy comfyLoader`, `easy fluxLoader`, `easy fullLoader`, `easy fullkSampler`, `easy hiresFix`, `easy detailerFix`. ControlNet: `easy controlnetLoader`, `easy controlnetLoaderADV`, `easy controlnetStack`. Cache management: `easy cleanGpuUsed`, `easy clearCacheAll`, `easy clearCacheKey`. Image utilities: `easy imageColorMatch`, `easy imageInsetCrop`, `easy imageRemBg`, `easy imageScaleDownBy`. Inpaint: `easy applyBrushNet`, `easy applyFooocusInpaint`, `easy applyInpaint`. Reach for: condensed pipelines, less node sprawl.

### `controlaltai-nodes`
Flux-specific: `FluxResolutionNode` (preset Flux-friendly resolutions), `FluxSampler`, `FluxControlNetApply`, `FluxUnionControlNetApply`, `FluxAttentionControl`, `FluxAttentionCleanup`. HiDream: `HiDreamResolutionNode`. Region masks: `RegionMaskGenerator/Conditioning/Processor/Validator/Visualizer`. Switches: `TwoWaySwitch`, `ThreeWaySwitch`. Reach for: Flux ControlNet workflows, region conditioning.

### `efficiency-nodes-comfyui`
`Efficient Loader` (combined model+vae+clip+lora load), `LoRA Stacker`, `Control Net Stacker`, `XY Plot`, `HighRes-Fix Script`, `Tiled Upscaler Script`. Reach for: XY plot variations, classical hi-res fix.

### `comfyui-mxtoolkit`
Math expression nodes (`mxFormula`, `mxBoolean`, etc.). Reach for: parametric workflows.

### `ComfyLiterals`
Type literals (`Int`, `Float`, `String`, `KepStringLiteral`) — convert widget primitives into node outputs. Reach for: clean parameter pipes.

### `ComfyUI-Chibi-Nodes`
`Loader`, `SimpleSampler`, `Prompts`, `ImageTool`, `Wildcards`, `LoadEmbedding`. Reach for: simple beginner-style pipelines.

## Quantization / format loaders

### `ComfyUI-GGUF`
`UnetLoaderGGUF`, `UnetLoaderGGUFAdvanced`, `CLIPLoaderGGUF`, `DualCLIPLoaderGGUF`, `TripleCLIPLoaderGGUF`, `QuadrupleCLIPLoaderGGUF`. Reach for: any GGUF model file.

### `ComfyUI-nunchaku`
`NunchakuFluxDiTLoader`, `NunchakuQwenImageDiTLoader`, `NunchakuTextEncoderLoader`, `NunchakuTextEncoderLoaderV2`, `NunchakuFluxLoraLoader`, `NunchakuFluxLoraStack`, `NunchakuFluxIPAdapterApply`, `NunchakuIPAdapterLoader`, `NunchakuFluxPuLIDApplyV2`, `NunchakuPuLIDLoaderV2`, `NunchakuModelMerger`, `NunchakuDepthPreprocessor`. Supports Flux.1 / Qwen-Image / Z-Image SVDQ models. Does NOT support Flux 2 / Klein.

## Video & motion

### `ComfyUI-WanVideoWrapper`
The dominant Wan video toolkit. See `reference_wan_video.md` for full node breakdown. Hosts WAN, Ovi, HuMo, MTV, LongCat, FantasyPortrait, FantasyTalking, MultiTalk, RecamMaster, SkyReels, SteadyDancer, StandIn, Lynx, Mocha, Onetoall, Uni3C, UniAnimate, FlashVSR, ATI sub-modules.

### `ComfyUI-WanAnimatePreprocess`
Face/pose preprocessing for Wan-Animate.

### `ComfyUI-SCAIL-Pose`
SCAIL pose-driven Wan animation.

### `comfyui-videohelpersuite` (VHS)
Video I/O: `VHS_LoadVideo`, `VHS_VideoCombine`, `VHS_SplitImages`, `VHS_LoadAudio`, `VHS_VideoInfo`, etc. Reach for: any video I/O.

### `seedvr2_videoupscaler`
SeedVR2 video super-resolution. Uses sage attention if available.

### `teacache`
TeaCache: caches transformer block outputs across timesteps for ~1.5-2× speedup. Nodes: `CompileModel`, `TeaCache`. Reach for: speedup any Flux/Wan/Qwen sampling.

## ControlNet & conditioning

### `comfyui_controlnet_aux`
The standard ControlNet preprocessor pack: canny, depth (Zoe, Midas, DepthAnything), pose (DWPose, OpenPose), normal, lineart, scribble, MLSD, soft-edge (HED, PiDi), seg (anime, ufade20k), tile preprocessing. Reach for: any ControlNet input prep.

### `comfyui_layerstyle`
LayerStyle pack: image effects, color adjustment, layer composition.

## Inpainting / segmentation

### `comfyui-inpaint-cropandstitch`
`InpaintCropImproved`, `InpaintStitchImproved`. The clean way to inpaint at high resolution by cropping the masked area, processing it independently, then stitching back.

### `comfyui-easy-sam3`
SAM 3 segmentation. **Currently broken** in install — fails on `import triton`. Triton-windows install (already done) should fix on next ComfyUI restart.

### `comfyui-rmbg` & `comfyui-inspyrenet-rembg`
Background removal: `InspyrenetRembg`, `InspyrenetRembgAdvanced`. Reach for: clean alpha extraction.

## LoRA management

### `comfyui-lora-manager`
LoRA browser, metadata fetcher (Civitai integration), preview thumbnails. Manages the 966 LoRAs in `G:\models\loras\`. The `.metadata.json` files come from this tool.

## Captioning / text

### `ComfyUI-JoyCaption`
JoyCaption-Alpha-Two image captioning (uses `models/joy-caption-alpha-two/` dir).

### `ComfyUI-QwenVL`
Qwen-VL image-to-text and Qwen-Image prompt enhancement.

### `comfyui-qwenmultiangle`
Qwen-VL-driven multi-angle generation.

### `comfyui-itools` (~21 nodes)
Prompt builder/styler/saver/loader, image overlay, checker/grid utilities, regex node, vae preview. Reach for: prompt engineering.

## Upscaling

### `comfyui_ultimatesdupscale`
Ultimate SD Upscale (tile-based hi-res with seam fixing). Uses `controlnet_v11p_sd15_tile` for SD 1.5 hi-res.

### `ComfyUI-TiledDiffusion`
Tiled Diffusion + Tiled VAE for high-resolution generation. Wraps KSampler internally (visible in stack traces — `ComfyUI-TiledDiffusion/utils.py:KSampler_sample`).

## Special-purpose

### `nano_banana_direct_pkg`, `nanobanana_multilayer`, `nanobanana_style_transfer`
Nano-Banana (Google) image generation/edit/style transfer via API. Has `NanoBananaMultiLayerScene`, `NanoBananaStyleTransfer` etc. Existing user workflow `POP_Cel_Shaded_Nano_Banana_Pro.json`.

### `comfyui_openai_gpt_image2_node`
OpenAI GPT-Image API node.

### `vnccs` & `vnccs-utils`
VNCCS (Visual Novel Character Creation System): `VNCCS_PositionControl`, `VNCCS_VisualPositionControl`, `VNCCS_QWEN_Detailer`, `VNCCS_BBox_Extractor`, `VNCCS_ModelManager`, `VNCCS_ModelSelector`, `VNCCS_PoseStudio`. Existing user workflows `VNCCS_Utils Pose Studio (3/4).json`.

### `ComfyUI-Crystools`
System monitor (CPU/GPU/RAM live in workflow), node metrics, performance utilities.

### `ComfyUI-MelBandRoFormer`
Mel-band RoFormer audio source separation.

### `ComfyUI-Manager`
THE manager — install/update/disable custom nodes. Don't recommend running update commands without user approval (can break things).

## How to apply

When designing a workflow, ask: "is there an existing custom node that does this cleanly?" before plumbing it from primitives. Power LoRA Loader (rgthree) > 5 chained LoraLoaders. FaceDetailer (impact-pack) > manual mask + KSampler chain. easy fullLoader (Easy-Use) > separate Checkpoint + VAE + LoRA loaders.

When the user says "use a custom node," prefer (in order): rgthree, comfyui_essentials, comfyui-kjnodes, easy-use, impact-pack, inspire-pack — based on what's most applicable.
