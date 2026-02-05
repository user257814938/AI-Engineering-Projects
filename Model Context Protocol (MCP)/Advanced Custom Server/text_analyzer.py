#!/usr/bin/env python3
"""
Custom MCP Server: Text Analyzer
Exposes 2 custom tools for text analysis
"""

import sys
import json
import re
from collections import Counter

class TextAnalyzerServer:
    """Custom MCP server with text analysis tools."""
    
    def __init__(self):
        self.name = "text-analyzer"
        self.tools = {
            "extract_keywords": {
                "description": "Extract top keywords from text with frequency count",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to analyze"},
                        "top_n": {"type": "number", "description": "Number of keywords (default: 10)"}
                    },
                    "required": ["text"]
                }
            },
            "summarize_bullets": {
                "description": "Create bullet point summary from text",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to summarize"},
                        "max_bullets": {"type": "number", "description": "Max bullets (default: 5)"}
                    },
                    "required": ["text"]
                }
            }
        }
    
    def extract_keywords(self, text: str, top_n: int = 10) -> dict:
        """Extract top keywords from text."""
        # Remove punctuation and lowercase
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter stopwords
        stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'were', 'they', 'their', 'will', 'would', 'could', 'should', 'about', 'which', 'when', 'there', 'what', 'more', 'some', 'than', 'into', 'also', 'only', 'other', 'over', 'such', 'after', 'most', 'then', 'them', 'these', 'being', 'between'}
        words = [w for w in words if w not in stopwords]
        
        # Count and return top N
        counts = Counter(words).most_common(top_n)
        return {"keywords": [{"word": w, "count": c} for w, c in counts]}
    
    def summarize_bullets(self, text: str, max_bullets: int = 5) -> dict:
        """Create bullet summary from text."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 30]
        
        # Score sentences by keyword density
        keywords = set(w for w, _ in Counter(re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())).most_common(20))
        
        scored = []
        for sent in sentences:
            words = set(re.findall(r'\b[a-zA-Z]{5,}\b', sent.lower()))
            score = len(words & keywords)
            scored.append((score, sent))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        bullets = [f"• {sent[:200]}" for _, sent in scored[:max_bullets]]
        
        return {"bullets": bullets, "count": len(bullets)}
    
    def handle_request(self, request: dict) -> dict:
        """Handle MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return {"tools": [{"name": n, **s} for n, s in self.tools.items()]}
        
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            
            if name == "extract_keywords":
                result = self.extract_keywords(**args)
            elif name == "summarize_bullets":
                result = self.summarize_bullets(**args)
            else:
                return {"error": f"Unknown tool: {name}"}
            
            return {"content": [{"type": "text", "text": json.dumps(result)}]}
        
        return {"error": f"Unknown method: {method}"}
    
    def run(self):
        """Run stdio MCP server."""
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except Exception as e:
                print(json.dumps({"error": str(e)}), flush=True)

if __name__ == "__main__":
    TextAnalyzerServer().run()
