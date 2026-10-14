# MCP Guard — Secure MCP Banking Demo

A Python project demonstrating how to protect banking tools exposed through the Model Context Protocol (MCP).

## Features

- MCP server using FastMCP over stdio
- Guarded account balance queries
- Authorization checks for account access
- Risk scoring and transfer limits
- Transfer approval workflow
- Audit and security monitoring
- Automated security and integration tests

## Architecture

MCP client → MCP server → Guard authorization and risk checks → Mock banking layer

Transfers are queued for approval before execution. This project uses fictional accounts and simulated banking operations. It is a demonstration, not production banking software.

## Requirements

- Python 3.10+
- MCP Python SDK compatible with the installed server code
- pytest

## Setup

Install dependencies:

```bash
python -m pip install "mcp<2" pytest
```

Run the MCP server:

```bash
python bank_mcp_server.py
```

Run the MCP client integration test in another terminal:

```bash
python test_mcp_client.py
```

Run the test suite:

```bash
python -m pytest -q
```

## Security notes

- Access is checked before protected operations.
- Transfers require approval.
- Approval IDs cannot be reused to execute the same transfer twice.
- Caller-supplied user IDs are not independently authenticated in this demo.
- Do not connect this demo to real banking accounts or production systems.

## Repository

https://github.com/amisha160/mcp-guard
