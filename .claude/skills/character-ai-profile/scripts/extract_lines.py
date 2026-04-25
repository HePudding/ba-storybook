"""从语料目录中提取指定角色的所有台词，输出 JSONL 到 stdout。

用法：
    python3 extract_lines.py "角色名" "语料目录" [--context N]

支持两种语料格式：
  A) 按章节的 Markdown（**角色名**: 台词 / *（角色名）旁白*）
  B) JSONL（每行 {"speaker": "...", "text": "..."}）

输出每行一个 JSON 对象：
  {"speaker": "角色名", "text": "台词", "source": "文件路径", "line_no": 42,
   "type": "dialogue|narration", "context_before": [...], "context_after": [...]}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DIALOGUE_RE = re.compile(r'^\*\*(.+?)\*\*:\s*(.+)$')
NARRATION_RE = re.compile(r'^\*（(.+?)）(.+)\*$')
CHOICE_RE = re.compile(r'^>\s*\*\*(.+?)\*\*:\s*(.+)$')


def parse_md_lines(path: Path) -> list[dict]:
    lines = path.read_text(encoding='utf-8').splitlines()
    parsed = []
    for i, line in enumerate(lines):
        line = line.strip()
        m = DIALOGUE_RE.match(line)
        if m:
            parsed.append({
                'speaker': m.group(1), 'text': m.group(2),
                'type': 'dialogue', 'line_no': i + 1,
            })
            continue
        m = NARRATION_RE.match(line)
        if m:
            parsed.append({
                'speaker': m.group(1), 'text': m.group(2),
                'type': 'narration', 'line_no': i + 1,
            })
            continue
        m = CHOICE_RE.match(line)
        if m:
            parsed.append({
                'speaker': m.group(1), 'text': m.group(2),
                'type': 'choice', 'line_no': i + 1,
            })
    return parsed


def parse_jsonl_lines(path: Path) -> list[dict]:
    parsed = []
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            obj.setdefault('type', 'dialogue')
            obj.setdefault('line_no', i + 1)
            parsed.append(obj)
        except json.JSONDecodeError:
            pass
    return parsed


def extract(character: str, corpus_dir: str, context_window: int = 3) -> None:
    root = Path(corpus_dir)
    if not root.exists():
        print(f'错误：语料目录不存在: {corpus_dir}', file=sys.stderr)
        sys.exit(1)

    total = 0
    files_with_hits = 0

    md_files = sorted(root.rglob('*.md'))
    jsonl_files = sorted(root.rglob('*.jsonl'))

    for path in md_files:
        if path.name.startswith('_') or path.name == 'README.md':
            continue
        all_lines = parse_md_lines(path)
        hits = [i for i, ln in enumerate(all_lines) if ln['speaker'] == character]
        if not hits:
            continue
        files_with_hits += 1
        rel = str(path.relative_to(root))
        for idx in hits:
            entry = all_lines[idx].copy()
            entry['source'] = rel
            ctx_before = []
            for j in range(max(0, idx - context_window), idx):
                ctx_before.append(f"{all_lines[j]['speaker']}: {all_lines[j]['text']}")
            ctx_after = []
            for j in range(idx + 1, min(len(all_lines), idx + 1 + context_window)):
                ctx_after.append(f"{all_lines[j]['speaker']}: {all_lines[j]['text']}")
            entry['context_before'] = ctx_before
            entry['context_after'] = ctx_after
            print(json.dumps(entry, ensure_ascii=False))
            total += 1

    for path in jsonl_files:
        all_lines = parse_jsonl_lines(path)
        hits = [i for i, ln in enumerate(all_lines) if ln.get('speaker') == character]
        if not hits:
            continue
        files_with_hits += 1
        rel = str(path.relative_to(root))
        for idx in hits:
            entry = all_lines[idx].copy()
            entry['source'] = rel
            ctx_before = []
            for j in range(max(0, idx - context_window), idx):
                ctx_before.append(f"{all_lines[j].get('speaker','')}: {all_lines[j].get('text','')}")
            ctx_after = []
            for j in range(idx + 1, min(len(all_lines), idx + 1 + context_window)):
                ctx_after.append(f"{all_lines[j].get('speaker','')}: {all_lines[j].get('text','')}")
            entry['context_before'] = ctx_before
            entry['context_after'] = ctx_after
            print(json.dumps(entry, ensure_ascii=False))
            total += 1

    print(f'提取完成: {total} 句台词, 来自 {files_with_hits} 个文件', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='从语料中提取指定角色的所有台词')
    parser.add_argument('character', help='角色名（精确匹配）')
    parser.add_argument('corpus_dir', help='语料根目录')
    parser.add_argument('--context', type=int, default=3, help='上下文窗口大小（默认 3）')
    args = parser.parse_args()
    extract(args.character, args.corpus_dir, args.context)


if __name__ == '__main__':
    main()
