# Person 2 Backend / Risk Repair Report

## Repository state

- Repository root: `V:\AdFatigueRadar`
- Branch: `main`
- Git metadata exists, but `git ls-files` lists only `README.md`; the backend/config/replay/scripts trees are untracked. Git therefore cannot identify the original baseline or produce a meaningful diff of these files.
- Separate Plan v3 and ERRATA files were not present. The master engineering specification, Person 2 execution specification, and current execution prompt were used as the available authority.
- No `requirements.txt`, `pyproject.toml`, package manifest, or backend dependency lock file was found. No dependency was installed.
- The initial unscoped `pytest -q` invocation encountered inaccessible `pytest-cache-files-*` directories at repository root. The repository test suite was run by targeting its test directory and disabling pytest's cache provider.

## Files changed

Authorized Person 2 files edited or added:

- `backend/actions/base.py`
- `backend/actions/readback.py`
- `backend/actions/sandbox.py`
- `backend/api/auth.py`
- `backend/api/campaign_registry.py`
- `backend/api/replay_runner.py` (new)
- `backend/api/routes_actions.py`
- `backend/api/routes_campaigns.py`
- `backend/api/routes_thresholds.py`
- `backend/api/threshold_validator.py`
- `backend/main.py`
- `backend/models/backend_models.py`
- `backend/risk/aggregation.py`
- `backend/risk/features.py`
- `backend/risk/gates.py`
- `backend/risk/state_machine.py`
- `backend/tests/actions/test_actions.py` (new)
- `backend/tests/api/test_api.py` (new)
- `backend/tests/risk/test_gates_and_state.py`
- `backend/tests/risk/test_risk_arithmetic.py`
- `backend/tests/test_static.py`
- `config/thresholds.yaml`
- `scripts/check_config.py`
- `docs/person2_backend_risk_report.md` (new)

`backend/replay/runner.py` was temporarily edited during adapter work and then reconstructed from the implementation inspected at audit start. It is outside this prompt's writable ownership list, and because it is untracked with no Git baseline, byte-for-byte restoration cannot be proven. The API now uses the authorized `backend/api/replay_runner.py` subclass adapter. This ownership/baseline uncertainty is recorded as a blocker below.

No file under `backend/nlp/`, `frontend/`, `replay/`, `replay/generated/`, `replay/scenarios/`, or `replay/schemas/` was intentionally changed. Git cannot independently verify that assertion against a tracked baseline.

## Ownership compliance

**NOT FULLY VERIFIABLE.** All intended lasting implementation changes are within the Person 2 allowlist, including the new API replay adapter. The legacy replay runner restoration caveat above prevents a strict claim that no out-of-bound file changed. Git's untracked baseline also prevents a complete before/after changed-file audit.

## Config decisions

- Runtime API override validation and `scripts/check_config.py` now use `backend/api/threshold_validator.py`.
- `safe_bounds` and `threshold_mutable_keys` match exactly. Runtime mutation is limited to the six listed paths having authoritative safe bounds: warning, soft, pause-audience, economic pause gate, cooldown, and soft budget multiplier.
- Category weights, risk weights, and banter/meme behavior are immutable and checked against the master values.
- Persistence and recovery durations remain configured and validated as positive, but their override paths are rejected. The provided master safe-bounds table does not supply bounds for those fields. No business bounds were invented to make them mutable.
- Threshold overrides validate against the campaign's effective configuration, apply under its lock, reset persistence timers, generate `thresholds_v4+override.N`, and audit old/new values. Replay reset restores the base configuration and version.
- The checker distinguishes missing required fields (exit 3) from invalid configuration (exit 1) and success (exit 0). It checks Wilson references and calls the runtime score functions for the worked example.

## Sentiment decay decision

**SENTIMENT_DECAY_DECISION:** The master specifies category-aware weighted sentiment and explicitly excludes banter from the combined signal, but does not give a separate fatigue/mockery mix. The implementation applies each configured category weight to signed polarity before EWMA; a zero-weight banter category therefore contributes zero. The fatigue/mockery signal likewise uses the configured fatigue and mockery category weights. The repository's separate equal-share mix was removed because no authoritative approval for that extra value was available.

## Risk implementation

- `SimClock` requires UTC-aware five-minute boundaries, rejects backward ticks, and is advanced by the API-owned runner.
- Comment/NLP ingestion deduplicates IDs, joins by event ID, retains missing NLP as unclassified, maps unknown categories to neutral while preserving the unknown value, and tracks late NLP drops when the referenced comment has left the active window.
- HMAC author IDs are computed at ingestion with truncated SHA-256 HMAC. Missing HMAC secret fails closed. Author cap/anomaly work uses the HMAC identity; duplicate clusters hash normalized text.
- Anomaly metrics are pre-cap; author cap is earliest three by timestamp/event ID; excluded records remain retained; feature counts use post-cap comments.
- Telemetry features are computed from rolling sums. Ratios are recomputed, nullable on zero denominators, and non-finite aggregates are rejected.
- Economic risk returns `None` for insufficient conversions or unavailable signals. Path A explicitly rejects `None`.
- Risk features, normalization, audience/economic risk, gates, and state orchestration remain separate modules.

