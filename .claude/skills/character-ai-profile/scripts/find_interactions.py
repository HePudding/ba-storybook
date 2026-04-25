"""找出目标角色与其他角色之间的互动对话段落。

用法：
    python3 find_interactions.py "角色名" "语料目录" [--top N] [--snippets M]

输出 JSON 报告到 stdout：
  - 互动最多的 top N 角色
  - 每对关系的代表性对话片段（M 段，保留上下文）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

DIALOGUE_RE = re.compile(r'^\*\*(.+?)\*\*:\s*(.+)$')
NARRATION_RE = re.compile(r'^\*（(.+?)）(.+)\*$')
CHOICE_RE = re.compile(r'^>\s*\*\*(.+?)\*\*:\s*(.+)$')


def parse_file(path: Path) -> list[dict]:
    lines = path.read_text(encoding='utf-8').splitlines()
    parsed = []
    for i, line in enumerate(lines):
        line = line.strip()
        m = DIALOGUE_RE.match(line)
        if m:
            parsed.append({'speaker': m.group(1), 'text': m.group(2), 'type': 'dialogue', 'line_no': i + 1})
            continue
        m = NARRATION_RE.match(line)
        if m:
            parsed.append({'speaker': m.group(1), 'text': m.group(2), 'type': 'narration', 'line_no': i + 1})
            continue
        m = CHOICE_RE.match(line)
        if m:
            parsed.append({'speaker': m.group(1), 'text': m.group(2), 'type': 'choice', 'line_no': i + 1})
    return parsed


def find_interaction_segments(all_lines: list[dict], target: str, other: str, max_gap: int = 5) -> list[list[dict]]:
    """找连续对话段落：target 和 other 在 max_gap 行内交替出现。"""
    segments = []
    current_segment = []
    last_relevant_idx = -999

    for i, ln in enumerate(all_lines):
        if ln['speaker'] in (target, other):
            if i - last_relevant_idx > max_gap and current_segment:
                if any(l['speaker'] == target for l in current_segment) and \
                   any(l['speaker'] == other for l in current_segment):
                    segments.append(current_segment)
                current_segment = []
            current_segment.append(ln)
            last_relevant_idx = i
        elif current_segment and i - last_relevant_idx <= 2:
            current_segment.append(ln)

    if current_segment:
        if any(l['speaker'] == target for l in current_segment) and \
           any(l['speaker'] == other for l in current_segment):
            segments.append(current_segment)

    return segments


def score_segment(seg: list[dict], target: str, other: str) -> float:
    """按对话轮次数和长度打分，选出最有代表性的片段。"""
    turns = 0
    last_speaker = None
    total_len = 0
    for ln in seg:
        if ln['speaker'] in (target, other) and ln['speaker'] != last_speaker:
            turns += 1
            last_speaker = ln['speaker']
        total_len += len(ln['text'])
    length_penalty = 1.0 if len(seg) <= 20 else 20 / len(seg)
    return turns * length_penalty


def analyze(character: str, corpus_dir: str, top_n: int = 15, snippets: int = 3) -> dict:
    root = Path(corpus_dir)
    if not root.exists():
        print(f'错误：语料目录不存在: {corpus_dir}', file=sys.stderr)
        sys.exit(1)

    co_occurrence = Counter()
    interaction_segs: dict[str, list] = defaultdict(list)
    calling_patterns: dict[str, Counter] = defaultdict(Counter)

    md_files = sorted(root.rglob('*.md'))
    for path in md_files:
        if path.name.startswith('_') or path.name == 'README.md':
            continue
        all_lines = parse_file(path)
        if not any(ln['speaker'] == character for ln in all_lines):
            continue

        speakers_in_file = set(ln['speaker'] for ln in all_lines)
        speakers_in_file.discard(character)

        for other in speakers_in_file:
            co_occurrence[other] += 1
            segs = find_interaction_segments(all_lines, character, other)
            for seg in segs:
                interaction_segs[other].append({
                    'source': str(path.relative_to(root)),
                    'lines': seg,
                    'score': score_segment(seg, character, other),
                })

        for ln in all_lines:
            if ln['speaker'] == character:
                for other in speakers_in_file:
                    if other in ln['text']:
                        calling_patterns[other][other] += 1

    top_chars = co_occurrence.most_common(top_n)
    report = {
        'target': character,
        'total_co_occurrences': len(co_occurrence),
        'interactions': [],
    }

    for other, count in top_chars:
        segs = interaction_segs.get(other, [])
        segs.sort(key=lambda s: s['score'], reverse=True)
        best = segs[:snippets]

        formatted_snippets = []
        for seg in best:
            formatted_snippets.append({
                'source': seg['source'],
                'dialogue': [
                    f"{'**' + l['speaker'] + '**: ' if l['type'] == 'dialogue' else '*（' + l['speaker'] + '）'}{l['text']}{'*' if l['type'] == 'narration' else ''}"
                    for l in seg['lines'][:15]
                ],
            })

        entry = {
            'character': other,
            'co_occurrence_files': count,
            'interaction_segments': len(segs),
            'snippets': formatted_snippets,
        }
        if calling_patterns.get(other):
            entry['name_mentions'] = dict(calling_patterns[other].most_common(5))
        report['interactions'].append(entry)

    return report


def main():
    parser = argparse.ArgumentParser(description='角色互动对话段落提取')
    parser.add_argument('character', help='目标角色名')
    parser.add_argument('corpus_dir', help='语料根目录')
    parser.add_argument('--top', type=int, default=15, help='显示互动最多的前 N 个角色（默认 15）')
    parser.add_argument('--snippets', type=int, default=3, help='每对关系的对话片段数（默认 3）')
    args = parser.parse_args()
    result = analyze(args.character, args.corpus_dir, args.top, args.snippets)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
