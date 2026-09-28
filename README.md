# Benchmark Research Skill

一个可安装的 Codex skill，用于把用户指定的 benchmark 清单逐项调研为可复核的手册。输出强调五列总览、每项独立详细条目、真实原题的版本与记录定位、分类覆盖、缺口和再分发边界，并按项目章节生成紧凑 PDF。

本仓库只包含工作流程、格式约定和交付审计脚本；**不包含 `pretrain_eval` 的题库、论文全文、图片、PDF 或其他 benchmark 数据**。它也不声称运行了模型评测。

安装时把 [`benchmark-research`](benchmark-research) 整个目录复制到 `~/.codex/skills/benchmark-research`（Windows 通常是 `C:\Users\<用户名>\.codex\skills\benchmark-research`）。之后可用 `$benchmark-research` 调用，或在相关 benchmark 调研请求中由 Codex 自动选择。核心流程见 [`SKILL.md`](benchmark-research/SKILL.md)。

审计脚本只用 Python 标准库完成清单、详细条目和文件哈希检查；若需检查 PDF 可读性，先安装 `pypdf`。在产出目录中准备 `inventory.json`、`audit/entries.json`、`delivery/manifest.json`，格式见 [record contract](benchmark-research/references/record-contract.md)，然后运行：

```bash
python benchmark-research/scripts/audit_delivery.py --root PATH_TO_HANDBOOK --check-pdf
```

脚本会报告缺少的条目、错误的五列表头、详细节数量不符、错误的公开文件哈希、非公开文件进入 manifest 以及 PDF 打开失败。它不能代替原始来源核验、版权判断或逐页排版检查。

Skill 源代码按 [MIT License](LICENSE) 发布。使用本 skill 生成的调研报告、原题和附件各自受其来源许可约束；MIT 不授予第三方 benchmark 内容的再分发权。
