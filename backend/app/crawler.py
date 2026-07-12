"""
News crawler: Google News RSS per segment keyword + yfinance per-ticker news.
No API keys required. Degrades gracefully offline (returns empty lists and
the pipeline falls back to knowledge-base priors, flagged in the trace).
"""
import html
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

UA = {"User-Agent": "Mozilla/5.0 (bottleneck-agent research bot)"}
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def _fetch(url: str, timeout: int = 12) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _clean(text: str) -> str:
    text = html.unescape(text or "")
    return re.sub(r"<[^>]+>", "", text).strip()


def google_news(query: str, max_items: int = 8) -> list[dict]:
    """Fetch recent headlines for a query from Google News RSS."""
    url = GOOGLE_NEWS_RSS.format(q=urllib.parse.quote(query))
    try:
        raw = _fetch(url)
        root = ET.fromstring(raw)
        items = []
        for item in root.iter("item"):
            title = _clean(item.findtext("title", ""))
            link = item.findtext("link", "")
            pub = item.findtext("pubDate", "")
            source = _clean(item.findtext("source", ""))
            if title:
                items.append({
                    "title": title, "url": link, "published": pub,
                    "source": source, "query": query,
                })
            if len(items) >= max_items:
                break
        return items
    except Exception as e:
        return [{"error": f"{type(e).__name__}: {e}", "query": query}]


def ticker_news(ticker: str, max_items: int = 6) -> list[dict]:
    """Recent company headlines via yfinance; falls back to Google News."""
    try:
        import yfinance as yf
        raw = yf.Ticker(ticker).news or []
        items = []
        for n in raw[:max_items]:
            c = n.get("content", n)
            title = c.get("title") or ""
            url = ((c.get("clickThroughUrl") or {}).get("url")
                   or (c.get("canonicalUrl") or {}).get("url") or "")
            pub = c.get("pubDate") or c.get("displayTime") or ""
            if title:
                items.append({"title": title, "url": url, "published": pub,
                              "source": (c.get("provider") or {}).get("displayName", ""),
                              "query": ticker})
        if items:
            return items
    except Exception:
        pass
    return google_news(f"{ticker} stock", max_items=max_items)


def count_signal_hits(headlines: list[dict], words: list[str]) -> tuple[int, list[str]]:
    """Count headlines containing any signal word; return (count, evidence titles)."""
    hits, evidence = 0, []
    for h in headlines:
        title = (h.get("title") or "").lower()
        if any(w in title for w in words):
            hits += 1
            evidence.append(h.get("title", ""))
    return hits, evidence


def crawl_segment(segment: dict, per_query: int = 6, pause: float = 0.3) -> list[dict]:
    """Crawl all keyword queries for one supply-chain segment."""
    out = []
    for kw in segment["keywords"]:
        out.extend(google_news(kw, max_items=per_query))
        time.sleep(pause)
    # dedupe by title
    seen, deduped = set(), []
    for h in out:
        t = h.get("title", "")
        if t and t not in seen:
            seen.add(t)
            deduped.append(h)
    return deduped


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