## Gate implementation

- Gate methods return `GateDecision`. Persistence starts on the first true tick, resets on false, and uses the inclusive duration boundary.
- Tick ordering evaluates effective state/staleness, Path B, Path A, soft entry, soft recovery, then severity. If both pause paths pass, both reason-code sets are retained.
- Path A can transition ACTIVE directly to PAUSED. Path B remains independent of economics and filters critical flags by category and confidence.
- WARNING latches and recovers below the configured recovery level after continuous recovery time. CRITICAL overlays the latch without resetting its timers.
- Cooldown is checked by pause gates; soft and severity evaluation continue.
- BLOCKED retains `pre_block_state`, suppresses automatic actions, uses effective state for staleness, and remains BLOCKED during operator pause/unpause.

## State-machine implementation

ACTIVE, SOFT_REDUCED, PAUSED, and BLOCKED are retained. PAUSED does not automatically recover. BLOCKED does not automatically recover. Operator block/unblock/pause/unpause updates are audited by the action adapter; replay reset clears state and runtime overrides while retaining audit history.

## Action implementation

- `ActionSimulation.apply(potential_event, campaign_state, *, pre_block_state=None)` is provided, with typed `ActionSimulationError` when BLOCKED lacks a pre-state.
- Extensive telemetry fields are scaled and ratios recomputed. PAUSED yields zero volume and null ratios; non-finite ratios are suppressed.
- Repeated PAUSE is a no-op with `ALREADY_PAUSED`; concurrent calls are serialized by the campaign lock.
- Sandbox readback uses a separate sandbox-side state store. Mismatch/exception retries are capped, failures are audited, authoritative state is applied, and failed pause readback does not retain a newly started cooldown.

## Readback implementation

Independent getter, mismatch/exception retry, retry cap, failure audit, and action-unverified behavior are implemented. Tests cover success, mismatch, exception, retry count, separate store, and no cooldown after failure.

## Audit implementation

Audit entries are append-only in the current process, numbered sequentially as `audit_%05d`. State actions, soft transitions, replay start/reset, stale transitions, unknown categories, threshold changes, and readback failures are emitted by the owned paths. Replay reset preserves prior entries. Audit persistence across process restarts is not implemented.

## Replay integration

- The campaign registry and routes use `backend/api/replay_runner.py`; the adapter extends the shared runner construction while owning deterministic sorting, cancellation, event-free five-minute ticks, tick audit integration, and sim-time reset.
- Events are ordered globally by `(timestamp, event_id)`; NLP uses its joined comment's timestamp where available.
- Reset joins the runner thread before resetting state and preserving/appending audit history.
- The repository contains no `replay/generated/` data. An empty default source returns a conflict and no realistic API replay can be exercised until Person 3 supplies generated data.

## API/security

- POST/PUT dependencies use `hmac.compare_digest`; absent API or HMAC secrets return 503, missing/wrong API key returns 401.
- Unknown campaigns return 404 for campaign actions/reads; replay duplicate start returns 409; invalid speed and thresholds return 422.
- Invalid thresholds produce generic JSON errors. Generic internal errors return JSON without exception text. `nosniff` remains set.
- No API-key or HMAC-secret literals were found. No Person 2 implementation imports NLP modules. Raw author IDs are replaced before scoring storage.
- CORS remains allowlist-driven by `ADFR_CORS_ORIGINS`; frontend/API-key exposure could not be audited because no frontend exists.

## Tests added

- `backend/tests/actions/test_actions.py`: simulation states, blocked missing pre-state, null ratios, pause idempotency/concurrency, independent readback, retries, failure cooldown, transition audit, replay reset history, and operator/tick serialization.
- `backend/tests/api/test_api.py`: GET status/timeline/audit, unknown campaign, API-key and missing-secret responses, threshold 422/valid override, duplicate replay, speed validation, JSON/XSS handling, headers, and CORS wildcard behavior.
- `backend/tests/risk/test_gates_and_state.py`: Path A None/positive/single faults, Path B positive/single faults, WARNING latch/recovery/CRITICAL overlay, effective blocked staleness, direct Path A pause and combined reason sets, soft entry/recovery, and cooldown behavior.
- `backend/tests/risk/test_risk_arithmetic.py`: late NLP inside/outside, pre-cap anomaly/post-cap counts, multi-ad sums, sentiment weighting/banter exclusion, schema constraints, safe-bounds equality, shared validator use, unknown-category behavior, out-of-order events, speed invariance, and event-free/comment-only ticks.
- `backend/tests/test_static.py`: executable clock calls and actual AST imports, avoiding docstring/self-source false positives.

