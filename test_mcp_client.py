import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server = StdioServerParameters(
        command="python",
        args=["bank_mcp_server.py"],
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("MCP tools:", [tool.name for tool in tools.tools])

            balance = await session.call_tool(
                "get_balance",
                {"user_id": "riya", "account_id": "ACC-1001"},
            )
            print("AUTHORIZED BALANCE:", balance.content)

            denied = await session.call_tool(
                "get_balance",
                {"user_id": "arjun", "account_id": "ACC-1001"},
            )
            print("UNAUTHORIZED ACCESS:", denied.content)

            transfer = await session.call_tool(
                "transfer",
                {
                    "user_id": "riya",
                    "from_account": "ACC-1001",
                    "to_account": "ACC-1002",
                    "amount": 500,
                },
            )
            print("TRANSFER APPROVAL:", transfer.content)

asyncio.run(main())
