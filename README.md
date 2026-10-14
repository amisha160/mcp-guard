\# MCP Guard



MCP Guard is a Python-based security layer for controlling access to banking tools. It validates tool requests, checks account permissions, applies transfer limits, and queues high-risk transfers for approval.



\## Features



\- \*\*Tool allowlisting:\*\* Only registered tools can be called.

\- \*\*Argument validation:\*\* Rejects missing, unexpected, or incorrectly typed arguments.

\- \*\*Account authorization:\*\* Checks whether a user is permitted to access the requested account.

\- \*\*Transfer limits:\*\* Rejects invalid, non-finite, non-positive, or over-limit transfer amounts.

\- \*\*Transfer approval:\*\* Queues transfers for approval before executing them.

\- \*\*Approval controls:\*\* Supports approving or rejecting pending transfers and prevents reuse of consumed approval IDs.

\- \*\*Audit logging:\*\* Records security decisions in an in-memory log and attempts to append them to a JSON Lines file.

\- \*\*Automated tests:\*\* Uses pytest to verify security rules and transfer behavior.



\## Project Structure



```text

mcp-guard/

├── bank.py

├── guard.py

└── tests/

```



Additional files may be present depending on the project version.



\## Requirements



\- Python 3

\- pytest to run the test suite



Install pytest if needed:



```powershell

python -m pip install pytest

```



\## Run the Demo



From the project directory, run:



```powershell

python guard.py

```



The script demonstrates a balance request and prints the resulting audit log.



\## Run the Tests



Run the complete test suite with:



```powershell

python -m pytest tests/ -v

```



The tests cover request validation, authorization, prompt-injection-style inputs, transfer approval, and security edge cases.



\## Transfer Approval Workflow



1\. A user submits a transfer request.

2\. MCP Guard validates the tool, arguments, amount, and account permissions.

3\. A valid high-risk transfer is placed in the pending approval queue. No money moves at this stage.

4\. An authorized approver approves or rejects the request.

5\. An approved transfer is executed, while a rejected transfer does not move money.

6\. The decision is recorded in the audit log.



\## Security Limitations



This project is a prototype and is not production-ready.



\- Approver identity is represented by a hardcoded demo allowlist.

\- Pending approvals and the in-memory audit list do not survive process restarts.

\- Audit file write failures are suppressed, so a successful security decision does not guarantee that the record was persisted.

\- Production deployments would need trusted authentication, stronger authorization, durable and protected audit storage, and appropriate concurrency controls.



\## Future Improvements



\- Integrate a trusted authentication and authorization provider.

\- Persist pending approvals securely.

\- Improve audit-log durability and monitoring.

\- Add concurrency and failure-recovery tests.

\- Configure continuous integration to run tests automatically on pull requests.



\## Disclaimer



MCP Guard is an educational security prototype. Do not use it to protect real banking transactions without substantial additional security engineering and independent review.

