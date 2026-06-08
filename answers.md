# Deep-Dive Questions

## Question 1: Guardrails for `device_reboot` on Healthy Devices

Language models can misinterpret data and trigger a reboot on a device that is operating normally. To prevent this, I would implement several layers of protection between the MCP Server and the physical hardware:

**1. Pre-condition check inside the tool**
Before dispatching the reboot command, the tool queries the latest telemetry and verifies that the device actually shows signs of a problem — elevated power consumption, temperature above a threshold, or a recent anomaly flag. If the device reads as healthy, the tool returns a warning instead of proceeding.

**2. Human-in-the-loop confirmation**
For destructive or irreversible actions like a reboot, the tool first returns a confirmation request to the LLM (e.g. `"requires_confirmation": true, "summary": "DEV-003 is currently healthy. Are you sure you want to reboot?"`). The LLM must receive explicit user approval before the second call that actually sends the command.

**3. Rate limiting and cooldown**
The server enforces a cooldown period per device (e.g. no more than one reboot per 5 minutes). This prevents the model from triggering a reboot loop if it keeps re-evaluating the same incorrect conclusion.

**4. Audit log**
Every reboot command — whether executed or rejected — is written to an immutable audit log with a timestamp, the device ID, the triggering reason, and whether a human confirmed it. This allows post-incident review.

**5. Role-based access at the hardware gateway**
The MCP Server itself should not have direct hardware access. Reboot commands should go through a separate hardware gateway that applies its own authorization checks, ensuring that even a compromised MCP Server cannot cause damage without a second layer of approval.

---

## Question 2: When to Use Predefined MCP Prompts in an Energy Monitoring System

MCP Prompts are predefined templates that guide the model toward a specific, repeatable task. They are useful when the interaction is predictable and the cost of an incorrect or creative response is high.

**Scenario 1: Daily fleet health report**
A prompt template like `"Summarize the current state of the fleet. List any anomalies, their severity, and recommend actions."` ensures the model always produces a structured, consistent report rather than an open-ended response that differs each run. This is important for reports that go to humans or downstream systems.

**Scenario 2: Anomaly investigation workflow**
When an anomaly is detected, a prompt can guide the model step by step: first read telemetry, then compare against the baseline, then decide whether to escalate or reboot. This prevents the model from skipping steps or jumping straight to a destructive action.

**Scenario 3: On-call alerts**
When a device breaches a threshold at 3am and an on-call engineer asks "what happened?", a prompt can pre-load the relevant context (device ID, last 24h readings, anomaly details) so the model gives a focused, factual answer instead of a generic one.

**Scenario 4: Compliance-driven queries**
In regulated industries, energy usage must be reported in a fixed format. A prompt that enforces the exact output structure (fields, units, time ranges) ensures the model cannot deviate from the required format.

In summary: use MCP Prompts when the task is routine, the output format must be consistent, or the stakes of a wrong interpretation are high. Use open-ended Tools when the model needs flexibility to reason about unfamiliar situations.
