"""将 GroupId 对应的 ScenarioScript 原始行流 → 结构化对话流.

策略：
- TextJp 是净化过的日文（无 directive），用于实际文本
- ScriptKr 的 **第一行** 揭示说话人/类型（#na, #stm, #st, #place, #title, [s], 或者 "pos;speaker;emotion"）
- TextJp 为空 && ScriptKr 只是控制指令 (#wait/#hidemenu/#clearst) → 跳过
"""
from __future__ import annotations

import re
from typing import Any

from .load_data import (
    character_id_from_favor_group,
    classify_group,
    get_script_rows,
    kr_name_to_jp,
    load_event_scenario_index,
    load_scenario_mode_index,
)

# ScriptKr 的第一行 pattern
RE_DIALOGUE_HEAD = re.compile(r"^\s*(\d+)\s*;\s*([^;]+?)\s*;\s*([^\n;]*)\s*(?:;\s*(.*))?$")
RE_NA = re.compile(r"^#na\s*;\s*([^;\n]*)\s*;\s*(.*)$", re.DOTALL)
RE_ST_OR_STM = re.compile(r"^#st(m)?\s*;[^;]*;[^;]*;[^;]*;(.*)$", re.DOTALL)
RE_PLACE = re.compile(r"^#place\s*;\s*(.*)$", re.DOTALL)
RE_TITLE = re.compile(r"^#title\s*;\s*(.*)$", re.DOTALL)
RE_SELECTION = re.compile(r"^\s*\[s\]\s*(.*)$", re.DOTALL)


def _first_line(s: str) -> str:
    return (s or "").split("\n", 1)[0]


def _classify_row(row: dict) -> dict[str, Any] | None:
    """单行 → 结构化对象，跳过纯指令返回 None."""
    script_kr = row.get("ScriptKr", "") or ""
    text_jp = (row.get("TextJp", "") or "").strip()
    voice_jp = row.get("VoiceJp", "") or ""

    first = _first_line(script_kr).strip()

    # Selection option (player choice)
    m = RE_SELECTION.match(first)
    if m:
        # TextJp 也会有 "[s] text" 前缀，去掉
        choice_text = text_jp
        m2 = RE_SELECTION.match(choice_text)
        if m2:
            choice_text = m2.group(1).strip()
        if not choice_text:
            return None
        return {"type": "choice", "text": choice_text, "selection_group": row.get("SelectionGroup", 0)}

    # Title banner
    m = RE_TITLE.match(first)
    if m:
        t = text_jp or m.group(1).strip()
        return {"type": "title", "text": t} if t else None

    # Place label
    m = RE_PLACE.match(first)
    if m:
        t = text_jp or m.group(1).strip()
        return {"type": "place", "text": t} if t else None

    # Narration with speaker: #na;<speaker_kr>;<text>
    m = RE_NA.match(first)
    if m:
        speaker_kr = m.group(1).strip()
        speaker_jp = kr_name_to_jp(speaker_kr) if speaker_kr and speaker_kr != "???" else ""
        if speaker_kr == "???":
            speaker_jp = "？？？"
        if not text_jp:
            return None
        return {"type": "narration", "speaker": speaker_jp, "text": text_jp, "voice": voice_jp}

    # Scroll narration: #stm;[...]; / #st;[...];
    m = RE_ST_OR_STM.match(first)
    if m:
        if not text_jp:
            return None
        return {"type": "narration", "speaker": "", "text": text_jp, "voice": voice_jp}

    # Character dialogue: "pos;speaker;emotion[;text]"
    m = RE_DIALOGUE_HEAD.match(first)
    if m:
        speaker_kr = m.group(2).strip()
        # 跳过控制代码（如 "3;h" 表示 hide）
        if not speaker_kr or speaker_kr in ("h", "a", "em", "greeting"):
            pass
        else:
            speaker_jp = kr_name_to_jp(speaker_kr)
            if not text_jp:
                # 只有位置/表情变化，无实际台词
                return None
            return {
                "type": "dialogue",
                "speaker": speaker_jp,
                "text": text_jp,
                "voice": voice_jp,
                "selection_group": row.get("SelectionGroup", 0),
            }

    # 无法分类：若 TextJp 非空，作为旁白降级
    if text_jp:
        return {"type": "narration", "speaker": "", "text": text_jp, "voice": voice_jp}

    return None


def parse_group(group_id: int) -> dict:
    """读取某 GroupId 全部脚本行并返回结构化对象.

    Returns:
        {
            "group_id": int,
            "line_count": int,
            "lines": [ {type, ...}, ... ],
            "characters": [jp_name, ...]  # 去重
        }
    """
    rows = get_script_rows(group_id)
    lines: list[dict] = []
    characters: list[str] = []
    for row in rows:
        obj = _classify_row(row)
        if obj is None:
            continue
        lines.append(obj)
        if obj.get("type") == "dialogue" and obj.get("speaker"):
            sp = obj["speaker"]
            if sp and sp not in characters:
                characters.append(sp)

    # 合并连续的 choice 为 choice_group
    merged: list[dict] = []
    buf_choices: list[str] = []
    for obj in lines:
        if obj["type"] == "choice":
            buf_choices.append(obj["text"])
            continue
        if buf_choices:
            merged.append({"type": "choice_group", "options": buf_choices})
            buf_choices = []
        merged.append(obj)
    if buf_choices:
        merged.append({"type": "choice_group", "options": buf_choices})

    return {
        "group_id": group_id,
        "line_count": len(merged),
        "lines": merged,
        "characters": characters,
    }


if __name__ == "__main__":
    import sys, json
    gid = int(sys.argv[1]) if len(sys.argv) > 1 else 11010
    result = parse_group(gid)
    print(json.dumps(result, ensure_ascii=False, indent=2)[:3000])
