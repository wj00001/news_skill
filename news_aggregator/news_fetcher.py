"""RSS 新闻抓取模块（支持自动翻译）"""

import logging
import re

import feedparser
import requests

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30
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
    return text[:300] + "..." if len(text) > 300 else text


def _translate_text(text, target="zh"):
    """使用阿里翻译将英文文本翻译成中文（带 10s 超时保护）"""
    if not text or len(text.strip()) < 3:
        return text
    try:
        import translators as ts
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

        def do_translate():
            return ts.translate_text(
                text, translator="alibaba",
                from_language="en", to_language=target,
            )

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(do_translate)
            result = future.result(timeout=10)
        return result.strip()
    except FuturesTimeout:
        logger.debug(f"翻译超时（10s），跳过: {text[:40]}...")
        return text
    except Exception as e:
        logger.debug(f"翻译失败: {e}")
        return text


def fetch_rss(source):
    """从单个 RSS 源抓取新闻。返回 {"source_name": str, "articles": [dict]}"""
    name = source.get("name", "未知")
    url = source["url"]
    max_articles = source.get("max_articles", 10)
    need_translate = source.get("translate", False)

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

        if need_translate:
            title_cn = _translate_text(title)
            if title_cn and title_cn != title:
                title = f"{title_cn}（{title}）"
            if summary and summary != "暂无摘要":
                summary_cn = _translate_text(summary[:200])
                if summary_cn and summary_cn != summary[:200]:
                    summary = summary_cn

        articles.append({
            "title": title,
            "link": link,
            "summary": summary or "暂无摘要",
            "published": published,
        })

    logger.info(f"  -> 获取 {len(articles)} 条来自 {name}"
                + ("（已翻译）" if need_translate else ""))
    return {"source_name": name, "articles": articles}


def fetch_all(news_sources):
    """遍历抓取所有新闻源"""
    results = []
    for source in news_sources:
        result = fetch_rss(source)
        results.append(result)
    return results
