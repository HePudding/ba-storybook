# 蔚蓝档案日服剧情文本提取 & 章节整理 实施计划

## Context

用户需要从 **Blue Archive 日服客户端数据（TableBundles / FlatBuffers）** 中提取**全部**剧情与角色文本的日文（Yostar 精翻）版本，按类型（主線 / グループ / イベント / モモトーク / 絆 / ミニ）和章节整理成可读的 Markdown 文件。

**工作目录**：`/Users/hepudding/Desktop/ba-story/`（当前为空）

**核心挑战**：
- 数据量极大（几十万行对话），必须**大量派遣 subagent 保持主上下文清洁**
- 字段名、GroupId 命名规则只能靠实地探查，不能凭推测写代码
- 输出 Markdown 需要符合统一风格（对话 / 选择肢 / 旁白）

**外部工具调研结论**（已通过 WebFetch 验证）：
| 工具 | 状态 | 角色 |
|---|---|---|
| arisu-archive/bluearchive-data | 活跃，持续自动更新 | **首选捷径**：预解密 JSON |
| Deathemonic/BA-AD | 活跃 | 备选：Rust 下载器，下载加密 TableBundles |
| Deathemonic/BA-FB | 活跃，v1.7.3 (2025-10) | 备选：FlatBuffers 解密/导出 JSON |
| K0lb3/Asset-Downloader | **已弃用（2023-10 存档）** | 不采用 |

## 架构原则

**主 agent**：只做调度、环境准备、数据探查、工具脚本编写、最终验证。
**Subagent**：承担全部重复性的文件处理（按剧情类型切分，单类型数据量过大时再分批）。
每个 subagent 的 prompt **自包含**：数据路径、utils 路径、字段映射路径、输出目录、规则、格式示例全部内嵌。

---

## Phase 1 — 获取 JSON 数据（主 agent，串行）

### 1.1 先走捷径：arisu-archive

```bash
cd /Users/hepudding/Desktop/ba-story
git clone --depth=1 https://github.com/arisu-archive/bluearchive-data.git raw-data
ls raw-data/
```

**验收条件**：`raw-data/` 下能找到（或通过 `find` 定位到）日服版本且包含以下至少 8 个表：
- ScenarioScriptExcelTable
- ScenarioCharacterNameExcelTable
- LocalizeScenarioExcelTable
- AcademyMessangerExcelTable
- LocalizeCharProfileExcelTable
- CharacterDialogExcelTable
- FavorItemExcelTable + LocalizeFavorItemExcelTable
- CharacterExcelTable

仓库目录层级**按实际看到的为准**（可能是 `Excel/jp/xxx.json` 或 `japan/Excel/xxx.json`）。用 `find raw-data -name 'ScenarioScriptExcelTable*' -maxdepth 5` 确认实际路径。

**若 JSON 是日文文本**（抽查前 3 条记录搜索假名/汉字字段）→ **直接进入 Phase 3**，跳过 1.2 和 Phase 2。

### 1.2 备选：BA-AD + BA-FB

仅在 1.1 的 arisu-archive 数据不全或不含日服文本时启用：

```bash
# 需要 rustup 已安装；macOS 可用 brew install rustup && rustup-init -y
cargo install --git https://github.com/Deathemonic/BA-AD --locked
cargo install --git https://github.com/Deathemonic/BA-FB --locked

cd /Users/hepudding/Desktop/ba-story
baad download japan --tables --output ./encrypted-tables
bafb dump japan -i ./encrypted-tables -o ./raw-data
```

**若 Rust 编译失败**，记录错误进 `setup-errors.log`，回退至 arisu-archive 部分可用的子集，缺失的表标注在最终 README 的「已知缺口」中。不要自行写下载/解密代码。

### 1.3 统一入口

无论走哪条路径，最终令 `./ba-json/` 为所有 JSON 的扁平化软链或直接目录（用 `ln -s` 不要复制，数据量大）：

```bash
mkdir -p ./ba-json
# 根据实际目录结构把日服 Excel JSON 都链接过来
```

---

## Phase 2 — 数据结构探查（主 agent，最关键）

**绝不在未查阅实际 JSON 前写处理代码。** 用户 prompt 列的字段名全部是推测。

### 2.1 抽样查看

对以下每个文件用 `Read`（或 `jq '.[:3]'` via Bash）查看**前 3-5 条记录**：

1. `ScenarioScriptExcelTable.json`
   - 日文文本字段真实 key（候选：`TextJp` / `ScriptKr` / `LocalizeJP` / `DialogJp`）
   - 角色 ID 字段名
   - GroupId 命名规律
   - 旁白、选择肢、系统指令怎么标记
