# Project Attribution Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 明确说明本项目是基于 Amatsutsumi 原项目的非官方二次修改版，并将插件展示名改为“Bangumi 魔改版”。

**Architecture:** 只调整项目说明与插件元数据，不触碰 Python 运行逻辑、命令注册、依赖或版本兼容范围。README 负责完整版权归属说明，metadata.yaml 负责 AstrBot 展示信息和上游仓库指向。

**Tech Stack:** Markdown、YAML、PowerShell 静态校验、Git。

## Global Constraints

- README 必须明确“非官方二次修改版”、当前维护者 `united_pooh`、上游项目 `Amatsutsumi/astrbot_plugin_bangumi` 及不代表原项目官方。
- README 必须提醒保留原项目署名、版权信息和 `LICENSE-2.0`。
- `metadata.yaml` 的 `display_name` 必须为 `Bangumi 魔改版`。
- `metadata.yaml` 的 `desc` 必须明确“基于 Amatsutsumi 原项目的非官方二次修改版”。
- `metadata.yaml` 的 `author` 必须同时标明当前维护者 `united_pooh` 与上游作者/项目 `Amatsutsumi`。
- `metadata.yaml` 的 `repo` 必须为 `https://github.com/Amatsutsumi/astrbot_plugin_bangumi`。
- 保持版本号、AstrBot 兼容范围、命令和运行代码不变。

---

### Task 1: 更新 README 项目来源声明

**Files:**
- Modify: `README.md:12-17`

**Interfaces:**
- Consumes: 当前项目简介和已有的二次开发说明。
- Produces: 面向用户的完整项目来源与版权说明。

- [ ] **Step 1: 替换现有二次开发提示**

在项目简介后加入标题 `## 项目来源与版权说明`，使用以下文案：

```markdown
## 项目来源与版权说明

本项目是 `astrbot_plugin_bangumi` 的非官方二次修改版，基于 [Amatsutsumi/astrbot_plugin_bangumi](https://github.com/Amatsutsumi/astrbot_plugin_bangumi) 开发，由 `united_pooh` 维护。

本项目不代表原项目官方，也不与原作者构成官方关联。除本项目新增或修改部分外，原项目的版权、署名及许可证权益归原作者/权利人所有。分发和使用时请保留原有署名与 [LICENSE-2.0](LICENSE-2.0) 文件。
```

- [ ] **Step 2: 检查 README 文案位置和链接**

运行：

```powershell
rg -n "项目来源与版权说明|Amatsutsumi/astrbot_plugin_bangumi|LICENSE-2.0|united_pooh" README.md
```

预期：新声明出现在核心命令章节之前，且四个关键词均能匹配。

### Task 2: 更新 metadata.yaml 展示信息

**Files:**
- Modify: `metadata.yaml:2-7`

**Interfaces:**
- Consumes: 当前 AstrBot 插件元数据字段。
- Produces: 明确归属关系的插件展示名、描述、作者和上游仓库地址。

- [ ] **Step 1: 更新元数据字段**

将相关字段调整为：

```yaml
display_name: Bangumi 魔改版
desc: Bangumi 非官方二次修改版，基于 Amatsutsumi 原项目开发，由 united_pooh 维护，不代表原项目官方
author: united_pooh（上游作者/项目：Amatsutsumi）
repo: https://github.com/Amatsutsumi/astrbot_plugin_bangumi
```

保持 `version`、`license`、`astrbot_version` 和其他字段不变。

### Task 3: 静态验证并检查变更范围

**Files:**
- Test: `README.md`
- Test: `metadata.yaml`

**Interfaces:**
- Consumes: Task 1 和 Task 2 的文档变更。
- Produces: 可解析的元数据和仅限说明文件的变更集。

- [ ] **Step 1: 解析 YAML 并断言关键字段**

运行：

```powershell
@'
import yaml
from pathlib import Path

metadata = yaml.safe_load(Path("metadata.yaml").read_text(encoding="utf-8"))
assert metadata["display_name"] == "Bangumi 魔改版"
assert "Amatsutsumi" in metadata["desc"]
assert "非官方二次修改版" in metadata["desc"]
assert "united_pooh" in metadata["author"]
assert "Amatsutsumi" in metadata["author"]
assert metadata["repo"] == "https://github.com/Amatsutsumi/astrbot_plugin_bangumi"
'@ | python -
```

预期：命令正常退出且无断言错误。

- [ ] **Step 2: 检查差异范围和空白错误**

运行：

```powershell
git diff --check
git diff -- README.md metadata.yaml
```

预期：只有 README 和 metadata.yaml 的项目说明字段发生变化；没有 Python、依赖、版本或命令代码变更。

- [ ] **Step 3: Commit**

```powershell
git add README.md metadata.yaml
git commit -m "docs: clarify project attribution"
```
