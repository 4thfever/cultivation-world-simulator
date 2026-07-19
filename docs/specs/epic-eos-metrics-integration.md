# Epic EOS Metrics Integration

This spec records the intended design for adding Epic Online Services (EOS)
runtime telemetry to the Epic desktop build without affecting GitHub, source,
Docker, or generic desktop usage.

## Context

The project already has two separate distribution paths:

1. GitHub release packaging, driven by `tools/package/publish_github.ps1`.
2. Desktop store packaging, driven by `tools/package/pack_desktop.ps1` and
   store-specific publish scripts such as `tools/package/publish_epic.ps1`.

The current Epic pipeline only uploads the packaged desktop build through
BuildPatchTool. It does not initialize EOS at runtime.

The first EOS goal is intentionally narrow: collect Epic-player session data so
the developer can inspect player activity and CCU-like metrics in Epic's
backend. This maps to the EOS Metrics interface, especially begin/end player
session calls. Epic's documentation describes the Metrics interface as the path
for collecting concurrent online user and retention data:

- https://dev.epicgames.com/docs/epic-online-services/player-and-game-data/eos-metrics-interface
- https://dev.epicgames.com/docs/en-US/api-ref/functions/eos-metrics-begin-player-session
- https://dev.epicgames.com/docs/en-US/api-ref/interfaces/metrics

Epic artifact deployment selection is also required so Epic Games Launcher can
pass the correct deployment information to the game at launch:

- https://dev.epicgames.com/docs/epic-games-store/store-presence/manage-artifacts
- https://dev.epicgames.com/docs/epic-games-store/testing-guide

## Goals

1. Enable EOS Metrics for Epic desktop builds.
2. Keep GitHub, source, Docker, and generic desktop builds free of EOS runtime
   dependencies.
3. Treat EOS as a channel adapter, not as core game simulation state.
4. Fail open: if EOS is unavailable, misconfigured, offline, or not launched
   through Epic Games Launcher, the game still starts normally.
5. Store local Epic credentials only in ignored local files.
6. Support Dev-first testing and a later Live switch without rewriting runtime
   code.

## Non-Goals

1. No achievements in the first phase.
2. No friends, presence, overlay, lobbies, sessions, P2P, voice, leaderboards,
   or anti-cheat.
3. No cloud saves or player data storage.
4. No frontend-visible Epic login UI.
5. No EOS state in save files, `RunConfig`, `settings.json`, or `secrets.json`.
6. No Python backend dependency on EOS.

## Portal State

Known local portal setup as of this spec:

1. EOS product id has been found and saved in local ignored runtime config.
2. Dev deployment id has been found and is currently the active local runtime
   deployment.
3. Live deployment id has been found and confirmed on the Live side.
4. Epic runtime client id has been created and saved locally.
5. Epic runtime client secret was found by the developer and must remain local.
6. Dev artifact is bound to the Dev deployment.
7. The policy choice for the initial implementation is `GameClient`.

The current local ignored file is:

```text
tools/package/epic/eos_runtime.env
```

That file must stay ignored by git. It may contain:

```env
EPIC_EOS_PRODUCT_ID=
EPIC_EOS_SANDBOX_ID=
EPIC_EOS_DEPLOYMENT_ID=
EPIC_EOS_DEV_DEPLOYMENT_ID=
EPIC_EOS_LIVE_DEPLOYMENT_ID=
EPIC_EOS_CLIENT_ID=
EPIC_EOS_CLIENT_SECRET=
```

Do not commit real values in documentation, tests, templates, or source files.
If an example is needed, create `tools/package/epic/eos_runtime.env.example`
with empty placeholder values only.

## Policy Decision

The first implementation may use Epic's `GameClient` client policy because the
developer chose to prioritize setup velocity. This is acceptable for initial
Dev testing.

This decision carries a security and maintenance tradeoff: `GameClient` may
enable more EOS features than the project currently uses. The runtime client
credentials are distributed with the Epic desktop package, so policy scope still
matters even if the game code does not call unused EOS interfaces.

Before depending on this for long-term Live operation, reevaluate whether to
replace it with a custom minimal policy that allows only the actions needed for
Auth/Connect and Metrics.

## Architecture

EOS runtime support must be isolated behind an Electron-side telemetry adapter.

```text
desktop Electron main process
  |
  |-- TelemetryProvider
  |     |
  |     |-- NullTelemetryProvider
  |     |     default for GitHub, source, Docker, generic desktop
  |     |
  |     |-- EpicEosTelemetryProvider
  |           only enabled for Epic desktop builds
  |
  |-- optional eos-helper.exe sidecar
        |
        |-- EOS SDK C# wrapper / native EOS runtime dll
        |-- authenticate from Epic Launcher exchange code when available
        |-- begin/end EOS Metrics player session
```

The core game backend remains unaware of EOS. Vue remains unaware of EOS. Save
and load remain unaware of EOS.

