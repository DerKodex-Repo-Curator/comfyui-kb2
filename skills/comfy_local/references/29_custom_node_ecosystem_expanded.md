---
name: Custom node ecosystem — expanded landscape (rgthree, kjnodes, WanVideoWrapper, Easy-Use)
description: Findings from reading the canonical README files of Luis's most-used custom node packages. Discovered powerful nodes I hadn't fully indexed before — rgthree Power Puter, KJNodes Set/Get + WidgetToString, Easy-Use's deep integration list, WanVideoWrapper's 20+ video model coverage.
type: reference
---

**Source:** Web fetched 2026-05-09 from each package's GitHub README. This expands `references/09_custom_nodes_catalog.md` and `references/26_custom_node_deep_dives.md` with the bigger picture from each maintainer's own description.

## rgthree-comfy — much more than just Power Lora Loader

Complete node list (some highlighted in 26):

**Workflow utility:**
- **Seed** — A1111-style seed control. `-1` = random each time. `-2` = increment last. `-3` = decrement.
- **Reroute** — improved with multi-direction, sizing, toggleable resizability and title display.
- **Bookmark (🔖)** — place anywhere on screen, jump to it via shortcut key. Multi-key shortcuts supported (`alt + shift + !`).
- **Label** — purely visual floating label. Multiline text via `\n`, custom font/color/background, can be pinned to make clicks pass through.
- **Display Any** — display ANY data type as text after execution.

**Pipe / state passing:**
- **Context / Context Big** — pipe nodes that pass workflow state. Backwards compatible with each other. Pro tip: drag Context output over a node and **hold ctrl + release** to auto-connect all matching outputs.
- **Context Switch / Context Switch Big** — choose first non-null Context input. KEY for branching workflows.
- **Any Switch** — same as Context Switch but for arbitrary types.

**Smart logic / control flow (advanced):**
- **Mute / Bypass Repeater** — dispatches mute/bypass/active mode to all connected nodes (or to all nodes in its group if no inputs). Pair with **Fast Muter / Fast Bypasser** for one-click control of many nodes.
- **Mute / Bypass Relay** — when input nodes change mode, relay sends signal to a connected Repeater. Configurable inverse logic.
- **Random Unmuter** — randomly unmute one of N muted inputs at queue time. Useful for randomized branch selection.

**Group operations:**
- **Fast Groups Muter / Fast Groups Bypasser** — auto-collects all groups in workflow, exposes mute/bypass toggles. Properties: `matchColors`, `matchTitle`, `showNav`, `sort` (alphanumeric/position/custom), `customSortAlphabet`, `toggleRestriction` (max one / always one).

**Prompts:**
- **Power Prompt** — like a String primitive but with embedding/lora dropdowns. If model is connected, parses `<lora:...>` tags automatically (no separate LoraLoader needed).
- **Power Prompt - Simple** — same minus LoRA support (negatives).
- **SDXL Power Prompt - Positive / Simple** — SDXL-specific (text_g + text_l).
- **SDXL Config** — SDXL prompting config helper.

**Lora:**
- **Power Lora Loader** — already documented in ref 26. Stack any number of LoRAs with on/off toggles. `Show Strengths` property toggles between simple and advanced (model + clip strengths separately).

**Primitives:**
- **Power Primitive** — outputs STRING/INT/FLOAT/BOOLEAN. Auto-casts when input is connected. Type can be hidden from menu or fast-switched.
- **Power Puter** — **THE killer node.** Mini Python in a node:
  - Multi-line code parsing
  - Outputs INT/FLOAT/STRING/BOOLEAN
  - Can target other nodes by ID. Example: `[v.lora for v in node(5).inputs.values() if 'lora' in v and v.on]` — gets enabled LoRAs from node #5
  - Image dimension access: `a.shape[2]` for width
  - Math operations: `a + b`, `ceil(1 / 2)`
  - List comprehensions for advanced workflows

**Image:**
- **Image Comparer** — A/B slider/click compare. `comparer_mode` property: "Slide" or "Click". Right-click image options apply to image_a (left half) or image_b (right half).
- **Image Inset Crop** — crop by pixel value or percentage.

**Action:**
- **Fast Actions Button** — click button to mute/bypass/enable connected nodes. Some nodes (like Seed) expose extra actions (Randomize, Use Last). Configurable shortcut key.

**The "muting works backwards" insight (CRITICAL):**

> When a workflow is processed, it *first moves backwards* starting at each "Output Node" (Preview Image, Save Image, Display String etc.) and walks back to all paths leading there.

So muting an output node stops the whole upstream branch from running. **Context Switch + Fast Muter** is the canonical pattern for branching workflows: feed multiple Context inputs (from different "branches"), Switch chooses first non-null, mute the one you don't want via Fast Muter — that branch's nodes won't execute (saving GPU). This is more efficient than `select` switches that still run all branches.

