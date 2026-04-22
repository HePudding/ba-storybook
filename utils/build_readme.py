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
    """CharacterId → 日文名 + 学校 + 部活 表格."""
    id_to_name = load_character_id_to_jp_name()
    meta = load_character_meta()
    rows = []
    for cid in sorted(id_to_name.keys()):
        name = id_to_name[cid]
        m = meta.get(cid, {})
        rows.append(f"| {cid} | {name} | {m.get('school', '')} | {m.get('club', '')} |")
    header = "| ID | 名前 | 学校 | 部活 |\n|----|------|------|------|\n"
    return header + "\n".join(rows)


def aggregate_errors() -> str:
    """收集各子目录的 _errors.log."""
    lines = []
    for p in sorted(OUT_DIR.glob("*/_errors.log")):
        lines.append(f"## {p.parent.name}\n")
        content = p.read_text(encoding="utf-8").strip()
        if content:
            lines.append("```\n" + content + "\n```\n")
        else:
            lines.append("*（エラーなし）*\n")
    return "\n".join(lines) if lines else "*（全カテゴリ エラーなし）*\n"


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
        "# Blue Archive 日本語ストーリー アーカイブ",
        "",
        f"**データ取得日**: {DATA_DATE}",
        f"**生成日時**: {agg['generated_at']}",
        f"**データソース**: [electricgoat/ba-data @ jp branch](https://github.com/electricgoat/ba-data/tree/jp)",
        "",
        "## 統計",
        "",
        f"- 総 Markdown ファイル数: **{total_files:,}**",
        f"- 総対話行数（シナリオ）: **{total_lines:,}**",
        f"- 総 MomoTalk メッセージ数: **{total_messages:,}**",
        f"- 既知エラー数: {total_errors}",
        "",
        "### カテゴリ別",
        "",
        "| カテゴリ | ファイル数 | 対話行数 | エラー |",
        "|---------|-----------|---------|-------|",
    ]
    jp_label = {
        "主線": "主線ストーリー",
        "グループストーリー": "グループストーリー",
        "イベント": "イベントストーリー",
        "絆ストーリー": "絆ストーリー",
        "ミニストーリー": "ミニストーリー",
        "モモトーク": "MomoTalk",
        "キャラクターデータ": "キャラクターデータ (プロフィール+台詞)",
    }
    for dirname, data in stats.items():
        label = jp_label.get(dirname, dirname)
        files = data.get("files", 0)
        cnt = data.get("lines", 0) or data.get("messages", 0)
        errs = data.get("errors", 0)
        lines.append(f"| [{label}](./{dirname}/) | {files} | {cnt} | {errs} |")

    lines += [
        "",
        "## ディレクトリ構造",
        "",
        "```",
        "ba-stories/",
        "├── 主線/                  # ヴォリューム→章→話 階層",
        "│   ├── 第0篇_プロローグ/",
        "│   ├── 第1篇_対策委員会編/",
        "│   ├── 第2篇_時計じかけの花のパヴァーヌ/",
        "│   ├── 第3篇_エデン条約編/",
        "│   ├── 第4篇_カルバノの兎編/",
        "│   ├── 第5篇_百花繚乱編/",
        "│   └── 最終編/",
        "├── グループストーリー/       # 部活/クラブ別エピソード",
        "├── イベント/                # イベント ID ごとに 1 ディレクトリ (51 events)",
        "├── 絆ストーリー/             # キャラクター別 絆エピソード (167 characters)",
        "├── ミニストーリー/           # 短編エピソード",
        "├── モモトーク/              # キャラクターとの SNS 対話",
        "└── キャラクターデータ/       # プロフィール・台詞・愛用品一覧",
        "```",
        "",
        "## Markdown 仕様",
        "",
        "各ファイルは YAML frontmatter 付き。本文での表現は：",
        "",
        "- `**話者**: セリフ` — キャラクター対話",
        "- `*ナレーション*` — 三人称ナレーション",
        "- `*（話者）セリフ*` — 特定キャラクターのナレーション",
        "- `*（先生（心の声））セリフ*` — 先生の内面独白",
        "- `> **先生（選択肢）**: 選項1 / 選項2` — プレイヤーの選択肢",
        "- `**【場所】**` — 場面切り替え",
        "",
        "Ruby 表記は `漢字（かな）` に展開。原文の `[FF6666]...[-]` などの色タグは除去。",
        "",
        "## 既知の不完全性",
        "",
        "- 主線 第1篇第3章 (Vol1 Ch3) : ScenarioMode に ID 記載があるが ScenarioScript 側に対応スクリプトなし。8 話分が空。",
        "- イベントタイトル: ローカライズされた日本語名がデータ内に存在せず、`event_<EventContentId>` の数値キーで表示。",
        "- グループストーリー のバケット名は `club_<volume>_<chapter>` 形式（実際の社団名は各ファイル内のキャラクター一覧から推測）。",
        "- 一部の GroupId で ScriptKr が純粋な指令のみ（TextJp 空）の場合はスキップ。",
        "",
        "## 角色名一覧",
        "",
        "<details>",
        "<summary>244 キャラクターの ID ↔ 名前対応表 (クリックで展開)</summary>",
        "",
        build_character_table(),
        "",
        "</details>",
        "",
        "## エラーログ (カテゴリ別)",
        "",
        aggregate_errors(),
        "",
        "---",
        "",
        "*本データは Yostar Japan 版 Blue Archive の精翻訳 (Japanese Yostar translation) に基づく。データ抽出パイプラインは `utils/` 参照。*",
    ]

    readme = "\n".join(lines) + "\n"
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")

    # Also write a combined errors.log
    errlog_content = aggregate_errors()
    (OUT_DIR / "errors.log").write_text(errlog_content, encoding="utf-8")

    print(json.dumps(agg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
