# Bangumi LLM Tool 增强设计

## 目标

在不改变现有 `/bgm`、`/calendar`、订阅和渲染行为的前提下，新增 `bgm_search`、`bgm_subject`、`bgm_calendar` 三个 AstrBot LLM Tool，供 Agent 以结构化结果调用 Bangumi 能力。

## 设计原则

- Tool 复用现有 `BangumiService`，不模拟聊天命令，也不新增第二套 HTTP 客户端。
- Command 和 Tool 分离：Command 继续生成原有用户消息和图片；Tool 返回 JSON 文本作为模型可处理的 Tool 结果。
- Tool 不调用 `event.send()`，不主动向用户发送消息。
- Tool 只暴露有限字段，不直接返回完整 Bangumi 原始响应。
- API、代理、Access Token、缓存和现有配置继续由现有服务负责。

## 组件与职责

### `src/app/llm_tool_service.py`

新增轻量业务门面 `BangumiToolService`，依赖现有 `BangumiService`，提供：

- `search(keyword: str)`: 调用 `search_subjects()`，最多返回 5 条结果。
- `subject(subject_id: int)`: 调用 `get_subject_details()`，整理条目名称、类型、日期、评分、排名、简介、集数和链接。
- `calendar(weekday: int | None)`: 调用 `get_calendar()`；省略星期时使用当前 ISO 星期，显式参数限制为 1-7。

该服务将异常转换为 `success: false` 的结构化结果，并记录简短日志，不把 traceback 返回给模型。

### `main.py`

在 `BangumiPlugin` 中初始化 `BangumiToolService`，并添加三个 `@filter.llm_tool` 方法。每个方法使用完整 docstring 和 `Args:` 参数描述，通过 `event.plain_result(json.dumps(...))` 返回 JSON Tool 结果，不改变任何既有 command handler。

Tool 描述：

- `bgm_search`：当用户尚未获得明确 subject ID，需要搜索作品名称或确认条目时使用。
- `bgm_subject`：当已有明确 subject ID，需要查询详细资料时使用。
- `bgm_calendar`：当用户询问今天或指定星期的动画放送/更新时使用。

## 结构化结果

正常结果统一包含 `success: true`：

```json
{
  "success": true,
  "query": "孤独摇滚",
  "results": [
    {
      "id": 328609,
      "name": "ぼっち・ざ・ろっく！",
      "name_cn": "孤独摇滚！",
      "type": "动画",
      "date": "2022-10-09",
      "rating": 8.6,
      "rank": 80,
      "summary": "...",
      "url": "https://bgm.tv/subject/328609"
    }
  ]
}
```

具体字段只在现有 API 返回对应数据时输出，不伪造缺失数据。详情结果使用 `rating.score` 和 `rating.total` 等有价值字段；日历结果按指定星期返回条目列表和星期信息。

错误结果使用：

```json
{
  "success": false,
  "error": "No matching subject found"
}
```

## 测试策略

- 新增 `tests/app/test_llm_tool_service.py`，测试搜索结果限制和字段整理、详情字段整理、日历星期筛选、默认星期、空结果和异常转换。
- 在 `tests/test_main_plugin.py` 增加 Tool handler 测试，确认三个工具调用门面并返回 JSON，不调用发送接口。
- 保留现有 command 测试不变，并通过现有项目测试验证命令注册和 README/metadata 兼容性。

## 非目标

- 不新增角色、人物、Staff、关联条目等后续 Tool。
- 不新增配置项。
- 不修改任何既有 command 名称、参数、回复格式、图片渲染、API 地址或订阅逻辑。
- 不在插件内部实现自然语言意图识别、关键词分类器或 Agent Router。
