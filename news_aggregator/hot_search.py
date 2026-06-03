"""热搜抓取模块（微博、百度）"""

import json
import logging
import re

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}

REQUEST_TIMEOUT = 15


def fetch_weibo_hot(max_items=20):
    """抓取微博热搜"""
    logger.info("正在抓取微博热搜...")
    try:
        headers = {
            **HEADERS,
            "Referer": "https://weibo.com/",
            "Cookie": "SUB=_2AkMx7GkIf8NxqwJRmfwRyGzjaYpJzQzEieKjWSLnJRMxHRl-yT9jqhUAtRB6OY-1aZyGONFhbnYpYiF8LO3Z5bVtGX_1;",
        }
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        realtime = data.get("data", {}).get("realtime", [])
        items = []
        for i, item in enumerate(realtime[:max_items], 1):
            word = item.get("word", "").strip()
            if not word:
                continue
            hot_num = item.get("num", "")
            items.append({
                "rank": i,
                "title": word,
                "hot": f"{hot_num} 万" if isinstance(hot_num, (int, float)) else str(hot_num),
            })

        logger.info(f"  -> 获取 {len(items)} 条微博热搜")
        return {"source": "微博热搜", "items": items}
    except Exception as e:
        logger.warning(f"抓取微博热搜失败: {e}")
        return {"source": "微博热搜", "items": []}


def fetch_baidu_hot(max_items=20):
    """抓取百度热搜 - 多种策略"""
    logger.info("正在抓取百度热搜...")

    headers = {**HEADERS, "Accept": "text/html,application/json,*/*"}

    # 策略1: 从 __INITIAL_STATE__ 提取页面数据
    try:
        url = "https://top.baidu.com/board"
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text

        match = re.search(
            r"window\.__INITIAL_STATE__\s*=\s*({.*?});", text, re.DOTALL
        )
        if match:
            state = json.loads(match.group(1))
            cards = state.get("data", {}).get("cards", [])
            items = []
            rank = 0
            for card in cards:
                content = card.get("content", [])
                for entry in content:
                    word = entry.get("word", entry.get("query", "")).strip()
                    if not word:
                        continue
                    rank += 1
                    items.append({
                        "rank": rank,
                        "title": word,
                        "hot": entry.get("hotDesc", ""),
                    })
                    if rank >= max_items:
                        break
                if rank >= max_items:
                    break
            if items:
                logger.info(f"  -> 获取 {len(items)} 条百度热搜")
                return {"source": "百度热搜", "items": items}
    except Exception as e:
        logger.debug(f"策略1失败: {e}")

    # 策略2: 直接解析 HTML 中的 a[class^=title] 标签
    try:
        url = "https://top.baidu.com/board"
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        text = resp.text

        # 提取热搜标题 - 匹配 "title-xxx"><div class="c-single-text-ellipsis">关键词</div>
        titles = re.findall(
            r'class="c-single-text-ellipsis"[^>]*>([^<]+)<', text
        )
        if titles:
            items = []
            for i, t in enumerate(titles[:max_items], 1):
                t = t.strip()
                if t:
                    items.append({"rank": i, "title": t, "hot": ""})
            if items:
                logger.info(f"  -> 获取 {len(items)} 条百度热搜（HTML解析）")
                return {"source": "百度热搜", "items": items}
    except Exception as e:
        logger.debug(f"策略2失败: {e}")

    # 策略3: 使用热搜API
    try:
        backup_url = "https://top.baidu.com/api/board?tab=realtime"
        resp2 = requests.get(backup_url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp2.raise_for_status()
        data = resp2.json()
        items = []
        for i, entry in enumerate(data.get("data", {}).get("cards", []), 1):
            word = entry.get("word", entry.get("query", "")).strip()
            if not word:
                continue
            items.append({
                "rank": i,
                "title": word,
                "hot": entry.get("hotDesc", ""),
            })
            if len(items) >= max_items:
                break
        if items:
            logger.info(f"  -> 获取 {len(items)} 条百度热搜（API）")
            return {"source": "百度热搜", "items": items}
    except Exception as e:
        logger.debug(f"策略3失败: {e}")

    logger.warning("所有策略均未获取到百度热搜")
    return {"source": "百度热搜", "items": []}


FETCHERS = {
    "weibo": fetch_weibo_hot,
    "baidu": fetch_baidu_hot,
}


def fetch_all(config):
    """抓取所有启用的热搜"""
    hs_config = config.get("hot_search", {})
    if not hs_config.get("enabled", False):
        return []

    sources = hs_config.get("sources", [])
    max_items = hs_config.get("max_items", 20)

    results = []
    for src in sources:
        fetcher = FETCHERS.get(src)
        if fetcher:
            result = fetcher(max_items)
            results.append(result)
    return results
