---
name: ComfyUI execution engine — what /prompt actually does
description: How a submitted workflow becomes node executions. PromptExecutor, PromptQueue, CacheSet, validate_prompt, execute(). Caching strategies, lazy inputs, async nodes, error propagation, the full WS event timeline. Source: ComfyUI/execution.py (1329 lines).
type: reference
---

# Execution engine internals

What happens between `POST /prompt` and the watcher seeing `executed` events. Reference 12 covers the API surface; this covers the underlying machinery.

**Source:** `ComfyUI/execution.py` (1329 lines). Read date: 2026-05-09.

## Top-level flow

```
1. Frontend posts {"prompt": api_workflow_dict, "client_id": ...} to POST /prompt
2. Server validates the workflow via validate_prompt() — emits node_errors back if it fails
3. If valid: PromptQueue.put((priority, prompt_id, prompt, extra_data)) — heapq priority queue
4. Background worker thread picks up via PromptQueue.get() (blocking)
5. Worker calls PromptExecutor.execute(prompt, prompt_id, extra_data, execute_outputs)
6. Inside: build DynamicPrompt → CacheSet → ExecutionList → loop over nodes
7. For each node: get cached if possible, else run execute() → cache outputs → emit WS events
8. On finish: write to PromptQueue.history; emit "execution_success" or "execution_error"
9. Watcher subscribed to /ws sees the WS events and reacts (download outputs, etc.)
```

## Key classes

| Class | Responsibility |
|---|---|
| `PromptQueue` | Thread-safe priority queue of pending workflows. Holds `queue`, `currently_running`, `history`. Mutex-protected. |
| `PromptExecutor` | Owns CacheSet + status_messages. Runs one workflow at a time via `execute_async()`. Created once at startup. |
| `CacheSet` | Caches: `outputs` (per-node output values, keyed by signature) + `objects` (instantiated node classes, keyed by node ID). |
| `DynamicPrompt` | Wrapper around the workflow dict. Resolves real_node_id, display_node_id, parent_node_id (used for subgraphs). |
| `ExecutionList` | Topo-sorted list of nodes to run. Stages nodes for execution, supports unstage/restage for lazy/pending dependencies. |
| `IsChangedCache` | Calls each node's `IS_CHANGED` / `fingerprint_inputs()` to invalidate its cache when inputs change. |

## CacheSet — three caching strategies

ComfyUI supports three cache types (selectable via `--cache-type` startup flag):

```python
class CacheType(Enum):
    NONE             # NullCache — nothing cached, every node runs every time
    LRU              # LRUCache with --cache-lru N max entries
    RAM_PRESSURE     # RAMPressureCache — keep until RAM hits a threshold, then evict oldest
    (default)        # init_classic_cache — HierarchicalCache, dump as soon as possible
```

`outputs` cache is keyed by `CacheKeySetInputSignature` — the cache key is derived from each node's resolved input values (so changing one upstream node invalidates only the descendants whose inputs really change).

`objects` cache is keyed by `CacheKeySetID` (just the node ID). The instantiated node Python object lives here — it's what makes `LoraLoader.loaded_lora` survive across runs.

## DynamicPrompt + subgraphs

Subgraphs (ref 39) are flattened at execution time. `DynamicPrompt` rewrites IDs:
- `real_node_id` — the node ID inside the flattened graph
- `display_node_id` — what the frontend sees (the subgraph instance node, or the actual leaf if not in a subgraph)
- `parent_node_id` — the subgraph instance, if any

This is why your watcher sees events keyed to internal IDs — they're the runtime IDs, not the IDs in the saved JSON.

## execute() — the per-node function

The async `execute()` function (line 427) is called once per node by the main loop. Critical path:

