"""热搜抓取模块 - 支持微博、百度、抖音、快手、微信、小红书、今日头条"""

import json
import logging
import re
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}

REQUEST_TIMEOUT = 30


def _make_baidu_link(keyword):
    """百度搜索链接"""
    return f"https://www.baidu.com/s?wd={quote(keyword)}"


def _make_weibo_link(keyword):
    """微博搜索链接"""
    return f"https://s.weibo.com/weibo?q={quote(keyword)}"


def _make_douyin_link(keyword):
    """抖音搜索链接"""
    return f"https://www.douyin.com/search/{quote(keyword)}"


def _make_toutiao_link(keyword):
    """今日头条搜索链接"""
    return f"https://www.toutiao.com/search/?keyword={quote(keyword)}"


def _make_kuaishou_link(keyword):
    """快手搜索链接"""
    return f"https://www.kuaishou.com/search/{quote(keyword)}"


def _make_weixin_link(keyword):
    """微信搜一搜链接"""
    return f"https://weixin.sogou.com/weixin?type=2&query={quote(keyword)}"


def _make_xiaohongshu_link(keyword):
    """小红书搜索链接"""
    return f"https://www.xiaohongshu.com/search_result?keyword={quote(keyword)}"


LINK_MAKERS = {
    "baidu": _make_baidu_link,
    "weibo": _make_weibo_link,
    "douyin": _make_douyin_link,
    "toutiao": _make_toutiao_link,
    "kuaishou": _make_kuaishou_link,
    "weixin": _make_weixin_link,
    "xiaohongshu": _make_xiaohongshu_link,
}


def fetch_weibo_hot(max_items=10):
    """微博热搜"""
    logger.info("正在抓取微博热搜...")
    try:
        headers = {**HEADERS, "Referer": "https://weibo.com/"}
        url = "https://weibo.com/ajax/side/hotSearch"
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}")

        data = resp.json()
        realtime = data.get("data", {}).get("realtime", [])
        items = []
        for i, item in enumerate(realtime[:max_items], 1):
            word = item.get("word", "").strip()
            if not word:
                continue
            hot = item.get("num", "")
            items.append({
                "rank": i,
                "title": word,
                "hot": f"热度 {hot}" if hot else "",
                "url": _make_weibo_link(word),
            })

        logger.info(f"  -> 获取 {len(items)} 条微博热搜")
        return {"source": "微博热搜", "items": items}
    except Exception as e:
        logger.warning(f"微博热搜失败: {e}")
        return {"source": "微博热搜", "items": []}


def fetch_baidu_hot(max_items=10):
    """百度热搜"""
    logger.info("正在抓取百度热搜...")
    try:
        url = "https://top.baidu.com/board"
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        # 同时提取标题和链接
        items = []
        # 匹配 <a href="..." class="title-wrapper"><div class="c-single-text-ellipsis">标题</div></a>
        pattern = r'<a[^>]*href="(https?://[^"]*baidu[^"]*)"[^>]*class="title-wrapper"[^>]*>.*?c-single-text-ellipsis[^>]*>([^<]+)<'
        matches = re.findall(pattern, resp.text, re.DOTALL)

        if matches:
            for i, (link, title) in enumerate(matches[:max_items], 1):
                title = title.strip()
                if title:
                    items.append({"rank": i, "title": title, "hot": "", "url": link})
        else:
            # 兜底：只提取标题，用搜索链接
            titles = re.findall(
                r'class="c-single-text-ellipsis"[^>]*>([^<]+)<', resp.text
            )
            for i, t in enumerate(titles[:max_items], 1):
                t = t.strip()
                if t:
                    items.append({"rank": i, "title": t, "hot": "", "url": _make_baidu_link(t)})

        if items:
            logger.info(f"  -> 获取 {len(items)} 条百度热搜")
            return {"source": "百度热搜", "items": items}
        raise Exception("未找到热搜内容")
    except Exception as e:
        logger.warning(f"百度热搜失败: {e}")
        return {"source": "百度热搜", "items": []}


def fetch_douyin_hot(max_items=10):
    """抖音热搜"""
    logger.info("正在抓取抖音热搜...")
    try:
        headers = {**HEADERS, "Referer": "https://www.douyin.com/hot/", "Accept": "application/json"}
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        word_list = data.get("data", {}).get("word_list", [])
        items = []
        for i, entry in enumerate(word_list[:max_items], 1):
            word = entry.get("word", "").strip()
            if not word:
                continue
            hot_value = entry.get("hot_value", 0)
            hot_str = f"{hot_value // 10000}万" if hot_value >= 10000 else str(hot_value)
            items.append({
                "rank": i,
                "title": word,
                "hot": hot_str,
                "url": _make_douyin_link(word),
            })

        if items:
            logger.info(f"  -> 获取 {len(items)} 条抖音热搜")
            return {"source": "抖音热搜", "items": items}
        raise Exception("word_list为空")
    except Exception as e:
        logger.warning(f"抖音热搜失败: {e}")
        return {"source": "抖音热搜", "items": []}


def fetch_toutiao_hot(max_items=10):
    """今日头条热搜 - 暂无可用的公开接口"""
    logger.info("今日头条热搜: 暂无可用公开接口")
    return {"source": "今日头条热搜", "items": []}


def fetch_kuaishou_hot(max_items=10):
    """快手热搜 - 暂无可用的公开接口"""
    logger.info("快手热搜: 暂无可用公开接口")
    return {"source": "快手热搜", "items": []}


def fetch_weixin_hot(max_items=10):
    """微信热门 - 暂无可用的公开接口"""
    logger.info("微信热门: 暂无可用公开接口")
    return {"source": "微信热门", "items": []}


def fetch_xiaohongshu_hot(max_items=10):
    """小红书热搜 - 暂无可用的公开接口"""
    logger.info("小红书热搜: 暂无可用公开接口")
    return {"source": "小红书热搜", "items": []}


FETCHERS = {
    "weibo": fetch_weibo_hot,
    "baidu": fetch_baidu_hot,
    "douyin": fetch_douyin_hot,
    "toutiao": fetch_toutiao_hot,
    "kuaishou": fetch_kuaishou_hot,
    "weixin": fetch_weixin_hot,
    "xiaohongshu": fetch_xiaohongshu_hot,
}


def fetch_all(config):
    """抓取所有启用的热搜"""
    hs_config = config.get("hot_search", {})
    if not hs_config.get("enabled", False):
        return []

    sources = hs_config.get("sources", [])
    max_items = hs_config.get("max_items", 10)

    results = []
    for src in sources:
        fetcher = FETCHERS.get(src)
        if fetcher:
            result = fetcher(max_items)
            results.append(result)
    return results
