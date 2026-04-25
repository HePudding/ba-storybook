背景：你是蔚蓝档案（Blue Archive / ブルーアーカイブ）日服剧情翻译对照表的 subagent。
主 agent 已从游戏数据中提取了部分 JP→CN 翻译（利用 electricgoat/ba-data 的 global 分支 Tw 字段），但有不少日服最新内容、学校/社团名、活动名、术语等 global 分支尚未更新，或不以独立 LocalizeEtc 条目存在。

工作目录：`/Users/hepudding/Desktop/ba-story`

## 输入

读 `utils/translation_gaps.json`。结构如下（每类都是数组）：
```json
{
  "schools": [{"jp_full":"...","jp_short":"...","code":"..."}, ...],
  "clubs":   [{"jp":"...","code":"..."}, ...],
  "characters": [{"jp_short":"...","jp_full":"...","dev_name":"...","character_id":...,"is_variant":false}, ...],
  "scenario_characters": [{"jp":"...","nickname_jp":"..."}, ...],
  "story_titles": [{"jp":"...","category":"..."}, ...],
  "events":  [{"event_dir":"event_801","event_id":"801"}, ...],
  "terms":   [{"jp":"..."}, ...]
}
```

## 输出

写到 `utils/translation_fills_moegirl.json`：
```json
{
  "schools":   {"赤冬連邦学園": {"cn":"赤冬联邦学园","source":"moegirl","url":"..."}},
  "clubs":     {"便利屋68":    {"cn":"便利屋68","source":"moegirl","url":"..."}},
  "characters":{"ウミカ":      {"cn":"海香","cn_full":"里浜海香","source":"moegirl","url":"..."}},
  "scenario_characters": {"ヒマリ|特異現象捜査部": {"cn":"日和","nickname_cn":"特异现象搜查部","source":"moegirl","url":"..."}},
  "story_titles": {"Vol.5 百花繚乱編": {"cn":"Vol.5 百花缭乱篇","source":"moegirl"}},
  "events": {"event_801": {"jp":"SRTスペシャル","cn":"SRT特别篇","source":"moegirl","url":"..."}},
  "terms":  {"モモトーク": {"cn":"MomoTalk","source":"moegirl"}}
}
```

key 用输入 gap 条目中的 JP 字段（`scenario_characters` 用 `jp|nickname_jp` 拼接，`events` 用 `event_dir`）。
找不到的条目**不要写入**或者写 `{"cn":"","source":"not_found"}`。**不要自己翻译**。

## 数据来源

优先级：
1. https://zh.moegirl.org.cn/蔚蓝档案/角色一览 — 角色总表（JP→CN）
2. https://zh.moegirl.org.cn/蔚蓝档案/活动一览 或 https://zh.moegirl.org.cn/蔚蓝档案 主词条的活动段落 — 活动名
3. https://zh.moegirl.org.cn/蔚蓝档案 主词条 — 学校、社团、主线篇、术语
4. https://zh.moegirl.org.cn/蔚蓝档案/主线剧情 — 主线标题
5. 单个角色独立词条（如果总表没有新角色）：https://zh.moegirl.org.cn/<角色日文名>

## 高效查询策略

**不要一个 JP 名一个 HTTP 请求**。正确做法：
1. **先一次性 `WebFetch` 抓取每个核心页面**（角色一览、学校列表、活动一览、主线剧情），让 WebFetch 的 prompt 提取你要的全部表格/列表
2. 把结果在内存里匹配 gaps 的每一条
3. 只有核心页没覆盖到的（如极新角色、小众 NPC），再去单独词条页

## 特殊注意

- **角色变体（泳装/单车/新年等）**：萌娘百科通常标记为 `白子（泳装）` / `白子（骑行）`。尽量识别变体后缀的中文标准译名。
- **最新 JP 角色（如 ウミカ、イブキ、マコト、ドレス 变体）**：萌娘百科通常有条目，多尝试搜索
- **クロスオーバー角色（如 御坂美琴、食蜂操祈、佐天涙子）**：这些是《魔法禁书目录》角色，用中文官方译名 "御坂美琴" / "食蜂操祈" / "佐天泪子"（注意**涙→泪**简繁差）
- **社团名**：萌娘百科"学校/社团"段落有总表；很多社团如 "便利屋68" 中文就是 "便利屋68"，"対策委員会" → "对策委员会"
- **活动名**：活动列表按 EventContentId 有时间顺序，801=2021-02 的 "SRTスペシャル"，依次递增。活动一览页通常标注了日文原名+中文译名+日期
- **术语**：モモトーク→MomoTalk、ヘイロー→光环/光圈、キヴォトス→基沃托斯、シャーレ→沙勒、先生→老师 等 — 这些是玩家社区共识，萌娘百科主词条会提到

## 限速

萌娘百科爬虫友好度适中。
- 单次 WebFetch 抓整页 OK
- 不要在短时间内对同一域名做 >10 次请求
- 如果遇到限流或 Cloudflare 校验，切换到其他关键词/页面

## 执行步骤

1. 读 `utils/translation_gaps.json`
2. `WebFetch` 抓取 https://zh.moegirl.org.cn/蔚蓝档案/角色一览 — prompt 要求列出所有角色的 日文名、中文名、变体名、所属学校、所属社团。从 HTML 表格中尽量全提取
3. `WebFetch` 抓取 https://zh.moegirl.org.cn/蔚蓝档案 — prompt 要求提取"学校"段落、"社团"段落、"世界观/术语"段落的 JP/CN 名称对照
4. `WebFetch` 抓取 https://zh.moegirl.org.cn/蔚蓝档案/活动一览（或搜索活动列表） — 提取所有活动的 EventContentId、日文原名、中文译名、日服开始日期
5. `WebFetch` 抓取 https://zh.moegirl.org.cn/蔚蓝档案/主线剧情 — 提取主线各卷/章的 JP/CN 标题对照
6. 对仍缺失的角色（极新角色如 ウミカ、イブキ、マコト、ツバキ、丹花等），单独搜索 https://zh.moegirl.org.cn/ + 关键词
7. 所有命中的条目写入 `utils/translation_fills_moegirl.json`
8. **最后写一份 200 字以内的总结报告**：填了多少条 / 每类命中率 / 还有哪些条目没找到

## 注意

- 繁简：萌娘百科用简体中文，与国服官方简中译名基本一致（比电视版 global 分支的繁中更贴近国服）
- 主 agent 会按 source 优先级合并：game_data_tw > moegirl > gamekee；你的产出会覆盖 game_data_tw 中"没有或空"的条目
- 不要把 game_data_tw 已有翻译的条目再写入（gap 里本来就没这些）
- 不要把萌娘百科的条目直接复制长段文字；只输出 JSON 条目
- 不要自动运行 python 脚本；主 agent 负责合并

## 完成后

简短汇报（<=200 字）：
- 每类填了多少条
- 哪些条目找不到（列出前 10）
- 可能需要 GameKee 补的数量
