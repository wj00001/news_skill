"""RSS 新闻抓取模块"""

import logging
import re

import feedparser
import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
}


def clean_html(text):
    """去除 HTML 标签，保留纯文本"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:200] + "..." if len(text) > 200 else text


def fetch_rss(source):
    """从单个 RSS 源抓取新闻。返回 {"source_name": str, "articles": [dict]}"""
    name = source.get("name", "未知")
    url = source["url"]
    max_articles = source.get("max_articles", 10)

    logger.info(f"正在抓取: {name} <{url}>")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except Exception as e:
        logger.warning(f"抓取失败 [{name}]: {e}")
        return {"source_name": name, "articles": []}

    articles = []
    for entry in feed.entries[:max_articles]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "")
        summary = entry.get("summary", entry.get("description", ""))
        summary = clean_html(summary)
        published = entry.get("published", entry.get("updated", ""))

        if not title:
            continue

        articles.append({
            "title": title,
            "link": link,
            "summary": summary or "暂无摘要",
            "published": published,
        })

    logger.info(f"  -> 获取 {len(articles)} 条来自 {name}")
    return {"source_name": name, "articles": articles}


def fetch_all(news_sources):
    """遍历抓取所有新闻源"""
    results = []
    for source in news_sources:
        result = fetch_rss(source)
        results.append(result)
    return results

