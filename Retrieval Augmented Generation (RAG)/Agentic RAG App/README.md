# Agentic RAG Streamlit App

A Streamlit application that combines Retrieval-Augmented Generation (RAG) with tool-using agents for intelligent question answering.

## Overview

This application demonstrates an agentic RAG system that:
- **Uses LLM**: Groq's Llama3-70B for intelligent responses
- **Web Search**: Tavily API for real-time web search capabilities
- **Local Knowledge**: FAISS vector store for retrieving app-specific information
- **Interactive UI**: Streamlit chat interface for user interaction

## Prerequisites

- Python 3.8+
- API Keys:
  - [Groq API Key](https://console.groq.com/) (Free)
  - [Tavily API Key](https://tavily.com/) (Free)
  - [Google API Key](https://console.cloud.google.com/) (Optional)
  - [LangChain API Key](https://smith.langchain.com/) (Optional for tracing)

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set your keys:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   LANGCHAIN_API_KEY=your_langchain_api_key_here
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your browser. You can:
- Ask questions about current events (uses web search)
- Ask about the app itself (uses local knowledge base)
- Have natural conversations with the AI agent

## Features

- **Tool-Calling Agent**: Automatically selects the right tool for each query
- **RAG Pipeline**: Retrieves relevant context before generating responses
- **Web Search Integration**: Access to real-time information via Tavily
- **Chat Interface**: Modern chat UI with message history
- **Error Handling**: Graceful error messages and API key validation
- **Source Attribution**: Responses include sources when applicable

## Project Structure

- `app.py` - Main Streamlit application
- `agent_backend.py` - Agent and RAG pipeline setup
- `agentic_rag.ipynb` - Jupyter notebook for experimentation
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore rules

## Architecture

1. **User Query** → Streamlit UI
2. **Agent Executor** → Decides which tool to use
3. **Tools**:
   - `TavilySearchResults` - Web search
   - `search_local_knowledge` - RAG retriever
4. **LLM** → Groq Llama3-70B generates response
5. **Response** → Displayed in chat interface
