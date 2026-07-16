# CommandCenterUI Agent Instructions

This is the installer-bundled CommandCenterUI copy. Keep it portable:

- Do not hard-code a workstation-specific MAP path.
- Launch through `command-center-ui`, which sets `COMMAND_CENTER_UI_WORKSPACE`.
- Keep the backend bound to `127.0.0.1` unless the operator explicitly scopes a
  network-exposed mode.
- Treat ProjectUpdater data as browser-localStorage owned; CommandCenterUI may
  launch/embed ProjectUpdater and read explicit status exports only.
- Do not add automatic approval behavior. Operator actions must stay explicit.

