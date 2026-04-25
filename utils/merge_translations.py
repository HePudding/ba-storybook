"""Merge translation sources by priority: game_data_tw > moegirl > gamekee.

Rebuilds translation_table.json from scratch by running build_translation_table
first (implicit) and then applying moegirl + gamekee fills on top.
"""
from __future__ import annotations
import json
from pathlib import Path

import opencc

from utils.build_translation_table import build_all

_t2s = opencc.OpenCC('t2s')


def _to_sc(text: str) -> str:
    """Convert Traditional Chinese to Simplified Chinese."""
    if not text:
        return text
    return _t2s.convert(text)

ROOT = Path(__file__).resolve().parent.parent
UTILS = ROOT / 'utils'


def _load(name):
    p = UTILS / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def _apply(entry, fill, overwrite=False):
    """Copy cn/cn_full/nickname_cn/variant_cn from fill into entry.

    If overwrite=True, community sources (moegirl/gamekee) replace existing
    game_data_tw translations — community names are what 简中 players use.
    """
    changed = False
    for src, dst in (
        ('cn', 'cn'),
        ('cn_full', 'cn_full'),
        ('nickname_cn', 'nickname_cn'),
        ('variant_cn', 'variant_cn'),
    ):
        if fill.get(src) and (overwrite or not entry.get(dst)):
            entry[dst] = fill[src]
            changed = True
    if changed:
        entry['source'] = fill.get('source', 'unknown')
        if fill.get('url'):
            entry['url'] = fill['url']
    return changed


def _lookup(store, *keys):
    for k in keys:
        if k and k in store:
            return store[k]
    return None


def apply_fills(table, moegirl, gamekee):
    # Community translations (moegirl/gamekee) OVERWRITE game_data_tw.
    # 简中玩家用的是社区译名，不是国际服繁中机翻。

    # Simple categories
    for cat in ['schools', 'clubs', 'story_titles', 'favor_items', 'locations', 'terms']:
        m = moegirl.get(cat, {})
        g = gamekee.get(cat, {})
        for jp, entry in table.get(cat, {}).items():
            short = entry.get('jp_short', '') if cat == 'schools' else ''
            fill = _lookup(m, jp, short) or _lookup(g, jp, short)
            if fill:
                _apply(entry, fill, overwrite=True)

    # Events: seed from gaps if empty
    ev_gaps = _load('translation_gaps.json').get('events', [])
    if not table.get('events'):
        table['events'] = {}
    for ev in ev_gaps:
        eid = ev['event_dir']
        if eid not in table['events']:
            table['events'][eid] = {'cn': '', 'event_id': ev['event_id'], 'source': 'not_found'}
    m_ev = moegirl.get('events', {})
    g_ev = gamekee.get('events', {})
    for eid, entry in table['events'].items():
        fill = _lookup(m_ev, eid) or _lookup(g_ev, eid)
        if fill:
            if fill.get('cn'):
                _apply(entry, fill, overwrite=True)
            if fill.get('jp'):
                entry['jp'] = fill['jp']
            if fill.get('note'):
                entry['note'] = fill['note']

    # Characters — community overrides game_data_tw
    m_c = moegirl.get('characters', {})
    g_c = gamekee.get('characters', {})
    for jp, entry in table.get('characters', {}).items():
        fill = _lookup(m_c, jp) or _lookup(g_c, jp)
        if fill:
            _apply(entry, fill, overwrite=True)
        for vjp, vent in (entry.get('variants') or {}).items():
            fill = _lookup(m_c, vjp) or _lookup(g_c, vjp)
            if fill:
                _apply(vent, fill, overwrite=True)

    # scenario_characters
    m_sc = moegirl.get('scenario_characters', {})
    g_sc = gamekee.get('scenario_characters', {})
    for k, entry in table.get('scenario_characters', {}).items():
        jp = entry['jp']
        fill = _lookup(m_sc, k, f'{jp}|', jp) or _lookup(g_sc, k, f'{jp}|', jp)
        if fill:
            _apply(entry, fill, overwrite=True)

    return table


def compute_coverage(table):
    out = {}
    for cat in ['schools', 'clubs', 'story_titles', 'favor_items', 'locations', 'terms', 'events']:
        entries = table.get(cat, {}).values()
        by = {'game_data_tw': 0, 'moegirl': 0, 'gamekee': 0}
        nf = 0
        for e in entries:
            if not e.get('cn'):
                nf += 1
            else:
                s = e.get('source', 'game_data_tw')
                by[s] = by.get(s, 0) + 1
        total = len(table.get(cat, {}))
        trans = sum(by.values())
        out[cat] = {
            'total': total,
            'translated': trans,
            'not_found': nf,
            'coverage': f'{trans/total*100:.1f}%' if total else '0%',
            'by_source': by,
        }

    # characters
    by = {'game_data_tw': 0, 'moegirl': 0, 'gamekee': 0}
    nf = 0; total = 0
    for jp, e in table.get('characters', {}).items():
        total += 1
        if not e.get('cn'):
            nf += 1
        else:
            by[e.get('source', 'game_data_tw')] = by.get(e.get('source', 'game_data_tw'), 0) + 1
        for vjp, v in (e.get('variants') or {}).items():
            total += 1
            if not v.get('cn'):
                nf += 1
            else:
                by[v.get('source', 'game_data_tw')] = by.get(v.get('source', 'game_data_tw'), 0) + 1
    trans = sum(by.values())
    out['characters'] = {
        'total': total, 'translated': trans, 'not_found': nf,
        'coverage': f'{trans/total*100:.1f}%' if total else '0%',
        'by_source': by,
    }

    # scenario_characters
    by = {'game_data_tw': 0, 'moegirl': 0, 'gamekee': 0}
    nf = 0
    entries = list(table.get('scenario_characters', {}).values())
    for e in entries:
        if not e.get('cn'):
            nf += 1
        else:
            by[e.get('source', 'game_data_tw')] = by.get(e.get('source', 'game_data_tw'), 0) + 1
    trans = sum(by.values())
    out['scenario_characters'] = {
        'total': len(entries),
        'translated': trans,
        'not_found': nf,
        'coverage': f'{trans/len(entries)*100:.1f}%' if entries else '0%',
        'by_source': by,
    }
    return out


def _convert_all_to_sc(table):
    """Walk every entry and convert all CN text fields from Traditional to Simplified."""
    cn_fields = ('cn', 'cn_full', 'nickname_cn', 'variant_cn', 'family_cn', 'personal_cn')
    for cat in ('schools', 'clubs', 'story_titles', 'favor_items',
                'locations', 'terms', 'events', 'scenario_characters'):
        for entry in table.get(cat, {}).values():
            for f in cn_fields:
                if entry.get(f):
                    entry[f] = _to_sc(entry[f])
    for entry in table.get('characters', {}).values():
        for f in cn_fields:
            if entry.get(f):
                entry[f] = _to_sc(entry[f])
        for vent in (entry.get('variants') or {}).values():
            for f in cn_fields:
                if vent.get(f):
                    vent[f] = _to_sc(vent[f])


def main():
    table = build_all()
    moegirl = _load('translation_fills_moegirl.json')
    gamekee = _load('translation_fills_gamekee.json')
    apply_fills(table, moegirl, gamekee)
    _convert_all_to_sc(table)
    coverage = compute_coverage(table)
    (UTILS / 'translation_table.json').write_text(
        json.dumps(table, ensure_ascii=False, indent=2), encoding='utf-8')
    (UTILS / 'translation_coverage.json').write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(coverage, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