**rgthree extras (workflow improvements):**
- **Progress Bar** along the top of the app window with queue size, current progress, multi-step node progress.
- **"Queue Selected Output Nodes"** in right-click menu — execute just one output's path.
- **Auto-Nest Subdirectories** in long combos (Load Checkpoint, etc.) — off by default, enable in settings.
- **Quick Mute/Bypass Toggles** in group headers — off by default.
- **Import Individual Node Widgets** drag/drop — override widgets from a previous generation's image without changing the whole workflow.
- **"Copy Image"** in right-click menu (graduated to ComfyUI core).
- **Link Fixer** at `http://127.0.0.1:8188/rgthree/link_fixer` — drop in a workflow with broken links to repair.

## KJNodes (kijai) — quality-of-life utilities

**Repo:** `https://github.com/kijai/ComfyUI-KJNodes` (2.4k stars, GPL-3.0).

The maintainer admits: "I'm bad at documentation... grown from random practice nodes to too many lines in one file." But individual nodes have a `?` icon for in-app help.

**Highlights from README:**

**JS feature:**
- `browserstatus.js` — favicon turns red while processing, green when idle, shows progress %. Off by default.

**Set / Get nodes:**
- Visual state passing — set a value with a string key, get it elsewhere. Reduces visual link clutter.
- Right-click → visualize paths or jump to corresponding node.
- **Limitations:** doesn't work with dynamic-output nodes (reroute, other Set/Get), doesn't work with bypassed nodes, possible JS conflicts.

**Mask operations:**
- **ColorToMask** — RGB color value to mask, batch + AnimateDiff support.
- **GrowMaskWithBlur** — grow/shrink (negative values shrink) + blur. Returns mask + inverted mask.
- **RoundMask** — rounds mask edges.

**Conditioning:**
- **ConditioningMultiCombine** — combine N conditions in one node.
- **ConditioningSetMaskAndCombine** — mask + combine.

**WidgetToString — IMPORTANT:**
- Outputs the value of a widget on ANY node as a string
- Setup: enable "Node ID display" in Manager → get target node's ID → use that ID + widget name in WidgetToString
- **Caveat:** recreating or reloading the target node changes its ID, breaking the link. Update the ID after such changes.
- **Use case:** read a seed from elsewhere, read a checkpoint name into a save filename, read a sampler setting into a markdown note.

This is similar to rgthree's Power Puter `node(N)` mechanism — but more limited (just widget value, not full Python).

**Other (catalogued in ref 26 already):** ImageBatchMulti, ImageResizeKJv2, ModelSamplingAuraFlow shifts, PathchSageAttentionKJ.

## ComfyUI-WanVideoWrapper (kijai) — the video model SANDBOX

**Repo:** `https://github.com/kijai/ComfyUI-WanVideoWrapper` (6.1k stars, Apache 2.0).

**The maintainer's own framing:** "Personal sandbox to play with new video models. Standalone wrapper makes it easier to implement new models than going through ComfyUI core. Goal isn't to compete with native, just to enable testing things relatively quickly. Use native unless using a feature only available here."

**Models / techniques wrapped (full list from README):**

| Model | Source |
|---|---|
| WanAnimate (Wan 2.2 character animation) | `Wan-Video/Wan2.2/wan/modules/animate` |
| ReCamMaster | `KwaiVGI/ReCamMaster` |
| SkyReels v2 | `Skywork/skyreels-v2` |
| WanVideoFun v1.1 | `alibaba-pai/wan21-fun-v11` |
| VACE | `ali-vilab/VACE` |
| Phantom | `bytedance-research/Phantom` |
| ATI | `bytedance-research/ATI` |
| Uni3C | `alibaba-damo-academy/Uni3C` |
| MiniMaxRemover | `zibojia/minimax-remover` |
| MAGREF | `MAGREF-Video/MAGREF` |
| FantasyTalking | `Fantasy-AMAP/fantasy-talking` |
| FantasyPortrait | `Fantasy-AMAP/fantasy-portrait` |
| MultiTalk | `MeiGen-AI/MultiTalk` |
| EchoShot | `D2I-ai/EchoShot` |
| Stand-In | `WeChatCV/Stand-In` |
| HuMo | `Phantom-video/HuMo` |
| Lynx | `bytedance/lynx` |
| MoCha | `Orange-3DV-Team/MoCha` |
| UniLumos | `alibaba-damo-academy/Lumos-Custom` |
| Bindweave | `bytedance/BindWeave` |
| TimeToMove (training-free) | `time-to-move/TTM` |
| SteadyDancer (training-free) | `MCG-NJU/SteadyDancer` |
| One-to-all-Animation (training-free) | `ssj9596/One-to-All-Animation` |
| SCAIL (training-free) | `zai-org/SCAIL` |
| LongCat-Video | `meituan-longcat/LongCat-Video` |
| TeaCache (caching for speedup) | included |

