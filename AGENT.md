# Agent Guidelines — Fleet Management MCP Server

How to work with this codebase. Read this before making changes.

---

## Project overview

MCP server that exposes fleet telemetry, anomaly detection, and reboot tools to an AI agent (Cursor / Claude Desktop).

```
main.py                          → exposes `mcp` for CLI (`mcp run main.py`)
fleet/server/fleet_management_server.py  → registers resources + tools
fleet/data/                      → fleet_config.json + seeded telemetry
fleet/validation/                → DeviceValidator (input safety)
fleet/services/                  → TelemetryService, AnomalyService, RebootService
```

---

## Code philosophy

- **Simple over clever** — smallest change that solves the problem
- **Readable first** — full-word names, type hints, no acronyms (`device_validator` not `dv`)
- **No over-engineering** — no extra layers unless the task clearly needs them
- **No comments or docstrings** unless logic is genuinely non-obvious
- **Match existing patterns** — follow the `fleet/` package layout already in place

---

## Where to change what

| Task | File(s) to edit |
|---|---|
| Add/modify MCP tool or resource | `fleet/server/fleet_management_server.py` |
| Change fleet devices or settings | `fleet/data/fleet_config.json` |
| Change telemetry seed data | `fleet/data/telemetry_seed_builder.py` |
| Input validation rules | `fleet/validation/device_validator.py` |
| Telemetry read logic | `fleet/services/telemetry_service.py` |
| Anomaly detection / response shape | `fleet/services/anomaly_service.py` |
| Reboot guardrails / cooldown | `fleet/services/reboot_service.py` |
| MCP connection config | `mcp-config.json`, `.cursor/mcp.json` |
| Tests (business logic) | `tests/test_fleet_management.py` |
| Tests (MCP protocol) | `tests/test_part_a_mcp.py` |

**Do not** put business logic in `main.py` — keep it a thin entry point.

---

## Development flow

```bash
uv sync --extra dev          # install deps (uses mcp[cli])
uv run pytest -v             # run all 29 tests
uv run mcp run main.py       # start MCP server (stdio)
```

1. Read the relevant service/validator file first
2. Make the smallest change
3. Run `uv run pytest -v` before finishing
4. If adding a tool: register in `FleetManagementServer`, add test in both test files

---

## MCP tool conventions

- Tools that take `device_id` must call `DeviceValidator.validate()` first
- Invalid input returns `{"error": "..."}` — never raise to MCP
- `reboot_device` must keep anomaly pre-check and cooldown (production guardrail)
- `calculate_efficiency_anomalies` returns summary + capped list, not raw readings

---

## Testing conventions

- Use the `server` fixture from `tests/conftest.py` (`FleetManagementServer` instance)
- `test_fleet_management.py` — call services/tools directly
- `test_part_a_mcp.py` — call via `mcp.list_tools()`, `mcp.call_tool()`, `mcp.read_resource()`
- Reboot tests must call `server.reboot_service.clear_reboot_timestamps()` (handled by fixture)

---

## What to avoid

- System `python -m mcp` — use project `.venv/Scripts/mcp.exe` (see `mcp-config.json`)
- Returning all 48 telemetry rows to the LLM — return snapshots/summaries only
- Bypassing `DeviceValidator` for any user-supplied `device_id`
- Adding abstractions (repositories, factories) — services + data module is enough here

---

## Extra reference

- Architecture diagram: [`extras/architecture.html`](extras/architecture.html) — open in browser
- Part C integration log: [`integration/integration-log.md`](integration/integration-log.md)
- Deep-dive answers: [`answers.md`](answers.md)
