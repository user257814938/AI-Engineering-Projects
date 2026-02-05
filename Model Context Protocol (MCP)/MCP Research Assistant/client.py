import asyncio
import os
import shutil
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

import openai
from anthropic import Anthropic

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tools: List[Any] = []
        self.history = []
        self.provider = os.getenv("LLM_PROVIDER", "groq")
        
        # Configure Providers
        if self.provider == "groq":
            self.client = openai.AsyncOpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=os.getenv("GROQ_API_KEY")
            )
            self.model = "llama3-groq-70b-8192-tool-use-preview" 
        elif self.provider == "ollama":
            self.client = openai.AsyncOpenAI(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama" # not required
            )
            self.model = os.getenv("OLLAMA_MODEL", "llama3")
        else:
             # Fallback or other providers
             pass

    async def connect_to_server(self, name: str, command: str, args: List[str], env: Optional[Dict] = None):
        """Connects to an MCP server via stdio."""
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        
        transport = await self.session_stack.enter_async_context(stdio_client(server_params))
        session = await self.session_stack.enter_async_context(ClientSession(transport, transport))
        await session.initialize()
        
        self.sessions[name] = session
        
        # Discover tool
        result = await session.list_tools()
        self.tools.extend(result.tools)
        print(f"Connected to {name}, found tools: {[t.name for t in result.tools]}")

    async def initialize(self):
        """Initialize connections to default servers."""
        # 1. Brave Search Server
        brave_key = os.getenv("BRAVE_API_KEY")
        if brave_key:
             await self.connect_to_server(
                "brave-search",
                "npx", 
                ["-y", "@modelcontextprotocol/server-brave-search"],
                env={**os.environ, "BRAVE_API_KEY": brave_key}
            )
        
        # 2. Filesystem Server
        work_dir = os.path.join(os.getcwd(), "workspace")
        os.makedirs(work_dir, exist_ok=True)
        await self.connect_to_server(
            "filesystem",
            "npx",
            ["-y", "@modelcontextprotocol/server-filesystem", work_dir]
        )
        
        # Map tools to sessions for faster lookup
        self.tool_to_session = {}
        for name, session in self.sessions.items():
            result = await session.list_tools()
            for t in result.tools:
                self.tool_to_session[t.name] = session

    async def process_query(self, user_query: str):
        """Process a user query through the LLM and tools."""
        self.history.append({"role": "user", "content": user_query})
        
        llm_tools = []
        for tool in self.tools:
            llm_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })

        # 1. First call to LLM
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            tools=llm_tools if llm_tools else None,
            tool_choice="auto" if llm_tools else "none"
        )
        
        message = response.choices[0].message
        self.history.append(message)
        
        tool_calls = message.tool_calls
        results = []

        if tool_calls:
            for tool_call in tool_calls:
                func_name = tool_call.function.name
                func_args = tool_call.function.arguments
                
                session = self.tool_to_session.get(func_name)
                
                if session:
                    import json
                    try:
                        args_dict = json.loads(func_args)
                        print(f"Calling tool {func_name} with {args_dict}")
                        
                        result = await session.call_tool(func_name, arguments=args_dict)
                        
                        text_content = ""
                        for c in result.content:
                            if c.type == "text":
                                text_content += c.text
                        
                        results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": text_content
                        })
                    except Exception as e:
                         results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": func_name,
                            "content": f"Error: {str(e)}"
                        })
                else:
                    results.append({
                         "tool_call_id": tool_call.id,
                         "role": "tool",
                         "name": func_name,
                         "content": "Error: Tool not found on connected servers."
                    })
            
            # Append tool results to history
            for res in results:
                self.history.append(res)
            
            # 2. Second call to LLM with tool results
            final_response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.history
            )
            final_msg = final_response.choices[0].message
            self.history.append(final_msg)
            return final_msg.content, results
        
        return message.content, []

    async def cleanup(self):
        await self.session_stack.aclose()
