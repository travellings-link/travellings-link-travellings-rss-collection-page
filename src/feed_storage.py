import bisect
import re
import time
from typing import cast

from feedparser import FeedParserDict

from src.config import ConfigManager
from src.utils import SingletonMeta

MAX_ENTRIES = ConfigManager().get("settings", "max_entries", 100)


class FormattedFeedParserDict(FeedParserDict):
    def __init__(self, feed_parser_dict: FeedParserDict):
        self.__dict__ = feed_parser_dict
        self.formatted_published: str = time.strftime(
            "%Y.%m.%d %H:%M:%S", self.published_parsed
        )
        self.formatted_summary: str = re.sub(r"<[^>]*>", "", self.summary)


class FeedStorage(metaclass=SingletonMeta):
    def __init__(self, entries: list[FeedParserDict] | None = None):
        self._formatted_entries_is_outdated: bool = (
            True  # 标记 formatted_entries 需要更新
        )
        self._oldest_entry_time: time.struct_time = time.strptime(
            "1949-10-01 8:00:00", "%Y-%m-%d %H:%M:%S"
        )  # 存储最老的 entry 时间
        self._formatted_last_fetched_time: str = time.strftime(
            "%Y.%m.%d %H:%M:%S", time.localtime()
        )
        self._entries: list[FeedParserDict]
        self._formatted_entries: list[FormattedFeedParserDict]
        if entries is not None:
            self._entries = entries
        else:
            self._entries = []

        self._format_entries()  # 初始化 self._formatted_entries

    def update_entries(self, new_entries: list[FeedParserDict]):
        """
        更新条目列表。

        Args:
            new_entries (list[FeedParserDict]): 新的条目列表，将替换当前的条目列表。
        """
        self._entries = new_entries

    def add_entry(self, entry: FeedParserDict):
        """
        添加一个新的条目到条目列表中，如果它比最老的条目更新或者当前条目数量未达到最大限制。
        确保条目不重复添加。

        Args:
            entry (FeedParserDict): 要添加的 feed 条目，表示为 FeedParserDict 对象。
        """
        # 如果新的 entry 比最老的 entry 还要新，或者当前的 entry 数量还没有达到上限，就插入
        # 并且保证 entry 不在 _entries 中，避免重复插入
        if (
            self._oldest_entry_time < entry["published_parsed"]
            or len(self._entries) < MAX_ENTRIES
        ) and entry not in self._entries:
            bisect.insort_right(
                self._entries,
                entry,
                key=lambda elem: -int(time.mktime(elem["published_parsed"])),
            )  # 按时间插入 从新到旧排序 index较小的较新
            self._entries = self._entries[:MAX_ENTRIES]  # 去掉多余的 entry
            self._oldest_entry_time = self._entries[-1][
                "published_parsed"
            ]  # 更新最老的 entry 时间
            self._formatted_entries_is_outdated = True  # 标记 formatted_entries 需要更新

    def get_raw_entries(self) -> list[FeedParserDict]:
        """
        获取内部存储的原始条目。

        Returns:
            list[FeedParserDict]: 包含原始条目的列表。
        """
        return self._entries

    def _format_entry(self, entry: FeedParserDict) -> FormattedFeedParserDict:
        """
        格式化 RSS 订阅条目。

        Args:
            entry (FeedParserDict): RSS 订阅条目，包含原始数据。

        Returns:
            FormattedFeedParserDict: 格式化后的条目。
        """
        return cast(
            FormattedFeedParserDict,
            {
                **entry,
                "formatted_published": time.strftime(
                    "%Y 年 %m 月 %d 日 %H:%M:%S", entry["published_parsed"]
                ),
                "formatted_summary": re.sub(r"<[^>]*>", "", entry["summary"]),
            },
        )

    def _format_entries(self):
        """
        格式化 _entries 列表中的条目并更新 _formatted_entries 列表。

        该方法将 _formatted_entries_is_outdated 标志设置为 False 并清空 _formatted_entries 列表。
        然后，它遍历 _entries 列表中的每个条目，使用 _format_entry 方法格式化条目，
        并将格式化后的条目添加到 _formatted_entries 列表中。
        """
        self._formatted_entries_is_outdated = False
        self._formatted_entries = []
        for entry in self._entries:
            self._formatted_entries.append(self._format_entry(entry))

    def get_formatted_entries(self) -> list[FormattedFeedParserDict]:
        """
        获取格式化的条目列表。
        如果格式化的条目列表已过期，则重新格式化条目列表。

        Returns:
            list[FormattedFeedParserDict]: 格式化的条目列表。
        """
        if self._formatted_entries_is_outdated:
            self._format_entries()
            self._formatted_last_fetched_time = time.strftime(
                "%Y.%m.%d %H:%M:%S", time.localtime()
            )
        return self._formatted_entries

    def get_formatted_last_fetched_time(self) -> str:
        """
        获取最后一次获取格式化条目的时间。

        Returns:
            str: 最后一次获取格式化条目的时间，格式为 "%Y.%m.%d %H:%M:%S"。
        """
        return self._formatted_last_fetched_time
