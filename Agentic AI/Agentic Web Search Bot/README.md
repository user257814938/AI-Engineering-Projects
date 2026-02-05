# HTTP Web Search Briefing Bot

HTTP server and CLI client for web search, content fetching, and LLM summarization with citations.

## Prerequisites

- Node.js 18+
- [Ollama](https://ollama.com/) running locally
- [Tavily API Key](https://tavily.com/) (free tier)

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your values.

3. **Start Ollama:**
   ```bash
   ollama run llama3
   ```

## Usage

1. **Start the server:**
   ```bash
   node server.js
   ```

2. **Run the client:**
   ```bash
   node client.js "Artificial Intelligence"
   ```

## API Endpoints

All endpoints require `Authorization: Bearer <MCP_HTTP_TOKEN>`.

### GET /tools
```bash
curl -H "Authorization: Bearer your-token" http://localhost:3000/tools
```

### POST /tools/search_web
```bash
curl -X POST http://localhost:3000/tools/search_web \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "AI trends", "k": 3}'
```

### POST /tools/fetch_readable
```bash
curl -X POST http://localhost:3000/tools/fetch_readable \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article"}'
```

### POST /tools/summarize_with_citations
```bash
curl -X POST http://localhost:3000/tools/summarize_with_citations \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI",
    "docs": [
      {"title": "Article 1", "url": "https://example.com/1", "text": "Content..."},
      {"title": "Article 2", "url": "https://example.com/2", "text": "Content..."}
    ]
  }'
```

### POST /tools/save_markdown
```bash
curl -X POST http://localhost:3000/tools/save_markdown \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"filename": "brief.md", "content": "# Title\n\nContent..."}'
```

## Sample Output

See `brief_2024-12-06.md` for example output with 5 bullets and citations.

## Troubleshooting

- **401 Unauthorized**: Check `MCP_HTTP_TOKEN` in `.env`
- **Search fails**: Verify `TAVILY_API_KEY`
- **LLM timeout**: Ensure Ollama is running: `ollama list`
- **Connection refused**: Start server: `node server.js`
