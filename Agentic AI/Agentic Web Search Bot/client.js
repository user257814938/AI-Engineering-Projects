require('dotenv').config();
const axios = require('axios');

const MCP_HTTP_TOKEN = process.env.MCP_HTTP_TOKEN;
const SERVER_URL = process.env.SERVER_URL || 'http://localhost:3000';

const client = axios.create({
    baseURL: SERVER_URL,
    headers: { 'Authorization': `Bearer ${MCP_HTTP_TOKEN}` },
    timeout: 30000
});

async function main() {
    const topic = process.argv[2];

    if (!topic) {
        console.error('Usage: node client.js "your topic"');
        console.error('Example: node client.js "Artificial Intelligence"');
        process.exit(1);
    }

    console.log(`\n🔍 Researching: "${topic}"...\n`);

    try {
        // 1. Search web
        console.log('1. Searching web...');
        const searchRes = await client.post('/tools/search_web', { query: topic, k: 3 });
        const results = searchRes.data;
        console.log(`   ✓ Found ${results.length} results\n`);

        // 2. Fetch readable content
        console.log('2. Fetching content...');
        const docs = [];
        for (const result of results) {
            console.log(`   Fetching ${result.url}...`);
            const readRes = await client.post('/tools/fetch_readable', { url: result.url });
            if (readRes.data.text && readRes.data.text.length > 0) {
                docs.push(readRes.data);
                console.log(`   ✓ Success`);
            } else {
                console.log(`   ⚠ No content`);
            }
        }
        console.log(`   ✓ Fetched ${docs.length} documents\n`);

        if (docs.length === 0) {
            throw new Error('No content fetched from any result');
        }

        // 3. Summarize
        console.log('3. Summarizing with AI...');
        const summaryRes = await client.post('/tools/summarize_with_citations', { topic, docs });
        const { bullets, sources } = summaryRes.data;
        console.log(`   ✓ Generated ${bullets.length} bullet points\n`);

        // 4. Format markdown
        const date = new Date().toISOString().split('T')[0];
        let mdContent = `# Briefing: ${topic}\nDate: ${date}\n\n`;
        mdContent += `## Summary\n`;
        bullets.forEach(b => mdContent += `${b}\n`);
        mdContent += `\n## Sources\n`;
        sources.forEach(s => mdContent += `[${s.i}] ${s.title} - ${s.url}\n`);

        // 5. Save
        console.log('4. Saving briefing...');
        const filename = `brief_${date}.md`;
        const saveRes = await client.post('/tools/save_markdown', { filename, content: mdContent });

        console.log(`\n✅ Briefing saved to: ${saveRes.data.path}\n`);

    } catch (error) {
        if (error.response) {
            console.error(`\n❌ Error: ${error.response.status} - ${error.response.data.error || error.response.statusText}`);
        } else if (error.code === 'ECONNREFUSED') {
            console.error(`\n❌ Error: Cannot connect to server at ${SERVER_URL}`);
            console.error('   Make sure the server is running: node server.js');
        } else {
            console.error(`\n❌ Error: ${error.message}`);
        }
        process.exit(1);
    }
}

main();
