# AGENTS

## MQTT script shutdown guidance

- Keep MQTT shutdown handling simple by default.
- For small CLI utilities in this repo, assume users stop with Ctrl+C.
- Do not add complex signal-handling and disconnect orchestration unless there is a demonstrated reliability issue.
- Prefer straightforward `KeyboardInterrupt`-friendly loops and minimal cleanup code.
