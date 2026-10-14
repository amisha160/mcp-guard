\# MCP Guard — AI Prompts and Development Record



\## Purpose



This document records AI-assisted work on MCP Guard so all team members can understand the prompts, findings, implementation decisions, and verification results.



\## 1. Bob's Security Audit



\*\*Source:\*\* Bob's conversation  

\*\*Status:\*\* Handoff summary available; full original report should be preserved separately.



\### Findings reported in the handoff summary



\- Transfer amount validation may mishandle `NaN` and infinity values.

\- Audit logging is stored in memory and does not persist across restarts.

\- Automated tests were not present at the time of the audit.

\- The project uses a local Python gateway and bank functions; the current implementation is not yet a complete MCP client/server architecture.

\- User identity is supplied in the request and is not independently authenticated.



\*\*Note:\*\* Verify each finding against the current source code before making changes.



\## 2. ChatGPT Development Plan



The planned implementation order is:



1\. Review amount validation and authorization checks.

2\. Add automated tests for valid and invalid transfers, permissions, malformed arguments, and audit coverage.

3\. Improve audit logging and test persistence if implemented.

4\. Add an explicit tool inventory and risk levels.

5\. Implement and test the actual MCP server/client integration.

6\. Add explainable risk scoring and human approval for high-risk calls.

7\. Build prompt-injection and poisoned-response containment tests.

8\. Prepare a demo showing a legitimate request succeeding and a malicious request being blocked with an audit record.

9\. Add incident replay and other stretch features only after the core flow works.



\## 3. Verification Record



Record each change using this template:



\### Change: \[short description]



\- \*\*Date:\*\*

\- \*\*Prompt used:\*\*

\- \*\*Files changed:\*\*

\- \*\*Expected behavior:\*\*

\- \*\*Tests run:\*\*

\- \*\*Actual results:\*\*

\- \*\*Known limitations:\*\*

\- \*\*Commit:\*\*



Do not mark a feature as implemented or tested without evidence.



\## 4. Team Rules



\- Review existing code before modifying it.

\- Coordinate edits to avoid overwriting another teammate's work.

\- Use fictional banking data only.

\- Never commit passwords, API keys, tokens, or other secrets.

\- Keep the GitHub repository as the shared source of truth.

\- Distinguish recommendations from implemented changes and verified test results.



\## 5. Original AI Conversation References



Add links or copies of the original prompts and responses here when available. Summaries must be labelled as summaries; do not present reconstructed wording as an exact quotation.

