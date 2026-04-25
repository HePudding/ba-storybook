"""Generate 翻訳対照表.md — human-readable Markdown version of translation_table.json."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTILS = ROOT / 'utils'


def _src_badge(src):
    return {
        'game_data_tw': '📗',     # 游戏数据 (global branch Tw)
        'moegirl': '📘',           # 萌娘百科
        'gamekee': '📙',           # GameKee
        'bilibili_wiki': '📙',
        'not_found': '❓',
    }.get(src, '·')


def main():
    table = json.loads((UTILS / 'translation_table.json').read_text(encoding='utf-8'))
    cov = json.loads((UTILS / 'translation_coverage.json').read_text(encoding='utf-8'))

    out = []
    out.append('# 蔚蓝档案 日→中 翻訳対照表\n')
    out.append('## 数据来源\n')
    out.append('| 徽標 | 来源 | 优先级 |')
    out.append('|------|------|--------|')
    out.append('| 📗 | 国际服游戏数据（electricgoat/ba-data @ global 分支的 Tw 字段，繁体中文） | 1 |')
    out.append('| 📘 | 萌娘百科 `zh.moegirl.org.cn`（社区维护，简体中文） | 2 |')
    out.append('| 📙 | GameKee `ba.gamekee.com` / B站 wiki / bluearchive.cn（国服官方简中） | 3 |')
    out.append('| ❓ | 未找到（不编造，交后续人工确认） | — |\n')

    out.append('## 覆盖率\n')
    out.append('| 类别 | 总数 | 已翻译 | 未找到 | 覆盖率 | 来源分布 |')
    out.append('|------|------|--------|--------|--------|----------|')
    for cat, s in cov.items():
        by = s['by_source']
        src_str = ', '.join(f'{k}:{v}' for k, v in by.items() if v)
        out.append(f'| {cat} | {s["total"]} | {s["translated"]} | {s["not_found"]} | {s["coverage"]} | {src_str} |')
    out.append('')

    # Characters
    out.append('## 角色（Characters）\n')
    out.append('| JP | CN | 全名 (JP) | 全名 (CN) | 学校 | 社团 | 来源 |')
    out.append('|----|----|-----------|-----------|------|------|------|')
    for jp, e in sorted(table['characters'].items()):
        out.append(f'| {jp} | {e.get("cn","")} | {e.get("jp_full","")} | {e.get("cn_full","")} | {e.get("school","")} | {e.get("club","")} | {_src_badge(e.get("source"))} |')
    out.append('')

    # Character variants
    out.append('## 角色变体（Variants）\n')
    out.append('| 本体 JP | 本体 CN | 变体 JP | 变体 CN | 来源 |')
    out.append('|---------|---------|---------|---------|------|')
    for jp, e in sorted(table['characters'].items()):
        for vjp, v in (e.get('variants') or {}).items():
            out.append(f'| {jp} | {e.get("cn","")} | {vjp} | {v.get("cn","")} | {_src_badge(v.get("source"))} |')
    out.append('')

    # Schools
    out.append('## 学校（Schools）\n')
    out.append('| JP (full) | JP (short) | CN | CN (full) | 英文代码 | 来源 |')
    out.append('|-----------|-------------|------|-----------|----------|------|')
    for jp, e in sorted(table['schools'].items()):
        out.append(f'| {jp} | {e.get("jp_short","")} | {e.get("cn","")} | {e.get("cn_full","")} | {e.get("code","")} | {_src_badge(e.get("source"))} |')
    out.append('')

    # Clubs
    out.append('## 社团（Clubs）\n')
    out.append('| JP | CN | 英文代码 | 来源 |')
    out.append('|----|----|---------|------|')
    for jp, e in sorted(table['clubs'].items()):
        out.append(f'| {jp} | {e.get("cn","")} | {e.get("code","")} | {_src_badge(e.get("source"))} |')
    out.append('')

    # Story titles
    out.append('## 剧情标题（Story Titles）\n')
    out.append('| JP | CN | 类别 | 来源 |')
    out.append('|----|----|------|------|')
    for jp, e in sorted(table['story_titles'].items()):
        out.append(f'| {jp} | {e.get("cn","")} | {e.get("category","")} | {_src_badge(e.get("source"))} |')
    out.append('')

    # Events
    out.append('## 活动（Events）\n')
    out.append('| Event Dir | JP | CN | 备注 | 来源 |')
    out.append('|-----------|----|----|------|------|')
    for eid, e in sorted(table['events'].items()):
        out.append(f'| {eid} | {e.get("jp","")} | {e.get("cn","")} | {e.get("note","")} | {_src_badge(e.get("source"))} |')
    out.append('')

    # Favor items (abridged — first 20)
    out.append('## 爱用品（Favor Items） — 前 20 条\n')
    out.append('| JP | CN | 来源 |')
    out.append('|----|----|------|')
    for jp, e in list(table['favor_items'].items())[:20]:
        out.append(f'| {jp} | {e.get("cn","")} | {_src_badge(e.get("source"))} |')
    out.append(f'\n（共 {len(table["favor_items"])} 条，其余见 `translation_table.json`）\n')

    # Locations (abridged)
    out.append('## 地名（Locations） — 前 20 条\n')
    out.append('| JP | CN | 来源 |')
    out.append('|----|----|------|')
    for jp, e in list(table['locations'].items())[:20]:
        out.append(f'| {jp} | {e.get("cn","")} | {_src_badge(e.get("source"))} |')
    out.append(f'\n（共 {len(table["locations"])} 条，其余见 `translation_table.json`）\n')

    # Terms
    out.append('## 术语（Terms）\n')
    out.append('| JP | CN | 来源 |')
    out.append('|----|----|------|')
    for jp, e in table['terms'].items():
        out.append(f'| {jp} | {e.get("cn","")} | {_src_badge(e.get("source"))} |')
    out.append('')

    # Scenario characters (abridged)
    sc = table['scenario_characters']
    out.append(f'## 剧情角色 NPC（Scenario Characters） — 前 40 条\n')
    out.append('| JP | Nickname JP | CN | Nickname CN | 来源 |')
    out.append('|----|-------------|----|-------------|------|')
    for k, e in list(sc.items())[:40]:
        out.append(f'| {e.get("jp","")} | {e.get("nickname_jp","")} | {e.get("cn","")} | {e.get("nickname_cn","")} | {_src_badge(e.get("source"))} |')
    out.append(f'\n（共 {len(sc)} 条，其余见 `translation_table.json`）\n')

    (ROOT / '翻译对照表.md').write_text('\n'.join(out), encoding='utf-8')
    print(f'wrote {ROOT / "翻译对照表.md"} ({sum(len(l) for l in out)} chars)')


if __name__ == '__main__':
    main()
