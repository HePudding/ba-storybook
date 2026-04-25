"""对角色台词做句式 pattern 统计，辅助发现口癖。

用法：
    python3 find_patterns.py /tmp/profile_lines.jsonl [--top N]

输入：extract_lines.py 的 JSONL 输出
输出：JSON 报告到 stdout，包含句首/句尾/一人称/高频 n-gram 统计
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

FIRST_PERSON_JP = [
    '私', 'わたし', 'ワタシ', 'あたし', 'アタシ',
    '僕', 'ぼく', 'ボク',
    '俺', 'おれ', 'オレ',
    'あたくし', 'わし', 'ワシ',
    'うち', 'ウチ',
    '自分', 'じぶん',
    'おじさん', 'このおじさん',
]

FIRST_PERSON_CN = [
    '我', '俺', '本人', '在下', '老子', '本小姐', '人家', '咱',
    '本大爷', '奴家', '妾身', '小生',
]

SENTENCE_END_RE = re.compile(
    r'([　-〿぀-ゟ゠-ヿ一-鿿\w]+[。！？～…♪♡☆]+|'
    r'[぀-ゟ゠-ヿ]{1,6}[。！？～…]*)$'
)


def analyze(lines_path: str, top_n: int = 20) -> dict:
    path = Path(lines_path)
    if not path.exists():
        print(f'错误：文件不存在: {lines_path}', file=sys.stderr)
        sys.exit(1)

    texts = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if obj.get('text'):
                texts.append(obj['text'])
        except json.JSONDecodeError:
            pass

    if not texts:
        print('警告：没有找到台词', file=sys.stderr)
        return {}

    report: dict = {'total_lines': len(texts)}

    # --- 一人称统计 ---
    first_person = Counter()
    all_candidates = FIRST_PERSON_JP + FIRST_PERSON_CN
    for text in texts:
        for fp in all_candidates:
            count = len(re.findall(rf'(?:^|[^a-zA-Z一-鿿]){re.escape(fp)}(?:[はがもをのにで、。！？\s]|$)', text))
            if count:
                first_person[fp] += count
    report['first_person'] = dict(first_person.most_common(10))

    # --- 句首 pattern ---
    start_patterns = Counter()
    for text in texts:
        text = text.strip()
        if len(text) < 2:
            continue
        for length in (5, 4, 3, 2):
            prefix = text[:length]
            if re.match(r'^[぀-ゟ゠-ヿ一-鿿]', prefix):
                start_patterns[prefix] += 1
    filtered_starts = Counter()
    for pat, cnt in start_patterns.most_common(100):
        if cnt >= 3:
            is_substring = False
            for longer, lcnt in filtered_starts.items():
                if longer.startswith(pat) and lcnt >= cnt * 0.8:
                    is_substring = True
                    break
            if not is_substring:
                filtered_starts[pat] = cnt
    report['sentence_starts'] = dict(list(filtered_starts.most_common(top_n)))

    # --- 句尾 pattern ---
    end_patterns = Counter()
    for text in texts:
        text = text.rstrip()
        if len(text) < 2:
            continue
        for length in (6, 5, 4, 3, 2):
            suffix = text[-length:]
            if re.search(r'[぀-ゟ゠-ヿ]', suffix):
                end_patterns[suffix] += 1
    filtered_ends = Counter()
    for pat, cnt in end_patterns.most_common(100):
        if cnt >= 3:
            is_substring = False
            for longer, lcnt in filtered_ends.items():
                if longer.endswith(pat) and lcnt >= cnt * 0.8:
                    is_substring = True
                    break
            if not is_substring:
                filtered_ends[pat] = cnt
    report['sentence_ends'] = dict(list(filtered_ends.most_common(top_n)))

    # --- 高频短语（word n-gram 近似）---
    # 用字符 n-gram（日语没有天然分词边界）
    char_ngrams = Counter()
    for text in texts:
        clean = re.sub(r'[。！？、…～♪♡☆「」『』（）\s]', '', text)
        for n in (4, 5, 6, 3):
            for i in range(len(clean) - n + 1):
                gram = clean[i:i + n]
                if re.search(r'[぀-ゟ゠-ヿ一-鿿]', gram):
                    char_ngrams[gram] += 1
    freq_phrases = Counter()
    for gram, cnt in char_ngrams.most_common(200):
        if cnt >= 3:
            is_sub = False
            for longer, lcnt in freq_phrases.items():
                if gram in longer and lcnt >= cnt * 0.7:
                    is_sub = True
                    break
            if not is_sub:
                freq_phrases[gram] = cnt
    report['frequent_phrases'] = dict(list(freq_phrases.most_common(top_n)))

    # --- 特殊表达 ---
    special = Counter()
    special_patterns = [
        (r'うへ[へぇ～ー]*', 'うへへ系'),
        (r'～+', '～（波浪号）'),
        (r'……+', '……（省略号）'),
        (r'[！!]{2,}', '连续感叹号'),
        (r'[？?]{2,}', '连续问号'),
        (r'♪+', '♪'),
        (r'♡+', '♡'),
    ]
    for text in texts:
        for pat, label in special_patterns:
            if re.search(pat, text):
                special[label] += 1
    report['special_expressions'] = dict(special.most_common())

    return report


def main():
    parser = argparse.ArgumentParser(description='角色台词句式 pattern 统计')
    parser.add_argument('lines_file', help='extract_lines.py 输出的 JSONL 文件')
    parser.add_argument('--top', type=int, default=20, help='每类显示前 N 个（默认 20）')
    args = parser.parse_args()
    result = analyze(args.lines_file, args.top)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
