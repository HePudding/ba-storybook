# 蔚蓝档案 日语剧情文本提取存档

从 Blue Archive 日服 (Yostar Japan) 客户端 Excel JSON 数据中，提取全部剧情文本与角色数据并整理为 Markdown 格式的存档。附带 JP→CN 翻译对照表和 AI 角色卡生成工具。

## 成果物

### 剧情文本

所有日语文本位于 `ba-stories/` 目录下：

| 类别 | 文件数 | 行数 |
|------|--------|------|
| 主线 | 310 | 30,829 |
| 社团故事 | 53 | 4,387 |
| 活动 | 492 | 31,846 |
| 羁绊故事 | 694 | 42,790 |
| 迷你故事 | 5 | 496 |
| MomoTalk | 223 | 12,821 条消息 |
| 角色数据 | 245 | 档案 + 台词 |
| **合计** | **2,022** | **110,348+** |

→ 详细统计和角色名一览见 [`ba-stories/README.md`](./ba-stories/README.md)

### 翻译对照表

JP→CN 翻译表覆盖角色、学校、社团、剧情标题、地名、术语等 9 个类别。翻译来源优先级：**社区译名 > 游戏数据**。

| 类别 | 总数 | 覆盖率 | 来源 |
|------|------|--------|------|
| 角色 | 240 | 100.0% | 📘 萌娘百科 (240) |
| 学校 | 14 | 100.0% | 📗 游戏数据 (8) + 📘 (6) |
| 社团 | 49 | 100.0% | 📗 (1) + 📘 (48) |
| 剧情标题 | 107 | 99.1% | 📗 (104) + 📘 (2) |
| 爱用品 | 52 | 100.0% | 📗 (52) |
| 地名 | 87 | 100.0% | 📗 (87) |
| 术语 | 24 | 95.8% | 📗 (10) + 📘 (11) + 📙 (2) |
| 活动 | 51 | 54.9% | 📙 (28)，其余国服未开 |
| 剧情角色 | 968 | 99.6% | 📗 (901) + 📘 (63) |

来源：📗 国际服游戏数据 / 📘 萌娘百科（社区标准简中） / 📙 GameKee

人类可读版：[`翻译对照表.md`](./翻译对照表.md) · 机器可读版：`utils/translation_table.json`

### AI 角色卡生成（Claude Code Skill）

从剧情语料自动分析角色说话方式、口癖、关系动态，生成 AI roleplay 人设档案，支持导出 SillyTavern 酒馆卡。

详见 [`.claude/skills/character-ai-profile/`](.claude/skills/character-ai-profile/)

## 快速开始

### 环境要求

- Python 3.7+
- `pip install opencc-python-reimplemented`（翻译管线的繁转简）
- `pip install Pillow`（可选，仅酒馆卡 PNG 导出需要）

### 剧情文本生成

```bash
cd raw-data && git pull origin jp     # 更新 JP 数据
cd ..
python3 -m utils.build_manifest       # 重建 GroupId 分类
python3 -m utils.generate_all         # 生成全部剧情 Markdown
python3 -m utils.build_readme         # 重建统计
```

### 翻译表生成

```bash
python3 -m utils.build_translation_table   # 从游戏数据提取 JP→CN
python3 -m utils.build_gaps                # 找出缺失条目
python3 -m utils.merge_translations        # 合并（社区译名覆盖游戏数据）
python3 -m utils.build_md_report           # 生成 翻译对照表.md
```

### AI 角色卡（需要 Claude Code）

```
为ホシノ生成角色档案
```

Claude Code 会自动调用 skill，通过 subagent 并行分析语料，生成完整人设档案到 `profiles/` 目录，可选导出 SillyTavern 角色卡。

## 项目结构

```
ba-story/
├── raw-data/                        # electricgoat/ba-data @ jp 分支
├── raw-data-global/                 # electricgoat/ba-data @ global 分支
├── ba-json -> raw-data/Excel        # 软链接
├── utils/                           # 数据处理管线
│   ├── load_data.py                 # 数据加载与索引
│   ├── parse_dialogue.py            # ScriptKr → 结构化对话
│   ├── format_markdown.py           # 对话 → Markdown
│   ├── generate_all.py              # 7 类剧情生成调度
│   ├── build_translation_table.py   # JP→CN 翻译提取
│   ├── merge_translations.py        # 多来源合并（社区优先）
│   ├── translation_table.json       # 翻译表（机器可读）
│   └── ...
├── ba-stories/                      # 最终产物：2,022 个 Markdown
├── .claude/skills/                  # Claude Code Skill
│   └── character-ai-profile/        # AI 角色卡生成
├── 翻译对照表.md                     # 翻译表（人类可读）
└── profiles/                        # 生成的角色档案（输出目录）
```

## 数据来源

| 来源 | 用途 |
|------|------|
| [electricgoat/ba-data @ jp](https://github.com/electricgoat/ba-data/tree/jp) | 日语剧情文本 |
| [electricgoat/ba-data @ global](https://github.com/electricgoat/ba-data/tree/global) | 多语言对译（Tw 字段） |
| [萌娘百科 · 蔚蓝档案](https://zh.moegirl.org.cn/蔚蓝档案) | 简中社区标准译名（优先） |
| [GameKee BA wiki](https://ba.gamekee.com/) | 国服简中译名 |

数据版本：380 个 Excel JSON 文件，Yostar Japan v1.68.x

## 声明

本存档仅供研究和学习用途。Blue Archive 游戏内数据版权归 Yostar 株式会社 · 上海蛮啾网络科技所有。代码部分使用 MIT 许可证。
