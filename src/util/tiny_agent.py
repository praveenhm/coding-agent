"""
1. Make sure you have `uv` install. (e.g. `brew install uv`)
2. Setup Python venv `uv venv && source .venv/bin/activate`
3. Setup the model API key (e.g. `export ANTHROPIC_API_KEY=<your_api_key>`)
4. Run it! `uv run python tiny_agent.py`
"""


import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from rich.console import Console
from rich.markdown import Markdown

server = MCPServerStdio('npx', ['-y', '@playwright/mcp@latest'])

system_prompt = """
You are an private assistant to perform the task given by the user.

You have several tools at your disposal. A major one is a web browser (running in a macOS).
There are some tricks about using this browser:
    1. Use browser_snapshot function to read the content of the web page.
    2. Many web pages today are lazy loading. That is, it will load more items in a list only when you scroll to the bottom.
    3. When you want to scroll up or down, you have to use the keyboard (e.g. cmd + down to scroll to the bottom).
    4. If you need to input the information you don't have, for example, the login credentials, you can ask a human to intervene and then take on the task from there.
"""
agent = Agent('anthropic:claude-3-5-sonnet-latest',
              system_prompt=system_prompt,
              mcp_servers=[server])


@agent.tool_plain
def request_human_intervention() -> str:
    """
    This tool is used to pause the agent and wait for human intervention.

    It's useful when the agent needs to wait for the user to perform some action (e.g. login with anthentication) before continuing.
    """
    input("👩‍💻 Human intervention required (press enter to continue)")
    return "Human intervention completed"


console = Console()

def display_run_node(node):
    """Display different content based on node type"""
    node_type = node.__class__.__name__

    if node_type == 'CallToolsNode':
        # Get AI reply text
        for part in node.model_response.parts:
            if part.part_kind == 'text':
                console.print("💭")
                console.print(Markdown(part.content))
            elif part.part_kind == 'tool-call':
                console.print(f"🔧 using tool: {part.tool_name}")


async def main():
    async with agent.run_mcp_servers():
        message_history = []
        console.print("😊 What can I do for you")
        while True:
            # press ctrl + c to exit the loop
            task = input("> ")
            async with agent.iter(task, message_history=message_history) as agent_run:
                async for node in agent_run:
                    display_run_node(node)
            console.print(agent_run.usage())
            message_history = agent_run.result.all_messages()

asyncio.run(main())
