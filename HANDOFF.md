# MCP Guard — Audit and Team Handoff

> **Document status:** Evidence-based report. All code claims are verified against the
> actual source files read on the date of this session. Recommendations are clearly
> labelled. No code changes have been applied to any file.
>
> **Last verified files:** `bank.py`, `guard.py` (no other source files exist in the repo)
> **Test files found:** None
> **Date of audit session:** Current hackathon session (see git log for exact timestamp)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Conversation Summary](#2-conversation-summary)
3. [Repository Structure](#3-repository-structure)
4. [Architecture (Planned vs Actual)](#4-architecture-planned-vs-actual)
5. [File-by-File Review](#5-file-by-file-review)
6. [Security Vulnerabilities and Weaknesses](#6-security-vulnerabilities-and-weaknesses)
7. [Feature Implementation Status](#7-feature-implementation-status)
8. [Tests: Required Cases and Current Coverage](#8-tests-required-cases-and-current-coverage)
9. [Recommended Implementation Order](#9-recommended-implementation-order)
10. [Claims We Must NOT Make During the Demo](#10-claims-we-must-not-make-during-the-demo)
11. [Judge Questions and Honest Answers](#11-judge-questions-and-honest-answers)
12. [Instructions for the Third Teammate](#12-instructions-for-the-third-teammate)

---

## 1. Project Overview

**MCP Guard** is a runtime security gateway for AI agents that use tool-calling
(MCP-connected or otherwise). The core idea: an AI agent should not be able to
call banking tools freely — every call must pass through a guard that validates,
authorizes, and audits the request before it reaches the backend.

**Demo scenario:** A fictional local bank (`bank.py`) exposes two operations —
`get_balance` and `transfer`. An AI agent sends requests through a guard layer
(`guard.py`) that enforces:

- A tool allowlist (only known tools may be called)
- Strict argument schemas (exact keys, correct types)
- User-to-account authorization (a user may only access accounts assigned to them)
- A full audit trail of every decision

**Hackathon angle:** This is security infrastructure *around* AI agents, not the
agent itself. The project addresses prompt injection, unauthorized tool use, and
unvalidated parameters — real, unsolved problems in production AI deployments.

---

## 2. Conversation Summary

> **Note:** The following is an accurate summary of the two prior exchanges, not
> verbatim transcripts. Exact wording may differ from what was originally typed.

### Session 1 — Architecture Explanation (Planning Only)

**Team request (summary):** Explain the project architecture, how the AI agent
communicates with the gateway and mock banking MCP server, and how to prevent
path traversal, command injection, and unauthorized access. No files to be
created or modified.

**Bob's response (summary):** Provided a full architecture explanation covering:

- What MCP (Model Context Protocol) is and how JSON-RPC 2.0 works
- The three-layer flow: AI Agent → MCP Guard → Mock Banking MCP Server
- Component table: Gateway, Policy Engine, Audit Logger, Dashboard (optional)
- Detailed mitigation strategies for each of the three threat types:
  - **Path traversal:** `os.path.realpath()` normalization, base-directory check,
    extension allowlist, null-byte rejection
  - **Command injection:** Shell metacharacter detection, strict regex allowlists
    per argument, JSON schema enforcement
  - **Unauthorized access:** API key / JWT validation, RBAC with per-tool role
    requirements, tool allowlist per agent, parameter-level account checks,
    rate limiting
- Recommended tech stack (Python + FastAPI or asyncio, official MCP SDK, plain
  JSON rules file, Flask dashboard)
- Suggested directory structure with `gateway/`, `banking_server/`, `agent/`,
  `policies/`, `dashboard/`
- A four-step hackathon demo flow showing a success call and three blocked attacks
- What makes the project hackathon-worthy (novel layer, live attack demo,
  extensible architecture)

### Session 2 — Full Code Audit (Read-Only)

**Team request (summary):** Audit-only review of `bank.py`, `guard.py`, and any
existing tests. Check the five organizer core requirements (A), six specific
security concerns (B), eleven planned features (C), and whether the implementation
is actually MCP (D). Produce an evidence-based report with file and line numbers.
Explicitly forbidden: no edits, no file creation, no speculative claims.

**Bob's response:** The full audit report, reproduced in sections 5–11 of this
document with all original line-number citations preserved.

---

## 3. Repository Structure

```
mcp-guard/
├── bank.py          ← Fictional bank backend (verified, 61 lines)
├── guard.py         ← Security gateway and policy engine (verified, 119 lines)
└── __pycache__/     ← Compiled bytecaches (auto-generated, not source)
```

**What does NOT exist (verified by directory listing):**

- No `tests/` directory
- No `test_*.py` or `*_test.py` files
- No `agent.py`
- No `dashboard/` or any HTML file
- No `policies/` directory or `rules.json`
- No `requirements.txt` or `pyproject.toml`
- No MCP SDK import or dependency anywhere

---

## 4. Architecture (Planned vs Actual)

### Planned Architecture (from Session 1)

```
AI Agent  ──►  MCP Guard (Gateway)  ──►  Mock Banking MCP Server
              (inspect, filter,
               log, block)
```

All communication uses MCP JSON-RPC 2.0 over stdio or HTTP/SSE. The guard is
a transparent proxy — the agent thinks it is talking to the bank, but the guard
intercepts every call.

### Actual Architecture (verified from source)

```
Python dict  ──►  handle_request()  ──►  get_balance() / transfer()
  (in-process)     (guard.py)             (bank.py, same process)
```

There is no network transport. There is no MCP SDK. The "request" is a plain
Python dictionary created in the same process that evaluates it. The guard calls
bank functions directly as Python function calls. This is a correct and working
local implementation, but **it is not MCP**.

### Gap Summary

| Planned layer | Actual state |
|---|---|
| MCP server (banking) | Not implemented — direct Python functions |
| MCP client (agent) | Not implemented — plain dict passed to function |
| JSON-RPC transport | Not implemented — no network layer |
| Guard as MCP proxy | Not implemented — guard calls functions directly |
| Agent script | Not implemented — only a `__main__` demo block |

---

## 5. File-by-File Review

### `bank.py` (61 lines)

**Purpose:** Fictional banking backend. No real data, no network calls.

**Data:** Three hardcoded accounts —
- `ACC-1001`: ₹25,000.00
- `ACC-1002`: ₹8,000.00
- `ACC-2001`: ₹40,000.00

**Functions:**

- `get_balance(account_id)` (line 11): Returns balance dict. Raises `KeyError`
  for unknown accounts. No other validation.

- `transfer(from_account, to_account, amount)` (line 23):
  - Line 25: Raises `KeyError` for unknown accounts
  - Line 28–29: Raises `ValueError` if source == destination
  - Line 31–32: Raises `ValueError` if amount is `bool` or non-numeric
  - Line 34–35: Raises `ValueError` if `amount <= 0`
  - Line 37–38: Raises `ValueError` if balance is insufficient
  - Lines 40–41: Mutates in-memory `ACCOUNTS` dict (state is lost on restart)
  - Returns a dict with `"status": "simulated"`

**`__main__` block (line 52):** Runs a balance check and a transfer directly,
bypassing the guard entirely.

**Safety:** Confirmed fictional — explicit comment at line 2, `"status": "simulated"`
in all transfer returns, no PINs, OTPs, or personal data.

---

### `guard.py` (119 lines)

**Purpose:** Policy engine and audit logger. Single entry point: `handle_request(request)`.

**Key data structures:**

- `ALLOWED_TOOLS` (line 8): `{"get_balance", "transfer"}` — the tool allowlist
- `USER_ACCOUNTS` (line 11–14): Maps user IDs to sets of permitted account IDs
  - `"riya"` → `{"ACC-1001", "ACC-1002"}`
  - `"arjun"` → `{"ACC-2001"}`
- `AUDIT_LOG` (line 16): Plain Python list — **in-memory only**

**`audit()` function (line 19):** Appends a dict with `time`, `user_id`, `tool`,
`allowed`, and `reason` to `AUDIT_LOG`. Does not write to any file.

**`handle_request()` flow (line 30):**

1. Extract `user_id`, `tool`, `args` from request dict
2. Validate `user_id` is a non-empty string (line 36)
3. Check tool is in `ALLOWED_TOOLS` (line 40)
4. Check `args` is a dict (line 44)
5. For `get_balance`: enforce exact key set `{"account_id"}` (line 49)
6. For `transfer`: enforce exact key set, validate amount type and sign (lines 56–69)
7. Validate `account_id` is a string (line 71)
8. Check source account is in user's permitted set (line 75)
9. For `transfer`: check destination is a string and in user's permitted set (lines 79–90)
10. Call bank function inside `try/except (KeyError, ValueError)` (lines 92–103)
11. Audit success (line 105) or caught exception (line 102)

**`__main__` block (line 109):** Runs one successful `get_balance` call and prints
the audit log. Does not demonstrate a blocked call.

---

## 6. Security Vulnerabilities and Weaknesses

> **Key:** 🔴 Bug / vulnerability | ⚠️ Gap / weakness | ✅ Working correctly | N/A Not applicable

### 6.1 Transfer Amount Validation

| Input value | Guard result | Bank result | Status |
|---|---|---|---|
| `0` | Blocked — `amount <= 0` (line 67) | Would also block | ✅ |
| `-100` | Blocked — `amount <= 0` | Would also block | ✅ |
| `True` | Blocked — `isinstance(bool)` check (line 63) | Would also block | ✅ |
| `False` | Blocked — same | Would also block | ✅ |
| `"500"` (string) | Blocked — `not isinstance(int, float)` (line 63) | Would also block | ✅ |
| `float('-inf')` | Blocked — `-inf <= 0` is `True` | Would also block | ✅ |
| `float('nan')` | 🔴 **Passes guard** | 🔴 **Corrupts balance** | **BUG** |
| `float('inf')` | 🔴 **Passes guard** | Blocked by insufficient funds | **BUG** |
| `10_000_000_000` | Passes guard | Blocked by insufficient funds | ⚠️ No explicit cap |

**Critical NaN explanation:**
In Python, any comparison involving `NaN` returns `False`. Therefore:
- `float('nan') <= 0` → `False` — the guard's check at line 67 does **not** trigger
- `float('nan') > 0` → also `False` — NaN passes as if it were a valid positive number
- At `bank.py` line 37: `balance < nan` → `False` — the insufficient-funds check also passes
- At `bank.py` line 40: `balance -= nan` → the account balance becomes `nan` permanently
  for the rest of the process lifetime

**Fix required (recommendation only — not yet applied):**
Add `import math` and insert `if not math.isfinite(amount):` before the `<= 0` check
in both `guard.py` (line 67) and `bank.py` (line 34).

**`float('inf')` explanation:**
`inf > 0` is `True`, so it passes the positivity check. At the bank, `balance < inf`
is always `True`, so "Insufficient funds" is raised. The bank stops it in practice,
but only by accident — the guard should block it explicitly.

**No maximum transfer cap:** No upper bound exists in either file. A valid user can
drain their entire account in a single call. This is a design gap, not a crash bug.

---

### 6.2 Audit Coverage

Every handled exit path in `handle_request()` generates exactly one audit entry.

| Exit path | Line | Audited? |
|---|---|---|
| Invalid `user_id` | 37–38 | ✅ |
| Tool not allowed | 41–42 | ✅ |
| Args not a dict | 45–46 | ✅ |
| Wrong keys for `get_balance` | 50–51 | ✅ |
| Wrong keys for `transfer` | 57–58 | ✅ |
| Non-numeric amount | 64–65 | ✅ |
| Non-positive amount | 68–69 | ✅ |
| Non-string account ID | 72–73 | ✅ |
| Source account unauthorized | 76–77 | ✅ |
| Non-string destination | 82–83 | ✅ |
| Destination account unauthorized | 86–90 | ✅ |
| `KeyError` / `ValueError` from bank | 102–103 | ✅ |
| Successful call | 105–106 | ✅ |
| **Any other exception** (e.g. `TypeError`, `RuntimeError`) | — | 🔴 **NOT audited** |

**Gap:** The `except` clause at line 101 catches only `(KeyError, ValueError)`.
Any other exception raised by `get_balance()` or `transfer()` propagates to the
caller with no audit entry written. If `bank.py` is ever changed to raise a
different exception type, that invocation will be silently unlogged.

---

### 6.3 Audit Persistence

`AUDIT_LOG` is defined at `guard.py` line 16 as `AUDIT_LOG = []`.

**Verified facts:**
- It is a plain Python list in module memory
- There is no `open()`, `write()`, `json.dump()`, database connection, or `atexit`
  handler anywhere in either file
- The `__main__` block prints the log to stdout — this is display only, not storage

**Conclusion:** Audit logs do not survive process termination. If the process is
restarted between the demo setup and the demo presentation, all log entries are lost.
This must be disclosed to judges if asked.

---

### 6.4 Authorization

**User identity (self-attested):**
`user_id` is read directly from the request dict at line 32. Any caller can claim
any user ID. There is no token, password, session cookie, or cryptographic credential.
This is acceptable for a demo but must not be presented as "authenticated."

**Source account authorization:** ✅ Enforced at line 75. The source `account_id`
must be in `USER_ACCOUNTS[user_id]`.

**Destination account authorization:** ✅ Enforced at line 85. The destination must
also be in the same user's account set. This means `riya` cannot transfer to
`arjun`'s account, which is safe — but it also means no inter-user transfers are
possible by design. This may surprise a judge.

**Authorization bypass:** None found. Both checks are inside `if` blocks that
`return` immediately on failure. There is no logic path that reaches the bank call
at line 92 while bypassing either check.

---

### 6.5 Other Input and Security Issues

| Issue | Finding |
|---|---|
| Extra/missing argument keys | Rejected by exact set comparison at lines 49, 56 ✅ |
| Unknown account IDs | `bank.py` raises `KeyError`, caught and audited at line 102 ✅ |
| Same-account transfer | Rejected by `bank.py` line 28–29, `ValueError` caught at line 102 ✅ |
| Insufficient balance | Rejected by `bank.py` line 37–38, `ValueError` caught ✅ |
| Path traversal | **Not applicable.** No file paths exist in any argument. Tools only accept account ID strings. |
| Command injection | **Not applicable.** No `subprocess`, `os.system`, `eval`, or `exec` exists anywhere. |
| Unsafe tool output handling | Tool output is returned as a Python dict. No shell execution or `eval` of results. ✅ |

---

## 7. Feature Implementation Status

> A feature is only "tested" if test code exists that verifies it. No test files
> exist in this repository, so nothing can be marked "implemented and tested."

| Feature | Status | Evidence |
|---|---|---|
| Tool allowlist | ✅ Implemented, not tested | `ALLOWED_TOOLS` set at `guard.py:8`; enforced at line 40 |
| Argument schema enforcement | ✅ Implemented, not tested | Exact key sets + type checks in `handle_request()` |
| User-to-account authorization | ✅ Implemented, not tested | `USER_ACCOUNTS` at line 11; enforced at lines 75, 85 |
| Audit logging (in-memory) | ✅ Implemented, not tested | `audit()` called on every code path |
| Fictional safety (no real data) | ✅ Implemented | Comment at `bank.py:2`; `"status":"simulated"` on transfers |
| Blocked-call demo case | ⚠️ Partial | `__main__` shows only a success case; no blocked call scripted |
| Explicit risk levels per tool | ❌ Not implemented | No risk metadata anywhere |
| Context-aware risk scoring | ❌ Not implemented | No scoring function exists |
| Human approval for high-risk calls | ❌ Not implemented | No approval workflow |
| Prompt-injection test suite | ❌ Not implemented | No test files of any kind |
| Taint tracking / poisoned-response containment | ❌ Not implemented | No taint flag or response inspection |
| Confused-deputy protection | ❌ Not implemented | No principal/delegate model |
| Explainable incident replay | ❌ Not implemented | No replay engine; audit is a flat list |
| Multi-agent trust boundaries | ❌ Not implemented | Single-user model only |
| Policy learning with rollback | ❌ Not implemented | Policy is hardcoded |
| Persistent audit logging | ❌ Not implemented | In-memory list only |
| MCP protocol (actual) | ❌ Not implemented | No MCP SDK; direct Python calls |
| Agent script | ❌ Not implemented | No `agent.py`; only a `__main__` demo block |
| Dashboard | ❌ Not implemented | No HTML, no Flask/FastAPI routes |

---

## 8. Tests: Required Cases and Current Coverage

### Current Coverage

**Zero test files exist.** Nothing has been tested by automated means.

### Required Test Cases

#### Transfer Amount Validation

```python
# These must be BLOCKED (currently: nan and inf are NOT blocked — BUG)
float('nan')            # BUG: passes both guard and bank, corrupts balance
float('inf')            # BUG: passes guard; bank blocks only by luck
float('-inf')           # OK: blocked by <= 0 check
0                       # OK: blocked
-1                      # OK: blocked
True                    # OK: blocked
False                   # OK: blocked
"500"                   # OK: blocked
None                    # OK: blocked (not numeric)

# These must be ALLOWED
0.01                    # smallest valid amount
500                     # normal integer
500.00                  # normal float
24999.99                # just under full balance — currently allowed (no cap)

# These expose the missing cap (no fix exists yet)
25000.0                 # drains full account — currently allowed
```

#### Permissions

```python
# Allowed
{"user_id": "riya",  "tool": "get_balance", "arguments": {"account_id": "ACC-1001"}}
{"user_id": "riya",  "tool": "transfer",    "arguments": {"from_account": "ACC-1001", "to_account": "ACC-1002", "amount": 500}}
{"user_id": "arjun", "tool": "get_balance", "arguments": {"account_id": "ACC-2001"}}

# Must be denied
{"user_id": "riya",         "tool": "get_balance", "arguments": {"account_id": "ACC-2001"}}  # arjun's account
{"user_id": "unknown_user", "tool": "get_balance", "arguments": {"account_id": "ACC-1001"}}  # unknown user
{"user_id": "riya",         "tool": "transfer",    "arguments": {"from_account": "ACC-1001", "to_account": "ACC-2001", "amount": 500}}  # destination not riya's
{"user_id": "",             "tool": "get_balance", "arguments": {"account_id": "ACC-1001"}}  # empty user_id
{"user_id": None,           "tool": "get_balance", "arguments": {"account_id": "ACC-1001"}}  # null user_id
```

#### Audit Coverage

```python
# For every deny case above: assert exactly one entry is appended to AUDIT_LOG
# with allowed=False and a non-empty reason string.

# For every success case above: assert exactly one entry with allowed=True.

# Unhandled exception path (requires monkeypatching):
# Patch get_balance to raise RuntimeError; assert an audit entry IS written.
# Currently: no entry is written — BUG.
```

#### Persistence

```python
# No test is possible with the current implementation.
# The feature does not exist. Any test would simply confirm absence.
```

---

## 9. Recommended Implementation Order

Work is ordered to satisfy organizer core requirements first, then security
correctness, then strong-tier features, then stretch goals.

### Priority 1 — Fix Before Any Demo (Bugs)

1. **Fix NaN and Inf validation in `guard.py`**
   Add `import math` and check `math.isfinite(amount)` before the `<= 0` check
   at line 67. Also add the same check to `bank.py` line 34 as defence-in-depth.

2. **Add a blocked-call demo case to `__main__`**
   Insert a second `handle_request()` call with a clearly malicious request
   (e.g. unknown tool, or `user_id="riya"` accessing `ACC-2001`) so the demo
   shows both success and denial side-by-side.

3. **Widen the `except` clause at `guard.py:101`**
   Change `except (KeyError, ValueError) as exc` to `except Exception as exc`
   (or add a final `except Exception` block that audits before re-raising) to
   ensure no invocation is silently unlogged.

### Priority 2 — Core Requirements (Judges Will Check)

4. **Add a transfer cap**
   Define `MAX_TRANSFER = 10_000` and check `amount > MAX_TRANSFER` in `guard.py`
   before passing to the bank. Audit and block if exceeded.

5. **Write a pytest test file**
   Cover all cases in Section 8. A test file with ~20 cases takes under an hour
   and directly addresses judge question "where are your tests?"

6. **Persist the audit log**
   In `audit()`, open `audit.jsonl` in append mode and write one JSON line per
   entry. This is a three-line change that turns the log into a real artifact.

### Priority 3 — Strong-Tier Features (Differentiators)

7. **Add risk metadata to tool definitions**
   Replace `ALLOWED_TOOLS` set with a dict like
   `{"get_balance": {"risk": "low"}, "transfer": {"risk": "high"}}`.

8. **Wrap `bank.py` as a real MCP server**
   Using `pip install mcp`, expose `get_balance` and `transfer` as MCP tool
   handlers. Run as a separate process. This is ~30 lines.

9. **Make `guard.py` an MCP proxy**
   Accept MCP JSON-RPC requests, run the existing `handle_request` policy logic
   unchanged, and if allowed, forward the call to the banking MCP server using
   an MCP client. The existing logic requires no changes.

10. **Write `agent.py`**
    A small script that connects to the guard (now an MCP server) and completes
    a routine task: check balance, then transfer ₹500. This is the end-to-end
    demo entrypoint.

### Priority 4 — Stretch Features (If Time Permits)

11. **Dashboard** — a minimal Flask route serving `audit.jsonl` as a JSON endpoint
    with a single-page HTML viewer.

12. **Context-aware risk scoring** — combine tool risk level + transfer amount +
    user history into a numeric score; block or flag calls above a threshold.

13. **Human-approval stub** — for calls scoring above the high-risk threshold, print
    a confirmation prompt before proceeding (even a `input()` call is sufficient
    for a demo).

---

## 10. Claims We Must NOT Make During the Demo

The following claims are **not supported by the current code**. Making them to
judges without qualification risks credibility damage if challenged.

| ❌ Claim to avoid | Why it is false |
|---|---|
| "The system uses MCP" | Communication is direct Python function calls, not MCP JSON-RPC |
| "Audit logs are persistent / stored securely" | The log is a Python list; it is lost when the process exits |
| "Users are authenticated" | `user_id` is self-attested; there are no credentials |
| "The system is safe against all numeric edge cases" | NaN and Inf pass validation and can corrupt state |
| "The guard is tested" | No test file exists; nothing has been run |
| "We have a dashboard" | No frontend exists |
| "Risk scoring is implemented" | No scoring function or risk variable exists |
| "We handle prompt injection" | No prompt-injection detection or test suite exists |
| "The system supports multiple agents" | Single hardcoded user table; no multi-agent model |

---

## 11. Judge Questions and Honest Answers

These are questions a judge is likely to ask, with honest answers based on the
current code state.

| Judge question | Honest answer |
|---|---|
| "If I send `amount: NaN`, what happens?" | Currently it passes validation and corrupts the in-memory account balance. This is a known bug that has not yet been fixed. |
| "How does the system know the request is really from Riya?" | It doesn't. `user_id` is self-declared in the request. There are no credentials. |
| "Where are your audit logs stored? Can I see the file?" | The log is in-memory for this session only. There is no log file yet. |
| "Is this actually using MCP? Can you show me the server process?" | Not yet. The current implementation uses direct Python calls. We plan to add the MCP transport layer next. |
| "What happens if the bank throws an unexpected error?" | It propagates to the caller without an audit entry. We know this is a gap. |
| "Can Riya transfer money to Arjun's account?" | No — by policy design, destination accounts must belong to the same user. Inter-user transfers are not yet supported. |
| "Where are your tests?" | We don't have automated tests yet. Writing them is the next task. |
| "What's your transfer limit? Can someone send ₹100 crore?" | No per-call cap exists. Only the account balance prevents it. We need to add an explicit limit. |
| "What is the risk score for this call?" | Risk scoring is not yet implemented. |

---

## 12. Instructions for the Third Teammate

Welcome to the project. Here is everything you need to get up to speed and
start contributing immediately.

### What the project is

MCP Guard is a security gateway that sits between an AI agent and a fictional
banking backend. Every tool call the agent makes is intercepted, validated,
authorized, and logged. The project demonstrates that AI agents should not have
unmediated access to sensitive tools.

### Current code state (honest summary)

- **`bank.py`** — a clean, safe fictional bank with `get_balance` and `transfer`.
  Works correctly for normal inputs.
- **`guard.py`** — a working policy engine that validates and authorizes requests.
  Has two confirmed bugs (NaN/Inf pass through) and one gap (no audit on unexpected
  exceptions). No tests exist.
- **Everything else** — not yet built. No MCP server, no agent, no tests, no dashboard,
  no persistent logs.

### How to run what exists

```bash
cd mcp-guard

# Run the bank demo directly (bypasses guard)
python bank.py

# Run the guard demo (one success case + audit printout)
python guard.py
```

### First tasks you can do right now

These are the highest-priority items from the build order:

**Task 1 — Fix NaN/Inf validation in `guard.py`**
- Open `guard.py`
- Add `import math` at the top
- After line 67 (`if amount <= 0:`), add a preceding check:
  `if not math.isfinite(amount): ...` (block and audit)
- Add the same check to `bank.py` line 34 as defence-in-depth

**Task 2 — Add a blocked-call demo to `__main__` in `guard.py`**
- After the existing demo dict, add a second dict with a request that should
  be denied (e.g. `user_id="riya"` accessing `account_id="ACC-2001"`)
- Print both results so the demo shows a success and a denial side-by-side

**Task 3 — Write `tests/test_guard.py`**
- Create a `tests/` directory and a `test_guard.py` file
- Write pytest cases covering all inputs listed in Section 8
- Run with `pytest tests/`
- Priority: NaN, Inf, and all permission denial cases first

**Task 4 — Persist the audit log**
- In `guard.py`'s `audit()` function, add three lines to append each entry as
  a JSON line to `audit.jsonl`
- Verify by running `python guard.py` and checking the file was created

### Design decisions already made (do not change without team discussion)

- All accounts and data are fictional — never add real account numbers
- `USER_ACCOUNTS` is the source of truth for who owns which account
- The `audit()` function must be called on every exit path — do not add returns
  without adding an audit call
- `bank.py` must remain callable directly (bypassing the guard) for testing

### Communication norms

- Do not commit code that breaks the existing `python guard.py` demo run
- Do not remove the `"status": "simulated"` marker from transfer results
- Label any claim in the demo script with its evidence source
- If you are unsure whether a feature exists, read the file before asserting it

---

*End of handoff document. All code citations verified against source files read
during this session. No code changes have been applied.*