1. **Cache hit check** — call `caches.outputs.get(unique_id)`. If hit, fire `_send_cached_ui()` for that node and return SUCCESS immediately.
2. **Async/subgraph result resolution** — if this node was previously waiting on async tasks or subgraph outputs, collect them now.
3. **Resolve inputs** — call `get_input_data(inputs, class_def, unique_id)`. This is where `["upstream_node_id", output_slot]` references get resolved by reading the upstream's cached output.
4. **Get/create node instance** — `caches.objects.get(unique_id)` or `class_def()` if new. **This is why class `__init__()` runs once per workflow per node.**
5. **Lazy status check** (if the node has `check_lazy_status`) — call it; if it returns a list of inputs needing evaluation, return `PENDING` and stage those inputs first.
6. **Run** — call `_async_map_node_over_list(... func, ...)` which invokes the node's `FUNCTION` (e.g. `KSampler.sample`).
7. **Wrap output** — call `get_output_from_returns()`. Splits the return into `output_data`, `output_ui` (if the return was a dict with `"ui"` key), and detects subgraph-expansion returns.
8. **Cache outputs** — `caches.outputs.set(unique_id, ...)`.
9. **Send WS event** — `executing` (when starting) and `executed` (when done) per node, plus per-step `progress` from the sampler callback.
10. Return SUCCESS / FAILURE / PENDING.

## ExecutionResult enum

```python
class ExecutionResult(Enum):
    SUCCESS    # node finished, advance to next
    FAILURE    # node raised — abort entire prompt, send execution_error
    PENDING    # node has lazy inputs that need evaluation first; come back to it
```

## Error propagation

`handle_execution_error()` distinguishes `InterruptProcessingException` (ESC pressed in UI / interrupt endpoint hit) from real exceptions:

- **Interrupt:** sends `execution_interrupted` event with `node_id`, `class_type`, list of executed nodes
- **Other exceptions:** sends `execution_error` event with the same plus `exception_message`, `exception_type`, `traceback`, `current_inputs`, `current_outputs`

The frontend pops the error in a modal showing the failing node + traceback. The watcher (Tier 2 of the runner architecture, ref 13) sees `execution_error` and can react accordingly.

## validate_prompt — the pre-execution gate

`validate_prompt()` (line 1065) runs BEFORE the workflow is queued. It:

1. Checks every referenced node class exists in `nodes.NODE_CLASS_MAPPINGS`
2. Calls `validate_inputs()` for each node — checks required inputs are present, types match, values are in valid ranges
3. Validates against the upstream's RETURN_TYPES — if a string node tries to feed a model input, fail
4. Builds a `node_errors` dict keyed by node ID

If `node_errors` is non-empty, `/prompt` returns `200 OK` with `{"prompt_id": "...", "node_errors": {...}, "number": N}` — the runner sees the error inline. Workflow is NOT queued.

This is what runners check after submission:

```python
result = http_post_json("/prompt", {"prompt": api_wf})
if result.get("node_errors"):
    print(f"REJECTED: {result['node_errors']}")
    sys.exit(3)
```

`partial_execution_list` allows submitting a request that only validates / runs a subset of nodes (the "Run from this node" button in the canvas).

## Partial execution (extra_data)

`extra_data` in the POST body can include:

```json
{
    "client_id": "...",
    "preview_method": "auto" | "latent2rgb" | "taesd" | "none",
    "extra_pnginfo": { "workflow": {...graph format...} }
}
```

`extra_pnginfo.workflow` is what gets embedded in saved PNG files via SaveImage's hidden `extra_pnginfo` input — the full graph JSON drag-back-to-recover behavior.

## The PromptQueue heapq

```python
heapq.heappush(self.queue, item)    # item is (priority, number, prompt_id, prompt, extra_data)
```

Lower priority = runs first. `task_counter` is the FIFO tie-breaker. Default priority is `number` (queue position), so it's effectively FIFO.

`currently_running` is a dict keyed by task ID. The queue size as seen by `/queue` GET is `len(queue) + len(currently_running)`.

## History and cleanup

```python
MAXIMUM_HISTORY_SIZE = ...  # bounded
self.history[prompt_id] = {
    "prompt": prompt,
    "outputs": ui_outputs,    # the {"ui": {...}} returns from each OUTPUT_NODE
    "meta": meta_outputs,
    "status": {"status_str": "success" | "error", "completed": True, "messages": [...]}
}
```

`/history` GET returns this dict. The Watcher uses this to recover state if it reconnects after a disconnect.

## WS event timeline (per workflow)

A successful 5-node workflow generates approximately:

```
status → "execution_start" {prompt_id}
status → "execution_cached" {nodes: [...cached node IDs...], prompt_id}
status → "executing" {node: "1", display_node: "1", prompt_id}    # node 1 starts
status → "progress" {value: 0, max: 1, node: "1", prompt_id}
status → "executed" {node: "1", display_node: "1", output: {...}, prompt_id}
status → "executing" {node: "2", ...}
... (per node)
status → "executing" {node: null, prompt_id}                       # nothing executing
status → "execution_success" {prompt_id}
```

The `status` ping at the end with `node: null` indicates the queue moved on. The watcher uses `executed` events to decide what to download.

## Lazy inputs end-to-end

```
1. Node A has check_lazy_status() defined and an input marked lazy=True
2. Execution reaches A
3. execute() detects lazy_status_present, calls check_lazy_status() with currently-known inputs
4. check_lazy_status returns ["lazy_input_name"] — tells executor to compute it now
5. execute() calls execution_list.make_input_strong_link(unique_id, "lazy_input_name")
6. Returns ExecutionResult.PENDING
7. Main loop unstages A, stages the upstream of "lazy_input_name"
8. After upstream completes, A is re-staged
9. Now check_lazy_status returns [] (everything ready) → execute proceeds
```

## Async nodes

Some nodes (e.g. API-call nodes that hit external services) return an `asyncio.Task` instead of a result. The executor places the task in `pending_async_nodes[unique_id]` and returns PENDING. The main loop continues to other ready nodes; on next visit to this node, it awaits the task and proceeds.

This is what makes Nano Banana / GeminiImage2 / OpenAI nodes non-blocking. The graph keeps executing while their REST call is in-flight.

## Cache providers (registry plug-in)

```python
_get_cache_providers()    # extension hook — packs can register custom cache backends
provider.on_prompt_start(prompt_id)
provider.on_prompt_end(prompt_id)
```

Used by ComfyUI Manager and similar to track lifecycle for installed-node telemetry. Custom packs rarely need to touch this.

## Implications for runner / workflow authoring

- **`prompt_id` returned by `/prompt`** is what you pass to `/history/<prompt_id>` later to retrieve outputs.
- **Workflow rejection happens at `/prompt`** — `node_errors` is populated synchronously. No async wait.
- **A re-submitted identical workflow will have most/all nodes cached** unless inputs changed. The `execution_cached` event lists the skipped node IDs.
- **`OUTPUT_NODE = True` with no consumers IS the canonical pattern** — SaveImage runs even though nothing reads its (empty) RETURN_TYPES, because OUTPUT_NODE forces inclusion in the execution list.
- **Don't put heavy work in node `__init__`** — it runs once per workflow per node, and the instance is cached in `caches.objects` for re-runs.
- **Use `IS_CHANGED` / `fingerprint_inputs`** if your node has stable Python inputs but a changing external resource (file on disk, API quota). Otherwise the cache will stick.
- **`extra_pnginfo.workflow`** is how the graph format gets into saved PNGs. The runner can inject this when submitting if it wants the saved file to include the graph (most do).

## Mapping back to runner's existing pattern

The icon runner's submission pattern (ref 36):

```python
result = http_post_json("/prompt", {"prompt": api_wf})
# result == {"prompt_id": "...", "number": N, "node_errors": {}}
```

What's actually happening server-side after that POST:
1. `validate_prompt()` runs synchronously → `node_errors` populated → returned to runner.
2. If valid: `PromptQueue.put(...)` → returns `prompt_id` and `number`.
3. Worker thread picks up → `PromptExecutor.execute()` → emits WS events.
4. The watcher sees `executed` events as each SaveImage node fires.

So `prompt_id` = "ticket"; the watcher's job is to pair it with WS events to detect completion + download outputs.

## When we'd want a custom cache provider

Custom cache provider use cases (rare):
- Per-user telemetry on which models get loaded (analytics packs)
- Persistent cross-session output cache (saving expensive computations to disk)
- Cluster-aware cache (shared between multiple ComfyUI workers)

For Luis's single-machine setup, the default `init_classic_cache()` (HierarchicalCache, dump-fast) is fine.
