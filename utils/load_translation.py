"""Helpers for building the JP↔CN translation table."""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JP_EXCEL = ROOT / 'raw-data' / 'Excel'
GLOBAL_EXCEL = ROOT / 'raw-data-global' / 'Excel'


def _load(path: Path):
    with path.open(encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'DataList' in data:
        return data['DataList']
    return data


@lru_cache
def load_jp(table: str):
    return _load(JP_EXCEL / f'{table}.json')


@lru_cache
def load_global(table: str):
    return _load(GLOBAL_EXCEL / f'{table}.json')
