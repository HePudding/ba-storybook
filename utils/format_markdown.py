"""结构化对话流 → Markdown 文本（带 YAML frontmatter）."""
from __future__ import annotations

import re
from typing import Iterable


def _yaml_escape(s: str) -> str:
    s = (s or "").replace('"', '\\"').replace("\n", " ")
    return f'"{s}"'


def _clean_text(s: str) -> str:
    """清理游戏文本中的内嵌指令，保留可读内容."""
    if not s:
        return ""
    # #n → 换行
    s = s.replace("#n", "\n")
    # [ruby=かな]漢字[/ruby] → 漢字（かな）— 保留可读
    s = re.sub(r"\[ruby=([^\]]+)\]([^\[]+)\[/ruby\]", r"\2（\1）", s)
    # 颜色/样式标签 [FF6666] ... [-] → 去除
    s = re.sub(r"\[-\]", "", s)
    s = re.sub(r"\[[0-9A-Fa-f]{6}\]", "", s)
    # 多余空白
    s = s.strip()
    return s


def parsed_to_markdown(
    parsed: dict,
    *,
    title: str | None = None,
    chapter: str | None = None,
    story_type: str | None = None,
    extra_meta: dict | None = None,
) -> str:
    """
    把 parse_dialogue.parse_group() 的产出转换成 Markdown.

    Args:
        parsed: {group_id, lines:[{type,...}], characters:[...]} 结构
        title: 显式指定标题（覆盖从 lines 里抽取的 title 行）
        chapter: 所属章节/篇（仅写入 frontmatter）
        story_type: main_story / group_story / event / momotalk / bond / mini
        extra_meta: 额外写入 frontmatter 的字段（如 volume, episode）
    """
    lines = parsed.get("lines", [])
    group_id = parsed.get("group_id")
    characters = parsed.get("characters", [])

    # 从 lines 抽取 title 作为 fallback
    auto_title = ""
    for line in lines:
        if line["type"] == "title":
            auto_title = _clean_text(line["text"])
            break

    effective_title = title or auto_title or f"Group_{group_id}"

    meta = {
        "title": _yaml_escape(effective_title),
        "group_id": str(group_id),
    }
    if chapter:
        meta["chapter"] = _yaml_escape(chapter)
    if story_type:
        meta["type"] = story_type
    meta["characters"] = (
        "[" + ", ".join(_yaml_escape(c) for c in characters) + "]"
    )
    if extra_meta:
        for k, v in extra_meta.items():
            meta[k] = _yaml_escape(str(v)) if not isinstance(v, (int, float, bool)) else str(v)

    out: list[str] = ["---"]
    for k, v in meta.items():
        out.append(f"{k}: {v}")
    out.append("---")
    out.append("")
    out.append(f"# {effective_title}")
    out.append("")

    for line in lines:
        t = line["type"]
        if t == "title":
            # 已用作 H1，body 重复展示不必要；跳过
            continue
        if t == "place":
            place = _clean_text(line["text"])
            if place:
                out.append(f"**【{place}】**")
                out.append("")
        elif t == "dialogue":
            speaker = line.get("speaker") or ""
            text = _clean_text(line.get("text", ""))
            if not text:
                continue
            if speaker:
                out.append(f"**{speaker}**: {text}")
            else:
                out.append(f"**？？？**: {text}")
            out.append("")
        elif t == "narration":
            speaker = line.get("speaker") or ""
            text = _clean_text(line.get("text", ""))
            if not text:
                continue
            if speaker:
                out.append(f"*（{speaker}）{text}*")
            else:
                out.append(f"*{text}*")
            out.append("")
        elif t == "choice_group":
            opts = [_clean_text(o) for o in line.get("options", [])]
            opts = [o for o in opts if o]
            if not opts:
                continue
            out.append("> **先生（選択肢）**: " + " / ".join(opts))
            out.append("")
        elif t == "choice":  # 兜底，理论已合并
            txt = _clean_text(line.get("text", ""))
            if txt:
                out.append(f"> **先生**: {txt}")
                out.append("")

    return "\n".join(out).rstrip() + "\n"


def momotalk_to_markdown(character_name_jp: str, messages: Iterable[dict]) -> str:
    """MomoTalk 专用：角色-先生即时对话流渲染."""
    out: list[str] = [
        "---",
        f'title: "MomoTalk - {character_name_jp}"',
        f"character: {_yaml_escape(character_name_jp)}",
        "type: momotalk",
        "---",
        "",
        f"# MomoTalk - {character_name_jp}",
        "",
    ]

    msgs = list(messages)
    if not msgs:
        out.append("*（MomoTalk データ未収録）*\n")
        return "\n".join(out)

    last_group = None
    last_condition_value = None
    for m in msgs:
        group = m.get("MessageGroupId")
        cond = m.get("MessageCondition", "")
        cond_val = m.get("ConditionValue", 0)
        if group != last_group:
            # group 变更：加分隔
            if last_group is not None:
                out.append("---")
                out.append("")
            if cond == "FavorRankUp" and cond_val:
                out.append(f"## 好感度ランク {cond_val} 解放")
            elif cond and cond != "None":
                out.append(f"## {cond} ({cond_val})")
            else:
                out.append(f"## Group {group}")
            out.append("")
            last_group = group
            last_condition_value = cond_val

        msg_type = m.get("MessageType", "Text")
        text = _clean_text(m.get("MessageJP", ""))
        cid = m.get("CharacterId")
        if msg_type == "Image":
            img = m.get("ImagePath", "")
            out.append(f"**{character_name_jp}**: *（画像: {img or 'image'}）*")
        elif msg_type == "Sticker":
            out.append(f"**{character_name_jp}**: *（スタンプ）*")
        else:
            # Text
            if cond == "Choice":
                out.append(f"> **先生**: {text}")
            elif text:
                out.append(f"**{character_name_jp}**: {text}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"
