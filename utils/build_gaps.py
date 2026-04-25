"""Build translation_gaps.json from translation_table.json.

Collects all entries with source=="not_found" and groups by category.
These gaps feed the Phase 2 moegirl subagent.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UTILS = ROOT / 'utils'


def main():
    table = json.loads((UTILS / 'translation_table.json').read_text(encoding='utf-8'))

    gaps = {}

    # Schools
    gaps['schools'] = [
        {
            'jp_full': jp,
            'jp_short': v['jp_short'],
            'code': v['code'],
        }
        for jp, v in table['schools'].items()
        if v['source'] == 'not_found'
    ]

    # Clubs
    gaps['clubs'] = [
        {'jp': jp, 'code': v['code']}
        for jp, v in table['clubs'].items()
        if v['source'] == 'not_found'
    ]

    # Characters (base + variants)
    gaps['characters'] = []
    for jp, v in table['characters'].items():
        if v['source'] == 'not_found':
            gaps['characters'].append({
                'jp_short': jp,
                'jp_full': v['jp_full'],
                'dev_name': v['dev_name'],
                'character_id': v['character_id'],
                'is_variant': False,
            })
        for vjp, vv in (v.get('variants') or {}).items():
            if vv['source'] == 'not_found':
                gaps['characters'].append({
                    'jp_short': vjp,
                    'base_jp': jp,
                    'variant_jp': vv['variant_jp'],
                    'dev_name': vv['dev_name'],
                    'character_id': vv['character_id'],
                    'is_variant': True,
                })

    # Scenario characters (dialog NPCs)
    gaps['scenario_characters'] = [
        {'jp': v['jp'], 'nickname_jp': v['nickname_jp']}
        for k, v in table['scenario_characters'].items()
        if v['source'] == 'not_found'
    ]

    # Story titles
    gaps['story_titles'] = [
        {'jp': jp, 'category': v.get('category')}
        for jp, v in table['story_titles'].items()
        if v['source'] == 'not_found'
    ]

    # Events: game data gave us none, so pull event IDs from ba-stories/イベント/
    event_dir = ROOT / 'ba-stories' / 'イベント'
    if event_dir.exists():
        event_ids = sorted(
            p.name for p in event_dir.iterdir()
            if p.is_dir() and p.name.startswith('event_')
        )
        gaps['events'] = [{'event_dir': eid, 'event_id': eid.split('_', 1)[1]} for eid in event_ids]
    else:
        gaps['events'] = []

    # Favor items
    gaps['favor_items'] = [
        {'jp': jp, 'item_id': v['item_id']}
        for jp, v in table['favor_items'].items()
        if v['source'] == 'not_found'
    ]

    # Locations
    gaps['locations'] = [
        {'jp': jp}
        for jp, v in table['locations'].items()
        if v['source'] == 'not_found'
    ]

    # Terms
    gaps['terms'] = [
        {'jp': jp}
        for jp, v in table['terms'].items()
        if v['source'] == 'not_found'
    ]

    # Summary
    summary = {cat: len(items) for cat, items in gaps.items()}
    print('gap summary:', json.dumps(summary, ensure_ascii=False, indent=2))

    (UTILS / 'translation_gaps.json').write_text(
        json.dumps(gaps, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