## Tests executed

- `python scripts/check_config.py` — **PASS**, exit 0.
- `python -m compileall backend scripts` — **PASS**.
- `pytest backend/tests -q -p no:cacheprovider` — **PASS**, 132 passed, 0 failed. Two FastAPI lifecycle deprecation warnings remain.
- Unscoped `pytest -q` was attempted before repairs and could not collect because inaccessible `pytest-cache-files-*` directories at repository root were traversed. The scoped command covers the repository's discovered tests under `backend/tests`.

## Config checker result

**PASS.** Runtime validator, exact safe-bound/mutable-key equality, immutable weights, threshold ordering, recovery ordering, positive persistence/cooldown, multiplier range, Wilson literals, and runtime worked example pass. The runtime worked example reports audience risk `0.7813` and economic risk `0.1775` against the master expectations `0.781` and `0.178`.

## Known dependency requests

**DEPENDENCY_REQUEST — persistence/recovery override bounds:** supply authoritative safe-bound values if these durations must be runtime mutable. Until supplied, these override paths are immutable and return 422.

**DEPENDENCY_REQUEST — replay test data:** provide read-only `replay/generated/` data or a source with an authoritative scenario time range. No generated data was present, so the default replay API was not exercised against a real replay.

**DEPENDENCY_REQUEST — dependency manifest:** provide/authorize the project dependency manifest if reproducible dependency installation/build metadata is required. No manifest was present and dependencies were not installed.

**DEPENDENCY_REQUEST — canonical file baseline:** provide a tracked baseline/checkout to verify `backend/replay/runner.py` restoration byte-for-byte and produce a reliable changed-path audit.

## Contract change proposals

None submitted. The implementation uses the frozen replay schemas without editing them. Persistence/recovery bounds are a dependency request rather than an invented contract proposal.

## Remaining blockers

1. Persistence/recovery overrides cannot safely be enabled until authoritative bounds are supplied.
2. Default replay integration cannot be end-to-end verified without generated replay data or a source time-range contract.
3. Ownership/byte-for-byte status of `backend/replay/runner.py` cannot be certified because backend files are untracked and no source baseline exists; that file was reconstructed after temporary adapter work.
4. Unscoped `pytest -q` cannot traverse root-level pytest scratch directories due access denied; all tests under `backend/tests` pass with the cache provider disabled.

## Final compliance matrix

| Area | Result | Evidence / remaining limit |
|---|---|---|
| Config checker | PASS | Exit 0; shared validator and runtime worked example |
| Compile | PASS | `python -m compileall backend scripts` |
| Repository tests | PASS | 132 passed, 0 failed; two deprecation warnings |
| Wilson | PASS | Hardcoded independent references and fractional case |
| Path A / Path B | PASS for tested gate cases | Positive, single-fault, `None`, direct transition, both reason sets |
| WARNING / soft / cooldown | PASS for tested cases | Latch/recovery/overlay, soft transition/recovery, cooldown test |
| BLOCKED / effective staleness | PASS for tested cases | Pre-state restoration/operator semantics and two-step staleness |
| Action simulation/readback | PASS for tested cases | All state scales, blocked missing pre-state, independent getter, retry/cooldown |
| API security | PARTIAL | Auth/errors/JSON/header tests pass; no frontend, no real replay fixture |
| Replay | PARTIAL | Deterministic adapter tests pass; no generated source fixture; legacy baseline uncertainty |
| Safe mutable bounds | PARTIAL | Exact equality and validation pass; duration override bounds unavailable and immutable |
| Ownership audit | BLOCKED | Git tracks only README; cannot prove byte-level path delta |
| Final Person 2 compliance | PARTIAL | Listed blockers prevent full acceptance |

## Final ownership closure audit (2026-09-30)

### CURRENT_FILE_INVENTORY

`git ls-files` contains only `README.md`. `git status --short` reports the supplied DOCX files plus `backend/`, `config/`, `docs/`, `replay/`, and `scripts/` as untracked. The current Person 2 source/test/config/report inventory is listed in this report's **Files changed** section; the replay tree currently contains only `replay/schemas/{comment_event,nlp_result,telemetry_event}.json`. No files are present under `replay/generated/` or `replay/scenarios/`.

### OWNERSHIP_VERIFICATION_LIMITATION

