from unittest.mock import AsyncMock, MagicMock

import pytest

from astrbot_plugin_bangumi.src.app.llm_tool_service import BangumiToolService
from astrbot_plugin_bangumi.src.domain.exceptions import BangumiApiError, NoSubjectFound


@pytest.fixture
def mock_service() -> MagicMock:
    return MagicMock()


@pytest.mark.asyncio
async def test_search_trims_keyword_limits_results_and_normalizes_fields(
    mock_service: MagicMock,
) -> None:
    mock_service.search_subjects = AsyncMock(
        return_value={
            "data": [
                {
                    "id": 1,
                    "name": "Original",
                    "name_cn": "中文名",
                    "type": 2,
                    "date": "2024-01-01",
                    "summary": "A summary",
                    "rating": {"score": 8.5, "rank": 20},
                },
                {"id": 2, "name": "Second", "type": 4},
                {"id": 3, "name": "Third", "name_cn": "第三", "type": 1},
                {"id": 4, "name": "Fourth"},
                {"id": 5, "name": "Fifth"},
                {"id": 6, "name": "Ignored"},
            ]
        }
    )

    result = await BangumiToolService(mock_service, max_results=5).search(
        "  keyword  "
    )

    assert result["success"] is True
    assert result["query"] == "keyword"
    assert len(result["results"]) == 5
    assert result["results"][0] == {
        "id": 1,
        "name": "Original",
        "name_cn": "中文名",
        "type": 2,
        "date": "2024-01-01",
        "summary": "A summary",
        "rating": 8.5,
        "rank": 20,
        "type_name": "动画",
        "url": "https://bgm.tv/subject/1",
    }
    mock_service.search_subjects.assert_awaited_once_with(
        keyword="keyword", limit=5
    )


@pytest.mark.asyncio
async def test_subject_returns_selected_details(
    mock_service: MagicMock,
) -> None:
    mock_service.get_subject_details = AsyncMock(
        return_value={
            "id": 10,
            "name": "Original",
            "name_cn": "中文名",
            "type": 2,
            "date": "2024-01-01",
            "summary": "A summary",
            "eps": 12,
            "rating": {"score": 8.5, "total": 100, "rank": 20},
            "unused": "not exposed",
        }
    )

    result = await BangumiToolService(mock_service).subject(10)

    assert result == {
        "success": True,
        "subject": {
            "id": 10,
            "name": "Original",
            "name_cn": "中文名",
            "type": 2,
            "type_name": "动画",
            "date": "2024-01-01",
            "summary": "A summary",
            "episodes": 12,
            "rating": {"score": 8.5, "total": 100},
            "rank": 20,
            "url": "https://bgm.tv/subject/10",
        },
    }
    mock_service.get_subject_details.assert_awaited_once_with("10")


@pytest.mark.asyncio
async def test_calendar_filters_by_weekday_and_returns_items(
    mock_service: MagicMock,
) -> None:
    mock_service.get_calendar = AsyncMock(
        return_value=[
            {
                "weekday": {"id": 1, "cn": "星期一", "en": "Mon"},
                "items": [],
            },
            {
                "weekday": {"id": 2, "cn": "星期二", "en": "Tue"},
                "items": [
                    {"id": 20, "name": "Original", "name_cn": "中文名"},
                ],
            },
        ]
    )

    result = await BangumiToolService(mock_service).calendar(2)

    assert result == {
        "success": True,
        "weekday_id": 2,
        "weekday": {"id": 2, "cn": "星期二", "en": "Tue"},
        "items": [
            {
                "id": 20,
                "name": "Original",
                "name_cn": "中文名",
                "url": "https://bgm.tv/subject/20",
            }
        ],
    }
    mock_service.get_calendar.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_calendar_defaults_to_current_iso_weekday(
    mock_service: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_service.get_calendar = AsyncMock(return_value=[])
    fake_datetime = MagicMock()
    fake_datetime.now.return_value.isoweekday.return_value = 4
    monkeypatch.setattr(
        "astrbot_plugin_bangumi.src.app.llm_tool_service.datetime.datetime",
        fake_datetime,
    )

    result = await BangumiToolService(mock_service).calendar()

    assert result["success"] is True
    assert result["weekday_id"] == 4
    assert result["items"] == []


@pytest.mark.asyncio
async def test_tool_service_returns_stable_errors(
    mock_service: MagicMock,
) -> None:
    tool_service = BangumiToolService(mock_service)

    assert await tool_service.search(" ") == {
        "success": False,
        "error": "keyword is required",
    }
    assert await tool_service.calendar(8) == {
        "success": False,
        "error": "weekday must be between 1 and 7",
    }

    mock_service.search_subjects = AsyncMock(return_value={"data": []})
    assert await tool_service.search("missing") == {
        "success": False,
        "error": "No matching subject found",
    }

    mock_service.get_subject_details = AsyncMock(return_value={})
    assert await tool_service.subject(999) == {
        "success": False,
        "error": "Subject not found",
    }


@pytest.mark.asyncio
async def test_api_errors_are_not_exposed_to_the_model(
    mock_service: MagicMock,
) -> None:
    mock_service.search_subjects = AsyncMock(side_effect=BangumiApiError("secret"))

    result = await BangumiToolService(mock_service).search("keyword")

    assert result == {
        "success": False,
        "error": "Bangumi API request failed",
    }

    mock_service.get_subject_details = AsyncMock(side_effect=NoSubjectFound())
    assert await BangumiToolService(mock_service).subject(10) == {
        "success": False,
        "error": "Subject not found",
    }
