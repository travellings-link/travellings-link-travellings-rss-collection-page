import asyncio
import json
import os
import sys
import time

import aiohttp
import feedparser
from apscheduler.schedulers.background import BackgroundScheduler
from feedparser import FeedParserDict
from flask import Flask, render_template

# 用于解决运行出现 ModuleNotFoundError: No module named 'src' 问题
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/..")

from src.config import ConfigManager
from src.feed_storage import FeedStorage

HEADERS = ConfigManager().get("settings", "headers", default={})
MAX_CONCURRENT_CONNECTIONS = ConfigManager().get(
    "settings", "max_concurrent_connections", 10
)
MAX_ENTRIES = ConfigManager().get("settings", "max_entries", 100)

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore

# 由于目前没有可用 api，先从 json 文件中读取
with open("feed_urls.json", "r", encoding="utf-8") as f:
    feed_urls = json.load(f)["urls"]

app = Flask(__name__)
app.config["STATIC_FOLDER"] = "static"


async def async_fetch_feed(feed_url: str) -> FeedParserDict:
    """
    异步获取并解析给定 URL 的 RSS 订阅源。

    参数:
        feed_url (str): 要获取的 RSS 订阅源的 URL。

    返回:
        FeedParserDict: 解析后的 RSS 订阅源数据。

    异常:
        aiohttp.ClientError: 如果 HTTP 请求有问题。
        feedparser.FeedParserError: 如果解析订阅源有问题。
    """
    connector: aiohttp.BaseConnector = aiohttp.TCPConnector(
        limit=MAX_CONCURRENT_CONNECTIONS
    )  # 限制并发连接数为 MAX_CONCURRENT_CONNECTIONS
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(feed_url, headers=HEADERS) as response:
            return feedparser.parse(await response.text(encoding="utf-8"))


async def fetch_feeds_and_update_storage():
    """异步拉取 feeds 并更新存储"""
    print("拉取 feeds 中...")

    tasks = []

    for feed_url in feed_urls:
        tasks.append(asyncio.create_task(async_fetch_feed(feed_url)))

    for task in asyncio.as_completed(tasks):
        try:
            result = await task
            for entry in result["entries"]:
                FeedStorage().add_entry(entry)
        except Exception as e:
            print(f"拉取 feed 时出错: {e}")


def start_scheduler_task():
    """启动定期任务"""
    global formatted_next_fetched_time
    formatted_next_fetched_time = time.strftime(
        "%Y.%m.%d %H:%M:%S", time.localtime(time.time() + 60 * 60)
    )
    asyncio.run(fetch_feeds_and_update_storage())


@app.route("/")
def main_page():
    return render_template(
        "index.html",
        entries=FeedStorage().get_formatted_entries(),
        max_entries=MAX_ENTRIES,
        formatted_next_fetched_time=formatted_next_fetched_time,
    )


formatted_next_fetched_time = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())
# 先拉取一次
start_scheduler_task()
scheduler = BackgroundScheduler()
scheduler.add_job(start_scheduler_task, "interval", hours=1)
scheduler.start()


if __name__ == "__main__":
    app.run(debug=True)