**Recommended model source:** `https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled` (FP8 scaled, kijai's recommendation).

**Memory tactics:**
- Block swap (offload N transformer blocks to CPU/RAM) is the main VRAM savings tool
- Recent change: unmerged LoRA weights are now buffers attached to model blocks (better for torch.compile, async offloading, swappable)
- Side effect: if you don't use block swap, LoRAs increase VRAM usage. Compensate by swapping +2 blocks per ~1GB LoRA on a 14B model.
- After updates, may need to clear Triton cache: `C:\Users\<user>\.triton` and `C:\Users\<user>\AppData\Local\Temp\torchinductor_<user>`

**Native ComfyUI loaders work too:** the wrapper accepts text encoding and clip vision from ComfyUI's standard loaders — you don't have to use the wrapper's own.

**GGUF supported** in the main model loader.

**Examples shown in README:** WanAnimate, ReCamMaster, TeaCache, Context window (1025 frames at 81-frame windows with 16-frame overlap, used <5GB VRAM on 5090, 10 min for 1.3B T2V), Vid2vid (1.3B and 14B variants), 512×512×81 baseline (~16GB used, 20/40 blocks offloaded).

## ComfyUI-Easy-Use (yolain) — heavy integration package

**Repo:** `https://github.com/yolain/ComfyUI-Easy-Use` (2.3k stars, GPL-3.0). Built on TinyTerraNodes.

**What it is:** integration / optimization wrapper around 20+ other custom packages. Reduces workflow complexity through "pipe nodes" + simplified loaders.

**Major integrated features:**

- **Loaders:** `easy a1111Loader`, `easy comfyLoader`, `easy fluxLoader`, `easy fullLoader`, `easy hunyuanDiTLoader`, `easy pixArtLoader`, `easy cascadeLoader`, `easy zero123Loader`, `easy svdLoader`, `easy dynamiCrafterLoader`, `easy kolorsLoader`
- **Wildcards + LoRA Block Weight** (requires `ComfyUI-Inspire-Pack`)
- **Style selector:** Fooocus-style JSON, customizable, samples folder for previews
- **A1111 prompt mode** — replicates webui generation faithfully (requires `ComfyUI_smZNodes`)
- **Noise injection:** `easy latentNoisy` or `easy preSamplingNoiseIn`
- **Simplified flows:** SD1.x/SD2.x/SDXL, SVD, Zero123, Stable Cascade, Layer Diffuse, InstantID, Kolors, SD3, Flux
- **Logic nodes:** for/while loops (`easy forLoopStart` / `easy forLoopEnd`), if/else (`easy ifElse`), batchAny, anythingIndexSwitch
- **XYPlot:** `easy XYPlot` and `easy XYPlotAdvanced` with `easy XYInputs: Sampler/Scheduler/ControlNet/Lora/Checkpoint/PromptSR/ModelMergeBlocks` etc.
- **Background removal:** `easy imageRemBg` with BriaAI RMBG-1.4, RMBG-2.0, ben2, inspyrenet
- **Inpainting:** `easy applyBrushNet`, `easy applyPowerPaint`, `easy applyFooocusInpaint`, `easy applyInpaint`
- **IPAdapter:** `easy ipadapterApply`, `easy ipadapterApplyADV`, `easy ipadapterApplyEncoder`, `easy ipadapterApplyEmbeds`, `easy ipadapterApplyRegional`, `easy ipadapterApplyFromParams`, `easy ipadapterStyleComposition`, `easy ipadapterApplyFaceIDKolors`. Multiple presets including "REGULAR - FLUX and SD3.5 only" for InstantX Flux IPAdapter.
- **Face migration:** `easy instantIDApply`, `easy instantIDApplyADV`, `easy pulIDApply`, `easy pulIDApplyADV`
- **Detail fix:** `easy preDetailerFix`, `easy DetailerFix`, `easy ultralyticsDetectorPipe`, `easy samLoaderPipe`, `easy preMaskDetailerFix`
- **Pipe utilities:** `easy pipein`, `easy pipeout`, `easy pipeEdit`, `easy pipeToBasicPipe`
- **Light/shadow:** `easy icLightApply` (IC-Light integration)
- **Style aligned:** `easy styleAlignedBatchAlign`
- **Image utilities:** `easy imageColorMatch`, `easy imageInterrogator` (image→prompt), `easy imageRemBg`, `easy makeImageForICLora`, `easy imageSplitTiles`, `easy imageTilesFromBatch`, `easy imageSplitGrid`, `easy imagesSplitimage`, `easy imageCount`, `easy imageChooser`
- **Save:** `easy imageSave` (with date/format formatting), `easy saveImageLazy`, `easy saveText`
- **Cleanup:** `easy cleanGpuUsed`, `easy clearCacheAll`, `easy clearCacheKey`
- **External APIs:** `easy stableDiffusion3API`, `easy joycaption3API`
- **Schedulers:** GITS, alignYourSteps in scheduler widgets
- **AlignedYourSteps preset** integrated

**Right-click menu enhancements:**
- View checkpoint and lora information from any loader
- Quick replace nodes of the same type
- Auto-nest subdirectories in long combos (settings toggle)

**Keyboard shortcuts:**
- **Alt+1 to Alt+9** — paste node presets for templates 1-9

**Companion repo:** `https://github.com/yolain/ComfyUI-Yolain-Workflows` — collection of working example workflows using these nodes.

**Active development:** v1.3.6 released Jan 2026, frequent updates.

## ComfyUI_essentials (cubiq) — MAINTENANCE ONLY

**Repo:** `https://github.com/cubiq/ComfyUI_essentials` (1.1k stars, MIT).

**Critical status note (April 2025):** maintainer has stepped away from ComfyUI as primary tool. Repo is now **maintenance-only** — crucial fixes/PRs may merge, but no new feature work planned.

What's there is solid (see ref 26 for the node list — `+` suffix on every name). The ImageResize+, MaskBlur+, FluxSamplerParams+, KSamplerVariationsStochastic+ etc. all still work fine. Just don't expect new nodes from this package going forward.

## Summary table — when to reach for which package

| Need | Reach for |
|---|---|
| Stack many LoRAs with toggles | rgthree Power Lora Loader |
| Read a widget value programmatically | rgthree Power Puter (full Python) OR kjnodes WidgetToString (just widget value) |
| Branch a workflow without re-running both branches | rgthree Context Switch + Fast Muter |
| Visual A/B image compare | rgthree Image Comparer |
| Toggle a group of nodes via shortcut | rgthree Fast Groups Muter + Bookmark |
| Random branch selection per queue | rgthree Random Unmuter |
| Pass state across canvas without spaghetti | kjnodes Set/Get Node OR rgthree Context |
| Multi-image batch (>2 images) | kjnodes ImageBatchMulti |
| Sigma shift for AuraFlow models | kjnodes ModelSamplingAuraFlow |
| Image resize with crop/pad/stretch + GPU | kjnodes ImageResizeKJv2 |
| Sage attention dial in workflow | kjnodes PathchSageAttentionKJ |
| Wan video / character animation | WanVideoWrapper (kijai) — sandbox of 20+ video models |
| Simplified all-in-one model loader | Easy-Use easy fullLoader |
| LoRA block weight | Easy-Use (requires Inspire-Pack) |
| A1111-equivalent webui generation | Easy-Use a1111Loader (requires smZNodes) |
| For loops / if-else logic | Easy-Use easy forLoopStart/End / ifElse |
| Stable Cascade / Zero123 / SVD / DynamiCrafter / Kolors | Easy-Use easy*Loader |
| Background removal (BriaAI, ben2, inspyrenet) | Easy-Use easy imageRemBg |
| Inpainting (BrushNet/PowerPaint/Fooocus) | Easy-Use easy apply* |
| IPAdapter / InstantID / PuLID | Easy-Use easy ipadapterApply / instantIDApply / pulIDApply |
| Detail fix (FaceDetailer) | Easy-Use easy DetailerFix (or directly Impact-Pack) |
| Image filters (legacy / batch) | was-node-suite (already cataloged) |
| Image utilities (cubiq's collection) | comfyui_essentials (MAINTENANCE only — no new features) |

## How runners should apply these

Most of these are UI-organization / control-flow nodes (rgthree Context, Switches, Muters, kjnodes Set/Get). For headless API-format runners, **prefer direct links over named state passing** — direct links are more verifiable. Use Set/Get / Context only when adapting an existing template that already uses them.

For runners that need to dispatch one prompt to N models or N variations, the **N-parallel pattern** (ref 20) is still the right approach — N copies of the inference branch in one workflow, each with its own seed.

For LoRA stacking in runners, use **rgthree Power Lora Loader** (already documented in ref 26) — the API format kwargs pattern is `LORA_1: {"on": true, "lora": "name.safetensors", "strength": 1.0}`.

For Easy-Use's `easy fullLoader` and similar simplified loaders, runners CAN use them — they're a single-node alternative to the standard UNETLoader+CLIPLoader+VAELoader trio. But the standard 3-node setup is more verifiable and has better error messages. Save Easy-Use loaders for cases where their integrated features (Lora Block Weight, A1111 mode) are actually needed.
