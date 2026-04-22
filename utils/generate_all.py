"""遍历 manifest.json 为每个类型生成 Markdown 文件.

输出到 ba-stories/ 下各子目录。每个子目录写入 _stats.json。
错误写入 _errors.log。
"""
from __future__ import annotations

import json
import re
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .character_info import character_profile_markdown, favor_items_markdown, load_favor_items
from .format_markdown import momotalk_to_markdown, parsed_to_markdown
from .load_data import (
    ROOT,
    character_id_to_name,
    load_character_meta,
    load_scenario_mode_index,
    momotalk_groups_by_character,
)
from .parse_dialogue import parse_group


OUT_DIR = ROOT / "ba-stories"

VOLUME_TITLES_JP = {
    0: "第0篇_プロローグ",
    1: "第1篇_対策委員会編",
    2: "第2篇_時計じかけの花のパヴァーヌ",
    3: "第3篇_エデン条約編",
    4: "第4篇_カルバノの兎編",
    5: "第5篇_百花繚乱編",
    100: "最終編",
}

# Club internal key → Japanese display name
CLUB_NAMES_JP = {
    "Kohshinjo68": "便利屋68",
    "GameDev": "ゲーム開発部",
    "Veritas": "ヴェリタス",
    "Fuuki": "風紀委員会",
    "JusticeTask": "正義実現委員会",
    "Matsuri": "トリニティ祭りの準備委員会",
    "Countermeasure": "シャーレ",
    "Kendo": "剣道部",
    "MakeUpWork": "補習授業部",
    "Meihuayuan": "梅華園",
    "Pandemonium": "パンデモニウム",
    "TrainingClub": "トレーニングクラブ",
    "Ninjutsu": "忍術研究部",
    "HyakkiyakoAlliance": "百鬼夜行連合",
    "TheSeminar": "生徒会",
    "Cleaning": "清掃及課外活動部",
    "Sports": "運動部",
    "Engineer": "エンジニア部",
    "Arius": "アリウススクワッド",
    "Oniyuri": "鬼百合愛好会",
    "Happy": "Happyクラブ",
    "Onsen": "温泉開発部",
    "GoStop": "花札同好会",
    "HoukagoSweets": "放課後スイーツ部",
    "NinpoKenkyubu": "忍法研究部",
    "Gourmet": "美食研究会",
    "Tea": "茶道部",
    "SisterHood": "シスターフッド",
    "RedwinterLibrary": "レッドウィンター図書室",
    "Emergentology": "救急医学部",
    "CVC": "聖園中央",
    "FoodLore": "食料調査隊",
    "Scuba": "スキューバ同好会",
    "Endanchou": "演談場",
    "TrinityVigilance": "トリニティ守護委員会",
    "Rabbit": "Rabbit小隊",
    "PublicSafety": "治安維持委員会",
}


def sanitize_filename(s: str) -> str:
    # 移除文件系统特殊字符
    s = re.sub(r'[\\/:*?"<>|]', "_", s)
    return s.strip().replace(" ", "_")[:120] or "untitled"


