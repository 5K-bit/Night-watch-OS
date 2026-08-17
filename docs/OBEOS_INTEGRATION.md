# OBEOS Integration Contract

Nightwatch is the OBEOS **operator runtime** component. It owns deterministic work-session state and must remain independent from LLM reasoning.

## Responsibilities

Nightwatch owns:

- shift/session lifecycle
- shift notes
- task lifecycle and unfinished-task carryover
- local SQLite persistence and backups
- lightweight local system snapshots
- CLI and HTTP interfaces for deterministic state changes

Nightwatch does not own:

- conversation or semantic reasoning
- RAG or long-term AI memory
- Telegram or other channel-specific gateways
- security orchestration
- cloud synchronization
- model execution

Those responsibilities belong to OBEOS services such as DAISE, The Assistant, Sentinel, and gateway/HUD components.

## Integration boundary

OBEOS consumers should call Nightwatch through its API rather than reading the SQLite database directly. Python consumers may use `nightwatch.client.NightwatchClient`, which preserves the same HTTP boundary while avoiding duplicated request code.

```python
from nightwatch.client import NightwatchClient

nightwatch = NightwatchClient()
nightwatch.start_shift()
nightwatch.create_task("Review OBEOS telemetry")
```

Current stable endpoints:

- `GET /api/health`
- `GET /api/system`
- `GET /api/shift/current`
- `POST /api/shift/start`
- `POST /api/shift/end`
- `PUT /api/shift/{shift_id}/notes`
- `GET /api/tasks/current`
- `POST /api/tasks`
- `POST /api/tasks/{task_id}/complete`
- `POST /api/tasks/{task_id}/reopen`
- `DELETE /api/tasks/{task_id}`

## OBEOS consumers

Expected consumers include:

- DAISE for natural-language orchestration
- The Assistant for planning and work review
- OBEOS HUD surfaces for current-state display
- Legion/mobile interfaces
- Telegram gateway through OBEOS, not directly from Nightwatch

## Security rule

Nightwatch is local-first. The default bind address should remain loopback. Any future network exposure must sit behind an authenticated OBEOS gateway or add explicit Nightwatch authentication before binding to non-loopback interfaces.

## Failure rule

If Nightwatch is unavailable, OBEOS must report operator state as unavailable rather than reconstructing current shift/task state from DAISE conversational memory. Reads may degrade gracefully; mutations should fail closed and surface the Nightwatch error.

## Event direction

A later integration phase should emit deterministic OBEOS events such as:

- `operator.shift.started`
- `operator.shift.ended`
- `operator.task.created`
- `operator.task.completed`
- `operator.task.reopened`
- `operator.note.updated`

Nightwatch should emit facts. DAISE and other intelligent services should interpret those facts. Event publication belongs in the OBEOS adapter so a messaging outage cannot prevent Nightwatch from persisting local operator state.

## Evolution path

The existing `Shift` model remains the compatibility contract for now. A future migration may generalize shifts into typed operator sessions (`security_shift`, `development`, `research`, `creative`, `maintenance`, `focus`) without breaking existing API clients.

## Source-of-truth rule

The standalone `5K-bit/Night-watch-OS` repository is the authoritative Nightwatch source. OBEOS should reference it as a managed component rather than maintain copied source trees. This prevents drift between Nightwatch development and OBEOS integration.
