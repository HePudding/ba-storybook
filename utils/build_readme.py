"""读取 ba-stories/ 下所有 _stats.json 并生成顶层 README.md + 角色索引."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .load_data import (
    ROOT,
    character_id_to_name,
    load_character_id_to_jp_name,
    load_character_meta,
    load_character_names,
)


OUT_DIR = ROOT / "ba-stories"
DATA_DATE = "2026-04-22"


def collect_stats() -> dict:
    stats: dict[str, dict] = {}
    for p in OUT_DIR.glob("*/_stats.json"):
        with p.open(encoding="utf-8") as fh:
            stats[p.parent.name] = json.load(fh)
    return stats


def build_character_table() -> str:
    """CharacterId -> 日文名 + 学校 + 社团 表格."""
    id_to_name = load_character_id_to_jp_name()
    meta = load_character_meta()
    rows = []
    for cid in sorted(id_to_name.keys()):
        name = id_to_name[cid]
        m = meta.get(cid, {})
        rows.append(f"| {cid} | {name} | {m.get('school', '')} | {m.get('club', '')} |")
    header = "| ID | 名称 | 学校 | 社团 |\n|----|------|------|------|\n"
    return header + "\n".join(rows)


def aggregate_errors() -> str:
    """收集各子目录的 _errors.log."""
    lines = []
    for p in sorted(OUT_DIR.glob("*/_errors.log")):
        lines.append(f"### {p.parent.name}\n")
        content = p.read_text(encoding="utf-8").strip()
        if content:
            lines.append("```\n" + content + "\n```\n")
        else:
            lines.append("*（无错误）*\n")
    return "\n".join(lines) if lines else "*（所有类别无错误）*\n"


def main() -> None:
    stats = collect_stats()

    # Agg counts
    total_files = sum(int(s.get("files", 0)) for s in stats.values())
    total_lines = sum(int(s.get("lines", 0)) for s in stats.values())
    total_messages = sum(int(s.get("messages", 0)) for s in stats.values())
    total_errors = sum(int(s.get("errors", 0)) for s in stats.values())

    # Aggregate into a single json
    agg = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "data_date": DATA_DATE,
        "total_markdown_files": total_files,
        "total_dialog_lines": total_lines,
        "total_momotalk_messages": total_messages,
        "total_errors": total_errors,
        "by_type": stats,
    }
    (OUT_DIR / "_aggregate.json").write_text(
        json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Build README
    lines = [
        "# 蔚蓝档案 日语剧情文本存档",
        "",
        f"**数据获取日期**：{DATA_DATE}",
        f"**生成时间**：{agg['generated_at']}",
        f"**数据来源**：[electricgoat/ba-data @ jp 分支](https://github.com/electricgoat/ba-data/tree/jp)",
        "",
        "## 统计",
        "",
        f"- Markdown 文件总数：**{total_files:,}**",
        f"- 剧情对话行数：**{total_lines:,}**",
        f"- MomoTalk 消息条数：**{total_messages:,}**",
        f"- 已知错误数：{total_errors}",
        "",
        "### 分类统计",
        "",
        "| 类别 | 文件数 | 对话行数 | 错误 |",
        "|------|--------|---------|------|",
    ]
    cn_label = {
        "主線": "主线故事",
        "グループストーリー": "社团故事",
        "イベント": "活动故事",
        "絆ストーリー": "羁绊故事",
        "ミニストーリー": "迷你故事",
        "モモトーク": "MomoTalk",
        "キャラクターデータ": "角色数据（档案+台词）",
    }
    for dirname, data in stats.items():
        label = cn_label.get(dirname, dirname)
        files = data.get("files", 0)
        cnt = data.get("lines", 0) or data.get("messages", 0)
        errs = data.get("errors", 0)
        lines.append(f"| [{label}](./{dirname}/) | {files} | {cnt} | {errs} |")

    lines += [
        "",
        "## 目录结构",
        "",
        "```",
        "ba-stories/",
        "├── 主線/                  # 篇→章→话 层级",
        "│   ├── 第0篇_プロローグ/",
        "│   ├── 第1篇_対策委員会編/",
        "│   ├── 第2篇_時計じかけの花のパヴァーヌ/",
        "│   ├── 第3篇_エデン条約編/",
        "│   ├── 第4篇_カルバノの兎編/",
        "│   ├── 第5篇_百花繚乱編/",
        "│   └── 最終編/",
        "├── グループストーリー/       # 按社团分类的剧情",
        "├── イベント/                # 按活动 ID 分目录（51 个活动）",
        "├── 絆ストーリー/             # 按角色分类的羁绊故事（167 名角色）",
        "├── ミニストーリー/           # 短篇故事",
        "├── モモトーク/              # 角色 SNS 对话",
        "└── キャラクターデータ/       # 角色档案、台词、爱用品一览",
        "```",
        "",
        "## Markdown 格式说明",
        "",
        "每个文件带有 YAML frontmatter。正文格式：",
        "",
        "- `**说话人**: 台词` — 角色对话",
        "- `*旁白*` — 第三人称旁白",
        "- `*（说话人）台词*` — 特定角色的旁白",
        "- `*（先生（内心独白））台词*` — 先生的心理活动",
        "- `> **先生（选择肢）**: 选项1 / 选项2` — 玩家选择",
        "- `**【地点】**` — 场景切换",
        "",
        "Ruby 标记展开为 `漢字（かな）` 形式。原文中的颜色标签 `[FF6666]...[-]` 已移除。",
        "",
        "## 已知不完整项",
        "",
        "- 主线第 1 篇第 3 章（Vol1 Ch3）：ScenarioMode 中有 ID 记录，但 ScenarioScript 中无对应脚本，8 话为空。",
        "- 活动标题：本地化的日语名不在数据中，以 `event_<EventContentId>` 数字键显示。",
        "- 社团故事的分组名为 `club_<volume>_<chapter>` 格式（实际社团名从各文件内角色列表推断）。",
        "- 部分 GroupId 的 ScriptKr 仅含纯指令（TextJp 为空），已跳过。",
        "",
        "## 角色名一览",
        "",
        "<details>",
        "<summary>244 名角色 ID ↔ 名称对照表（点击展开）</summary>",
        "",
        build_character_table(),
        "",
        "</details>",
        "",
        "## 错误日志（按类别）",
        "",
        aggregate_errors(),
        "",
        "---",
        "",
        "*本数据基于 Yostar Japan 版 Blue Archive 的精翻译（Japanese Yostar translation）。数据提取管线见 `utils/`。*",
    ]

    readme = "\n".join(lines) + "\n"
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")

    # Also write a combined errors.log
    errlog_content = aggregate_errors()
    (OUT_DIR / "errors.log").write_text(errlog_content, encoding="utf-8")

    print(json.dumps(agg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
