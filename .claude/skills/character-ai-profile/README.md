# character-ai-profile

从对话语料自动生成 AI roleplay 角色人设档案。支持 Claude Code / Codex CLI / OpenCode / Cline / 任何 AI 编程 Agent。

## 功能

- 从游戏/视觉小说/动画的对话语料中分析单个角色的说话方式
- 提取口癖、语尾、一人称、称呼规则，每项附原文例句
- 分析角色关系（top 10-15 互动角色，每对附代表性对话）
- 自动构建世界观摘要
- 生成 AI Roleplay 检查清单（必须做 / 不能做）
- 支持导出 SillyTavern (酒馆 AI) 角色卡（V1/V2，可嵌入 PNG）

## 依赖

- Python 3.7+
- `pip install Pillow`（可选，仅酒馆卡 PNG 导出需要）

---

## 安装与使用

### Claude Code（原生支持）

复制到项目或全局 skills 目录：

```bash
# 项目级（仅当前项目）
mkdir -p .claude/skills
cp -r character-ai-profile .claude/skills/

# 全局（所有项目）
cp -r character-ai-profile ~/.claude/skills/
```

然后直接在 Claude Code 中说：

```
为ホシノ生成角色档案
```

Skill 自动触发，通过 subagent 并行分析语料。

---

### Codex CLI（OpenAI）

在项目根目录的 `AGENTS.md`（或 `codex.md`）中加入以下内容：

````markdown
## 角色档案生成

当用户要求「生成角色档案」「角色人设」「分析说话方式」时，按以下流程执行。

### 前置确认
先问用户三个问题（已回答的跳过）：
1. 角色卡用什么语言与用户对话？（中/日/英）
2. 是否保留原文例句？
3. 是否导出 SillyTavern 酒馆卡？（如需要，V1 还是 V2，以及头像图片路径）

### 执行流程

```bash
# 1. 提取台词
python3 .claude/skills/character-ai-profile/scripts/extract_lines.py "角色名" "./语料目录" > /tmp/profile_lines.jsonl

# 2. 分析口癖
python3 .claude/skills/character-ai-profile/scripts/find_patterns.py /tmp/profile_lines.jsonl > /tmp/profile_patterns.json

# 3. 提取互动
python3 .claude/skills/character-ai-profile/scripts/find_interactions.py "角色名" "./语料目录" > /tmp/profile_interactions.json

# 4. 导出酒馆卡（可选）
python3 .claude/skills/character-ai-profile/scripts/export_tavern_card.py profiles/角色名.md --avatar 头像.png
```

### 分析要求
运行脚本后，阅读原始语料文件做深度分析。不要只用脚本输出填模板。

关注维度：一人称 / 对主角称呼 / 对他人称呼 / 语尾 / 句首习惯 / 口头禅 / 日常 vs 认真模式切换 / 被夸奖反应 / 生气反应 / 害羞反应。每个特征附 2-3 句原文例句。

### 输出格式
完整档案模板见 `.claude/skills/character-ai-profile/SKILL.md` 的「档案结构」部分。
输出到 `profiles/角色名.md`。
````

---

### Cline / Roo Code（VS Code 扩展）

在项目根目录创建 `.clinerules` 文件：

```
# 角色档案生成规则

当用户要求生成角色档案或分析说话方式时：

1. 先问用户：角色卡语言（中/日/英）、是否保留原文、是否导出酒馆卡
2. 读取 .claude/skills/character-ai-profile/SKILL.md 了解完整流程
3. 运行 scripts/ 下的辅助脚本收集数据
4. 阅读原始语料做深度分析（不要只用脚本输出）
5. 输出到 profiles/角色名.md

脚本路径：.claude/skills/character-ai-profile/scripts/
- extract_lines.py — 提取角色台词
- find_patterns.py — 口癖统计
- find_interactions.py — 互动对话提取
- export_tavern_card.py — 酒馆卡导出
```

---

### Cursor

在 `.cursor/rules/` 目录下创建 `character-profile.mdc`：

