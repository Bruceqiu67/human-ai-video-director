# 案例一：《好帮手AI话术私教》5幕商业短视频规范模版

## 案例背景
本项目是《好帮手AI话术私教》产品宣传视频的开源配置模板（已彻底剔除企业私有音视频与真人肖像）。
完整验证了：
1. **杂志手账风 · 纸片人定格拼贴美学**（暖米白折痕网格底 `#FAF7F2` + 思源粗黑排版 + 荧光橙马克笔高亮）；
2. **微软官方 `zh-CN-YunxiNeural` 阳光亲和青年男声音色**（恒定 rate=+18%, 0% atempo）；
3. **大模型同底同质直出 (In-Context Conditioning)**（彻底废除文字卡片代码羽化切片，根除重影错位）；
4. **自适应居中防溢出胶囊字幕** 与 **BGM 动态侧链闪避混音**。

## 运行方式
```bash
python -m studio audio build --project examples/01_sales_coach_template
python -m studio prompt generate --project examples/01_sales_coach_template
```
