import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv
import time

load_dotenv()  # load environment variables from .env

SERVER_SCRIPT_PATH = "clickhouse_mcp_server.py"

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        self.total_claude_api_calls = 0  # Global counter for all API calls
        self.max_total_api_calls = 20  # Maximum allowed API calls for entire session
    # methods will go here


    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        print(f"\n🔌 Connecting to MCP server: {server_script_path}")
        
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        print(f"   Command: {command} {server_script_path}")
        
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        print("   Establishing stdio transport...")
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        
        print("   Creating client session...")
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        print("   Initializing session...")
        await self.session.initialize()

        # List available tools
        print("   Fetching available tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print(f"\n✅ Connected successfully!")
        print(f"   Available tools ({len(tools)}):")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        print()

    
    def check_api_call_limit(self):
        if self.total_claude_api_calls >= self.max_total_api_calls:
            error_msg = f"⛔ API call limit reached! Maximum {self.max_total_api_calls} calls allowed per session."
            print(f"\n{error_msg}")
            raise RuntimeError(error_msg)
        
        self.total_claude_api_calls += 1
        print(f"   📊 API Call Count: {self.total_claude_api_calls}/{self.max_total_api_calls}")

    
    async def make_claude_api_call(self, messages: list, available_tools: list):
        time.sleep(1)
        response = self.anthropic.messages.create(
            model="model_name",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )
        return response

    
    async def process_tool_calls(self, response, messages: list, available_tools: list, final_text: list, tool_call_count: int):
        """Process all tool calls in a response and continue the conversation"""
        
        while response.stop_reason == "tool_use":
            # Extract all tool_use blocks and text from this response
            tool_uses = []
            assistant_content = []
            
            for content in response.content:
                assistant_content.append(content)
                if content.type == "tool_use":
                    tool_uses.append(content)
                elif content.type == "text":
                    print(f"\n[Response] Claude says: {content.text[:150]}{'...' if len(content.text) > 150 else ''}")
                    final_text.append(content.text)
            
            if not tool_uses:
                break
            
            # Add assistant message with ALL content (including all tool_use blocks)
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Execute all tools and collect results
            tool_results = []
            for tool_content in tool_uses:
                tool_call_count += 1
                tool_name = tool_content.name
                tool_args = tool_content.input
                
                print(f"\n[Tool Call #{tool_call_count}] 🔧 Tool: {tool_name}")
                print(f"[Tool Call #{tool_call_count}] 📥 Arguments: {tool_args}")
                
                # Execute tool call
                print(f"[Tool Call #{tool_call_count}] ⚙️  Executing on server...")
                result = await self.session.call_tool(tool_name, tool_args)
                result_str = str(result.content)
                print(f"[Tool Call #{tool_call_count}] ✅ Result: {result_str[:200]}{'...' if len(result_str) > 200 else ''}")
                
                final_text.append(f"[Tool: {tool_name} | Args: {tool_args}]")
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_content.id,
                    "content": result.content
                })
            
            # Add ALL tool results in a single user message
            messages.append({
                "role": "user",
                "content": tool_results
            })
            
            print(f"\n📤 Sending {len(tool_results)} tool result(s) back to Claude...")
            
            # Check API limit and make next call
            self.check_api_call_limit()
            response = await self.make_claude_api_call(messages, available_tools)
            print(f"   Claude response stop_reason: {response.stop_reason}")
        
        # Process final text response (if any)
        for content in response.content:
            if content.type == "text":
                print(f"\n[Final Response] Claude says: {content.text[:150]}{'...' if len(content.text) > 150 else ''}")
                final_text.append(content.text)
        
        return final_text, tool_call_count


    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        print(f"\n{'='*60}")
        print(f"Processing query: {query}")
        print(f"{'='*60}")
        
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]
        
        print(f"\n📋 Available tools ({len(available_tools)}): {[tool['name'] for tool in available_tools]}")

        # Initial Claude API call
        print("\n🚀 Sending initial request to Claude...")
        
        # Check API call limit
        self.check_api_call_limit()
        
        response = await self.make_claude_api_call(messages, available_tools)
        time.sleep(1)
        print(f"   Claude response stop_reason: {response.stop_reason}")

        # Process response and handle tool calls
        final_text = []
        tool_call_count = 0
        
        # If no tool calls, just extract text
        if response.stop_reason != "tool_use":
            for content in response.content:
                if content.type == 'text':
                    print(f"\n[Response] Claude says: {content.text[:150]}{'...' if len(content.text) > 150 else ''}")
                    final_text.append(content.text)
        else:
            # Process tool calls (handles multiple sequential tool uses)
            final_text, tool_call_count = await self.process_tool_calls(
                response, messages, available_tools, final_text, tool_call_count
            )

        print(f"\n{'='*60}")
        print(f"✅ Query completed. Total tool calls: {tool_call_count}")
        print(f"📊 Session API Calls: {self.total_claude_api_calls}/{self.max_total_api_calls}")
        remaining_calls = self.max_total_api_calls - self.total_claude_api_calls
        if remaining_calls > 0:
            print(f"⚠️  Remaining API calls: {remaining_calls}")
        else:
            print(f"⛔ No more API calls available! Session will end after this query.")
        print(f"{'='*60}\n")
        
        return "\n".join(final_text)


    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\n" + "="*60)
        print("MCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        print(f"⚠️  API Call Limit: {self.max_total_api_calls} calls per session")
        print("="*60)

        query_count = 0
        while True:
            try:
                # Check if API limit reached
                if self.total_claude_api_calls >= self.max_total_api_calls:
                    print("\n" + "="*60)
                    print("⛔ API call limit reached!")
                    print(f"Maximum {self.max_total_api_calls} API calls per session exceeded.")
                    print("Session ending. Restart to continue.")
                    print("="*60)
                    break
                
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    print("\nShutting down...")
                    break
                
                if not query:
                    continue
                
                query_count += 1
                print(f"\n[Query #{query_count}]")

                response = await self.process_query(query)
                print("\n" + "="*60)
                print("FINAL RESPONSE:")
                print("="*60)
                print(response)

            except RuntimeError as e:
                # Handle API limit errors gracefully
                if "API call limit reached" in str(e):
                    print("\n" + "="*60)
                    print("Session ended due to API call limit.")
                    print("="*60)
                    break
                else:
                    print(f"\n❌ Error: {str(e)}")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                import traceback
                print("\nFull traceback:")
                traceback.print_exc()

    async def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up resources...")
        await self.exit_stack.aclose()
        print("✅ Cleanup complete")


async def main():
    client = MCPClient()
    try:
        await client.connect_to_server(SERVER_SCRIPT_PATH)
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())