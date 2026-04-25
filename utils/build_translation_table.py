"""Build JP→CN translation table from game data.

Data sources:
- raw-data/Excel           → JP server (Yostar jp)
- raw-data-global/Excel    → International server (has Tw/zh-TW field = primary CN source)

Join strategy: same numeric Ids / Keys across servers (JP ids are a superset of global).
For JP entries absent from global, CN translation is marked "not_found" → handed to
Phase 2 (moegirl) subagent.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

from utils.load_translation import load_jp, load_global

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'utils'


def _index(rows, key):
    return {r[key]: r for r in rows if key in r}


# ---------- schools & clubs ----------

# School/Club internal codes → JP text (hardcoded, cross-referenced with LocalizeEtc).
# CN is resolved from global Tw field of LocalizeEtc where possible, else left empty.
SCHOOL_CODE_JP = {
    # code → (jp_short, jp_full)
    'Gehenna': ('ゲヘナ', 'ゲヘナ学園'),
    'Trinity': ('トリニティ', 'トリニティ総合学園'),
    'Millennium': ('ミレニアム', 'ミレニアムサイエンススクール'),
    'Abydos': ('アビドス', 'アビドス高等学校'),
    'Shanhaijing': ('山海経', '山海経高級中学校'),
    'Hyakkiyako': ('百鬼夜行', '百鬼夜行連合学院'),
    'RedWinter': ('赤冬', '赤冬連邦学園'),
    'Valkyrie': ('ヴァルキューレ', 'ヴァルキューレ警察学校'),
    'SRT': ('SRT', 'SRT特殊学園'),
    'Arius': ('アリウス', 'アリウス分校'),
    'Tokiwa': ('常盤', '常盤学園'),
    'Sakugawa': ('佐官', '佐官学園'),
    'Highlander': ('ハイランダー', 'ハイランダー鉄道学園'),
    'WildHunt': ('野狩', '野狩高等学校'),
}

CLUB_CODE_JP = {
    # Based on actual club codes present in CharacterExcelTable (JP branch).
    # JP names are community-canonical forms; CN lookup happens against LocalizeEtc,
    # and gaps flow to Phase 2 (moegirl).
    'Kohshinjo68': '便利屋68',
    'GameDev': 'ゲーム開発部',
    'Veritas': 'ヴェリタス',
    'Fuuki': '風紀委員会',
    'SPTF': 'SPTF',
    'Justice': '正義実現委員会',
    'Endanbou': '掩蔽部',
    'HoukagoDessert': '放課後スイーツ部',
    'NinpoKenkyubu': '忍術研究部',
    'TrainingClub': 'トレーニングクラブ',
    'TheSeminar': 'セミナー',
    'Countermeasure': '対策委員会',
    'EmptyClub': '未所属',
    'Meihuayuan': '梅華園',
    'CleanNClearing': '掃除と洗濯部',
    'KnightsHospitaller': '救護騎士団',
    'MatsuriOffice': '祭り事務局',
    'RemedialClass': '補習授業部',
    'GourmetClub': '美食研究会',
    'HotSpringsDepartment': '温泉開発部',
    'RedwinterSecretary': '赤冬事務局',
    'RabbitPlatoon': 'RABBIT小隊',
    'Engineer': 'エンジニア部',
    'PandemoniumSociety': 'パンデモニウムソサエティ',
    'Class227': '2年27組',
    'SisterHood': 'シスターフッド',
    'TrinityVigilance': 'トリニティ風紀委員会',
    'BookClub': '古書研究会',
    'PublicPeaceBureau': '治安維持局',
    'AriusSqud': 'アリウススクワッド',
    'FoodService': '給食部',
    'AbydosStudentCouncil': 'アビドス生徒会',
    'BlackTortoisePromenade': '玄武商店街',
    'CentralControlCenter': '中央管理局',
    'Emergentology': '救急医学部',
    'FreightLogisticsDepartment': '物流部',
    'Genryumon': '玄龍門',
    'Hyakkayouran': '百花繚乱',
    'IndeGEHENNA': 'ゲヘナ在籍',
    'IndeHyakkiyako': '百鬼夜行在籍',
    'IndeShanhaijing': '山海経在籍',
    'KnowledgeLiberationFront': '知識解放戦線',
    'LaborParty': '労働党',
    'OccultClub': 'オカルト研究部',
    'Onmyobu': '陰陽部',
    'ShinySparkleSociety': 'シャイニングスパークル研究会',
    'Shugyobu': '修行部',
    'TeaParty': 'ティーパーティー',
    'anzenkyoku': '安全局',
    'None': '未所属',
}


def _lookup_tw_by_jp(etc_rows, jp_text):
    """Find NameTw in Localize Etc when NameJp matches exactly."""
    for e in etc_rows:
        if e.get('NameJp') == jp_text and e.get('NameTw'):
            return e['NameTw']
    return None


def build_schools(etc_global):
    out = {}
    for code, (jp_short, jp_full) in SCHOOL_CODE_JP.items():
        cn_short = _lookup_tw_by_jp(etc_global, jp_short)
        cn_full = _lookup_tw_by_jp(etc_global, jp_full)
        out[jp_full] = {
            'code': code,
            'jp_short': jp_short,
            'cn': cn_short or '',
            'cn_full': cn_full or '',
            'source': 'game_data_tw' if cn_short or cn_full else 'not_found',
        }
    return out


def build_clubs(etc_global):
    out = {}
    for code, jp in CLUB_CODE_JP.items():
        cn = _lookup_tw_by_jp(etc_global, jp)
        out[jp] = {
            'code': code,
            'cn': cn or '',
            'source': 'game_data_tw' if cn else 'not_found',
        }
    return out


# ---------- characters ----------

def build_characters():
    """Extract playable character name map with variants.

    Returns:
      - characters: base_jp → {jp_full, cn_full, cn, variants, ...}
    """
    jp_chars = load_jp('CharacterExcelTable')
    g_chars_ix = _index(load_global('CharacterExcelTable'), 'Id')
    jp_etc = _index(load_jp('LocalizeEtcExcelTable'), 'Key')
    g_etc = _index(load_global('LocalizeEtcExcelTable'), 'Key')
    jp_prof = _index(load_jp('LocalizeCharProfileExcelTable'), 'CharacterId')
    g_prof = _index(load_global('LocalizeCharProfileExcelTable'), 'CharacterId')

    # Group all CharacterExcelTable entries by CostumeGroupId (base character).
    by_costume = defaultdict(list)
    for c in jp_chars:
        if not c.get('IsPlayableCharacter'):
            continue
        if c.get('ProductionStep') != 'Release':
            continue
        # Only "real" playable entries: Id range 10000-20000, no _E/_Event suffixes
        dev = c.get('DevName', '')
        if any(tag in dev for tag in ('_E', '_FixedEchelon', '_Event')):
            continue
        if c['Id'] >= 100000:
            continue
        by_costume[c.get('CostumeGroupId', c['Id'])].append(c)

    out = {}
    for costume_id, group in by_costume.items():
        # Find base: the one whose Id == CostumeGroupId
        base = next((c for c in group if c['Id'] == costume_id), group[0])
        jp_short = (jp_etc.get(base.get('LocalizeEtcId')) or {}).get('NameJp') or ''
        cn_short = (g_etc.get(base.get('LocalizeEtcId')) or {}).get('NameTw') or ''
        prof_j = jp_prof.get(costume_id) or {}
        prof_g = g_prof.get(costume_id) or {}
        jp_full = prof_j.get('FullNameJp') or jp_short
        cn_full = prof_g.get('FullNameTw') or cn_short
        family_jp = prof_j.get('FamilyNameJp') or ''
        family_cn = prof_g.get('FamilyNameTw') or ''
        personal_jp = prof_j.get('PersonalNameJp') or ''
        personal_cn = prof_g.get('PersonalNameTw') or ''

        if not jp_short:
            continue

        entry = {
            'jp': jp_short,
            'cn': cn_short,
            'jp_full': jp_full,
            'cn_full': cn_full,
            'family_jp': family_jp,
            'family_cn': family_cn,
            'personal_jp': personal_jp,
            'personal_cn': personal_cn,
            'dev_name': base.get('DevName'),
            'character_id': base['Id'],
            'school': base.get('School'),
            'club': base.get('Club'),
            'source': 'game_data_tw' if cn_short else 'not_found',
            'variants': {},
        }

        # Collect variants (non-base entries in the same CostumeGroupId OR same base name stem).
        # Variants in BA typically live on adjacent Ids but different CostumeGroupId too.
        entry_stem = jp_short  # e.g., シロコ
        out[jp_short] = entry

    # Find variants: for every playable character NOT yet in `out`, match its stem name.
    for c in jp_chars:
        if not c.get('IsPlayableCharacter') or c.get('ProductionStep') != 'Release':
            continue
        dev = c.get('DevName', '')
        if any(tag in dev for tag in ('_E', '_FixedEchelon', '_Event')):
            continue
        if c['Id'] >= 100000:
            continue
        jp_name = (jp_etc.get(c.get('LocalizeEtcId')) or {}).get('NameJp') or ''
        if not jp_name:
            continue
        # If jp_name contains "（" it's a variant.
        if '（' in jp_name and '）' in jp_name:
            stem = jp_name.split('（', 1)[0]
            variant_suffix = jp_name.split('（', 1)[1].rstrip('）')
            cn_name = (g_etc.get(c.get('LocalizeEtcId')) or {}).get('NameTw') or ''
            if stem in out:
                out[stem]['variants'][jp_name] = {
                    'cn': cn_name,
                    'variant_jp': variant_suffix,
                    'variant_cn': cn_name.split('(', 1)[1].rstrip(')') if '(' in cn_name else '',
                    'dev_name': dev,
                    'character_id': c['Id'],
                    'source': 'game_data_tw' if cn_name else 'not_found',
                }
    return out


# ---------- story titles (main + content scenarios) ----------

def build_story_titles():
    """Extract story/chapter titles (Main, Group, Event, Bond, Mini) from
    LocalizeScenario + ContentsScenario. Also captures all short text entries that
    look like titles (no punctuation, < 40 chars)."""
    jp_ls = load_jp('LocalizeScenarioExcelTable')
    g_ls_ix = _index(load_global('LocalizeScenarioExcelTable'), 'Key')
    jp_ls_ix = _index(jp_ls, 'Key')
    out = {}

    # ContentsScenarioExcelTable: volumes / chapters for main+extra
    for row in load_jp('ContentsScenarioExcelTable'):
        lid = row.get('LocalizeId')
        if not lid:
            continue
        jp = (jp_ls_ix.get(lid) or {}).get('Jp') or ''
        cn = (g_ls_ix.get(lid) or {}).get('Tw') or ''
        if jp:
            out[jp] = {
                'cn': cn,
                'source': 'game_data_tw' if cn else 'not_found',
                'category': row.get('ScenarioContentType'),
                'localize_id': lid,
            }

    # All LocalizeScenario short strings that look like titles:
    # - starts with "Vol.", "第", contains "編", "章", "話"
    # - or short length without punctuation
    title_markers = ('Vol.', '第', '編', '章', '話', 'プロローグ', 'エピローグ')
    for row in jp_ls:
        jp = row.get('Jp') or ''
        if not jp or len(jp) > 50:
            continue
        if not any(m in jp for m in title_markers):
            continue
        if jp in out:
            continue
        cn = (g_ls_ix.get(row['Key']) or {}).get('Tw') or ''
        out[jp] = {
            'cn': cn,
            'source': 'game_data_tw' if cn else 'not_found',
            'category': 'scenario_title',
            'localize_id': row['Key'],
        }
    return out


# ---------- events ----------

def build_events():
    """Event names come from LocalizeEtc keyed by EventContent's LocalizeEtcId.

    EventContentSeasonExcelTable rows reference a LocalizeEtc key with the event name.
    """
    jp_etc = _index(load_jp('LocalizeEtcExcelTable'), 'Key')
    g_etc = _index(load_global('LocalizeEtcExcelTable'), 'Key')
    out = {}
    try:
        seasons = load_jp('EventContentSeasonExcelTable')
    except Exception:
        return out
    cols = seasons[0].keys() if seasons else ()
    localize_col = next((k for k in cols if 'Localize' in k and 'Etc' in k), None)
    if not localize_col:
        # fallback: any Localize* column
        localize_col = next((k for k in cols if 'Localize' in k), None)
    if not localize_col:
        return out
    for row in seasons:
        lid = row.get(localize_col)
        if not lid or lid == 0:
            continue
        jp = (jp_etc.get(lid) or {}).get('NameJp') or ''
        cn = (g_etc.get(lid) or {}).get('NameTw') or ''
        if jp and jp not in out:
            out[jp] = {
                'cn': cn,
                'event_content_id': row.get('EventContentId'),
                'source': 'game_data_tw' if cn else 'not_found',
            }
    return out


# ---------- favor items ----------

def build_favor_items():
    """Favor items: ItemExcelTable where ItemCategory == 'Favor' / 'FavorItem'."""
    jp_etc = _index(load_jp('LocalizeEtcExcelTable'), 'Key')
    g_etc = _index(load_global('LocalizeEtcExcelTable'), 'Key')
    items = load_jp('ItemExcelTable')
    out = {}
    for it in items:
        cat = (it.get('ItemCategory') or '').lower()
        if 'favor' not in cat:
            continue
        lid = it.get('LocalizeEtcId')
        jp = (jp_etc.get(lid) or {}).get('NameJp') or ''
        cn = (g_etc.get(lid) or {}).get('NameTw') or ''
        if jp and jp not in out:
            out[jp] = {
                'cn': cn,
                'item_id': it.get('Id'),
                'source': 'game_data_tw' if cn else 'not_found',
            }
    return out


# ---------- locations ----------

def build_locations():
    jp_etc = _index(load_jp('LocalizeEtcExcelTable'), 'Key')
    g_etc = _index(load_global('LocalizeEtcExcelTable'), 'Key')
    out = {}
    for tbl in ('AcademyLocationExcelTable', 'AcademyZoneExcelTable'):
        try:
            rows = load_jp(tbl)
        except Exception:
            continue
        for r in rows:
            lid = r.get('LocalizeEtcId')
            jp = (jp_etc.get(lid) or {}).get('NameJp') or ''
            cn = (g_etc.get(lid) or {}).get('NameTw') or ''
            if jp and jp not in out:
                out[jp] = {
                    'cn': cn,
                    'source': 'game_data_tw' if cn else 'not_found',
                    'table': tbl,
                }
    return out


# ---------- scenario characters (dialog speakers incl. NPCs) ----------

def build_scenario_characters():
    jp_sn = load_jp('ScenarioCharacterNameExcelTable')
    g_sn = _index(load_global('ScenarioCharacterNameExcelTable'), 'CharacterName')
    out = {}
    for r in jp_sn:
        jp = r.get('NameJP') or ''
        if not jp or jp in ('？？？', '???'):
            continue
        nick_jp = r.get('NicknameJP') or ''
        g_r = g_sn.get(r['CharacterName']) or {}
        cn = g_r.get('NameTW') or ''
        nick_cn = g_r.get('NicknameTW') or ''
        key = jp if not nick_jp else f'{jp}|{nick_jp}'
        out[key] = {
            'jp': jp, 'nickname_jp': nick_jp,
            'cn': cn, 'nickname_cn': nick_cn,
            'character_name_hash': r['CharacterName'],
            'source': 'game_data_tw' if cn else 'not_found',
        }
    return out


# ---------- terms (curated) ----------

CURATED_TERMS = [
    '先生', 'モモトーク', 'ヘイロー', 'シャーレ', 'キヴォトス',
    '先生と共に', 'オーパーツ', 'カルバノ山', 'ゲマトリア',
    '色彩', 'ブラックスーツ', 'アトラ・ハシース',
    '生徒', '学園', '連邦生徒会',
    '絆ストーリー', 'メモリアルロビー', 'グループストーリー', 'メインストーリー',
    'イベントストーリー', 'ミニストーリー',
    'レイド', '総力戦', '大決戦',
]


def build_terms():
    jp_etc = load_jp('LocalizeEtcExcelTable')
    g_etc_ix = _index(load_global('LocalizeEtcExcelTable'), 'Key')
    out = {}
    for term in CURATED_TERMS:
        hits = [e for e in jp_etc if e.get('NameJp') == term]
        if not hits:
            # substring match, take shortest
            cands = [e for e in jp_etc if term in (e.get('NameJp') or '')]
            if cands:
                hits = [min(cands, key=lambda e: len(e.get('NameJp') or ''))]
        if hits:
            g_row = g_etc_ix.get(hits[0]['Key']) or {}
            cn = g_row.get('NameTw') or ''
            out[term] = {
                'cn': cn,
                'source': 'game_data_tw' if cn else 'not_found',
            }
        else:
            out[term] = {'cn': '', 'source': 'not_found'}
    return out


# ---------- main ----------

def build_all():
    etc_global = load_global('LocalizeEtcExcelTable')
    table = {
        'schools': build_schools(etc_global),
        'clubs': build_clubs(etc_global),
        'characters': build_characters(),
        'scenario_characters': build_scenario_characters(),
        'story_titles': build_story_titles(),
        'events': build_events(),
        'favor_items': build_favor_items(),
        'locations': build_locations(),
        'terms': build_terms(),
    }
    return table


def coverage(table):
    out = {}
    for cat, entries in table.items():
        total = len(entries)
        if cat == 'characters':
            # Count base + variants
            translated = 0
            not_found = 0
            total_all = 0
            for jp, e in entries.items():
                total_all += 1
                (translated if e.get('cn') else not_found.__iadd__ if False else lambda: None)
                if e.get('cn'):
                    translated += 1
                else:
                    not_found += 1
                for vj, v in (e.get('variants') or {}).items():
                    total_all += 1
                    if v.get('cn'):
                        translated += 1
                    else:
                        not_found += 1
            total = total_all
        else:
            translated = sum(1 for e in entries.values() if e.get('cn'))
            not_found = total - translated
        coverage_pct = f'{(translated/total*100):.1f}%' if total else '0%'
        out[cat] = {
            'total': total,
            'translated': translated,
            'not_found': not_found,
            'coverage': coverage_pct,
        }
    return out


if __name__ == '__main__':
    table = build_all()
    (OUT / 'translation_table.json').write_text(
        json.dumps(table, ensure_ascii=False, indent=2), encoding='utf-8')
    cov = coverage(table)
    (OUT / 'translation_coverage.json').write_text(
        json.dumps(cov, ensure_ascii=False, indent=2), encoding='utf-8')
    print('--- coverage ---')
    print(json.dumps(cov, ensure_ascii=False, indent=2))
