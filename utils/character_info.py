"""角色非剧情文本聚合：Profile / 爱用品 / 大厅·战闘台词."""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from typing import Any

from .load_data import (
    character_id_to_name,
    load_character_meta,
    load_localize_etc,
    load_table,
)


@lru_cache(maxsize=1)
def load_profile_by_char() -> dict[int, dict]:
    """CharacterId → 全部 LocalizeCharProfile 字段."""
    return {r["CharacterId"]: r for r in load_table("LocalizeCharProfileExcelTable.json") if "CharacterId" in r}


@lru_cache(maxsize=1)
def load_dialogs_by_char() -> dict[int, list[dict]]:
    """CharacterId → CharacterDialog 行 (按 DialogCategory -> DisplayOrder 分组)."""
    result: dict[int, list[dict]] = defaultdict(list)
    for r in load_table("CharacterDialogExcelTable.json"):
        cid = r.get("CharacterId")
        if cid:
            result[cid].append(r)
    # 排序
    for cid in result:
        result[cid].sort(key=lambda r: (r.get("DialogCategory", ""), r.get("DisplayOrder", 0)))
    return result


@lru_cache(maxsize=1)
def load_favor_items() -> list[dict]:
    """全部 ItemCategory=Favor 的物品，已解析 name_jp / description_jp."""
    etc = load_localize_etc()
    items: list[dict] = []
    for r in load_table("ItemExcelTable.json"):
        if r.get("ItemCategory") != "Favor":
            continue
        loc = etc.get(r.get("LocalizeEtcId"), {})
        items.append({
            "item_id": r.get("Id"),
            "rarity": r.get("Rarity"),
            "name_jp": loc.get("name_jp", ""),
            "description_jp": loc.get("description_jp", ""),
            "tags": r.get("Tags", []),
        })
    return items


def character_profile_markdown(character_id: int) -> str:
    """为单个角色生成聚合 markdown."""
    name = character_id_to_name(character_id)
    profile = load_profile_by_char().get(character_id, {})
    meta = load_character_meta().get(character_id, {})
    dialogs = load_dialogs_by_char().get(character_id, [])

    out: list[str] = [
        "---",
        f'title: "{name}"',
        f"character_id: {character_id}",
        "type: character_profile",
        f"school: \"{meta.get('school', '') or '不明'}\"",
        f"club: \"{meta.get('club', '') or '不明'}\"",
        "---",
        "",
        f"# {name}",
        "",
    ]

    # プロフィール
    if profile:
        out.append("## プロフィール")
        out.append("")
        fields: list[tuple[str, Any]] = [
            ("フルネーム", profile.get("FullNameJp")),
            ("学校", meta.get("school")),
            ("部活", meta.get("club")),
            ("学年", profile.get("SchoolYearJp")),
            ("年齢", profile.get("CharacterAgeJp")),
            ("誕生日", profile.get("BirthdayJp")),
            ("身長", profile.get("CharHeightJp")),
            ("趣味", profile.get("HobbyJp")),
            ("ステータスメッセージ", profile.get("StatusMessageJp")),
            ("デザイナー", profile.get("DesignerNameJp")),
            ("イラストレーター", profile.get("IllustratorNameJp")),
            ("CV", profile.get("CharacterVoiceJp")),
        ]
        for label, value in fields:
            value = (value or "").strip() if isinstance(value, str) else value
            if value:
                out.append(f"- **{label}**: {value}")
        out.append("")

        # 自己紹介
        intro = (profile.get("ProfileIntroductionJp") or "").strip()
        if intro:
            out.append("### 自己紹介")
            out.append("")
            for para in intro.split("\n\n"):
                out.append(para.strip())
                out.append("")

        # 武器
        weap_name = (profile.get("WeaponNameJp") or "").strip()
        weap_desc = (profile.get("WeaponDescJp") or "").strip()
        if weap_name or weap_desc:
            out.append("### 武器")
            out.append("")
            if weap_name:
                out.append(f"- **名称**: {weap_name}")
            if weap_desc:
                out.append(f"- **説明**: {weap_desc}")
            out.append("")
    else:
        out.append("## プロフィール")
        out.append("")
        out.append("*（プロフィール情報未収録）*")
        out.append("")

    # 台詞（按类别分组）
    if dialogs:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for d in dialogs:
            grouped[d.get("DialogCategory", "その他")].append(d)

        out.append("## 台詞")
        out.append("")

        # 优先显示主要类别
        priority_cats = [
            "UILobby", "UILobby2", "UILobbySpecial", "Cafe",
            "CharacterGet", "UITitle", "UIMission",
            "UISchoolDungeon", "UIWeekDungeon",
            "UIWork", "UIAcademyLobby",
        ]
        seen_cats = set()
        for cat in priority_cats + sorted(grouped.keys()):
            if cat in seen_cats or cat not in grouped:
                continue
            seen_cats.add(cat)
            out.append(f"### {cat}")
            out.append("")
            for d in grouped[cat]:
                text = (d.get("LocalizeJP") or "").strip().replace("\n", " ")
                if not text:
                    continue
                cond = d.get("DialogCondition", "")
                favor = d.get("UnlockFavorRank", 0)
                suffix = ""
                if cond and cond != "Enter":
                    suffix = f" _({cond})_"
                if favor:
                    suffix += f" _(好感度 {favor} 解放)_"
                out.append(f"- {text}{suffix}")
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def favor_items_markdown() -> str:
    """全爱用品列表（一个文件，不按角色分）."""
    items = load_favor_items()
    out: list[str] = [
        "---",
        'title: "爱用品一覧"',
        "type: favor_items",
        "---",
        "",
        "# 愛用品一覧",
        "",
        f"*合計 {len(items)} 件*",
        "",
    ]
    for it in items:
        name = it.get("name_jp") or f"Item_{it['item_id']}"
        desc = it.get("description_jp", "").replace("\n", " ")
        tags = ", ".join(it.get("tags", []))
        out.append(f"## {name}  _({it.get('rarity', '')})_")
        out.append("")
        if desc:
            out.append(desc)
            out.append("")
        if tags:
            out.append(f"**Tags**: `{tags}`")
            out.append("")
    return "\n".join(out).rstrip() + "\n"


if __name__ == "__main__":
    import sys
    cid = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    print(character_profile_markdown(cid)[:3000])
