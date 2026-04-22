"""对多个 GroupId 跑 parse+format 烟雾测试。"""
from __future__ import annotations

import random
import sys

from .load_data import classify_group, iter_all_group_ids
from .format_markdown import parsed_to_markdown
from .parse_dialogue import parse_group


def main() -> None:
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
    random.seed(seed)

    all_ids = list(iter_all_group_ids())
    # 各类型抽 1 个
    type_samples: dict[str, int] = {}
    random.shuffle(all_ids)
    for gid in all_ids:
        t = classify_group(gid)
        if t not in type_samples:
            type_samples[t] = gid
        if len(type_samples) >= 6:
            break

    for t, gid in type_samples.items():
        print(f"\n===== {t} / GroupId={gid} =====\n")
        try:
            parsed = parse_group(gid)
            md = parsed_to_markdown(parsed, story_type=t)
            snippet = md if len(md) < 1200 else md[:1200] + "\n...(truncated)"
            print(snippet)
        except Exception as exc:  # noqa: BLE001
            print(f"!!! error: {exc}")


if __name__ == "__main__":
    main()