```markdown
---
description: 从对话语料生成 AI roleplay 角色人设档案
globs: ["profiles/**", "ba-stories/**"]
alwaysApply: false
---

当用户要求生成角色档案或分析说话方式时，读取并遵循
.claude/skills/character-ai-profile/SKILL.md 中的完整流程。

辅助脚本位于 .claude/skills/character-ai-profile/scripts/：
- extract_lines.py "角色名" "语料目录" — 提取台词
- find_patterns.py lines.jsonl — 口癖统计
- find_interactions.py "角色名" "语料目录" — 互动提取
- export_tavern_card.py profile.md --avatar img.png — 酒馆卡

先问用户：角色卡语言、是否保留原文、是否导出酒馆卡。
分析时必须阅读原始语料，不要只用脚本输出填模板。
每个口癖/反应必须附 2-3 句原文例句。
输出到 profiles/角色名.md。
```

---

### Aider

在 `.aider.conf.yml` 中添加：

```yaml
read:
  - .claude/skills/character-ai-profile/SKILL.md
```

或在对话中直接发送：

```
/read .claude/skills/character-ai-profile/SKILL.md
请按照这个流程为ホシノ生成角色档案。辅助脚本在 .claude/skills/character-ai-profile/scripts/ 目录下。
```

---

### 通用 Agent（Hermes / AutoGPT / 自建 Agent）

复制以下 system prompt 即可让任何 Agent 使用本 skill：

```
你是一个角色人设档案生成 agent。你的任务是从对话语料中分析一个角色的说话方式和性格，生成可直接用于 AI roleplay 的人设档案。

## 工作流程

1. 确认：角色名、语料目录路径、输出语言、是否导出酒馆卡
2. 运行辅助脚本收集数据（脚本路径按实际位置替换）：
   - extract_lines.py "角色名" "语料目录" > /tmp/lines.jsonl
   - find_patterns.py /tmp/lines.jsonl > /tmp/patterns.json
   - find_interactions.py "角色名" "语料目录" > /tmp/interactions.json
3. 阅读原始语料文件做深度分析（不要只看脚本输出）
4. 撰写档案，包含以下部分：
   - 基本设定（不含 CV/设计师等 meta 信息）
   - 世界观（角色所处世界的必要背景）
   - 说话方式（一人称/称呼/语尾/口头禅，每项附 2-3 句原文例句）
   - 情景反应（被夸奖/生气/害羞等，每项附实际台词+上下文）
   - 角色关系（top 10-15，每对附对话片段和互动模式描述）
   - 角色内核（弧光/价值观/与主角关系）
   - AI Roleplay 检查清单（必须做 5-7 条 + 不能做 3-5 条）
5. 输出到 profiles/角色名.md
6. 如需酒馆卡，运行 export_tavern_card.py 导出

## 关键规则
- 所有结论必须基于语料原文，不编造
- 不包含 CV、设计师、插画师等 meta 信息
- 关系描述必须具体（不写"关系很好"，写具体互动模式）
- 中文输出时称谓本地化：先生→老师、先輩→前辈、さん→按语境
```

---

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

| 脚本 | 用途 | 独立使用 |
|------|------|---------|
| `extract_lines.py` | 提取角色全部台词 + 上下文 | `python3 scripts/extract_lines.py "角色名" "语料目录"` |
| `find_patterns.py` | 句首/句尾/一人称/高频短语 | `python3 scripts/find_patterns.py lines.jsonl` |
| `find_interactions.py` | 角色互动对话段落 | `python3 scripts/find_interactions.py "角色名" "语料目录"` |
| `export_tavern_card.py` | SillyTavern 角色卡 | `python3 scripts/export_tavern_card.py profile.md [--avatar img.png] [--v1]` |

## 输出示例

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

## 适用范围

通用设计，适用于任何有结构化对话语料的角色分析：

- 游戏剧情（蔚蓝档案、原神、FGO、崩铁等）
- 视觉小说
- 动画字幕 / 台本
- 小说对话
