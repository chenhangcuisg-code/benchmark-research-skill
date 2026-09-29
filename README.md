# Benchmark Research Skill

一个可安装的 Codex skill，用于把用户指定的 benchmark 清单逐项调研为可搜索、可跳转、可离线打包的研究看板，也支持按需生成章节 PDF。原始案例、来源版本、分类覆盖、协议差异、剩余缺口和再分发边界始终保留。

本仓库包含工作流程、看板模板、构建器和交付审计脚本；**不包含 `pretrain_eval` 的题库、论文全文、图片、PDF 或其他 benchmark 数据**。它也不声称运行了模型评测。

安装时把 [`benchmark-research`](benchmark-research) 整个目录复制到 `~/.codex/skills/benchmark-research`（Windows 通常是 `C:\Users\<用户名>\.codex\skills\benchmark-research`）。之后可用 `$benchmark-research` 调用，或在相关 benchmark 调研请求中由 Codex 自动选择。核心流程见 [`SKILL.md`](benchmark-research/SKILL.md)。

## 研究看板

大目录以看板作为主要阅读入口，保留用户的章节与条目身份。支持：

- 章节卡片、条目目录、审核分组与筛选。
- 目录搜索，以及原题正文和选中完整附件的全文搜索；明确显示索引加载与搜索范围。
- 条目概览、完整说明、原题、来源文件之间的稳定链接与引用回链。
- JSON 字段阅读、原始 JSON、长文本、代码、图像，以及来源文件预览和下载。
- 收藏、最多 4 项并排比较、CSV/JSON/Markdown 导出。
- 现有 PDF 的精确页码跳转，完整目录与文件 SHA-256 清单。
- 解压后直接打开 `index.html`；所有交互使用本地资源，也可放到静态网站。

安装构建依赖，把现有研究记录规范化为 [dashboard format](benchmark-research/references/dashboard-format.md) 中的结构，再运行：

```bash
python -m pip install -r requirements-dashboard.txt
python benchmark-research/scripts/dashboard_engine.py --root PATH_TO_REPORT --data dashboard-records.json --manifest delivery/manifest.json --output PATH_TO_REPORT/dashboard --zip PATH_TO_REPORT/delivery/dashboard.zip
python benchmark-research/scripts/audit_dashboard.py --root PATH_TO_REPORT/dashboard --zip PATH_TO_REPORT/delivery/dashboard.zip
```

构建器不访问网络，附件必须位于明确允许的文件清单中并通过哈希检查。原题与附件按需加载；未获准随包的文件只保留来源定位。用户自定义目录通过小型适配器连接，不限定章节数量或某一本手册的结构。

## PDF 交付

PDF 审计脚本只用 Python 标准库完成清单、详细条目和文件哈希检查；若需检查 PDF 能否打开，先安装 `pypdf`。在产出目录中准备 `inventory.json`、`audit/entries.json`、`delivery/manifest.json`，格式见 [record contract](benchmark-research/references/record-contract.md)，然后运行：

```bash
python benchmark-research/scripts/audit_delivery.py --root PATH_TO_HANDBOOK --check-pdf
```

脚本会报告缺少的条目、错误的五列表头、详细节数量不符、错误的公开文件哈希、非公开文件进入 manifest 以及 PDF 打开失败。它不能代替原始来源核验、版权判断或逐页排版检查。

回归验证：`python -m unittest discover -s tests -v`。浏览器交互与视觉检查须在实际交付看板上完成；单元测试不能证明可读性。

Skill 源代码按 [MIT License](LICENSE) 发布。使用本 skill 生成的调研报告、原题和附件各自受其来源许可约束；MIT 不授予第三方 benchmark 内容的再分发权。
