---
name: pixaroma-workflows — YouTube ComfyUI course episode backups
description: Compact catalog repo that bundles workflow JSONs from Pixaroma's YouTube ComfyUI Free Course. 6 episodes as of 2026-05-09. Distributed primarily via Discord with GitHub Releases as a backup. Useful as a curated tutorial-paced learning resource.
type: reference
---

# pixaroma/pixaroma-workflows

Repo: https://github.com/pixaroma/pixaroma-workflows

**Read date:** 2026-05-09

## What I could and could NOT verify

**Verified via fetch:** the GitHub repo's README (15 stars, 7 commits, 6 releases EP01-EP06, distribution via Discord + GitHub Releases, paired YouTube playlist).

**NOT verified — Discord-gated content:** Per the README, the **primary** distribution channel is the Pixaroma Community Discord's `#pixaroma-workflows` channel, NOT GitHub. The GitHub Releases tab is explicitly labeled as a "backup." This means:

- Whatever is "current" or "newest" lives on Discord first
- The GitHub repo may lag behind Discord by days/weeks
- The actual workflow contents — what each episode covers, what techniques are demonstrated — are NOT inspectable by me without human-relay help

I cannot access Discord. It requires authentication, anti-scraping protections are active, and my fetch tool cannot crawl chat protocols. To verify what's actually in the Discord channel, Luis would need to either:

1. **Join the Discord, browse `#pixaroma-workflows`, and paste descriptions of what he sees** — episode names, pinned message summaries, listed workflow filenames
2. **Download specific workflow JSONs from the Discord and drop them somewhere local** (e.g., `ComfyUI/user/default/workflows/` or anywhere readable). I can then read the JSON via the Read tool and surface what techniques each demonstrates, just like I did for the Comfy-Org canonical templates.

Until that happens, this reference is documenting the *existence* of the Pixaroma workflow library, NOT its contents.

## What it is

A backup-distribution repo for ComfyUI workflows from **Pixaroma's "ComfyUI Free Course"** YouTube playlist. Each YouTube episode has a corresponding GitHub Release tag (EP01, EP02, ...). The workflow JSON files for each episode are distributed as the release's downloadable assets.

**Stats from fetch:**
- 15 stars, 0 forks, 7 commits — small repo, primarily distribution-driven
- 6 releases as of 2026-05-09: EP01 through EP06 (latest EP06 Feb 25, 2026)
- README only in main branch — no inline workflow files
- Bundled with a YouTube playlist + Discord community for support

## Two distribution channels

The README explicitly recommends Discord first, GitHub second:

1. **Pixaroma Community Discord** (main, free) → `discord.com/invite/gggpkVgBf3`. Workflows posted in the `#pixaroma-workflows` channel.
2. **GitHub Releases** → `github.com/pixaroma/pixaroma-workflows/releases` (backup mirror)

Both should have the same content; Discord is just the primary community.

## YouTube playlist

`https://www.youtube.com/playlist?list=PL-pohOSaL8P-FhSw1Iwf0pBGzXdtv4DZC` ("ComfyUI Free Course")

A 6-episode beginner-to-intermediate course paired with the workflows. The episodes likely build progressively (Episode 1 = basics, Episode 6 = advanced techniques) but specific contents weren't surfaced in the README.

## Why Luis might want to look at this

**As a learning resource:** if any of the 6 episodes covers a technique Luis wants to learn (advanced ControlNet stacking, AnimateDiff setup, regional prompting, IPAdapter chaining, video pipelines, etc.), the workflow JSON paired with the YouTube tutorial is a higher-value learning combo than reading docs alone. Drop the workflow into your canvas, press Play on the video, and follow along.

**As a workflow library:** if the techniques covered are still relevant by 2026 (some ComfyUI tutorials age fast — IPAdapter v1, AnimateDiff v1 era content is largely obsolete now), the workflows can serve as starting templates similar to the Comfy-Org canonical templates (ref 27, 53).

## Why Luis might NOT want to bother

1. **Small scope** — 6 episodes vs Comfy-Org's 42 official templates. Lower coverage of model families.
2. **Tutorial pacing** — each episode probably introduces one technique slowly. If Luis is past the introduction phase (he is), there's less marginal value vs reaching for a canonical template directly.
3. **Discord-first distribution** — to get the latest workflows promptly, Luis would need to join another Discord community. Adds friction.
4. **Likely SDXL/Pony focused** — most YouTube ComfyUI courses tilt toward SDXL/Pony rather than Flux/Qwen/Z-Image. The episode topics weren't surfaced from the fetch, but a 2025-2026 free-course audience usually starts with the most familiar model family.

## Recommended approach

If Luis wants to evaluate quickly:

1. **Check the YouTube playlist titles** at the URL above — episode titles will tell you what techniques are covered without watching anything.
2. **If a title matches a knowledge gap** (e.g., "Episode 4: Advanced AnimateDiff Workflows" if Luis wanted that), download the matching release's workflow JSON.
3. **Open the workflow in ComfyUI canvas** and inspect the node structure — the workflow itself is often more informative than the video.

If no episode title catches Luis's eye, skip — the Comfy-Org canonical templates and the civitai workflow recipes (refs 50, 51) are richer learning material.

## Caveat about this reference

The fetched README gave me the structure (Discord + GitHub releases distribution, 6 episodes) but the actual workflow contents and episode topics were NOT visible in the fetched HTML. Provenance constraints prevented fetching the releases page directly. To know what each EP covers, Luis or a future fetch would need to visit `github.com/pixaroma/pixaroma-workflows/releases` in browser.
