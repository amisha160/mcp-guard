from mcp.server.fastmcp import FastMCP
import guard

mcp = FastMCP("MCP Guarded Banking Server")


@mcp.tool()
def get_balance(user_id: str, account_id: str) -> dict:
    """Get a bank balance after guard authorization checks."""
    return guard.handle_request({
        "user_id": user_id,
        "tool": "get_balance",
        "arguments": {"account_id": account_id},
    })


@mcp.tool()
def transfer(
    user_id: str,
    from_account: str,
    to_account: str,
    amount: float,
) -> dict:
    """Request a guarded transfer. Transfers require approval before execution."""
    return guard.handle_request({
        "user_id": user_id,
        "tool": "transfer",
        "arguments": {
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
        },
    })


if __name__ == "__main__":
    mcp.run(transport="stdio")
