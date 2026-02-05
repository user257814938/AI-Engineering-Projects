# MCP Research Assistant

A Streamlit-based research assistant powered by MCP (Model Context Protocol) servers and LLM orchestration.

## Overview

This application demonstrates:
- **MCP Integration**: Connects to multiple MCP servers (Brave Search, Filesystem)
- **Tool-Using Agent**: LLM automatically selects and uses appropriate tools
- **Multi-Provider Support**: Works with Groq, Ollama, OpenAI, or Anthropic
- **Interactive UI**: Streamlit chat interface for research queries
- **Persistent Workspace**: Saves research results to local filesystem

## Architecture

```
┌─────────────────────────────────────────┐
│    Streamlit UI (app.py)                │
│    - Chat Interface                     │
│    - API Key Configuration              │
└─────────────────────────────────────────┘
                    │
┌─────────────────▼─────────────────────┐
│    MCP Client (client.py)             │
│    - LLM Orchestration                │
│    - Tool Discovery & Execution       │
│    - Session Management               │
└─────────────────────────────────────────┘
        │                       │
┌───────▼──────────┐  ┌────────▼─────────┐
│ Brave Search MCP │  │ Filesystem MCP   │
│ - Web Search     │  │ - Read/Write     │
│ - Real-time Data │  │ - File Mgmt      │
└──────────────────┘  └──────────────────┘
```

## Prerequisites

- Python 3.8+
- Node.js (for npx to run MCP servers)
- API Keys:
  - [Groq API Key](https://console.groq.com/) (Free) - **OR**
  - [Ollama](https://ollama.com/) running locally (Free)
  - [Brave Search API Key](https://brave.com/search/api/) (Free tier available)

## Setup

1. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and configure:
   ```
   # LLM Configuration
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   
   # OR for Ollama
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   
   # MCP Server Configuration
   BRAVE_API_KEY=your_brave_api_key_here
   ```

3. **If using Ollama, ensure it's running:**
   ```bash
   ollama run llama3
   ```

## Usage

### Run the Streamlit App

```bash
streamlit run app.py
```

The app will:
1. Connect to configured MCP servers
2. Discover available tools
3. Provide a chat interface for research queries

### Example Queries

- "Search for the latest news on AI developments"
- "Find information about Python async programming and save it to a file"
- "What are the current trends in web development?"

### Using the CLI Client

For programmatic access:
```python
import asyncio
from client import MCPClient

async def main():
    client = MCPClient()
    await client.initialize()
    
    response, tools_used = await client.process_query(
        "Search for information about MCP protocol"
    )
    print(response)
    
    await client.cleanup()

asyncio.run(main())
```

## Available MCP Servers

### Brave Search Server
- **Tool**: `brave_web_search`
- **Purpose**: Real-time web search
- **Requires**: BRAVE_API_KEY

### Filesystem Server
- **Tools**: `read_file`, `write_file`, `list_directory`, etc.
- **Purpose**: File management in workspace directory
- **Workspace**: `./workspace/` (auto-created)

## Project Structure

```
Day4_Exercice_1/
├── app.py                 # Streamlit UI application
├── client.py              # MCP client with LLM orchestration
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
└── workspace/             # Research output directory (auto-created)
```

## Features

- ✅ **Multi-Provider LLM**: Switch between Groq, Ollama, OpenAI, Anthropic
- ✅ **Tool Discovery**: Automatically discovers tools from all connected servers
- ✅ **Async Architecture**: Efficient async/await pattern for MCP communication
- ✅ **Error Handling**: Graceful error messages and recovery
- ✅ **Chat History**: Maintains conversation context
- ✅ **File Persistence**: Saves research results to workspace

## How It Works

1. **Initialization**: Client connects to MCP servers via stdio
2. **Tool Discovery**: Queries each server for available tools
3. **User Query**: User asks a research question
4. **LLM Planning**: LLM analyzes query and selects appropriate tools
5. **Tool Execution**: Client executes tool calls on respective servers
6. **Synthesis**: LLM synthesizes final answer from tool results
7. **Display**: Results shown in Streamlit chat interface

## Troubleshooting

**MCP servers not connecting:**
- Ensure Node.js is installed: `node --version`
- Check API keys are set in `.env`

**Ollama not working:**
- Ensure Ollama is running: `ollama list`
- Check base URL matches your Ollama instance

**Brave Search errors:**
- Verify BRAVE_API_KEY is valid
- Check API quota limits
