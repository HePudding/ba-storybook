"""枚举所有 GroupId 并按类型分组写入 manifest.json.

manifest 结构:
{
  "main_story": {
    "1_1_1": {"group_id": 11010, "volume": 1, "chapter": 1, "episode": 1},
    ...
  },
  "group_story": { "<club_key>": [ {group_id, order}, ... ], ... },
  "event_story": { "<event_id>": [ {group_id, order, is_recollection}, ... ], ... },
  "bond_story": { "<character_id>": [ {group_id, episode_hint}, ... ], ... },
  "mini_story": [ ... ],
  "momotalk_characters": [ ... ],
  "profile_characters": [ ... ],
  "misc_groups": [ ... ]
}
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .load_data import (
    ROOT,
    build_script_index,
    character_id_from_favor_group,
    load_character_meta,
    load_character_id_to_jp_name,
    load_event_scenario_index,
    load_scenario_mode_index,
    momotalk_groups_by_character,
)


def build_manifest() -> dict:
    mode_idx = load_scenario_mode_index()
    event_idx = load_event_scenario_index()
    script_idx = build_script_index()

    manifest: dict = {
        "main_story": {},       # key "V_C_E" -> {group_id, volume, chapter, episode, mode_id}
        "group_story": {},      # "club_<x>" -> [groups]
        "event_story": {},      # "event_<id>" -> [{group_id, order}]
        "bond_story": {},       # str(character_id) -> [{group_id, ...}]
        "mini_story": [],       # [{group_id, volume, chapter, episode}]
        "momotalk_characters": [],
        "profile_characters": [],
        "misc_groups": [],
    }

    # Main / Sub(Club) / Mini — 全部来自 ScenarioMode
    classified_by_mode: set[int] = set()
    for gid, meta in mode_idx.items():
        if meta.get("position") != "front":
            continue  # back scenarios 作为同一 episode 的后续，归到 main_story 的元数据扩展
        mt = meta["mode_type"]
        st = meta["sub_type"]
        v, c, e = meta["volume_id"], meta["chapter_id"], meta["episode_id"]
        entry = {
            "group_id": gid,
            "mode_id": meta["mode_id"],
            "volume": v,
            "chapter": c,
            "episode": e,
        }
        if mt == "Main" and st == "None":
            manifest["main_story"][f"{v}_{c}_{e}"] = entry
            classified_by_mode.add(gid)
        elif mt == "Mini":
            manifest["mini_story"].append(entry)
            classified_by_mode.add(gid)
        elif st == "Club":
            bucket = f"club_{v}_{c}"
            manifest["group_story"].setdefault(bucket, []).append(entry)
            classified_by_mode.add(gid)
        else:
            manifest["misc_groups"].append(entry)

    # Events
    event_buckets: dict[int, list[dict]] = defaultdict(list)
    for gid, meta in event_idx.items():
        event_buckets[meta["event_content_id"]].append({
            "group_id": gid,
            "order": meta["order"],
            "is_recollection": meta["is_recollection"],
            "is_omnibus": meta["is_omnibus"],
            "scenario_id": meta["scenario_id"],
        })
    for eid, arr in event_buckets.items():
        arr.sort(key=lambda x: x["order"])
        manifest["event_story"][f"event_{eid}"] = arr

    # Bond (Favor) — by source file
    bond_map: dict[int, list[dict]] = defaultdict(list)
    for gid, (fname, _) in script_idx.items():
        if "Favor" not in fname:
            continue
        # GroupId 格式: CharacterId * 100 + episode; 但 Favor 文件里有些 gid 是 CharacterId*10 或其它
        # 保守做法：后2位 = episode, 前面 = character ref
        cid = character_id_from_favor_group(gid)
        bond_map[cid].append({"group_id": gid, "episode_hint": gid % 100})
    for cid, arr in bond_map.items():
        arr.sort(key=lambda x: x["group_id"])
        manifest["bond_story"][str(cid)] = arr

    # MomoTalk
    momotalk = momotalk_groups_by_character()
    manifest["momotalk_characters"] = sorted(momotalk.keys())

    # Profile characters — 用 LocalizeCharProfile 作为权威列表
    manifest["profile_characters"] = sorted(load_character_id_to_jp_name().keys())

    # Group script misc: GroupId from ScenarioScriptGroup* not tagged by Mode
    for gid, (fname, _) in script_idx.items():
        if "Group" not in fname or gid in classified_by_mode:
            continue
        bucket = f"group_script_{fname.replace('ScenarioScriptGroup', '').replace('ExcelTable.json', '')}"
        manifest["group_story"].setdefault(bucket, []).append({"group_id": gid})

    # Main script misc (未在 ScenarioMode 中的 main script groups)
    for gid, (fname, _) in script_idx.items():
        if "Main" in fname and gid not in classified_by_mode:
            manifest["misc_groups"].append({"group_id": gid, "source_file": fname, "note": "main_script_not_in_ScenarioMode"})

    return manifest


def main() -> None:
    m = build_manifest()
    out_path = ROOT / "utils" / "manifest.json"
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(m, fh, ensure_ascii=False, indent=2)

    # 简要统计
    stats = {
        "main_story_episodes": len(m["main_story"]),
        "group_story_buckets": len(m["group_story"]),
        "group_story_total": sum(len(v) for v in m["group_story"].values()),
        "event_story_events": len(m["event_story"]),
        "event_story_total": sum(len(v) for v in m["event_story"].values()),
        "bond_story_characters": len(m["bond_story"]),
        "bond_story_total": sum(len(v) for v in m["bond_story"].values()),
        "mini_story": len(m["mini_story"]),
        "momotalk_characters": len(m["momotalk_characters"]),
        "profile_characters": len(m["profile_characters"]),
        "misc_groups": len(m["misc_groups"]),
    }
    print(json.dumps(stats, indent=2))
    print(f"\nManifest written to: {out_path}")


if __name__ == "__main__":
    main()
