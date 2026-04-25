"""将 Markdown 角色档案转换为 SillyTavern Character Card V2 格式。

用法：
    python3 export_tavern_card.py profiles/角色名.md [--avatar 头像.png] [--output 输出.png]

如果提供头像 PNG，角色卡 JSON 会嵌入 PNG 的 tEXt chunk（标准酒馆卡格式）。
如果不提供头像，只输出 JSON 文件。

依赖：Pillow（仅在嵌入 PNG 时需要）
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path


def parse_profile_md(text: str) -> dict:
    """从 Markdown 档案中提取各部分内容。"""
    sections: dict[str, str] = {}
    current_h2 = ''
    current_lines: list[str] = []

    for line in text.splitlines():
        m = re.match(r'^##\s+(.+)$', line)
        if m:
            if current_h2:
                sections[current_h2] = '\n'.join(current_lines).strip()
            current_h2 = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_h2:
        sections[current_h2] = '\n'.join(current_lines).strip()

    h1 = ''
    for line in text.splitlines():
        m = re.match(r'^#\s+(.+)$', line)
        if m:
            h1 = m.group(1).strip()
            break

    return {'title': h1, 'sections': sections}


def build_description(sections: dict[str, str]) -> str:
    """构建 description 字段：基本设定 + 世界观。"""
    parts = []
    for key in ('基本设定', '基本設定', 'Basic Info', 'Profile'):
        if key in sections:
            parts.append(sections[key])
            break
    for key in ('世界观', '世界觀', 'World', 'Worldview', 'Lore'):
        if key in sections:
            parts.append(sections[key])
            break
    return '\n\n'.join(parts) if parts else ''


def build_personality(sections: dict[str, str]) -> str:
    """构建 personality 字段：说话方式 + 情景反应。"""
    parts = []
    for key in sections:
        if any(k in key for k in ('说话方式', '話し方', 'Speech', '说话')):
            parts.append(sections[key])
        if any(k in key for k in ('情景反应', '情景', 'Reaction', '反応')):
            parts.append(sections[key])
    return '\n\n'.join(parts) if parts else ''


def build_scenario(sections: dict[str, str]) -> str:
    """构建 scenario 字段：世界观。"""
    for key in ('世界观', '世界觀', 'World', 'Worldview', 'Lore'):
        if key in sections:
            return sections[key]
    return ''


def build_mes_example(sections: dict[str, str], char_name: str) -> str:
    """从情景反应和大厅台词构建示例对话。"""
    lines = []

    for key in sections:
        if any(k in key for k in ('情景反应', '情景', 'Reaction', '反応')):
            content = sections[key]
            examples = re.findall(r'[「『](.+?)[」』]', content)
            if examples:
                lines.append('<START>')
                lines.append(f'{{{{user}}}}: *approaches*')
                for ex in examples[:3]:
                    lines.append(f'{{{{char}}}}: {ex}')
            break

    for key in sections:
        if any(k in key for k in ('大厅', '日常台詞', 'Lobby', 'Daily', 'ロビー')):
            content = sections[key]
            lobby_lines = re.findall(r'^[-・]\s*(.+?)(?:\s*_\(.+?\)_)?$', content, re.MULTILINE)
            if lobby_lines:
                lines.append('<START>')
                for ll in lobby_lines[:5]:
                    lines.append(f'{{{{char}}}}: {ll}')
            break

    return '\n'.join(lines)


def build_system_prompt(sections: dict[str, str]) -> str:
    """从检查清单构建 system_prompt。"""
    for key in sections:
        if any(k in key for k in ('检查清单', 'チェックリスト', 'Checklist', 'Roleplay')):
            return sections[key]
    return ''


def build_first_message(sections: dict[str, str], char_name: str) -> str:
    """从大厅台词生成第一条消息。"""
    for key in sections:
        if any(k in key for k in ('大厅', '日常台詞', 'Lobby', 'Daily', 'ロビー')):
            content = sections[key]
            first = re.search(r'^[-・]\s*(.+?)(?:\s*_\(.+?\)_)?$', content, re.MULTILINE)
            if first:
                return f'*{char_name} looks up* {first.group(1)}'
            break
    return f'*{char_name} notices you approaching*'


def build_card_v2(profile_path: str) -> dict:
    """从 Markdown 档案构建 Character Card V2 JSON。"""
    text = Path(profile_path).read_text(encoding='utf-8')
    parsed = parse_profile_md(text)
    sections = parsed['sections']
    char_name = parsed['title'] or Path(profile_path).stem

    return {
        'spec': 'chara_card_v2',
        'spec_version': '2.0',
        'data': {
            'name': char_name,
            'description': build_description(sections),
            'personality': build_personality(sections),
            'scenario': build_scenario(sections),
            'first_mes': build_first_message(sections, char_name),
            'mes_example': build_mes_example(sections, char_name),
            'creator_notes': '由 character-ai-profile skill 从游戏语料自动生成',
            'system_prompt': build_system_prompt(sections),
            'post_history_instructions': '',
            'alternate_greetings': [],
            'tags': ['auto-generated', 'game-character'],
            'creator': 'character-ai-profile',
            'character_version': '1.0',
            'extensions': {},
        },
    }


def build_card_v1(profile_path: str) -> dict:
    """从 Markdown 档案构建 Character Card V1 JSON（兼容更多前端）。"""
    text = Path(profile_path).read_text(encoding='utf-8')
    parsed = parse_profile_md(text)
    sections = parsed['sections']
    char_name = parsed['title'] or Path(profile_path).stem

    return {
        'name': char_name,
        'description': build_description(sections),
        'personality': build_personality(sections),
        'scenario': build_scenario(sections),
        'first_mes': build_first_message(sections, char_name),
        'mes_example': build_mes_example(sections, char_name),
    }


def build_card(profile_path: str, version: int = 2) -> dict:
    if version == 1:
        return build_card_v1(profile_path)
    return build_card_v2(profile_path)


def embed_in_png(card: dict, avatar_path: str, output_path: str) -> None:
    """将角色卡 JSON 嵌入 PNG 的 tEXt chunk。"""
    try:
        from PIL import Image
        from PIL.PngImagePlugin import PngInfo
    except ImportError:
        print('错误：嵌入 PNG 需要 Pillow 库。请运行: pip install Pillow', file=sys.stderr)
        sys.exit(1)

    img = Image.open(avatar_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    card_json = json.dumps(card, ensure_ascii=False)
    card_b64 = base64.b64encode(card_json.encode('utf-8')).decode('ascii')

    metadata = PngInfo()
    metadata.add_text('chara', card_b64)

    img.save(output_path, pnginfo=metadata)
    print(f'酒馆角色卡已保存: {output_path} ({Path(output_path).stat().st_size / 1024:.1f} KB)', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='将 Markdown 角色档案转换为 SillyTavern 角色卡')
    parser.add_argument('profile', help='Markdown 档案路径')
    parser.add_argument('--avatar', help='角色头像 PNG 路径（可选，提供则嵌入 PNG）')
    parser.add_argument('--output', help='输出文件路径（默认：profiles/角色名.card.png 或 .json）')
    parser.add_argument('--v1', action='store_true', help='使用 V1 格式（兼容更多前端，字段更少）')
    args = parser.parse_args()

    version = 1 if args.v1 else 2
    card = build_card(args.profile, version)
    char_name = card.get('name') or card.get('data', {}).get('name', 'character')

    if args.avatar:
        out = args.output or f'profiles/{char_name}.card.png'
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        embed_in_png(card, args.avatar, out)
    else:
        out = args.output or f'profiles/{char_name}.card.json'
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'角色卡 JSON (V{version}) 已保存: {out}', file=sys.stderr)


if __name__ == '__main__':
    main()
