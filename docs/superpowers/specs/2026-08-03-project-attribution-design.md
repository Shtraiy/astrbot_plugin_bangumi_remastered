# 项目来源与版权说明设计

## 目标

让 README 和插件元数据明确表达：本项目是基于 Amatsutsumi 原项目的非官方二次修改版，由当前维护者 `united_pooh` 维护，不代表原项目官方。

## 修改范围

### README.md

在项目简介附近增加醒目的“项目来源与版权说明”段落，包含：

- 上游项目名称和链接：`Amatsutsumi/astrbot_plugin_bangumi`
- 当前维护者：`united_pooh`
- 非官方二次修改版及不代表原项目官方的声明
- 保留原项目署名、版权信息和 `LICENSE-2.0` 的提醒

### metadata.yaml

- `display_name` 从“Bangumi 增强版”改为“Bangumi 魔改版”
- `desc` 明确这是基于 Amatsutsumi 原项目的非官方二次修改版
- `author` 标明当前维护者 `united_pooh` 与上游作者/项目 `Amatsutsumi`
- `repo` 指向上游仓库 `https://github.com/Amatsutsumi/astrbot_plugin_bangumi`
- 版本号、AstrBot 兼容范围和其他配置保持不变

## 验证

- 检查 README 新增声明位于项目简介区域且链接正确
- 解析并检查 metadata.yaml 的字段值
- 确认没有修改插件命令、版本或运行逻辑