## Runtime Flow

On desktop startup:

1. Electron starts the packaged Python backend as it does today.
2. Electron reads the distribution/runtime manifest from `process.resourcesPath`.
3. If the manifest does not enable Epic EOS Metrics, use
   `NullTelemetryProvider`.
4. If Epic EOS Metrics is enabled, create `EpicEosTelemetryProvider`.
5. The Epic provider reads Epic Launcher command-line arguments first.
6. If launcher arguments are missing, it falls back to packaged runtime config.
7. If required values are still missing, it logs and disables EOS.
8. If configured, it starts `eos-helper.exe`.
9. The helper authenticates and calls the EOS Metrics begin-session operation.
10. On window close or app shutdown, Electron asks the helper to end the
    session and exits even if helper cleanup fails.

The launch/config priority is:

```text
1. Epic Games Launcher command-line arguments
2. Packaged Epic runtime config generated from eos_runtime.env
3. Disabled EOS fallback
```

Relevant launcher arguments include values such as:

```text
-epicdeploymentid
-epicsandboxid
-AUTH_LOGIN
-AUTH_PASSWORD
-AUTH_TYPE=exchangecode
```

The implementation must not require these arguments for non-Epic builds.

## Helper Implementation Choice

Use a small C# helper first, not a Node native addon.

Reasons:

1. EOS provides C and C# SDK options.
2. A C# helper avoids Electron native addon ABI problems.
3. The helper can be published as a self-contained Windows executable.
4. The helper can crash or fail without bringing down the game.
5. The Electron main process can keep the integration narrow and testable.

The helper should live outside the existing Python backend and Vue frontend.
A possible layout:

```text
desktop-eos-helper/
  src/
  desktop-eos-helper.csproj
  README.md
```

The actual EOS SDK binaries should not be committed. The build or packaging
script should consume them from a local SDK path.

The C# SDK reference is:

- https://dev.epicgames.com/docs/epic-online-services/working-with-the-eos-sdk/eossdkc-sharp-getting-started
- https://onlineservices.epicgames.com/sdk

## Packaging Design

Add an explicit distribution/environment concept to desktop packaging.

Suggested parameters:

```powershell
tools/package/desktop/pack.ps1 -Distribution generic
tools/package/desktop/pack.ps1 -Distribution epic -EosEnv dev
tools/package/desktop/pack.ps1 -Distribution epic -EosEnv live
```

Default behavior must remain generic.

`publish_epic.ps1` may call desktop packaging with:

```powershell
-Distribution epic
```

For development uploads, use:

```powershell
-EosEnv dev
```

For final public Epic builds, use:

```powershell
-EosEnv live
```

The packaged Epic build may include:

```text
resources/eos-runtime.json
resources/eos-helper/eos-helper.exe
resources/eos-helper/EOSSDK-Win64-Shipping.dll
```

Generic and GitHub builds must not include those files.

The generated runtime config must not include BuildPatchTool upload secrets.
Separate concerns:

```text
tools/package/epic/epic_config.env
  BuildPatchTool upload configuration

tools/package/epic/eos_runtime.env
  EOS runtime client/deployment configuration
```

## Distribution Manifest

Add a small packaged manifest for desktop runtime feature detection.

Example for generic builds:

```json
{
  "distribution": "generic",
  "features": {
    "epicEosMetrics": false
  }
}
```

Example for Epic builds:

```json
{
  "distribution": "epic",
  "features": {
    "epicEosMetrics": true
  }
}
```

Electron should default to generic behavior if this manifest is absent,
malformed, or incomplete.

## Electron Interfaces

Add a small interface in the desktop package:

```ts
export interface TelemetryProvider {
  beginSession(): Promise<void>
  endSession(): Promise<void>
  shutdown(): Promise<void>
}
```

`NullTelemetryProvider` implements all methods as no-ops.

`EpicEosTelemetryProvider` owns helper process lifecycle. It must:

1. Never throw from public lifecycle methods in a way that prevents app startup.
2. Log enough diagnostic information to the desktop log directory.
3. Avoid logging client secret, exchange code, auth password, or raw launcher
   auth arguments.
4. Time out helper startup.
5. Treat missing helper files as disabled EOS.

## Helper Protocol

Keep the first protocol simple. Use stdin/stdout JSON lines or process args
plus a shutdown signal. Avoid HTTP servers unless needed.

Example command:

```text
eos-helper.exe begin-session --config <path-to-eos-runtime.json>
```

Preferred long-running shape:

```text
Electron starts helper
Electron sends begin-session JSON
Helper ticks EOS SDK
Electron sends end-session JSON on shutdown
Helper exits
```

The helper should return structured status messages:

```json
{"type":"status","state":"starting"}
{"type":"status","state":"session_active"}
{"type":"error","code":"missing_exchange_code"}
{"type":"status","state":"session_ended"}
```

