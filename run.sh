#!/bin/bash
# 每日新闻聚合 - 快速运行脚本
# 用法:
#   ./run.sh              # 立即抓取并发送
#   ./run.sh --dry-run    # 仅测试抓取，不发邮件
#   ./run.sh --test-send  # 发送测试邮件
#   ./run.sh --daemon     # 守护模式（每天定时执行）

cd "$(dirname "$0")"
python3 news_aggregator/main.py "$@"

