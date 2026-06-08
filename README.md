# Fleet Management MCP Server

An MCP (Model Context Protocol) server that allows an AI agent (Cursor, Claude Desktop) to query device telemetry, detect efficiency anomalies, and trigger device reboots on an industrial device fleet.

---

## Project Structure

```
mcp-server-challenge/
├── main.py                              ← Thin MCP entry point (exposes `mcp` for CLI)
├── fleet/
│   ├── data/
│   │   ├── fleet_config.json            ← Fleet device list and settings (loaded at startup)
│   │   ├── fleet_data.py                ← Loads config + builds in-memory telemetry history
│   │   └── telemetry_seed_builder.py    ← Generates 48 hourly readings per device
│   ├── validation/
│   │   ├── device_validator.py          ← Input validation (regex, allowlist, length)
│   │   └── exceptions.py                ← InvalidDeviceIdError
│   ├── services/
│   │   ├── telemetry_service.py         ← Latest snapshot per device
│   │   ├── anomaly_service.py           ← 24h baseline comparison + response shaping
│   │   └── reboot_service.py            ← Reboot simulation with guardrails
│   └── server/
│       └── fleet_management_server.py   ← FastMCP registration (resources + tools)
├── tests/
│   ├── conftest.py                      ← Shared `server` fixture
│   ├── test_fleet_management.py         ← Business logic and tool handler tests
│   └── test_part_a_mcp.py               ← MCP protocol tests (list_tools, call_tool, read_resource)
├── mcp-config.json                      ← Cursor / Claude Desktop connection config
├── pyproject.toml                       ← Project dependencies (used by uv)
├── uv.lock                              ← Locked dependency versions
└── answers.md                           ← Deep-dive question answers
```

---

## Setup

**Requirements:** Python 3.11+, [uv](https://github.com/astral-sh/uv)

```bash
# 1. Install dependencies (creates .venv automatically)
uv sync --extra dev

# 2. Verify the server starts
uv run mcp run main.py

# 3. Run automated tests
uv run pytest
```

---

## Connecting to Cursor

**Recommended:** this repo includes `.cursor/mcp.json` — Cursor loads it automatically when you open the project as your workspace.

Otherwise, copy from `mcp-config.json` into Cursor → Settings → MCP.

Use the project venv `mcp` CLI (not system `python -m mcp`):

| OS | `"command"` | `"args"` |
|---|---|---|
| Windows | `${workspaceFolder}/.venv/Scripts/mcp.exe` | `["run", "main.py"]` |
| Mac / Linux | `${workspaceFolder}/.venv/bin/mcp` | `["run", "main.py"]` |

Always set `"cwd": "${workspaceFolder}"`.

**Steps:**

1. Run `uv sync --extra dev` once after cloning (creates `.venv` with `mcp[cli]`)
2. Open this project folder as your Cursor workspace
3. Restart the MCP server (or restart Cursor)
4. Confirm `fleet-management` shows as connected with 3 tools

**Troubleshooting:** if you see `python.exe: No module named mcp`, Cursor is using system Python instead of the project venv. Remove any config that uses `"command": "python"` with `"-m", "mcp", "run", "main.py"` and use the venv `mcp.exe` path above.

The server will appear as `fleet-management` in the tool list.

---

## Part A: MCP Server Capabilities

### Resource

| URI | Description |
|---|---|
| `devices://fleet-config` | Returns the full fleet configuration from `fleet/data/fleet_config.json` |

### Tools

| Tool | Input | Description |
|---|---|---|
| `get_device_telemetry` | `device_id: str` | Returns the latest voltage, current, temperature, and power for a device |
| `calculate_efficiency_anomalies` | _(none)_ | Compares each device's last 24h power average to its historical baseline; returns anomalous devices |
| `reboot_device` | `device_id: str` | Simulates sending a reboot command to a device; returns operation status |

---

## Example Tool Outputs

### `get_device_telemetry("DEV-001")`

```json
{
  "device_id": "DEV-001",
  "timestamp": "2026-06-06T23:00:00+00:00",
  "voltage": 220.2,
  "current": 10.6,
  "temperature": 65.6,
  "power_watts": 2334.12
}
```

### `calculate_efficiency_anomalies()`

```json
{
  "status": "anomalies_detected",
  "summary": "2 of 5 devices anomalous, worst: DEV-004 (+101.0%)",
  "anomaly_count": 2,
  "truncated": false,
  "anomalies": [
    {
      "device_id": "DEV-004",
      "name": "Heat Exchanger D",
      "location": "Plant 2 - Zone B",
      "historical_average_power_watts": 2255.82,
      "recent_average_power_watts": 4534.9,
      "percent_increase": 101.0
    },
    {
      "device_id": "DEV-002",
      "name": "Pump Station B",
      "location": "Plant 1 - Zone B",
      "historical_average_power_watts": 2425.55,
      "recent_average_power_watts": 4410.83,
      "percent_increase": 81.8
    }
  ]
}
```

### `reboot_device("DEV-002")` — anomalous device

```json
{
  "device_id": "DEV-002",
  "status": "reboot_command_sent",
  "message": "Reboot command successfully dispatched to DEV-002. Device will restart within 30 seconds."
}
```

### `reboot_device("DEV-001")` — healthy device (rejected)

```json
{
  "device_id": "DEV-001",
  "status": "reboot_rejected",
  "error": "Device is operating within normal parameters. Reboot is only allowed for anomalous devices."
}
```

---

## Testing

```bash
# All tests
uv run pytest -v

# Part A MCP protocol tests only
uv run pytest tests/test_part_a_mcp.py -v

# Business logic tests only
uv run pytest tests/test_fleet_management.py -v
```

| Test file | What it covers |
|---|---|
| `test_fleet_management.py` | Services, validation, tool handlers, reboot guardrails |
| `test_part_a_mcp.py` | MCP registration, `read_resource`, `call_tool` end-to-end |

---

## Part B: Security and Optimization

### Input Validation (Tool Safety)

All `device_id` inputs are validated in `fleet/validation/device_validator.py` before reaching any business logic:

- Type check — must be a string
- Length check — max 20 characters (prevents buffer-style abuse)
- Format check — strict regex `DEV-\d{3}` (rejects SQL fragments, path traversal, script injections)
- Existence check — must be a known device ID from `fleet_config.json`
- Safe error messages — invalid input is rejected without echoing the raw value back to the LLM

Any invalid input returns a structured `{"error": "..."}` response instead of raising an unhandled exception.

Data is currently in-memory (no SQL), so injection protection is enforced at the input-validation layer. In production with a real database, the same validated IDs would be passed via parameterized queries.

### Context Optimization

Instead of returning all 48 raw telemetry rows per device, the tools return only what the LLM needs:

- `get_device_telemetry` returns a **single aggregated snapshot** (the latest reading + computed power)
- `calculate_efficiency_anomalies` runs the comparison server-side and returns a **summary line** plus capped anomaly details (top 5 by severity), not raw readings
- `devices://fleet-config` returns **compact JSON** (no pretty-printing) to reduce whitespace tokens

This keeps token usage minimal and prevents context window overflow when the fleet scales.

### Reboot Guardrails (Dangerous Action Protection)

`reboot_device` has additional checks beyond input validation:

- **Anomaly pre-condition** — reboot is rejected if the device is not flagged by `calculate_efficiency_anomalies`
- **Per-device cooldown** — enforced using `reboot_cooldown_seconds` from `fleet_config.json` (default: 5 minutes)
- **Structured rejection** — returns `reboot_rejected` with a reason instead of executing the command
