# MCP Project Part 2: Custom Server + Agentic Client

## Overview

Custom MCP server with unique tools, composed with external servers via LLM orchestration.

### Custom Server (Part 2)
- **Text Analyzer** with 2 tools:
  - `extract_keywords` - Extract top keywords with frequency
  - `summarize_bullets` - Create bullet point summary

### External Servers (Part 1)
- **Brave Search** - Web search
- **Filesystem** - File read/write

### Composition
- **Agentic Client** - LLM (Groq/Ollama) orchestrates all servers

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

## Usage

```bash
python agentic_client.py "analyze the text and extract keywords"
```

Interactive mode:
```bash
python agentic_client.py
```

## Architecture

```
User Query → LLM Planning → Tool Selection → Execution → Result
                ↓
    ┌───────────┼───────────┐
    │           │           │
 Custom     Brave       Filesystem
 Server     Search      Server
```

## Requirements

- Python 3.8+
- Node.js (for external MCP servers)
- Groq API key or Ollama running locally
