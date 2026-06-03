#!/usr/bin/env python3
"""每日新闻聚合 - 主入口"""

import argparse
import logging
import sys
from datetime import datetime

import schedule

from config import load_config
from news_fetcher import fetch_all as fetch_news
from hot_search import fetch_all as fetch_hot_search
from email_sender import send as send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news_aggregator")


def run_once(config_path=None, dry_run=False):
    """执行一次完整的抓取 + 发送流程"""
    logger.info("=" * 50)
    logger.info("每日新闻聚合 - 开始")
    logger.info("=" * 50)

    config = load_config(config_path)

    # 1. 抓取新闻
    logger.info("--- 抓取 RSS 新闻 ---")
    news_results = fetch_news(config["news_sources"])
    total_articles = sum(len(r["articles"]) for r in news_results)
    logger.info(f"共抓取 {total_articles} 篇文章")

    # 2. 抓取热搜
    hot_search_results = fetch_hot_search(config)
    total_hot = sum(len(hs["items"]) for hs in hot_search_results)
    logger.info(f"共抓取 {total_hot} 条热搜")

    # 3. 发送邮件
    if dry_run:
        logger.info("--- dry-run 模式，跳过发送 ---")
        logger.info(f"收件人: {config['email']['recipients']}")
        logger.info(f"RSS 来源: {len(news_results)} 个源, {total_articles} 条新闻")
        logger.info(f"热搜来源: {len(hot_search_results)} 个, {total_hot} 条")
        logger.info("完成（dry-run）")
        return True

    logger.info("--- 发送邮件 ---")
    send_email(config, news_results, hot_search_results)

    logger.info("=" * 50)
    logger.info("每日新闻聚合 - 完成")
    logger.info("=" * 50)
    return True


def run_daemon(config_path=None, dry_run=False):
    """守护模式：按配置的定时时间每天执行"""
    config = load_config(config_path)
    sched_config = config.get("schedule", {})

    if not sched_config.get("enabled", False):
        logger.info("定时调度未启用，执行一次后退出")
        run_once(config_path, dry_run)
        return

    send_time = sched_config.get("time", "08:00")
    logger.info(f"定时调度已启用，将在每天 {send_time} 执行")

    def job():
        logger.info("定时触发 - 开始执行")
        try:
            run_once(config_path, dry_run)
        except Exception as e:
            logger.error(f"执行失败: {e}")

    # 立即先执行一次
    job()

    # 设置定时任务
    schedule.every().day.at(send_time).do(job)

    logger.info("守护进程运行中...按 Ctrl+C 停止")
    try:
        while True:
            schedule.run_pending()
            import time
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("收到停止信号，退出")


def main():
    parser = argparse.ArgumentParser(
        description="每日新闻聚合 - 抓取新闻并发送到邮箱"
    )
    parser.add_argument(
        "-c", "--config",
        default=None,
        help="配置文件路径（默认: news_aggregator/config.yaml）",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="守护模式，按配置时间定时执行",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅测试抓取，不发送邮件",
    )
    parser.add_argument(
        "--test-send",
        action="store_true",
        help="测试模式：发送一封测试邮件验证配置是否正确",
    )

    args = parser.parse_args()

    if args.test_send:
        _test_send(args.config)
        return

    if args.daemon:
        run_daemon(args.config, args.dry_run)
    else:
        run_once(args.config, args.dry_run)


def _test_send(config_path=None):
    """发送测试邮件验证 SMTP 配置"""
    logger.info("发送测试邮件...")
    config = load_config(config_path)

    test_news = [{
        "source_name": "测试源",
        "articles": [{
            "title": "这是一封测试邮件",
            "link": "#",
            "summary": "如果你收到这封邮件，说明 SMTP 配置和新闻抓取系统工作正常。",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }],
    }]

    send_email(config, test_news, [])
    logger.info("测试邮件发送成功，请检查收件箱！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.exception(f"程序异常退出: {e}")
        sys.exit(1)

