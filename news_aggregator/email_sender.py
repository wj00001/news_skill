"""HTML 邮件生成与发送模块"""

import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

logger = logging.getLogger(__name__)


def _build_email_html(news_results, hot_search_results, config):
    """构建美观的 HTML 邮件内容"""
    today = datetime.now().strftime("%Y年%m月%d日")

    style = """
    <style>
        body { font-family: -apple-system, 'PingFang SC','Microsoft YaHei',sans-serif;
               background: #f5f5f5; margin: 0; padding: 0; }
        .container { max-width: 640px; margin: 0 auto; background: #fff; }
        .header { background: linear-gradient(135deg, #1a73e8, #0d47a1);
                  color: #fff; padding: 32px 24px; text-align: center; }
        .header h1 { margin: 0 0 4px; font-size: 22px; font-weight: 600; }
        .header p { margin: 0; font-size: 14px; opacity: 0.85; }
        .section { padding: 20px 24px; }
        .section-title { font-size: 16px; font-weight: 600; color: #1a73e8;
                         border-bottom: 2px solid #1a73e8; padding-bottom: 8px;
                         margin: 0 0 16px; }
        .article { margin-bottom: 16px; padding: 12px; border-radius: 6px;
                   border: 1px solid #eee; }
        .article:hover { border-color: #1a73e8; }
        .article a { color: #222; text-decoration: none; display: block; }
        .article a:hover { color: #1a73e8; }
        .article .title { font-size: 14px; font-weight: 500; line-height: 1.5;
                          margin-bottom: 4px; }
        .article .summary { font-size: 12px; color: #666; line-height: 1.5; }
        .article .meta { font-size: 11px; color: #999; margin-top: 6px; }

        .hot-section { background: #fff8f0; border-radius: 8px; padding: 12px 16px;
                       margin-bottom: 16px; }
        .hot-section .hot-title { font-size: 15px; font-weight: 600;
                                   color: #e65100; margin-bottom: 12px; }
        .hot-item { display: flex; align-items: center; padding: 7px 0;
                    border-bottom: 1px solid #f0e0d0; font-size: 13px; }
        .hot-item:last-child { border-bottom: none; }
        .hot-rank { flex-shrink: 0; width: 22px; height: 22px; border-radius: 4px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 11px; font-weight: 600; margin-right: 8px; }
        .hot-rank.top3 { background: #e65100; color: #fff; }
        .hot-rank.normal { background: #f5e6d8; color: #8d6e63; }
        .hot-text { flex: 1; line-height: 1.5; }
        .hot-text a { color: #333; text-decoration: none; }
        .hot-text a:hover { color: #e65100; text-decoration: underline; }
        .hot-number { font-size: 11px; color: #999; margin-left: 4px;
                       flex-shrink: 0; }
        .footer { background: #fafafa; padding: 20px 24px; text-align: center;
                  font-size: 12px; color: #999; border-top: 1px solid #eee; }
        .empty { color: #999; font-size: 13px; font-style: italic; }
    </style>
    """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8">{style}</head>
<body>
<div class="container">
<div class="header">
    <h1>📰 每日新闻摘要</h1>
    <p>{today}</p>
</div>
"""

    # === 热搜区域 ===
    if hot_search_results:
        html += '<div class="section">'
        html += '<div class="section-title">🔥 今日热搜</div>'
        for hs in hot_search_results:
            if not hs["items"]:
                continue
            html += f'<div class="hot-section">'
            html += f'<div class="hot-title">{hs["source"]}</div>'
            for item in hs["items"]:
                rank_class = "top3" if item["rank"] <= 3 else "normal"
                hot_str = f'<span class="hot-number">{item["hot"]}</span>' if item.get("hot") else ""

                if item.get("url"):
                    link = f'<a href="{item["url"]}" target="_blank">{item["title"]}</a>'
                else:
                    link = item["title"]

                html += (
                    f'<div class="hot-item">'
                    f'<span class="hot-rank {rank_class}">{item["rank"]}</span>'
                    f'<span class="hot-text">{link}</span>'
                    f'{hot_str}'
                    f'</div>'
                )
            html += '</div>'
        html += '</div>'

    # === 新闻区域 ===
    has_articles = any(r["articles"] for r in news_results)
    if has_articles:
        html += '<div class="section">'
        html += '<div class="section-title">📌 热点新闻</div>'
        for result in news_results:
            if not result["articles"]:
                continue
            html += f'<h3 style="font-size:14px;color:#333;margin:16px 0 8px;">📎 {result["source_name"]}</h3>'
            for article in result["articles"]:
                html += (
                    f'<div class="article">'
                    f'<a href="{article["link"]}" target="_blank">'
                    f'<div class="title">{article["title"]}</div>'
                    f'<div class="summary">{article["summary"]}</div>'
                    f'<div class="meta">{article["published"]}</div>'
                    f'</a>'
                    f'</div>'
                )
        html += '</div>'
    else:
        html += (
            '<div class="section"><p class="empty">'
            '暂无新闻数据，请检查网络连接或新闻源配置。</p></div>'
        )

    # 尾部
    html += (
        '<div class="footer">'
        f'<p>发送时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'
        f'<p>由 News Aggregator 自动发送</p>'
        '</div></div></body></html>'
    )

    return html


def send(config, news_results, hot_search_results):
    """构建并发送邮件"""
    today = datetime.now().strftime("%Y-%m-%d")
    subject = config.get("email_subject", "每日新闻摘要 - {date}").format(date=today)

    html_content = _build_email_html(news_results, hot_search_results, config)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = config["email"]["sender"]
    msg["To"] = ", ".join(config["email"]["recipients"])

    part = MIMEText(html_content, "html", "utf-8")
    msg.attach(part)

    logger.info(f"正在发送邮件到: {config['email']['recipients']}")

    try:
        smtp_host = config["email"]["smtp_host"]
        smtp_port = config["email"]["smtp_port"]
        sender = config["email"]["sender"]
        password = config["email"]["password"]
        recipients = config["email"]["recipients"]

        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())

        logger.info("邮件发送成功！")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP 认证失败，请检查邮箱地址和授权码是否正确")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP 发送失败: {e}")
        raise
    except Exception as e:
        logger.error(f"发送邮件时出错: {e}")
        raise
