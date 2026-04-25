# 蔚蓝档案 日语剧情文本存档

**数据获取日期**：2026-04-22
**生成时间**：2026-04-22T14:14:34.765933Z
**数据来源**：[electricgoat/ba-data @ jp 分支](https://github.com/electricgoat/ba-data/tree/jp)

## 统计

- Markdown 文件总数：**2,022**
- 剧情对话行数：**110,348**
- MomoTalk 消息条数：**12,821**
- 已知错误数：12

### 分类统计

| 类别 | 文件数 | 对话行数 | 错误 |
|------|--------|---------|------|
| [MomoTalk](./モモトーク/) | 223 | 12821 | 0 |
| [迷你故事](./ミニストーリー/) | 5 | 496 | 0 |
| [社团故事](./グループストーリー/) | 53 | 4387 | 4 |
| [角色数据（档案+台词）](./キャラクターデータ/) | 245 | 0 | 0 |
| [主线故事](./主線/) | 310 | 30829 | 8 |
| [活动故事](./イベント/) | 492 | 31846 | 0 |
| [羁绊故事](./絆ストーリー/) | 694 | 42790 | 0 |

## 目录结构

```
ba-stories/
├── 主線/                  # 篇→章→话 层级
│   ├── 第0篇_プロローグ/
│   ├── 第1篇_対策委員会編/
│   ├── 第2篇_時計じかけの花のパヴァーヌ/
│   ├── 第3篇_エデン条約編/
│   ├── 第4篇_カルバノの兎編/
│   ├── 第5篇_百花繚乱編/
│   └── 最終編/
├── グループストーリー/       # 按社团分类的剧情
├── イベント/                # 按活动 ID 分目录（51 个活动）
├── 絆ストーリー/             # 按角色分类的羁绊故事（167 名角色）
├── ミニストーリー/           # 短篇故事
├── モモトーク/              # 角色 SNS 对话
└── キャラクターデータ/       # 角色档案、台词、爱用品一览
```

## Markdown 格式说明

每个文件带有 YAML frontmatter。正文格式：

- `**说话人**: 台词` — 角色对话
- `*旁白*` — 第三人称旁白
- `*（说话人）台词*` — 特定角色的旁白
- `*（先生（内心独白））台词*` — 先生的心理活动
- `> **先生（选择肢）**: 选项1 / 选项2` — 玩家选择
- `**【地点】**` — 场景切换

Ruby 标记展开为 `漢字（かな）` 形式。原文中的颜色标签 `[FF6666]...[-]` 已移除。

## 已知不完整项

- 主线第 1 篇第 3 章（Vol1 Ch3）：ScenarioMode 中有 ID 记录，但 ScenarioScript 中无对应脚本，8 话为空。
- 活动标题：本地化的日语名不在数据中，以 `event_<EventContentId>` 数字键显示。
- 社团故事的分组名为 `club_<volume>_<chapter>` 格式（实际社团名从各文件内角色列表推断）。
- 部分 GroupId 的 ScriptKr 仅含纯指令（TextJp 为空），已跳过。

## 角色名一览

<details>
<summary>244 名角色 ID ↔ 名称对照表（点击展开）</summary>

| ID | 名称 | 学校 | 社团 |
|----|------|------|------|
| 10000 | アル | Gehenna | Kohshinjo68 |
| 10001 | エイミ | Millennium | SPTF |
| 10002 | ハルナ | Gehenna | GourmetClub |
| 10003 | ヒフミ | Trinity | RemedialClass |
| 10004 | ヒナ | Gehenna | Fuuki |
| 10005 | ホシノ | Abydos | Countermeasure |
| 10006 | イオリ | Gehenna | Fuuki |
| 10007 | マキ | Millennium | Veritas |
| 10008 | ネル | Millennium | CleanNClearing |
| 10009 | イズミ | Gehenna | GourmetClub |
| 10010 | シロコ | Abydos | Countermeasure |
| 10011 | シュン | Shanhaijing | Meihuayuan |
| 10012 | スミレ | Millennium | TrainingClub |
| 10013 | ツルギ | Trinity | Justice |
| 10014 | イズナ | Hyakkiyako | NinpoKenkyubu |
| 10015 | アリス | Millennium | GameDev |
| 10016 | ミドリ | Millennium | GameDev |
| 10017 | チェリノ | RedWinter | RedwinterSecretary |
| 10018 | ユズ | Millennium | GameDev |
| 10019 | アズサ | Trinity | RemedialClass |
| 10020 | コハル | Trinity | RemedialClass |
| 10021 | アズサ | Trinity | RemedialClass |
| 10022 | ヒナ | Gehenna | Fuuki |
| 10023 | イオリ | Gehenna | Fuuki |
| 10024 | シロコ | Abydos | Countermeasure |
| 10025 | シュン | Shanhaijing | Meihuayuan |
| 10026 | ネル | Millennium | CleanNClearing |
| 10027 | カリン | Millennium | CleanNClearing |
| 10028 | アスナ | Millennium | CleanNClearing |
| 10029 | ナツ | Trinity | HoukagoDessert |
| 10030 | チナツ | Gehenna | Fuuki |
| 10031 | アル | Gehenna | Kohshinjo68 |
| 10032 | ムツキ | Gehenna | Kohshinjo68 |
| 10033 | ワカモ | Hyakkiyako | EmptyClub |
| 10034 | ミモリ | Hyakkiyako | Shugyobu |
| 10035 | ウイ | Trinity | BookClub |
| 10036 | ヒナタ | Trinity | SisterHood |
| 10037 | マリナ | RedWinter | RedwinterSecretary |
| 10038 | ミヤコ | SRT | RabbitPlatoon |
| 10039 | ミユ | SRT | RabbitPlatoon |
| 10040 | ツクヨ | Hyakkiyako | NinpoKenkyubu |
| 10041 | ミサキ | Arius | AriusSqud |
| 10042 | アツコ | Arius | AriusSqud |
| 10043 | ワカモ | Hyakkiyako | EmptyClub |
| 10044 | ノノミ | Abydos | Countermeasure |
| 10045 | ホシノ | Abydos | Countermeasure |
| 10046 | イズナ | Hyakkiyako | NinpoKenkyubu |
| 10047 | チセ | Hyakkiyako | Onmyobu |
| 10048 | サオリ | Arius | AriusSqud |
| 10049 | カズサ | Trinity | HoukagoDessert |
| 10050 | ココナ | Shanhaijing | Meihuayuan |
| 10051 | ウタハ | Millennium | Engineer |
| 10052 | ノア | Millennium | TheSeminar |
| 10053 | ユウカ | Millennium | TheSeminar |
| 10054 | マリー | Trinity | SisterHood |
| 10055 | シグレ | RedWinter | Class227 |
| 10056 | セリナ | Trinity | KnightsHospitaller |
| 10057 | ハルナ | Gehenna | GourmetClub |
| 10058 | ミネ | Trinity | KnightsHospitaller |
| 10059 | ミカ | Trinity | TeaParty |
| 10060 | メグ | Gehenna | HotSpringsDepartment |
| 10061 | サクラコ | Trinity | SisterHood |
| 10062 | トキ | Millennium | CleanNClearing |
| 10063 | コユキ | Millennium | TheSeminar |
| 10064 | カヨコ | Gehenna | Kohshinjo68 |
| 10065 | カホ | Hyakkiyako | Onmyobu |
| 10066 | アリス | Millennium | GameDev |
| 10067 | トキ | Millennium | CleanNClearing |
| 10068 | レイサ | Trinity | TrinityVigilance |
| 10069 | ルミ | Shanhaijing | BlackTortoisePromenade |
| 10070 | ミナ | Shanhaijing | Genryumon |
| 10071 | ミヤコ | SRT | RabbitPlatoon |
| 10072 | サキ | SRT | RabbitPlatoon |
| 10073 | ウイ | Trinity | BookClub |
| 10074 | ハナコ | Trinity | RemedialClass |
| 10075 | メル | RedWinter | KnowledgeLiberationFront |
| 10076 | コトリ | Millennium | Engineer |
| 10077 | イチカ | Trinity | Justice |
| 10078 | カスミ | Gehenna | HotSpringsDepartment |
| 10079 | 美琴 | Tokiwadai | EmptyClub |
| 10080 | 操祈 | Tokiwadai | EmptyClub |
| 10081 | ユカリ | Hyakkiyako | Hyakkayouran |
| 10082 | レンゲ | Hyakkiyako | Hyakkayouran |
| 10083 | キキョウ | Hyakkiyako | Hyakkayouran |
| 10084 | コタマ | Millennium | Veritas |
| 10085 | ハレ | Millennium | Veritas |
| 10086 | ヒナ | Gehenna | Fuuki |
| 10087 | アコ | Gehenna | Fuuki |
| 10088 | カヨコ | Gehenna | Kohshinjo68 |
| 10089 | アル | Gehenna | Kohshinjo68 |
| 10090 | ウミカ | Hyakkiyako | MatsuriOffice |
| 10091 | カズサ | Trinity | HoukagoDessert |
| 10092 | ヨシミ | Trinity | HoukagoDessert |
| 10093 | キララ | Gehenna | ShinySparkleSociety |
| 10094 | モモイ | Millennium | GameDev |
| 10095 | ミドリ | Millennium | GameDev |
| 10096 | カンナ | Valkyrie | PublicPeaceBureau |
| 10097 | モエ | SRT | RabbitPlatoon |
| 10098 | ホシノ | Abydos | Countermeasure |
| 10099 | ホシノ | Abydos | Countermeasure |
| 10100 | シロコ | Abydos | AbydosStudentCouncil |
| 10101 | サオリ | Arius | AriusSqud |
| 10102 | ヒヨリ | Arius | AriusSqud |
| 10103 | マリナ | RedWinter | RedwinterSecretary |
| 10104 | レイジョ | Shanhaijing | BlackTortoisePromenade |
| 10105 | マリー | Trinity | SisterHood |
| 10106 | サクラコ | Trinity | SisterHood |
| 10107 | チアキ | Gehenna | PandemoniumSociety |
| 10108 | ユウカ | Millennium | TheSeminar |
| 10109 | ノア | Millennium | TheSeminar |
| 10110 | セイア | Trinity | TeaParty |
| 10111 | ネル | Millennium | CleanNClearing |
| 10112 | アスナ | Millennium | CleanNClearing |
| 10113 | セナ | Gehenna | Emergentology |
| 10114 | ジュリ | Gehenna | FoodService |
| 10115 | レイ | Millennium | TrainingClub |
| 10116 | サオリ | Arius | AriusSqud |
| 10117 | ヒカリ | Highlander | CentralControlCenter |
| 10118 | ノゾミ | Highlander | CentralControlCenter |
| 10119 | ナグサ | Hyakkiyako | Hyakkayouran |
| 10120 | ナツ | Trinity | HoukagoDessert |
| 10121 | ユカリ | Hyakkiyako | Hyakkayouran |
| 10122 | ミカ | Trinity | TeaParty |
| 10123 | セイア | Trinity | TeaParty |
| 10124 | ハスミ | Trinity | Justice |
| 10125 | エリ | WildHunt | OccultClub |
| 10126 | カノエ | WildHunt | OccultClub |
| 13000 | アカネ | Millennium | CleanNClearing |
| 13001 | チセ | Hyakkiyako | Onmyobu |
| 13002 | アカリ | Gehenna | GourmetClub |
| 13003 | ハスミ | Trinity | Justice |
| 13004 | ノノミ | Abydos | Countermeasure |
| 13005 | カヨコ | Gehenna | Kohshinjo68 |
| 13006 | ムツキ | Gehenna | Kohshinjo68 |
| 13007 | ジュンコ | Gehenna | GourmetClub |
| 13008 | セリカ | Abydos | Countermeasure |
| 13009 | ツバキ | Hyakkiyako | Shugyobu |
| 13010 | ユウカ | Millennium | TheSeminar |
| 13011 | モモイ | Millennium | GameDev |
| 13012 | キリノ | Valkyrie | anzenkyoku |
| 13013 | モミジ | RedWinter | KnowledgeLiberationFront |
| 13014 | レンゲ | Hyakkiyako | Hyakkayouran |
| 16000 | ハルカ | Gehenna | Kohshinjo68 |
| 16001 | アスナ | Millennium | CleanNClearing |
| 16002 | コトリ | Millennium | Engineer |
| 16003 | スズミ | Trinity | TrinityVigilance |
| 16004 | フィーナ | Hyakkiyako | MatsuriOffice |
| 16005 | ツルギ | Trinity | Justice |
| 16006 | イズミ | Gehenna | GourmetClub |
| 16007 | トモエ | RedWinter | RedwinterSecretary |
| 16008 | フブキ | Valkyrie | anzenkyoku |
| 16009 | ミチル | Hyakkiyako | NinpoKenkyubu |
| 16010 | ヒビキ | Millennium | Engineer |
| 16011 | ハスミ | Trinity | Justice |
| 16012 | ジュンコ | Gehenna | GourmetClub |
| 16013 | コハル | Trinity | RemedialClass |
| 16014 | イブキ | Gehenna | PandemoniumSociety |
| 16015 | アイリ | Trinity | HoukagoDessert |
| 16016 | ミネ | Trinity | KnightsHospitaller |
| 16017 | アオバ | Highlander | FreightLogisticsDepartment |
| 19002 |  | Hyakkiyako | NinpoKenkyubu |
| 19003 |  | Trinity | SisterHood |
| 19004 |  | Gehenna | IndeGEHENNA |
| 19005 |  | Hyakkiyako | NinpoKenkyubu |
| 19006 |  | Trinity | RemedialClass |
| 20000 | ヒビキ | Millennium | Engineer |
| 20001 | カリン | Millennium | CleanNClearing |
| 20002 | サヤ | Shanhaijing | Endanbou |
| 20003 | マシロ | Trinity | Justice |
| 20004 | マシロ | Trinity | Justice |
| 20005 | ヒフミ | Trinity | RemedialClass |
| 20006 | サヤ | Shanhaijing | Endanbou |
| 20007 | ミク | ETC | EmptyClub |
| 20008 | アコ | Gehenna | Fuuki |
| 20009 | チェリノ | RedWinter | RedwinterSecretary |
| 20010 | ノドカ | RedWinter | Class227 |
| 20011 | セリカ | Abydos | Countermeasure |
| 20012 | セナ | Gehenna | Emergentology |
| 20013 | チヒロ | Millennium | Veritas |
| 20014 | サキ | SRT | RabbitPlatoon |
| 20015 | カエデ | Hyakkiyako | Shugyobu |
| 20016 | イロハ | Gehenna | PandemoniumSociety |
| 20017 | ヒヨリ | Arius | AriusSqud |
| 20018 | モエ | SRT | RabbitPlatoon |
| 20019 | アカネ | Millennium | CleanNClearing |
| 20020 | ヒマリ | Millennium | SPTF |
| 20021 | ハナエ | Trinity | KnightsHospitaller |
| 20022 | フウカ | Gehenna | FoodService |
| 20023 | カンナ | Valkyrie | PublicPeaceBureau |
| 20024 | ナギサ | Trinity | TeaParty |
| 20025 | ハルカ | Gehenna | Kohshinjo68 |
| 20026 | ミノリ | RedWinter | LaborParty |
| 20027 | シロコ | Abydos | Countermeasure |
| 20028 | ヒナタ | Trinity | SisterHood |
| 20029 | ミモリ | Hyakkiyako | Shugyobu |
| 20030 | ハルナ | Gehenna | GourmetClub |
| 20031 | シグレ | RedWinter | Class227 |
| 20032 | エイミ | Millennium | SPTF |
| 20033 | マコト | Gehenna | PandemoniumSociety |
| 20034 | アカリ | Gehenna | GourmetClub |
| 20035 | ツバキ | Hyakkiyako | Shugyobu |
| 20036 | セリカ | Abydos | Countermeasure |
| 20037 | フブキ | Valkyrie | anzenkyoku |
| 20038 | トモエ | RedWinter | RedwinterSecretary |
| 20039 | キサキ | Shanhaijing | Genryumon |
| 20040 | サツキ | Gehenna | PandemoniumSociety |
| 20041 | リオ | Millennium | TheSeminar |
| 20042 | マキ | Millennium | Veritas |
| 20043 | イズミ | Gehenna | GourmetClub |
| 20044 | スミレ | Millennium | TrainingClub |
| 20045 | フィーナ | Hyakkiyako | MatsuriOffice |
| 20046 | ニヤ | Hyakkiyako | Onmyobu |
| 20047 | キキョウ | Hyakkiyako | Hyakkayouran |
| 20048 | ナギサ | Trinity | TeaParty |
| 20049 | ミサキ | Arius | AriusSqud |
| 23000 | アイリ | Trinity | HoukagoDessert |
| 23001 | フウカ | Gehenna | FoodService |
| 23002 | ハナエ | Trinity | KnightsHospitaller |
| 23003 | ハレ | Millennium | Veritas |
| 23004 | ウタハ | Millennium | Engineer |
| 23005 | アヤネ | Abydos | Countermeasure |
| 23006 | シズコ | Hyakkiyako | MatsuriOffice |
| 23007 | ハナコ | Trinity | RemedialClass |
| 23008 | マリー | Trinity | SisterHood |
| 26000 | チナツ | Gehenna | Fuuki |
| 26001 | コタマ | Millennium | Veritas |
| 26002 | ジュリ | Gehenna | FoodService |
| 26003 | セリナ | Trinity | KnightsHospitaller |
| 26004 | シミコ | Trinity | BookClub |
| 26005 | ヨシミ | Trinity | HoukagoDessert |
| 26006 | ノドカ | RedWinter | Class227 |
| 26007 | アヤネ | Abydos | Countermeasure |
| 26008 | シズコ | Hyakkiyako | MatsuriOffice |
| 26009 | ユズ | Millennium | GameDev |
| 26010 | ミユ | SRT | RabbitPlatoon |
| 26011 | 涙子 | Sakugawa | EmptyClub |
| 26012 | キリノ | Valkyrie | anzenkyoku |
| 26013 | アツコ | Arius | AriusSqud |
| 26014 | カリン | Millennium | CleanNClearing |
| 26015 | イチカ | Trinity | Justice |
| 29003 |  | Trinity | SisterHood |
| 100050001 | ホシノ |  |  |
| 100980001 | ホシノ |  |  |
| 100990001 | ホシノ |  |  |

</details>

## 错误日志（按类别）

### 社团故事

```
empty club_13_1 gid=2302
empty club_23_1 gid=3301
empty club_23_1 gid=3302
empty club_23_1 gid=3303
```

### 主线

```
empty scenario vol1/ch3/ep1 gid=13010
empty scenario vol1/ch3/ep2 gid=13020
empty scenario vol1/ch3/ep3 gid=13030
empty scenario vol1/ch3/ep4 gid=13040
empty scenario vol1/ch3/ep5 gid=13050
empty scenario vol1/ch3/ep6 gid=13060
empty scenario vol1/ch3/ep7 gid=13070
empty scenario vol1/ch3/ep8 gid=13080
```


---

*本数据基于 Yostar Japan 版 Blue Archive 的精翻译（Japanese Yostar translation）。数据提取管线见 `utils/`。*