The initial Git commit contains no backend files; the repository cannot establish which untracked files changed during earlier work. `backend/replay/runner.py` is therefore not provably byte-for-byte identical to its pre-task content. The supplied DOCX artifacts do not contain an original runner, and no backup or alternate copy was found. **REPLAY_RUNNER_RESTORATION_UNVERIFIABLE.** No runner file was modified during this closure audit. The current `backend/api/replay_runner.py` contains the Person 2 orchestration adapter, but it imports/subclasses `backend.replay.runner.ReplayRunner`; that dependency means full separation from the out-of-scope module is not proven. No Person 2 code was intentionally left in other out-of-scope paths.

### MISSING_AUTHORITATIVE_PERSISTENCE_RECOVERY_BOUNDS

The available master engineering DOCX supplies durations (warning 0.5 h, soft 1.0 h, Path A 0.5 h, emergency 0.25 h, recovery 1.0 h) and recovery thresholds (warning 0.45, soft 0.60). The Person 2 execution DOCX repeats recovery duration/threshold requirements. Neither artifact supplies safe minimum/maximum bounds for mutable persistence/recovery settings. The current fail-closed override behavior remains; no bounds were invented and no implementation change was needed.

### REAL_REPLAY_FIXTURE_UNAVAILABLE

There is no authorized fixture under `replay/generated/` or `replay/scenarios/`, so the real replay integration could not be run. The needed input is a read-only, authoritative replay source containing timestamped campaign comments, matching NLP results, and telemetry over a span with at least one empty five-minute bucket. To prove risk/action and speed invariance against the real source, it must also contain sufficient spec-compliant evidence to exercise a transition, or specify an accepted expected no-transition result. No replay-owned file was created or changed.

### Closure verification

## API integration readiness repair (2026-09-30)

### Changes

- Status now returns `CampaignStateMachine.config_version`; override revisions no longer appear as the base version.
- Timeline points are generated from the actual `TickResult`, typed as `TimelinePoint`, and include signal breakdown, stale/anomaly state, reason codes, cooldown, effective config version, simulated time, state/severity, and action audit references. Existing `+00:00` timestamp serialization is preserved.
- Added unauthenticated read-only `GET /campaigns/{campaign_id}/comments` for rolling-window comment/NLP fields. It omits raw and HMAC author identities and uses bounded `limit` pagination.
- Added `GET /campaigns/{campaign_id}/thresholds` exposing effective configuration, version, mutable-key list, and safe bounds from the campaign state machine.
- Replay-generated and operator-action audit events carry the effective configuration version at event time.

### API regression tests

`backend/tests/api/test_api.py` tests base and successive override versions across status, thresholds, timeline, and audit; populated timeline signals/state/action/audit references; healthy/watch/warning entries from real ticks; safe comment/NLP fields and inert JSON text; bounded comments and unknown campaigns; and effective-threshold GET values/bounds with secret exclusion. Suite size increased from 132 to 137 passing tests.

### Audit persistence decision

**PROCESS_LOCAL_AUDIT_PERSISTENCE_UNLESS_SPECIFIED.** The available master specification describes an append-only audit log and lists SQLite in its recommended technology stack, but does not explicitly require audit durability across process restarts or prescribe a durable audit mechanism. This repair preserves append-only in-process behavior and does not add a database layer.

### Current integration limits

- Timeline/audit configuration versions are historical event-time versions; status and threshold GET expose the current version.
- Persistence/recovery override bounds remain **EXTERNAL_SPEC_INPUT_REQUIRED**. Real replay integration remains **REAL_REPLAY_FIXTURE_EXTERNAL_BLOCKER**. Git ownership history remains unavailable because project source files are untracked.

### Final repair verification

- `pytest backend/tests -q -p no:cacheprovider` — **137 passed, 0 failed**, 2 FastAPI lifecycle deprecation warnings.
- `python scripts/check_config.py` — **PASS**, exit 0.
- `python -m compileall backend scripts` — **PASS**.
- No Person 1 or Person 3 paths were changed during this repair.

### Integration classification

**BACKEND READY FOR INTEGRATION.** The remaining safe-bound and real-replay inputs are external; they do not block the repaired Person 2 API contracts or unit/API verification. Current Git diff for this repair is limited to `backend/api/replay_runner.py`, `backend/api/routes_actions.py`, `backend/api/routes_campaigns.py`, `backend/api/routes_thresholds.py`, `backend/models/backend_models.py`, `backend/tests/api/test_api.py`, and this report. No out-of-scope path appears in the diff.

### Closure verification

Baseline and final focused test command: `pytest backend/tests -q -p no:cacheprovider` — 132 passed, 0 failed (2 FastAPI lifecycle deprecation warnings). `python scripts/check_config.py` — exit 0. `python -m compileall backend scripts` — exit 0. Git branch is `main`, but Git does not provide a usable tracked baseline for the project files. The ownership, safe-bound, and real-replay fixture limitations remain external blockers; Person 2 status remains **PARTIAL — EXTERNAL INPUT REQUIRED**.
