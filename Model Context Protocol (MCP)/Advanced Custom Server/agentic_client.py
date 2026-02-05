#!/usr/bin/env python3
"""
Agentic Client - Composes custom MCP server + external servers
Uses Groq/Ollama for LLM planning
"""

import os
import sys
import json
import subprocess
import time
from typing import List, Dict, Any
from dotenv import load_dotenv
import requests

load_dotenv()

class MCPClient:
    """Simple MCP client for stdio servers."""
    
    def __init__(self, command: str, args: List[str]):
        self.command = command
        self.args = args
        self.process = None
        self.tools = []
    
    def start(self):
        self.process = subprocess.Popen(
            [self.command] + self.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, bufsize=1
        )
        time.sleep(0.5)
        self._send({"method": "tools/list", "params": {}})
        resp = self._read()
        if resp and "tools" in resp:
            self.tools = resp["tools"]
    
    def call(self, name: str, args: dict) -> Any:
        self._send({"method": "tools/call", "params": {"name": name, "arguments": args}})
        resp = self._read()
        if resp and "content" in resp:
            for item in resp["content"]:
                if item.get("type") == "text":
                    try:
                        return json.loads(item["text"])
                    except:
                        return item["text"]
        return resp
    
    def _send(self, req: dict):
        if self.process and self.process.stdin:
            self.process.stdin.write(json.dumps(req) + "\n")
            self.process.stdin.flush()
    
    def _read(self) -> dict:
        if self.process and self.process.stdout:
            line = self.process.stdout.readline()
            if line:
                try:
                    return json.loads(line)
                except:
                    return None
        return None
    
    def stop(self):
        if self.process:
            self.process.terminate()


class AgenticOrchestrator:
    """Orchestrates custom + external MCP servers with LLM planning."""
    
    def __init__(self):
        self.clients = {}
        self.all_tools = []
        self.tool_map = {}
        
        self.llm_provider = os.getenv("LLM_PROVIDER", "groq")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LLM_MODEL", "llama3-groq-70b-8192-tool-use-preview")
        
        print(f"🤖 LLM: {self.llm_provider} ({self.model})")
    
    def start_servers(self):
        """Start custom + external servers."""
        print("\n🚀 Starting MCP Servers...")
        
        # Custom server
        base = os.path.dirname(os.path.abspath(__file__))
        print("   📦 Custom: Text Analyzer")
        custom = MCPClient("python", [os.path.join(base, "custom_server", "text_analyzer.py")])
        custom.start()
        self.clients["custom"] = custom
        print(f"      ✓ {len(custom.tools)} tools")
        
        # External: Brave Search (if key available)
        if os.getenv("BRAVE_API_KEY"):
            print("   🌐 External: Brave Search")
            try:
                brave = MCPClient("npx", ["-y", "@modelcontextprotocol/server-brave-search"])
                brave.start()
                self.clients["brave"] = brave
                print(f"      ✓ {len(brave.tools)} tools")
            except Exception as e:
                print(f"      ⚠ Failed: {e}")
        
        # External: Filesystem
        print("   📁 External: Filesystem")
        try:
            fs = MCPClient("npx", ["-y", "@modelcontextprotocol/server-filesystem", base])
            fs.start()
            self.clients["filesystem"] = fs
            print(f"      ✓ {len(fs.tools)} tools")
        except Exception as e:
            print(f"      ⚠ Failed: {e}")
        
        # Collect all tools
        for name, client in self.clients.items():
            for tool in client.tools:
                self.all_tools.append(tool)
                self.tool_map[tool["name"]] = client
        
        print(f"\n✅ Total: {len(self.all_tools)} tools\n")
    
    def call_llm(self, messages: list, tools: list) -> dict:
        """Call Groq or Ollama."""
        if self.llm_provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        else:
            url = f"{self.ollama_url}/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
        
        payload = {"model": self.model, "messages": messages, "tools": tools, "tool_choice": "auto", "temperature": 0}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()
    
    def run(self, query: str, max_iter: int = 10) -> str:
        """Run agentic loop."""
        print(f"🎯 Query: {query}\n")
        
        tools_fmt = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}} for t in self.all_tools]
        
        messages = [
            {"role": "system", "content": "You are an assistant with access to tools. Use them to help the user."},
            {"role": "user", "content": query}
        ]
        
        for i in range(max_iter):
            print(f"--- Step {i+1} ---")
            resp = self.call_llm(messages, tools_fmt)
            msg = resp["choices"][0]["message"]
            messages.append(msg)
            
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    name = tc["function"]["name"]
                    args = json.loads(tc["function"]["arguments"])
                    print(f"🔧 {name}({args})")
                    
                    try:
                        result = self.tool_map[name].call(name, args)
                        messages.append({"role": "tool", "tool_call_id": tc["id"], "name": name, "content": json.dumps(result)})
                        print(f"   ✓ Done")
                    except Exception as e:
                        messages.append({"role": "tool", "tool_call_id": tc["id"], "name": name, "content": json.dumps({"error": str(e)})})
                        print(f"   ❌ {e}")
            else:
                answer = msg.get("content", "")
                print(f"\n✅ Answer:\n{answer}\n")
                return answer
        
        return "Max iterations reached"
    
    def cleanup(self):
        for c in self.clients.values():
            c.stop()


def main():
    orch = AgenticOrchestrator()
    try:
        orch.start_servers()
        
        if len(sys.argv) > 1:
            orch.run(" ".join(sys.argv[1:]))
        else:
            print("Usage: python agentic_client.py 'your query'")
            print("\nInteractive mode:")
            while True:
                try:
                    q = input("Query: ").strip()
                    if q.lower() in ['quit', 'exit', 'q']:
                        break
                    if q:
                        orch.run(q)
                except KeyboardInterrupt:
                    break
    finally:
        orch.cleanup()

if __name__ == "__main__":
    main()
