# 🛡️ MCP Guard

> **⚠️ SIMULATED DEMO — All accounts, balances, and transactions are entirely fictional.
> No real financial data is used or stored anywhere in this project.**

MCP Guard is a runtime security gateway that intercepts every AI agent tool call before
it reaches a sensitive banking backend. It validates, authorises, and audits each request,
blocking anything that violates policy.

Built as a college hackathon project demonstrating how to secure AI-accessible tools using
the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) pattern.

---

## Architecture

```
AI Agent / Dashboard
        │
        ▼
  guard.handle_request()          ← Policy engine (guard.py)
        │
        ├── Tool allowlist check
        ├── Argument schema check
        ├── User-to-account authorisation
        ├── Amount validation (finite, positive, ≤ ₹10,000)
        ├── Audit log entry written
        │
        ▼  (if allowed)
  bank.get_balance() / bank.transfer()    ← Fictional backend (bank.py)
        │
        ▼
  Result or pending-approval response
```

All communication is in-process Python (no network transport in the current prototype).
The guard pattern mirrors an MCP proxy: every tool call must pass through the policy engine.

---

## Fictional Mock Accounts

| Account ID | Balance (INR) | Owner(s)        |
|------------|---------------|-----------------|
| ACC-1001   | ₹25,000.00    | riya            |
| ACC-1002   | ₹8,000.00     | riya            |
| ACC-2001   | ₹40,000.00    | arjun           |

Balances are in-memory and reset to these values on every process restart.

---

## Security Policies

| Policy                  | Detail                                                                 |
|-------------------------|------------------------------------------------------------------------|
| Tool allowlist          | Only `get_balance` and `transfer` may be called                        |
| Exact argument schema   | Extra or missing keys are rejected                                     |
| User-to-account auth    | Users may only access accounts assigned to them                        |
| Amount validation       | Must be numeric (not bool), finite (no NaN/Inf), positive, and ≤ ₹10k |
| Approval workflow       | All transfers are queued; no money moves until `admin` approves        |
| Full audit trail        | Every request (allowed or denied) is logged to `audit.jsonl`          |

---

## Project Structure

```
mcp-guard/
├── bank.py              ← Fictional banking backend (get_balance, transfer)
├── guard.py             ← Security policy engine and audit logger
├── dashboard.py         ← Streamlit interactive security dashboard
├── requirements.txt     ← Python dependencies
├── audit.jsonl          ← Persistent audit log (JSONL, one entry per line)
├── tests/
│   ├── test_bank.py
│   ├── test_guard.py
│   ├── test_guard_audit.py
│   ├── test_prompt_injection.py
│   └── test_transfer_approval.py
├── docs/
│   ├── DEMO_SCRIPT.md
│   ├── AI_PROMPTS.md
│   └── PROMPT_INJECTION_TEST_PLAN.md
└── HANDOFF.md           ← Full code audit and team handoff notes
```

---

## Dashboard Features

The Streamlit dashboard (`dashboard.py`) provides six interactive sections:

| Section               | What it does                                                              |
|-----------------------|---------------------------------------------------------------------------|
| 🏦 Account Overview   | Read-only view of all fictional accounts, balances, and user permissions  |
| 🔧 Tool Inventory     | Full details of every tool registered in the guard (risk level, args, ACL)|
| 💰 Balance Check      | Submit balance requests through the guard; see live allow/deny decisions  |
| 💸 Transfer Request   | Submit transfers; they queue for approval — no money moves immediately    |
| ⏳ Pending Approvals  | Admin view; approve or reject queued transfers via `approve_transfer()`   |
| 📋 Audit Log          | Tabbed view of session and persistent audit records, with security alerts  |

All buttons and forms call the **actual** `guard.handle_request()`,
`approve_transfer()`, and `reject_transfer()` functions — no mock responses.

---

## Installation

### Prerequisites

- Python 3.11 or newer
- `pip`

### Install dependencies

```bash
pip install -r requirements.txt
```

Or install just Streamlit manually:

```bash
pip install streamlit
```

---

## Running the Dashboard

```bash
streamlit run dashboard.py
```

Then open your browser to:

```
http://localhost:8501
```

---

## Running the Tests

```bash
python -m pytest tests/ -q
```

Expected output:

```
90 passed in 0.XX s
```

The test suite covers:

- Allowed and denied balance requests (REQ-1, REQ-2)
- Unknown tools, unauthorized accounts, invalid user IDs (REQ-3)
- Malformed arguments including booleans, NaN, Inf, strings (REQ-4, REQ-6)
- Rejected transfers leaving balances unchanged (REQ-5)
- Unexpected bank exceptions audited and returned safely (REQ-7)
- Full approval workflow: queue → approve / reject → balance verification
- Prompt injection and shell-injection attempts

---

## Running the Guard Demo (CLI)

```bash
python guard.py
```

Prints a sample `get_balance` result and the in-memory audit log.

---

## Environment Variables

| Variable              | Default      | Description                              |
|-----------------------|--------------|------------------------------------------|
| `MCP_GUARD_AUDIT_LOG` | `audit.jsonl`| Path to the persistent JSONL audit file  |

---

## Known Limitations and Security Considerations

### Prototype limitations

- **User identity is self-attested.** `user_id` comes from the request dict —
  there are no passwords, tokens, or cryptographic credentials.
  Do not use this as-is in a system with real users.

- **In-memory state.** Account balances and the pending-approval queue are stored
  in Python module memory. They reset on every process restart.
  The `audit.jsonl` file survives restarts; balances and pending transfers do not.

- **No network transport.** The guard calls bank functions directly as Python
  function calls in the same process. A production MCP proxy would use JSON-RPC
  over stdio or HTTP/SSE with a separate bank server process.

- **Admin approver is hardcoded.** Only `"admin"` is a valid approver ID
  (`guard.APPROVER_IDS`). This is a demo-only stub.

- **No cross-user transfers.** By policy, a user's destination account must also
  belong to them. Riya cannot transfer to Arjun's account. This is intentional.

### Security design that IS working

- Tool allowlist enforced on every call
- Exact argument schema validation (extra keys rejected)
- All numeric edge cases handled: NaN, ±Inf, bool, string, zero, negative
- Transfer cap of ₹10,000 per call
- Every request — allowed or denied — produces an audit entry
- Transfers are queued, not executed immediately
- Approval IDs are single-use UUIDs (cannot be replayed)

---

## Git Workflow

```bash
# Review changes
git diff HEAD

# Stage and commit
git add dashboard.py requirements.txt README.md
git commit -m "feat: add Streamlit security dashboard"

# Push
git push origin ci/github-actions
```

---

## Disclaimer

This project uses entirely **fictional mock data** for educational and demonstration purposes.

- No real bank accounts, customers, or financial institutions are represented.
- No personal or financial data is collected, stored, or transmitted.
- This software is not suitable for use in any real financial system.