2. `ScenarioCharacterNameExcelTable.json` —— 角色 ID → 日文名映射字段
3. `AcademyMessangerExcelTable.json` —— MomoTalk 结构（可能有分支、图片、Sticker）
4. `CharacterDialogExcelTable.json` —— 大厅/战斗/编成台词的分类字段
5. `FavorItemExcelTable.json` + `LocalizeFavorItemExcelTable.json`
6. `LocalizeCharProfileExcelTable.json` —— 角色 profile 字段（身长/生日/趣味/自我介绍）
7. `CharacterExcelTable.json` —— 学校/社团归属字段
8. `LocalizeScenarioExcelTable.json` —— 章节/话标题的日文本地化

### 2.2 产出 `utils/field_mapping.json`

格式示例（**具体 key 以实际为准**，下方仅占位）：

```json
{
  "ScenarioScript": {
    "group_id": "GroupId",
    "script_kr": "ScriptKr",
    "text_jp": "TextJp",
    "character_name": "CharacterName",
    "bgm_id": "BGMId",
    "_notes": "旁白用 CharacterName=0 标记；选择肢 TextJp 字段以 [s]xxx[/s] 包裹"
  },
  "CharacterName": { "character_id": "CharacterId", "name_jp": "NameJp", "nickname_jp": "NicknameJp" },
  "AcademyMessanger": { "..." : "..." },
  "CharacterDialog": { "..." : "..." },
  "FavorItem": { "..." : "..." },
  "LocalizeCharProfile": { "..." : "..." },
  "Character": { "..." : "..." },
  "LocalizeScenario": { "..." : "..." }
}
```

### 2.3 产出 `utils/group_rules.json`

GroupId 分类规则**不要猜**，做如下实验：

```bash
jq -r '.[] | .GroupId' ba-json/ScenarioScriptExcelTable.json | sort -u > /tmp/all_groups.txt
head -50 /tmp/all_groups.txt; tail -50 /tmp/all_groups.txt
```

观察前缀/数字段规律，列出主線 / グループ / イベント / 絆 / ミニ 的识别规则。

```json
{
  "main_story": { "pattern": "^Main", "examples": ["..."] },
  "group_story": { "pattern": "...", "examples": ["..."] },
  "event_story": { "pattern": "^Event", "examples": ["..."] },
  "momotalk": { "source_table": "AcademyMessanger" },
  "bond_story": { "pattern": "^Favor", "examples": ["..."] },
  "mini_story": { "pattern": "^Mini", "examples": ["..."] },
  "_unclassified_samples": ["列出无法匹配的 GroupId 前 20 个作为 review"]
}
```

---

## Phase 3 — 共用工具脚本（主 agent，使用 Python 3）

**目录布局**：

```
ba-story/
├── raw-data/            # Phase 1 克隆的原始仓库（只读）
├── ba-json/             # Phase 1 链接过来的统一入口
├── utils/
│   ├── field_mapping.json      # Phase 2 产出
│   ├── group_rules.json        # Phase 2 产出
│   ├── load_data.py            # JSON/角色名映射/章节元数据 加载器
│   ├── parse_dialogue.py       # 单个 GroupId 原始数据 → 结构化对话流
│   ├── format_markdown.py      # 结构化对话 → Markdown 文本
│   └── character_info.py       # 角色 profile/爱用品/学校社团 加载器
├── ba-stories/          # 最终输出
└── subagent-prompts/    # 每个 subagent 的自包含 prompt 档案（便于调度和复用）
```

### 3.1 `utils/load_data.py`

必须暴露：
- `load_field_mapping() -> dict`
- `load_group_rules() -> dict`
- `load_character_names() -> dict[int, str]` —— 含 NPC fallback：`NPC_{id}`
- `load_scenario_titles() -> dict[group_id, {title, chapter, volume}]`
- `load_scripts_by_group(group_id) -> list[row]` —— 按顺序（字段名以 `field_mapping` 中指定的 order 为准）

使用 `functools.lru_cache` 缓存。按需懒加载，**避免一次性把 ScenarioScriptExcelTable 全部读入**（可用流式解析或按 GroupId 建索引后分段读）。

### 3.2 `utils/parse_dialogue.py`

`parse_group(group_id) -> ParsedScene` 返回的结构：

```python
{
  "group_id": str,
  "title_jp": str | None,
  "lines": [
    {"type": "dialogue", "speaker": "シロコ", "text": "..."},
    {"type": "narration", "text": "..."},
    {"type": "choice", "options": ["はい", "いいえ"]},
    {"type": "system", "text": "..."}    # BGM/场景切换等，可选保留
  ]
}
```

