"""配置加载模块"""

import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def load_config(path=None):
    """加载 YAML 配置文件"""
    config_file = path or CONFIG_PATH
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"配置文件不存在: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _validate(config)
    return config


def _validate(config):
    """基本配置校验"""
    if "email" not in config:
        raise ValueError("配置缺少 email 段")
    email = config["email"]
    required = ["smtp_host", "smtp_port", "sender", "password", "recipients"]
    for field in required:
        if field not in email:
            raise ValueError(f"email 配置缺少字段: {field}")
    if not email["recipients"]:
        raise ValueError("收件人列表不能为空")

    if "news_sources" not in config or not config["news_sources"]:
        raise ValueError("至少需要一个新闻源")

