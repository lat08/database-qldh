from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import requests
from xml.etree import ElementTree as ET
import re
from typing import List, Dict
import asyncio
import json
from urllib.parse import urlparse, parse_qs

app = FastAPI(title="Local Proxy with News")

# ← PASTE YOUR COLAB NGROK URL HERE
COLAB_URL = "https://nonprejudicial-scoutingly-jaiden.ngrok-free.dev"

# =========================================================
# NEWS PULLING (runs locally)
# =========================================================
class NewsAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

    def search_news(self, query: str, max_results: int = 10) -> List[Dict]:
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"News API error: {e}")
            return []

        try:
            root = ET.fromstring(r.content)
        except ET.ParseError as e:
            print(f"XML parse error: {e}")
            return []

        articles = []
        for item in root.findall(".//item")[:max_results]:
            source_elem = item.find("source")
            desc = item.find("description")
            link_elem = item.find("link")
            
            if desc is None or not desc.text:
                continue
            
            source_name = source_elem.text.strip() if source_elem is not None else "Unknown"
            url = link_elem.text if link_elem is not None else ""
            
            content = re.sub(r"<[^>]+>", " ", desc.text)
            content = re.sub(r"&[a-z]+;", " ", content)
            content = re.sub(r"\s+", " ", content).strip()
            
            if len(content) < 50:
                continue
            
            articles.append({
                "source": source_name,
                "content": content,
                "url": url
            })

        return articles

def prepare_context(articles: List[Dict], query: str) -> str:
    """Prepare context from articles (limit to ~400 words)"""
    lines = []
    for idx, a in enumerate(articles):
        content = a["content"]
        sentences = [s.strip() + "." if not s.strip().endswith(('.', '!', '?')) else s.strip()
                    for s in re.split(r'(?<=[.!?])\s+', content)
                    if len(s.strip()) > 30]
        snippet = " ".join(sentences[:2])
        lines.append(f"Article {idx+1}: {snippet}")

    context_lines = []
    word_count = 0
    for line in lines:
        line_words = line.split()
        if word_count + len(line_words) > 400:
            line_words = line_words[:400 - word_count]
        context_lines.append(" ".join(line_words))
        word_count += len(line_words)
        if word_count >= 400:
            break

    return "\n".join(context_lines)

news_api = NewsAPI()

# =========================================================
# REQUEST MODELS
# =========================================================
class ClaimRequest(BaseModel):
    claim: str

class QueryRequest(BaseModel):
    query: str
    max_articles: int = 10

# =========================================================
# ENDPOINTS
# =========================================================
@app.get("/")
def root():
    return {
        "status": "Local proxy running",
        "colab_url": COLAB_URL,
        "endpoints": ["/is_worthy", "/summarize"]
    }

@app.post("/is_worthy")
def proxy_is_worthy(req: ClaimRequest):
    """Forward worthiness check to Colab"""
    try:
        r = requests.post(f"{COLAB_URL}/is_worthy", json=req.dict(), timeout=120)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@app.post("/summarize")
async def proxy_summarize(req: QueryRequest):
    """
    1. Pull news locally
    2. Prepare context
    3. Send to Colab model
    4. Stream response back
    """
    try:
        # Step 1: Pull news locally
        articles = news_api.search_news(req.query, max_results=req.max_articles)
        
        if not articles:
            async def no_news():
                yield f"data: {json.dumps({'error': 'No news found'})}\n\n"
            return StreamingResponse(no_news(), media_type="text/event-stream")
        
        # Step 2: Prepare context
        context = prepare_context(articles, req.query)
        
        # Step 3: Prepare sources metadata
        sources_dict = {a["source"]: a["url"] for a in articles}
        
        # Step 4: Send to Colab and stream back
        async def stream_from_colab():
            # Send metadata first
            metadata = {
                "type": "metadata",
                "sources": sources_dict,
                "num_articles": len(articles)
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Stream tokens from Colab
            payload = {"query": req.query, "context": context}
            with requests.post(f"{COLAB_URL}/summarize", json=payload, stream=True, timeout=300) as r:
                for line in r.iter_lines():
                    if line:
                        yield f"{line.decode('utf-8')}\n"
                    await asyncio.sleep(0)
        
        return StreamingResponse(
            stream_from_colab(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
        
    except Exception as e:
        print(f"Error: {e}")
        async def error_stream():
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")