def load_manifest() -> dict:
    with (ROOT / "utils" / "manifest.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def write_stats(dir_path: Path, stats: dict) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    with (dir_path / "_stats.json").open("w", encoding="utf-8") as fh:
        json.dump(stats, fh, ensure_ascii=False, indent=2)


def log_error(dir_path: Path, msg: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    with (dir_path / "_errors.log").open("a", encoding="utf-8") as fh:
        fh.write(msg + "\n")


def extract_title_from_parsed(parsed: dict) -> str:
    for line in parsed.get("lines", []):
        if line["type"] == "title":
            return line["text"].split(";", 1)[-1].strip() or line["text"].strip()
    return ""


# ─────────────────────────────────────────── Main Story ────────────────────────────────────

def gen_main_story(manifest: dict) -> dict:
    base = OUT_DIR / "主線"
    base.mkdir(parents=True, exist_ok=True)

    # 组织：Volume → Chapter → Episode list
    volumes: dict[int, dict[int, list]] = defaultdict(lambda: defaultdict(list))
    for key, entry in manifest["main_story"].items():
        v, c, e = entry["volume"], entry["chapter"], entry["episode"]
        volumes[v][c].append(entry)

    files = 0
    lines = 0
    errors = 0

    for v, chapters in sorted(volumes.items()):
        vol_title = VOLUME_TITLES_JP.get(v, f"第{v}篇")
        vol_dir = base / sanitize_filename(vol_title)
        for c, episodes in sorted(chapters.items()):
            chapter_dir = vol_dir / f"第{c}章"
            chapter_dir.mkdir(parents=True, exist_ok=True)
            for entry in sorted(episodes, key=lambda x: x["episode"]):
                gid = entry["group_id"]
                try:
                    parsed = parse_group(gid)
                    if not parsed["lines"]:
                        log_error(base, f"empty scenario vol{v}/ch{c}/ep{entry['episode']} gid={gid}")
                        errors += 1
                        continue
                    title = extract_title_from_parsed(parsed) or f"第{entry['episode']}話"
                    md = parsed_to_markdown(
                        parsed,
                        chapter=f"{vol_title} / 第{c}章 / 第{entry['episode']}話",
                        story_type="main_story",
                        extra_meta={"volume": v, "chapter": c, "episode": entry["episode"]},
                    )
                    fname = f"{entry['episode']:02d}話_{sanitize_filename(title)}.md"
                    (chapter_dir / fname).write_text(md, encoding="utf-8")
                    files += 1
                    lines += parsed["line_count"]
                except Exception as exc:  # noqa: BLE001
                    log_error(base, f"error vol{v}/ch{c}/ep{entry['episode']} gid={gid}: {exc}\n{traceback.format_exc()}")
                    errors += 1

    stats = {"type": "main_story", "files": files, "lines": lines, "errors": errors}
    write_stats(base, stats)
    return stats


# ─────────────────────────────────────────── Group Story ───────────────────────────────────

def gen_group_story(manifest: dict) -> dict:
    base = OUT_DIR / "グループストーリー"
    base.mkdir(parents=True, exist_ok=True)

    files = 0
    lines = 0
    errors = 0

    for bucket, entries in manifest["group_story"].items():
        bucket_dir = base / sanitize_filename(bucket)
        bucket_dir.mkdir(parents=True, exist_ok=True)
        for i, entry in enumerate(sorted(entries, key=lambda x: x.get("group_id", 0))):
            gid = entry["group_id"]
            try:
                parsed = parse_group(gid)
                if not parsed["lines"]:
                    log_error(base, f"empty {bucket} gid={gid}")
                    errors += 1
                    continue
                title = extract_title_from_parsed(parsed) or f"Episode_{i+1}"
                md = parsed_to_markdown(
                    parsed,
                    chapter=bucket,
                    story_type="group_story",
                    extra_meta=entry,
                )
                fname = f"{i+1:02d}話_{sanitize_filename(title)}.md"
                (bucket_dir / fname).write_text(md, encoding="utf-8")
                files += 1
                lines += parsed["line_count"]
            except Exception as exc:  # noqa: BLE001
                log_error(base, f"error {bucket} gid={gid}: {exc}")
                errors += 1

    stats = {"type": "group_story", "files": files, "lines": lines, "errors": errors}
    write_stats(base, stats)
    return stats


# ─────────────────────────────────────────── Event Story ───────────────────────────────────

def gen_event_story(manifest: dict) -> dict:
    base = OUT_DIR / "イベント"
    base.mkdir(parents=True, exist_ok=True)

    files = 0
    lines = 0
    errors = 0

    for event_key, entries in manifest["event_story"].items():
        event_dir = base / sanitize_filename(event_key)
        event_dir.mkdir(parents=True, exist_ok=True)
        for i, entry in enumerate(entries):
            gid = entry["group_id"]
            try:
                parsed = parse_group(gid)
                if not parsed["lines"]:
                    continue  # 空场景不记 error
                title = extract_title_from_parsed(parsed) or f"Scene_{entry.get('order', i+1)}"
                suffix = ""
                if entry.get("is_recollection"):
                    suffix = "_rec"
                md = parsed_to_markdown(
                    parsed,
                    chapter=event_key,
                    story_type="event_story",
                    extra_meta=entry,
                )
                fname = f"{(entry.get('order') or i+1):03d}{suffix}_{sanitize_filename(title)}.md"
                (event_dir / fname).write_text(md, encoding="utf-8")
                files += 1
                lines += parsed["line_count"]
            except Exception as exc:  # noqa: BLE001
                log_error(base, f"error {event_key} gid={gid}: {exc}")
                errors += 1

    stats = {"type": "event_story", "files": files, "lines": lines, "errors": errors,
             "events_count": len(manifest["event_story"])}
    write_stats(base, stats)
    return stats


# ─────────────────────────────────────────── Bond Story ────────────────────────────────────

def gen_bond_story(manifest: dict) -> dict:
    base = OUT_DIR / "絆ストーリー"
    base.mkdir(parents=True, exist_ok=True)

    files = 0
    lines = 0
    errors = 0

    for cid_str, entries in manifest["bond_story"].items():
        cid = int(cid_str)
        char_name = character_id_to_name(cid)
        char_dir = base / sanitize_filename(char_name)
        char_dir.mkdir(parents=True, exist_ok=True)

        # 每个 gid 一个文件；同时汇总成一个 _all.md
        all_sections: list[str] = [f"# {char_name} — 絆ストーリー\n"]

        for entry in sorted(entries, key=lambda x: x["group_id"]):
            gid = entry["group_id"]
            try:
                parsed = parse_group(gid)
                if not parsed["lines"]:
                    continue
                title = extract_title_from_parsed(parsed) or f"ep{entry.get('episode_hint')}"
                md = parsed_to_markdown(
                    parsed,
                    chapter=f"{char_name} 絆ストーリー",
                    story_type="bond_story",
                    extra_meta={"character_id": cid, "episode_hint": entry.get("episode_hint")},
                )
                fname = f"{entry.get('episode_hint', 0):02d}_{sanitize_filename(title)}.md"
                (char_dir / fname).write_text(md, encoding="utf-8")
                files += 1
                lines += parsed["line_count"]
                all_sections.append(f"\n## {title}\n")
                # 抽取 body（跳过 frontmatter + H1）
                body = md.split("\n", 1)[1] if md.startswith("---") else md
                all_sections.append(body)
            except Exception as exc:  # noqa: BLE001
                log_error(base, f"error cid={cid} gid={gid}: {exc}")
                errors += 1

    stats = {"type": "bond_story", "files": files, "lines": lines, "errors": errors,
             "characters_count": len(manifest["bond_story"])}
    write_stats(base, stats)
    return stats


# ─────────────────────────────────────────── Mini Story ────────────────────────────────────

def gen_mini_story(manifest: dict) -> dict:
    base = OUT_DIR / "ミニストーリー"
    base.mkdir(parents=True, exist_ok=True)

    files = 0
    lines = 0
    errors = 0

    for entry in manifest["mini_story"]:
        gid = entry["group_id"]
        try:
            parsed = parse_group(gid)
            if not parsed["lines"]:
                continue
            title = extract_title_from_parsed(parsed) or f"Mini_{gid}"
            md = parsed_to_markdown(
                parsed,
                chapter="ミニストーリー",
                story_type="mini_story",
                extra_meta=entry,
            )
            fname = f"{gid}_{sanitize_filename(title)}.md"
            (base / fname).write_text(md, encoding="utf-8")
            files += 1
            lines += parsed["line_count"]
        except Exception as exc:  # noqa: BLE001
            log_error(base, f"error mini gid={gid}: {exc}")
            errors += 1

    stats = {"type": "mini_story", "files": files, "lines": lines, "errors": errors}
    write_stats(base, stats)
    return stats


# ─────────────────────────────────────────── MomoTalk ──────────────────────────────────────

def gen_momotalk(manifest: dict) -> dict:
    base = OUT_DIR / "モモトーク"
    base.mkdir(parents=True, exist_ok=True)

    files = 0
    lines = 0
    errors = 0

    mt_map = momotalk_groups_by_character()
    for cid in sorted(manifest["momotalk_characters"]):
        messages = mt_map.get(cid, [])
        if not messages:
            continue
        try:
            name = character_id_to_name(cid)
            md = momotalk_to_markdown(name, messages)
            fname = f"{cid}_{sanitize_filename(name)}.md"
            (base / fname).write_text(md, encoding="utf-8")
            files += 1
            lines += len(messages)
        except Exception as exc:  # noqa: BLE001
            log_error(base, f"error momotalk cid={cid}: {exc}")
            errors += 1

    stats = {"type": "momotalk", "files": files, "messages": lines, "errors": errors}
    write_stats(base, stats)
    return stats


# ─────────────────────────────────────────── Character Data ────────────────────────────────

def gen_character_data(manifest: dict) -> dict:
    base = OUT_DIR / "キャラクターデータ"
    base.mkdir(parents=True, exist_ok=True)

    files = 0
    errors = 0

    for cid in sorted(manifest["profile_characters"]):
        try:
            md = character_profile_markdown(cid)
            name = character_id_to_name(cid)
            fname = f"{cid}_{sanitize_filename(name)}.md"
            (base / fname).write_text(md, encoding="utf-8")
            files += 1
        except Exception as exc:  # noqa: BLE001
            log_error(base, f"error profile cid={cid}: {exc}")
            errors += 1

    # Favor items 汇总
    try:
        md = favor_items_markdown()
        (base / "_favor_items.md").write_text(md, encoding="utf-8")
        files += 1
    except Exception as exc:  # noqa: BLE001
        log_error(base, f"error favor items: {exc}")
        errors += 1

    stats = {"type": "character_data", "files": files, "errors": errors}
    write_stats(base, stats)
    return stats


# ─────────────────────────────────────────── Dispatcher ────────────────────────────────────

def main() -> None:
    only = set(sys.argv[1:])
    manifest = load_manifest()
    all_stats = {}

    tasks = [
        ("main", gen_main_story),
        ("group", gen_group_story),
        ("event", gen_event_story),
        ("bond", gen_bond_story),
        ("mini", gen_mini_story),
        ("momotalk", gen_momotalk),
        ("character", gen_character_data),
    ]

    for key, fn in tasks:
        if only and key not in only:
            continue
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running {key}...")
        try:
            s = fn(manifest)
            print(f"  → {s}")
            all_stats[key] = s
        except Exception as exc:  # noqa: BLE001
            print(f"  !!! FAILED: {exc}")
            traceback.print_exc()
            all_stats[key] = {"error": str(exc)}

    print("\nOverall stats:")
    print(json.dumps(all_stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
