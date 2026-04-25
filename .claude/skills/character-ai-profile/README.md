# character-ai-profile

Claude Code Skill：从对话语料自动生成 AI roleplay 角色人设档案。

## 功能

- 从游戏/视觉小说/动画的对话语料中分析单个角色的说话方式
- 提取口癖、语尾、一人称、称呼规则，每项附原文例句
- 分析角色关系（top 10-15 互动角色，每对附代表性对话）
- 自动构建世界观摘要
- 生成 AI Roleplay 检查清单（必须做 / 不能做）
- 支持导出 SillyTavern (酒馆 AI) 角色卡（V1/V2，可嵌入 PNG）

## 安装

复制整个目录到你的项目 `.claude/skills/` 下：

```bash
cp -r character-ai-profile /你的项目/.claude/skills/
```

或者全局安装（所有项目可用）：

```bash
cp -r character-ai-profile ~/.claude/skills/
```

## 使用

在 Claude Code 中直接说：

```
为ホシノ生成角色档案
```

```
generate profile for Hoshino
```

```
分析シロコ的说话方式
```

Skill 会先问你三个问题：
1. 角色卡用什么语言对话（中/日/英）
2. 是否保留原文例句
3. 是否导出酒馆卡（V1/V2），如需要请提供头像

然后自动通过 subagent 并行分析语料，输出完整 Markdown 档案到 `profiles/` 目录。

## 语料格式要求

支持两种格式，自动检测：

**Markdown（按章节）**
```
**角色名**: 台词内容
*（角色名）旁白内容*
> **先生（選択肢）**: 选项1 / 选项2
```

**JSONL（按行）**
```jsonl
{"speaker": "角色名", "text": "台词", "source": "文件路径"}
```

## 辅助脚本

| 脚本 | 用途 |
|------|------|
| `scripts/extract_lines.py` | 提取指定角色的全部台词 + 上下文 |
| `scripts/find_patterns.py` | 句首/句尾/一人称/高频短语统计 |
| `scripts/find_interactions.py` | 角色互动对话段落提取 |
| `scripts/export_tavern_card.py` | 导出 SillyTavern 角色卡（V1/V2 + PNG） |

脚本可独立使用：

```bash
# 提取角色台词
python3 scripts/extract_lines.py "ホシノ" "./ba-stories" > lines.jsonl

# 分析口癖
python3 scripts/find_patterns.py lines.jsonl

# 找互动对话
python3 scripts/find_interactions.py "ホシノ" "./ba-stories"

# 导出酒馆卡
python3 scripts/export_tavern_card.py profiles/ホシノ.md --avatar avatar.png
```

## 输出示例

生成的档案结构：

```
# 角色名
## 基本设定
## 世界观
## 说话方式（一人称/称呼/语尾/口头禅，每项附例句）
## 情景反应（被夸奖/生气/害羞等，每项附实际台词）
## 角色关系（top 10-15，每对附对话片段）
## 角色内核（弧光/价值观/与主角关系）
## 大厅/日常台词
## AI Roleplay 检查清单
```

## 依赖

- Python 3.7+
- `Pillow`（仅酒馆卡 PNG 导出需要）：`pip install Pillow`

## 适用范围

虽然随 ba-story 项目开发，但 skill 本身是通用设计，适用于任何有结构化对话语料的角色分析：
- 游戏剧情（蔚蓝档案、原神、FGO 等）
- 视觉小说
- 动画字幕/台本
- 小说对话

只需按上述格式准备语料即可。