Errors are diagnostic only. The game remains playable.

## Security Rules

1. Never commit real `.env` files.
2. Never commit client secrets.
3. Never log client secrets or Epic exchange codes.
4. Do not reuse BuildPatchTool upload credentials as runtime credentials.
5. Do not expose EOS credentials to Vue.
6. Do not store EOS runtime state in save data.
7. Do not block game startup on EOS.
8. Keep EOS helper out of GitHub/generic packages.

## Failure Behavior

EOS must disable itself silently, with logs, in these cases:

1. Not an Epic distribution build.
2. Missing manifest.
3. Missing `eos-runtime.json`.
4. Missing helper executable or EOS dll.
5. Missing launcher auth arguments.
6. Offline Epic Launcher or missing exchange code.
7. SDK initialization failure.
8. Auth failure.
9. Metrics begin-session failure.
10. Metrics end-session failure during shutdown.

User-facing UI should not change for the first phase.

## Testing Plan

Contract tests:

1. Generic desktop packaging defaults to `epicEosMetrics: false`.
2. GitHub publishing scripts do not read `eos_runtime.env`.
3. Epic publishing scripts are the only scripts that may package EOS runtime
   files.
4. Generic/GitHub content roots must not contain `eos-helper.exe` or
   `EOSSDK-Win64-Shipping.dll`.
5. `eos_runtime.env.example` contains placeholders only.
6. No tests print real local EOS credentials.

Electron unit tests:

1. Missing manifest creates `NullTelemetryProvider`.
2. Generic manifest creates `NullTelemetryProvider`.
3. Epic manifest with missing helper logs and disables EOS.
4. Epic provider masks sensitive command-line values in logs.
5. Provider shutdown tolerates helper process exit/failure.

Manual Epic Dev test:

1. Package an Epic Dev build.
2. Upload it through the existing Epic BuildPatchTool flow.
3. Add the Dev artifact to an Epic library with a test key if needed.
4. Launch from Epic Games Launcher.
5. Confirm launcher args include the expected deployment id.
6. Confirm helper reports an active session.
7. Quit the game.
8. Confirm helper ends the session.
9. Check Epic backend Metrics/Analytics for Dev session activity after the
   expected reporting delay.

Manual Live checklist:

1. Switch active EOS runtime deployment to Live, or use `-EosEnv live`.
2. Confirm Live artifact deployment id matches the Live deployment.
3. Verify the packaged build does not contain Dev-only config.
4. Verify GitHub release artifacts still contain no EOS helper or EOS dll.

## Implementation Phases

### Phase 1: Spec and Config Scaffolding

1. Add this spec.
2. Add `eos_runtime.env.example` with placeholder fields.
3. Keep real values only in ignored `eos_runtime.env`.
4. Add packaging contract tests for config separation.

### Phase 2: Desktop Distribution Manifest

1. Add desktop distribution manifest generation.
2. Add default generic behavior.
3. Teach Epic packaging to generate Epic manifest/config.
4. Verify GitHub packaging remains unchanged.

### Phase 3: Electron Telemetry Adapter

1. Add `TelemetryProvider`.
2. Add `NullTelemetryProvider`.
3. Add `EpicEosTelemetryProvider` with helper lifecycle but no SDK dependency
   yet.
4. Add tests for disabled/failure behavior.

### Phase 4: C# EOS Helper

1. Add helper project.
2. Integrate local EOS C# SDK.
3. Implement SDK initialization, auth, begin session, tick loop, end session.
4. Publish self-contained Windows helper.
5. Package helper only in Epic builds.

### Phase 5: Dev Launcher Validation

1. Upload a Dev Epic build.
2. Launch through Epic Games Launcher.
3. Validate exchange-code auth and Metrics session reporting.
4. Iterate on logs and failure messages.

### Phase 6: Live Rollout

1. Switch Epic runtime deployment to Live.
2. Package and upload release build.
3. Verify Live analytics after launch.
4. Revisit custom minimal client policy after the first successful Live signal.

## Open Questions

1. Whether the C# helper requires Epic Account Auth only, Connect only, or both
   for the chosen Metrics call path.
2. Whether the packaged runtime config should include a sandbox id fallback or
   rely entirely on launcher arguments plus deployment id.
3. Whether helper logs should be surfaced in a developer-only diagnostics
   command later.
4. Whether a custom minimal client policy should replace `GameClient` before
   Live metrics become long-term operational data.

## References

1. Existing desktop packaging spec: `docs/specs/desktop-distribution-pipeline.md`
2. Short packaging command list: `docs/packaging.md`
3. Epic publish script: `tools/package/publish_epic.ps1`
4. Epic BuildPatchTool wrapper: `tools/package/epic/publish.ps1`
5. Electron main process: `desktop/src/main.ts`
6. Electron builder config: `desktop/electron-builder.config.cjs`