规则：
- 角色 ID 缺失 → `NPC_{id}`
- 选择肢字段有特殊标记（Phase 2 查明） → 展开成 `options` 列表
- 旁白（CharacterName=0 或类似） → `type=narration`
- 连续同角色多行合并为同一 dialogue 还是分开？**一行一个 dialogue**（保真优先）

### 3.3 `utils/format_markdown.py`

对话格式：
```
**角色名**: 台词内容

> 先生（選択肢）: 选项1 / 选项2

*ナレーション: 旁白文本*
```

文件头 YAML 元数据：
```markdown
---
title: "話タイトル"
chapter: "所属章节"
type: "main_story | group_story | event | momotalk | bond | mini"
group_id: "Main_01_01"
characters: ["シロコ", "ホシノ"]
---

# 話タイトル

<对话正文>
```

### 3.4 `utils/character_info.py`

加载单个角色的 profile、爱用品、全类 dialog 台词；供 Subagent G 使用。

### 3.5 自测

写一个 `utils/_smoke_test.py`，随机挑 3 个 group_id 跑通 parse + format，打印结果到 stdout，肉眼检查是否可读。

---

## Phase 4 — 派遣 Subagent 处理各类型（主 agent 调度）

### 调度原则
- **按用户指定优先级顺序启动**：主線 → モモトーク → 絆 → グループ → キャラクター → イベント → ミニ
- 低相互依赖的 subagent 可**并行**（同一 Agent 消息内多个 tool call）；数据量大的（イベント）必要时**串行分批**
- 每个 subagent 使用 `subagent_type=general-purpose`，prompt 落盘到 `subagent-prompts/<letter>_<name>.md` 再读入，便于复用和复跑

### Subagent prompt 通用模板（每个 subagent 必含）

```
背景：你是 Blue Archive 日服剧情文本提取任务的 subagent。
工作目录：/Users/hepudding/Desktop/ba-story

必读文件（先全部读一遍再动手）：
- utils/field_mapping.json
- utils/group_rules.json
- utils/load_data.py, utils/parse_dialogue.py, utils/format_markdown.py

必须复用这些 util，禁止另写解析逻辑。

你负责的类型：<TYPE>
筛选规则：<FROM group_rules.json>
输出目录：./ba-stories/<DIR>/
目录结构：<见下>
章节/话标题：优先从 LocalizeScenarioExcelTable 查找；查不到用 GroupId fallback
错误日志：追加到 ./ba-stories/<DIR>/_errors.log
统计产出：./ba-stories/<DIR>/_stats.json，含 { files: N, lines: M, groups: [...], missing_titles: [...] }

完成后简短汇报（不超过 200 字）：产出文件数、台词数、已知问题。
不要把原始 JSON 内容贴进对话。
```

### Subagent A：主線ストーリー

```
目录结构：
ba-stories/主線/
├── 第1篇_対策委員会/{第1章, 第2章, ...}/{01話.md, ...}
├── 第2篇_時計じかけの花のパヴァーヌ/
├── 第3篇_エデン条約/
├── 第4篇_カルバノの兎/
├── 第5篇_百花繚乱/
├── 最終編/
└── Extra/
```

篇/章/话层级从 `LocalizeScenarioExcelTable` + `ScenarioModeExcelTable` 推断；查不到时层级名用 GroupId。

### Subagent B：グループストーリー

```
ba-stories/グループストーリー/
├── 便利屋68/01話.md ...
├── ゲーム開発部/
├── 補習授業部/
├── 美食研究会/
├── 温泉開発部/
├── 正義実現委員会/
├── 忍術研究部/
├── トレーニングクラブ/
└── ...（全部社团）
```

社团归属通过 `CharacterExcelTable` + 角色参演关系推断；需要时跨表 join。

### Subagent C：イベントストーリー（**预期需要分批**）

```
ba-stories/イベント/<活动日文名>/01話.md
```

先统计活动数量。**> 30 个活动时**，主 agent 分批派 subagent（每批 20-30 个活动，传入白名单 GroupId 列表）。

### Subagent D：モモトーク

```
ba-stories/モモトーク/<角色名>.md
```

每角色单文件，多段按好感等级 / 解锁顺序排列。
清楚标注发言方（角色 / 先生）、选择肢分支、贴图 / 图片占位（若 AcademyMessanger 有 MessageType 区分）。

### Subagent E：絆ストーリー

```
ba-stories/絆ストーリー/<角色名>.md
```

单文件含该角色所有好感等级解锁剧情，按 Favor Level 升序。

### Subagent F：ミニストーリー

```
ba-stories/ミニストーリー/<剧情名>/01話.md
```

