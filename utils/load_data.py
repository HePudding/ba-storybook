"""数据加载层：JSON / 角色名 / 章节元数据，支持按 GroupId 索引和懒加载。

所有路径基于 `ba-story/` 根目录相对定位。表字段从 field_mapping.json 读取。
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
JSON_DIR = ROOT / "ba-json"
UTILS_DIR = ROOT / "utils"

SCRIPT_FILES: tuple[str, ...] = (
    "ScenarioScriptMain1ExcelTable.json",
    "ScenarioScriptMain2ExcelTable.json",
    "ScenarioScriptMain3ExcelTable.json",
    "ScenarioScriptMain4ExcelTable.json",
    "ScenarioScriptMain5ExcelTable.json",
    "ScenarioScriptGroup1ExcelTable.json",
    "ScenarioScriptGroup2ExcelTable.json",
    "ScenarioScriptGroup3ExcelTable.json",
    "ScenarioScriptGroup4ExcelTable.json",
    "ScenarioScriptGroup5ExcelTable.json",
    "ScenarioScriptFavor1ExcelTable.json",
    "ScenarioScriptFavor2ExcelTable.json",
    "ScenarioScriptFavor3ExcelTable.json",
    "ScenarioScriptFavor4ExcelTable.json",
    "ScenarioScriptFavor5ExcelTable.json",
    "ScenarioScriptEvent1ExcelTable.json",
    "ScenarioScriptEvent2ExcelTable.json",
    "ScenarioScriptEvent3ExcelTable.json",
    "ScenarioScriptEvent4ExcelTable.json",
    "ScenarioScriptEvent5ExcelTable.json",
    "ScenarioScriptField1ExcelTable.json",
    "ScenarioScriptContentExcelTable.json",
)


@lru_cache(maxsize=1)
def load_field_mapping() -> dict:
    with (UTILS_DIR / "field_mapping.json").open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def load_group_rules() -> dict:
    with (UTILS_DIR / "group_rules.json").open(encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def load_table(name: str) -> list[dict]:
    """读取 JSON 表并返回 DataList。路径相对 ba-json/。"""
    path = JSON_DIR / name
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload.get("DataList", [])


@lru_cache(maxsize=1)
def build_script_index() -> dict[int, tuple[str, list[int]]]:
    """返回 {GroupId: (filename, row_indices)}。只存索引不存 row 数据。"""
    idx: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for fname in SCRIPT_FILES:
        fpath = JSON_DIR / fname
        if not fpath.exists():
            continue
        rows = load_table(fname)
        for i, row in enumerate(rows):
            gid = row.get("GroupId")
            if gid is not None:
                idx[gid].append((fname, i))
    # 压缩为 {gid: (fname, [indices...])}. 每个 gid 应只在一个 file 中
    collapsed: dict[int, tuple[str, list[int]]] = {}
    for gid, locs in idx.items():
        fnames = {f for f, _ in locs}
        # 如果同一 GroupId 出现在多个 file，按第一个（一般不会发生，记录警告在上层）
        fname = next(iter(fnames))
        collapsed[gid] = (fname, [i for _, i in locs if _ == fname])
    return collapsed


def get_script_rows(group_id: int) -> list[dict]:
    """返回某 GroupId 对应的所有原始行，按原文件顺序。"""
    index = build_script_index()
    if group_id not in index:
        return []
    fname, indices = index[group_id]
    rows = load_table(fname)
    return [rows[i] for i in indices]


@lru_cache(maxsize=1)
def load_character_names() -> dict[str, dict]:
    """Kr name → {name_jp, nickname_jp 列表}.

    Returns:
        { "아루": { "name_jp": "アル", "variants": [{"nickname_kr": "흥신소 68", "nickname_jp": "便利屋68"}, ...] } }
    """
    rows = load_table("ScenarioCharacterNameExcelTable.json")
    mapping: dict[str, dict] = {}
    for r in rows:
        name_kr = (r.get("NameKR") or "").strip()
        name_jp = (r.get("NameJP") or "").strip()
        if not name_kr:
            continue
        entry = mapping.setdefault(name_kr, {"name_jp": name_jp, "variants": []})
        if not entry["name_jp"] and name_jp:
            entry["name_jp"] = name_jp
        entry["variants"].append({
            "nickname_kr": r.get("NicknameKR") or "",
            "nickname_jp": r.get("NicknameJP") or "",
        })
    return mapping


@lru_cache(maxsize=1)
def _sorted_known_kr_names() -> list[str]:
    """按长度降序的已知 KR 名，用于子串匹配."""
    names = [n for n, v in load_character_names().items() if v.get("name_jp")]
    return sorted(names, key=len, reverse=True)


@lru_cache(maxsize=None)
def kr_name_to_jp(name_kr: str) -> str:
    """Korean speaker name → Japanese name. 未命中时尝试子串回退；仍失败返回 KR 原文."""
    name_kr = (name_kr or "").strip()
    if not name_kr:
        return ""
    mapping = load_character_names()
    if name_kr in mapping and mapping[name_kr]["name_jp"]:
        return mapping[name_kr]["name_jp"]
    # 子串回退：匹配任何已知长名称（如 "통신아로나" 包含 "아로나"）
    # 按长度降序避免短名误匹配
    for known in _sorted_known_kr_names():
        if len(known) >= 2 and known in name_kr:
            return mapping[known]["name_jp"]
    return name_kr  # fallback 保留 Korean 原文便于后续审查


@lru_cache(maxsize=1)
def load_character_id_to_jp_name() -> dict[int, str]:
    """CharacterId → FullNameJp (主要使用 LocalizeCharProfile)."""
    result: dict[int, str] = {}
    for r in load_table("LocalizeCharProfileExcelTable.json"):
        cid = r.get("CharacterId")
        name = r.get("PersonalNameJp") or r.get("FullNameJp") or ""
        if cid:
            result[cid] = name.strip()
    return result


def character_id_to_name(cid: int) -> str:
    mapping = load_character_id_to_jp_name()
    if cid in mapping and mapping[cid]:
        return mapping[cid]
    return f"NPC_{cid}"


@lru_cache(maxsize=1)
def load_scenario_mode_index() -> dict[int, dict]:
    """GroupId → {mode_type, sub_type, volume_id, chapter_id, episode_id, mode_id}.

    同一 GroupId 可能在 Front + Back 出现，保留第一个；Back 标记附加信息。
    """
    idx: dict[int, dict] = {}
    for r in load_table("ScenarioModeExcelTable.json"):
        base = {
            "mode_id": r.get("ModeId"),
            "mode_type": r.get("ModeType"),
            "sub_type": r.get("SubType"),
            "volume_id": r.get("VolumeId"),
            "chapter_id": r.get("ChapterId"),
            "episode_id": r.get("EpisodeId"),
        }
        for gid in r.get("FrontScenarioGroupId") or []:
            idx.setdefault(gid, {**base, "position": "front"})
        for gid in r.get("BackScenarioGroupId") or []:
            idx.setdefault(gid, {**base, "position": "back"})
    return idx


@lru_cache(maxsize=1)
def load_event_scenario_index() -> dict[int, dict]:
    """GroupId → {event_content_id, order, is_recollection}."""
    idx: dict[int, dict] = {}
    for r in load_table("EventContentScenarioExcelTable.json"):
        meta = {
            "event_content_id": r.get("EventContentId"),
            "order": r.get("Order"),
            "is_recollection": r.get("IsRecollection", False),
            "is_omnibus": r.get("IsOmnibus", False),
            "scenario_id": r.get("Id"),
        }
        for gid in r.get("ScenarioGroupId") or []:
            idx.setdefault(gid, meta)
    return idx


@lru_cache(maxsize=1)
def load_contents_scenario_index() -> dict[int, dict]:
    """GroupId → {scenario_content_type, localize_id, display_order}."""
    idx: dict[int, dict] = {}
    for r in load_table("ContentsScenarioExcelTable.json"):
        meta = {
            "content_type": r.get("ScenarioContentType"),
            "localize_id": r.get("LocalizeId"),
            "display_order": r.get("DisplayOrder"),
        }
        for gid in r.get("ScenarioGroupId") or []:
            idx.setdefault(gid, meta)
    return idx


@lru_cache(maxsize=1)
def load_localize_scenario() -> dict[int, str]:
    """Key → Jp text (LocalizeScenarioExcelTable)."""
    return {r["Key"]: r.get("Jp", "") for r in load_table("LocalizeScenarioExcelTable.json") if "Key" in r}


@lru_cache(maxsize=1)
def load_localize_etc() -> dict[int, dict]:
    """Key → {name_jp, description_jp}."""
    return {
        r["Key"]: {"name_jp": r.get("NameJp", ""), "description_jp": r.get("DescriptionJp", "")}
        for r in load_table("LocalizeEtcExcelTable.json") if "Key" in r
    }


@lru_cache(maxsize=1)
def load_character_meta() -> dict[int, dict]:
    """CharacterId → {school, club, dev_name, is_playable, scenario_character}."""
    result: dict[int, dict] = {}
    for r in load_table("CharacterExcelTable.json"):
        cid = r.get("Id")
        if not cid:
            continue
        result[cid] = {
            "school": r.get("School", ""),
            "club": r.get("Club", ""),
            "dev_name": r.get("DevName", ""),
            "is_playable": r.get("IsPlayableCharacter", False),
            "is_npc": r.get("IsNPC", False),
            "scenario_character": r.get("ScenarioCharacter", ""),
            "localize_etc_id": r.get("LocalizeEtcId"),
            "weapon_localize_id": r.get("WeaponLocalizeId"),
        }
    return result


def classify_group(group_id: int, source_file: str | None = None) -> str:
    """判定 GroupId 所属类型。返回 main_story / group_story / mini_story / event_story / bond_story / misc."""
    mode_info = load_scenario_mode_index().get(group_id)
    if mode_info:
        mt = mode_info["mode_type"]
        st = mode_info["sub_type"]
        if mt == "Main" and st == "None":
            return "main_story"
        if st == "Club" and mt == "Sub":
            return "group_story"
        if mt == "Mini":
            return "mini_story"
        if st == "Club" and mt == "Mini":
            return "mini_story"
    if group_id in load_event_scenario_index():
        return "event_story"
    # Fallback: file-based
    if source_file is None:
        source_file = build_script_index().get(group_id, ("", None))[0]
    name = source_file.lower()
    if "favor" in name:
        return "bond_story"
    if "group" in name:
        return "group_story"
    if "event" in name:
        return "event_story"
    if "main" in name:
        return "main_story"
    return "misc"


def character_id_from_favor_group(group_id: int) -> int:
    """bond story 的 GroupId = CharacterId*100 + EpisodeId"""
    return group_id // 100


def iter_all_group_ids() -> Iterable[int]:
    """所有已知的 scenario GroupId."""
    return build_script_index().keys()


def momotalk_groups_by_character() -> dict[int, list[dict]]:
    """CharacterId → 已排序的 MomoTalk 消息行列表 (全部 AcademyMessanger 表合并)."""
    result: dict[int, list[dict]] = defaultdict(list)
    for fname in ("AcademyMessanger1ExcelTable.json", "AcademyMessanger2ExcelTable.json",
                   "AcademyMessanger3ExcelTable.json", "AcademyMessangerExcelTable.json"):
        fpath = JSON_DIR / fname
        if not fpath.exists():
            continue
        for r in load_table(fname):
            cid = r.get("CharacterId")
            if cid:
                result[cid].append(r)
    # 按 MessageGroupId, Id 排序
    for cid in result:
        result[cid].sort(key=lambda r: (r.get("MessageGroupId", 0), r.get("Id", 0)))
    return result


if __name__ == "__main__":
    import sys
    # 烟雾测试
    print(f"Field mapping keys: {list(load_field_mapping().keys())[:5]}...")
    print(f"Script index size: {len(build_script_index())}")
    print(f"ScenarioMode index size: {len(load_scenario_mode_index())}")
    print(f"Event scenario index size: {len(load_event_scenario_index())}")
    print(f"Characters with profile: {len(load_character_id_to_jp_name())}")
    print(f"KR->JP names: {len(load_character_names())}")
    print(f"Sample char id 10000 name: {character_id_to_name(10000)}")
    print(f"Sample Kr->Jp 아루: {kr_name_to_jp('아루')}")
    print(f"Classify 11010: {classify_group(11010)}")
    print(f"Classify 1000002: {classify_group(1000002)}")
    print(f"Classify 10000005: {classify_group(10000005)}")
    mt = momotalk_groups_by_character()
    print(f"MomoTalk characters: {len(mt)}")
