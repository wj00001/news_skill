# 每日新闻聚合 (News Aggregator)

自动抓取中文热点新闻，整理后发送到 QQ 邮箱（支持多人）。

## 功能

- 从多个 RSS 源抓取新闻（36氪、虎嗅、澎湃新闻、BBC中文、知乎日报）
- 抓取微博热搜和百度热搜
- 生成美观的 HTML 邮件
- 支持多人收件
- 支持定时调度（每天自动发送）

## 快速开始

### 1. 安装依赖

```bash
pip3 install -r news_aggregator/requirements.txt
```

### 2. 配置

编辑 `news_aggregator/config.yaml`：

- **email.recipients**: 添加收件人邮箱（支持多人）
- **news_sources**: 增删新闻源
- **hot_search**: 开关热搜抓取
- **schedule.time**: 定时发送时间

### 3. 运行

```bash
# 测试 SMTP 配置（先发一封测试邮件确认一切正常）
./run.sh --test-send

# 立即执行一次抓取并发送
./run.sh

# 仅测试抓取，不发送
./run.sh --dry-run

# 守护模式（每天按配置时间自动发送）
./run.sh --daemon
```

### 4. 设置开机自启（推荐）

使用 crontab 代替守护进程更稳定：

```bash
crontab -e
```

添加一行（每天早上 8:00 执行）：

```
0 8 * * * cd /path/to/news_skill && /usr/bin/python3 news_aggregator/main.py >> news_cron.log 2>&1
```

也可以 `chmod +x run.sh` 后直接使用 launchd。

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| email.smtp_host | SMTP 服务器 | smtp.qq.com |
| email.smtp_port | SMTP 端口（SSL） | 465 |
| email.sender | 发件邮箱 | 1980821093@qq.com |
| email.password | SMTP 授权码 | （已配置） |
| email.recipients | 收件人列表 | [1980821093@qq.com] |
| schedule.time | 定时发送时间 | 08:00 |
| hot_search.enabled | 是否抓取热搜 | true |
| hot_search.sources | 热搜来源 | [baidu, weibo] |

## 添加新新闻源

在 `config.yaml` 的 `news_sources` 列表中添加：

```yaml
news_sources:
  - name: 你的新闻源
    url: https://example.com/rss
    max_articles: 10
```

## 添加多人收件

```yaml
email:
  recipients:
    - 1980821093@qq.com
    - friend@example.com   # 加在这里
    - colleague@example.com
```