### Subagent G：キャラクターデータ（非剧情）

不走 `parse_dialogue`，改用 `character_info`，为每个角色生成：

```markdown
# 角色名

## プロフィール
- フルネーム / 学校 / 部活 / 年齢 / 誕生日 / 身長 / 趣味
- デザイナー / イラストレーター / CV
- 自己紹介：...

## 愛用品
- <礼物名>：<描述>（喜好度 S/A/B）

## ロビー台詞
- 通常：...
- 好感度UP後：...

## 戦闘台詞
- スキル / EX / 勝利 / 撤退 / 編成時 / カフェ
```

变体角色（シロコ（ライディング）等）保留独立文件，但文件内部写明「本体：シロコ」。

---

## Phase 5 — 汇总验证（主 agent 或最终 subagent）

### 5.1 汇总
```bash
# 合并所有 _stats.json
find ba-stories -name '_stats.json' -exec cat {} \; | jq -s 'reduce .[] as $x (...)' > ba-stories/_aggregate.json
```

### 5.2 产出 `ba-stories/README.md`

```markdown
# 蔚蓝档案 日本語剧情テキスト アーカイブ

## 統計
- 総ファイル数 / 総台詞数 / データ取得日：2026-04-22
- データソース：<arisu-archive commit hash 或 BA-AD 版本>

## 目次
- [主線](主線/) / [グループストーリー](グループストーリー/) / [イベント](イベント/)
- [モモトーク](モモトーク/) / [絆ストーリー](絆ストーリー/) / [ミニストーリー](ミニストーリー/)
- [キャラクターデータ](キャラクターデータ/)

## 角色名一覧
| ID | 日文名 | 変体 |
|----|--------|------|
| ... | ... | ... |

## 已知缺口
<从各 _errors.log 汇总的条目>
```

### 5.3 随机抽查（主 agent 自己做，不派 subagent）

用 `find ba-stories -name '*.md' | shuf -n 5` 随机挑 5 个文件 Read 检查：
- YAML 头完整
- 对话格式正确（**粗体角色名** / *ナレーション* / 选择肢）
- 没有 `NPC_{id}` 泛滥（< 5% 行数为阈值）
- 日文没有乱码

### 5.4 错误汇总
```bash
find ba-stories -name '_errors.log' -exec cat {} + > ba-stories/errors.log
```

---

## 关键文件（供执行者快速定位）

| 路径 | 作用 | 何时产出 |
|---|---|---|
| `raw-data/` | 原始 JSON 克隆 | Phase 1.1 |
| `ba-json/` | 统一 JSON 入口 | Phase 1.3 |
| `utils/field_mapping.json` | **所有 subagent 依赖** | Phase 2.2 |
| `utils/group_rules.json` | GroupId 分类 | Phase 2.3 |
| `utils/load_data.py` | 数据加载器 | Phase 3.1 |
| `utils/parse_dialogue.py` | 对话解析 | Phase 3.2 |
| `utils/format_markdown.py` | Markdown 生成 | Phase 3.3 |
| `utils/character_info.py` | 角色元数据 | Phase 3.4 |
| `subagent-prompts/*.md` | 各 subagent 的自包含 prompt | Phase 4 前 |
| `ba-stories/` | 最终成品 | Phase 4 各 subagent |
| `ba-stories/README.md` | 入口 | Phase 5.2 |

## 关键注意事项（再次强调）

1. **字段名以实际 JSON 为准**，用户 prompt 列出的字段名全是推测
2. **每个 subagent 只加载自己需要的 GroupId**，用 jq 预先切片或让 `load_data.py` 懒加载
3. **主上下文保持清洁**：主 agent 只读小样本，大批量处理全部派 subagent
4. **错误不 crash**：单条记录解析失败 → 记 error log，继续下一条
5. **角色名变体**（水着 / 正月 / ライディング 等）在文件名保留区分，内容开头注明本体
6. **不要下载 AssetBundles**，只要 TableBundles（剧情文本在这里面）
7. **不新增工具仓库依赖**：只用 BA-AD / BA-FB / arisu-archive + Python 标准库 + jq

---

## 验证 end-to-end 成功的标准

1. `find ba-stories -name '*.md' | wc -l` ≥ 500（保守下限；实际应该数千）
2. 随机抽 5 个 .md 文件打开，日文对话完整、可读、格式一致
3. `ba-stories/README.md` 统计数字与 `_aggregate.json` 对齐
4. `ba-stories/errors.log` 中没有「整章缺失」级别错误
5. 7 个顶级目录（主線/グループ/イベント/モモトーク/絆/ミニ/キャラクター）全部存在且非空
