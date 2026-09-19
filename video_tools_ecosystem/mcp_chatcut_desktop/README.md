# 剪映 / CapCut 桌面端 MCP 协议中枢 (`mcp_chatcut_desktop`)

本目录打包了与 **剪映 / CapCut 桌面客户端** 进行实时双向交互的 MCP（Model Context Protocol）工具集。

## 目录内容
- `instructions.md`：详细的操作指南、调用范例与桌面自动化最佳实践。
- `schemas/`：包含全部 60 个原子工具的 JSON 定义，涵盖工程创建、时间线编辑、音频分离、画中画合成与成片导出。

## 核心原子工具速查
- **项目与工程**：`create_project`, `read_project`, `edit_project`, `delete_project`, `list_projects`
- **时间线控制**：`edit_track`, `edit_item`, `split_item`, `detach_audio`, `smooth_audio`
- **动效与字幕**：`create_motion_graphic_from_code`, `read_captions`, `edit_captions`
- **渲染与导出**：`local_export`, `export_motion_graphic_prores`

## 如何在 Agent 中启用？
将此目录的配置注册到你的 Agent（如 Antigravity / Claude Desktop / Cursor）的 MCP 配置中，即可让 Agent 拥有直接操作剪映桌面客户端的“双手”。
