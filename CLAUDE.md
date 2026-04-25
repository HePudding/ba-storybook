# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言

始终使用简体中文与用户交流。所有文档使用简体中文。

## 常用命令

```bash
# 剧情文本生成管线
python3 -m utils.build_manifest       # 重建 manifest.json（GroupId 分类）
python3 -m utils.generate_all         # 生成全部 7 类剧情 Markdown
python3 -m utils.build_readme         # 重建 ba-stories/README.md 和统计

# 翻译表管线
python3 -m utils.build_translation_table   # 从游戏数据提取 JP→CN
python3 -m utils.build_gaps                # 找出缺失条目
python3 -m utils.merge_translations        # 合并所有来源（优先级：game_data_tw > moegirl > gamekee）
python3 -m utils.build_md_report           # 生成 翻译对照表.md

# 冒烟测试
python3 -m utils._smoke_test
```

所有模块通过 `python3 -m utils.<module>` 运行，不要直接 `python3 utils/<module>.py`。

## 架构概览

两条独立管线：

**剧情提取管线**：`raw-data/Excel` (JP JSON) → `load_data.py` (加载+索引) → `parse_dialogue.py` (ScriptKr 指令解析) → `format_markdown.py` (Markdown 输出) → `generate_all.py` (调度 7 类生成) → `ba-stories/` (2022 个 Markdown 文件)

**翻译表管线**：`raw-data-global/Excel` (Tw 字段，繁中) → `build_translation_table.py` (初始提取) → `build_gaps.py` (缺失识别) → 外部补全 (moegirl/gamekee JSON) → `merge_translations.py` (合并+繁转简) → `translation_table.json`

## 关键设计决策

- **数据源结构**：Excel JSON 都包在 `{"DataList": [...]}` 里，加载时需要 unwrap。`load_translation.py` 和 `load_data.py` 都处理了这一点。
- **角色名解析**：ScriptKr 用韩语角色名，需通过 `ScenarioCharacterNameExcelTable` 映射到日语。无法匹配时用子串回退（如 "통신아로나" 包含 "아로나" → "アロナ"），最终兜底为 `NPC_<id>`。
- **繁简转换**：翻译表的主要来源是 global 分支的 Tw 字段（繁体中文），通过 `opencc` 的 `t2s` 配置转为简体中文。转换在 `merge_translations.py` 的 `_convert_all_to_sc()` 中执行。
- **社团名/活动名**：大部分社团名和全部活动名不在 Excel 表中（存在于 UI AssetBundle），需从萌娘百科/GameKee 外部补全。
- **目录名是日语**：`ba-stories/` 下的子目录名（主線、イベント 等）是日语，这是实际文件夹名，不要改。

## 外部依赖

唯一的第三方包是 `opencc-python-reimplemented`（繁转简）。其余全部使用标准库。
