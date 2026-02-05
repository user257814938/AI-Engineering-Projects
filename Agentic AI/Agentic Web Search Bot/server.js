require('dotenv').config();
const express = require('express');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');
const { Readability } = require('@mozilla/readability');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const MCP_HTTP_TOKEN = process.env.MCP_HTTP_TOKEN;
const TAVILY_API_KEY = process.env.TAVILY_API_KEY;
const LLM_BASE_URL = process.env.LLM_BASE_URL || 'http://localhost:11434';
const LLM_MODEL = process.env.LLM_MODEL || 'llama3';

// Bearer auth middleware
function authMiddleware(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ') || authHeader.split(' ')[1] !== MCP_HTTP_TOKEN) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}

app.use(authMiddleware);

// GET /tools - List available tools
app.get('/tools', (req, res) => {
    res.json([
        {
            name: 'search_web',
            description: 'Search the web for a query',
            input_schema: {
                type: 'object',
                properties: {
                    query: { type: 'string', description: 'Search query' },
                    k: { type: 'number', description: 'Number of results (default: 3)' }
                },
                required: ['query']
            }
        },
        {
            name: 'fetch_readable',
            description: 'Fetch and parse a webpage into readable text',
            input_schema: {
                type: 'object',
                properties: {
                    url: { type: 'string', description: 'URL to fetch' }
                },
                required: ['url']
            }
        },
        {
            name: 'summarize_with_citations',
            description: 'Summarize content with inline citations',
            input_schema: {
                type: 'object',
                properties: {
                    topic: { type: 'string', description: 'Topic to summarize' },
                    docs: { type: 'array', description: 'Documents to summarize' }
                },
                required: ['topic', 'docs']
            }
        },
        {
            name: 'save_markdown',
            description: 'Save content to a markdown file',
            input_schema: {
                type: 'object',
                properties: {
                    filename: { type: 'string', description: 'Filename' },
                    content: { type: 'string', description: 'Markdown content' }
                },
                required: ['filename', 'content']
            }
        }
    ]);
});

// POST /tools/search_web
app.post('/tools/search_web', async (req, res) => {
    const { query, k = 3 } = req.body;

    if (!query) {
        return res.status(400).json({ error: 'Missing required field: query' });
    }

    try {
        const response = await axios.post('https://api.tavily.com/search', {
            api_key: TAVILY_API_KEY,
            query: query,
            search_depth: 'basic',
            max_results: k
        }, { timeout: 10000 });

        const results = response.data.results.map(r => ({
            title: r.title,
            url: r.url,
            snippet: r.content,
            source: 'tavily'
        }));

        res.json(results);
    } catch (error) {
        console.error('Search error:', error.message);
        res.status(500).json({ error: 'Search failed: ' + error.message });
    }
});

// POST /tools/fetch_readable
app.post('/tools/fetch_readable', async (req, res) => {
    const { url } = req.body;

    if (!url) {
        return res.status(400).json({ error: 'Missing required field: url' });
    }

    try {
        const response = await axios.get(url, {
            headers: { 'User-Agent': 'Mozilla/5.0 (compatible; BriefingBot/1.0)' },
            timeout: 5000
        });

        const dom = new JSDOM(response.data, { url });
        const reader = new Readability(dom.window.document);
        const article = reader.parse();

        if (!article || !article.textContent) {
            return res.json({ url, title: 'No content', text: '' });
        }

        res.json({
            url,
            title: article.title || 'Untitled',
            text: article.textContent.trim()
        });
    } catch (error) {
        console.error(`Fetch error for ${url}:`, error.message);
        res.json({ url, title: 'Error', text: '' });
    }
});

// POST /tools/summarize_with_citations
app.post('/tools/summarize_with_citations', async (req, res) => {
    const { topic, docs } = req.body;

    if (!topic || !docs || !Array.isArray(docs) || docs.length === 0) {
        return res.status(400).json({ error: 'Missing required fields: topic, docs' });
    }

    const context = docs.map((d, i) =>
        `[${i + 1}] Title: ${d.title}\nURL: ${d.url}\nContent: ${d.text.slice(0, 1500)}...`
    ).join('\n\n');

    const systemPrompt = `You are a briefing bot. Write exactly 5 bullet points summarizing the topic "${topic}" based on the provided documents.

Rules:
- Each bullet must be ≤ 200 characters
- Use inline citations like [1], [2], [3] referring to the document numbers
- Format: "- Bullet text [1]"
- Output ONLY the bullets, nothing else`;

    try {
        const response = await axios.post(`${LLM_BASE_URL}/api/chat`, {
            model: LLM_MODEL,
            messages: [
                { role: 'system', content: systemPrompt },
                { role: 'user', content: context }
            ],
            stream: false
        }, { timeout: 30000 });

        const content = response.data.message.content;
        const bullets = content.split('\n')
            .filter(line => line.trim().startsWith('-'))
            .map(line => line.trim())
            .slice(0, 5);

        while (bullets.length < 5 && bullets.length < docs.length) {
            bullets.push(`- ${docs[bullets.length].title} [${bullets.length + 1}]`);
        }

        const sources = docs.map((d, i) => ({ i: i + 1, title: d.title, url: d.url }));

        res.json({ bullets, sources });
    } catch (error) {
        console.error('LLM error:', error.message);
        res.status(500).json({ error: 'Summarization failed: ' + error.message });
    }
});

// POST /tools/save_markdown
app.post('/tools/save_markdown', (req, res) => {
    const { filename, content } = req.body;

    if (!filename || !content) {
        return res.status(400).json({ error: 'Missing required fields: filename, content' });
    }

    const sanitizedFilename = path.basename(filename);
    if (!sanitizedFilename.endsWith('.md')) {
        return res.status(400).json({ error: 'Filename must end with .md' });
    }

    try {
        const filePath = path.join(__dirname, sanitizedFilename);
        fs.writeFileSync(filePath, content);
        res.json({ path: filePath });
    } catch (error) {
        console.error('Save error:', error.message);
        res.status(500).json({ error: 'Save failed: ' + error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Auth token: ${MCP_HTTP_TOKEN ? 'configured' : 'NOT SET'}`);
});
