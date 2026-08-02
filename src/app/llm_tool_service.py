import datetime
import logging
from collections.abc import Mapping
from typing import cast

from ..api import BangumiService
from ..bangumi_types import JsonObject, JsonValue
from ..domain.exceptions import BangumiApiError, BangumiRateLimitError, NoSubjectFound

logger = logging.getLogger(__name__)


class BangumiToolService:
    """Adapt Bangumi API responses into compact, model-friendly JSON objects."""

    def __init__(self, service: BangumiService, max_results: int = 5) -> None:
        self.service = service
        self.max_results = max(1, min(max_results, 5))

    async def search(self, keyword: str) -> JsonObject:
        normalized_keyword = keyword.strip() if isinstance(keyword, str) else ""
        if not normalized_keyword:
            return {"success": False, "error": "keyword is required"}

        try:
            response = await self.service.search_subjects(
                keyword=normalized_keyword,
                limit=self.max_results,
            )
            raw_items = response.get("data", [])
            items = [
                self._normalize_search_item(item)
                for item in raw_items[: self.max_results]
                if isinstance(item, Mapping)
            ]
        except (
            BangumiApiError,
            BangumiRateLimitError,
            NoSubjectFound,
            RuntimeError,
            ValueError,
            TypeError,
        ):
            logger.error("Bangumi search tool failed")
            return {"success": False, "error": "Bangumi API request failed"}

        if not items:
            return {"success": False, "error": "No matching subject found"}
        return {"success": True, "query": normalized_keyword, "results": items}

    async def subject(self, subject_id: int) -> JsonObject:
        if isinstance(subject_id, bool) or not isinstance(subject_id, int):
            return {"success": False, "error": "subject_id must be a positive integer"}
        if subject_id <= 0:
            return {"success": False, "error": "subject_id must be a positive integer"}

        try:
            details = await self.service.get_subject_details(str(subject_id))
        except NoSubjectFound:
            return {"success": False, "error": "Subject not found"}
        except (
            BangumiApiError,
            BangumiRateLimitError,
            RuntimeError,
            ValueError,
            TypeError,
        ):
            logger.error("Bangumi subject tool failed")
            return {"success": False, "error": "Bangumi API request failed"}

        if not isinstance(details, Mapping) or not details:
            return {"success": False, "error": "Subject not found"}

        subject = self._normalize_subject(details, fallback_id=subject_id)
        return {"success": True, "subject": subject}

    async def calendar(self, weekday: int | None = None) -> JsonObject:
        if weekday is None:
            weekday_id = datetime.datetime.now().isoweekday()
        elif isinstance(weekday, bool) or not isinstance(weekday, int):
            return {"success": False, "error": "weekday must be between 1 and 7"}
        else:
            weekday_id = weekday

        if weekday_id < 1 or weekday_id > 7:
            return {"success": False, "error": "weekday must be between 1 and 7"}

        try:
            days = await self.service.get_calendar()
        except (
            BangumiApiError,
            BangumiRateLimitError,
            NoSubjectFound,
            RuntimeError,
            ValueError,
            TypeError,
        ):
            logger.error("Bangumi calendar tool failed")
            return {"success": False, "error": "Bangumi API request failed"}

        matched_day: Mapping[str, object] | None = None
        for day in days:
            if not isinstance(day, Mapping):
                continue
            raw_weekday = day.get("weekday")
            if not isinstance(raw_weekday, Mapping):
                continue
            if raw_weekday.get("id") == weekday_id:
                matched_day = day
                break

        weekday_info: JsonObject = {"id": weekday_id}
        items: list[JsonObject] = []
        if matched_day is not None:
            raw_weekday = matched_day.get("weekday")
            if isinstance(raw_weekday, Mapping):
                weekday_info = self._normalize_weekday(raw_weekday, weekday_id)
            raw_items = matched_day.get("items", [])
            if isinstance(raw_items, list):
                items = [
                    self._normalize_calendar_item(item)
                    for item in raw_items
                    if isinstance(item, Mapping)
                ]

        return {
            "success": True,
            "weekday_id": weekday_id,
            "weekday": weekday_info,
            "items": items,
        }

    @classmethod
    def _normalize_search_item(cls, item: Mapping[str, object]) -> JsonObject:
        normalized: JsonObject = {}
        cls._copy_field(item, normalized, "id")
        cls._copy_field(item, normalized, "name")
        cls._copy_field(item, normalized, "name_cn")
        cls._copy_field(item, normalized, "type")
        date = item.get("date") or item.get("air_date")
        if date is not None:
            normalized["date"] = cast(JsonValue, date)
        cls._copy_field(item, normalized, "summary")
        cls._copy_rating_fields(item, normalized)
        subject_type = item.get("type")
        type_name = cls._subject_type_name(subject_type)
        if type_name is not None:
            normalized["type_name"] = type_name
        subject_id = item.get("id")
        if isinstance(subject_id, (int, str)) and not isinstance(subject_id, bool):
            normalized["url"] = f"https://bgm.tv/subject/{subject_id}"
        return normalized

    @classmethod
    def _normalize_subject(
        cls, details: Mapping[str, object], fallback_id: int
    ) -> JsonObject:
        normalized: JsonObject = {}
        subject_id = details.get("id", fallback_id)
        if isinstance(subject_id, (int, str)) and not isinstance(subject_id, bool):
            normalized["id"] = subject_id
            normalized["url"] = f"https://bgm.tv/subject/{subject_id}"
        for field in ("name", "name_cn", "type", "summary"):
            cls._copy_field(details, normalized, field)

        subject_type = details.get("type")
        type_name = cls._subject_type_name(subject_type)
        if type_name is not None:
            normalized["type_name"] = type_name

        date = details.get("date") or details.get("air_date")
        if date is not None:
            normalized["date"] = cast(JsonValue, date)

        episodes = details.get("eps")
        if episodes is None:
            episodes = details.get("total_episodes")
        if episodes is not None:
            normalized["episodes"] = cast(JsonValue, episodes)

        rating = details.get("rating")
        if isinstance(rating, Mapping):
            normalized_rating: JsonObject = {}
            for field in ("score", "total"):
                cls._copy_field(rating, normalized_rating, field)
            if normalized_rating:
                normalized["rating"] = normalized_rating
            rank = details.get("rank", rating.get("rank"))
            if rank is not None:
                normalized["rank"] = cast(JsonValue, rank)
        else:
            cls._copy_rating_fields(details, normalized)
        return normalized

    @classmethod
    def _normalize_weekday(
        cls, weekday: Mapping[str, object], fallback_id: int
    ) -> JsonObject:
        normalized: JsonObject = {"id": fallback_id}
        for field in ("cn", "en", "ja"):
            cls._copy_field(weekday, normalized, field)
        return normalized

    @classmethod
    def _normalize_calendar_item(cls, item: Mapping[str, object]) -> JsonObject:
        normalized: JsonObject = {}
        for field in ("id", "name", "name_cn"):
            cls._copy_field(item, normalized, field)
        cls._copy_rating_fields(item, normalized)
        subject_id = item.get("id")
        if isinstance(subject_id, (int, str)) and not isinstance(subject_id, bool):
            normalized["url"] = f"https://bgm.tv/subject/{subject_id}"
        return normalized

    @staticmethod
    def _copy_field(
        source: Mapping[str, object], target: JsonObject, field: str
    ) -> None:
        value = source.get(field)
        if value is not None:
            target[field] = cast(JsonValue, value)

    @classmethod
    def _copy_rating_fields(
        cls, source: Mapping[str, object], target: JsonObject
    ) -> None:
        raw_rating = source.get("rating")
        if isinstance(raw_rating, Mapping):
            cls._copy_field(raw_rating, target, "score")
            if "score" in target:
                target["rating"] = target.pop("score")
            rank = source.get("rank", raw_rating.get("rank"))
        else:
            if raw_rating is not None:
                target["rating"] = cast(JsonValue, raw_rating)
            rank = source.get("rank")
        if rank is not None:
            target["rank"] = cast(JsonValue, rank)

    @staticmethod
    def _subject_type_name(subject_type: object) -> str | None:
        names = {
            1: "书籍",
            2: "动画",
            3: "音乐",
            4: "游戏",
            6: "三次元",
        }
        if isinstance(subject_type, int) and not isinstance(subject_type, bool):
            return names.get(subject_type)
        return None
