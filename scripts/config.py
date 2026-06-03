"""Configuration file for Kindle reading data sync - V3 Premium Edition"""

import os
from pathlib import Path

# 📁 1. 基础物理路径定义 (使用高级 Path 架构)
# 脚本位于 scripts/ 目录下，通过两层 parent 完美死锁项目物理根目录
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data"

# 🔍 自动化防御：确保数据存储文件夹在云端/本地物理存在
DATA_DIR.mkdir(exist_ok=True)

# 🌐 2. 亚马逊接口爬虫网络底盘
# Amazon Kindle URL (amazon.cn service has been discontinued)
KINDLE_HISTORY_URL = "https://www.amazon.com/kindle/reading/insights/data"

# Headers for requests (模拟原生浏览器防止接口风控弹 403)
KINDLE_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# 📄 3. 核心持久化文件路径注册表
KINDLE_DATA_FILE = DATA_DIR / "kindle_data.json"
READING_DATA_FILE = DATA_DIR / "reading_data.json"

# 🌟 核心补齐点：全面接入 V3 引擎所需的本地原生书摘原材料物理路径
# 必须显式将 Path 对象转换成标准的字符串字符串（str()），以 100% 免疫 Python 跨模块 import 时的类型崩溃
CLIPPINGS_FILE = str(DATA_DIR / "My Clippings.txt")

# 物理对齐历史老数据文件的字符串类型转换，防止第三方脚本解析发生类型冲突
READING_DATA_FILE_STR = str(READING_DATA_FILE)
