# Blue Archive 日本語ストーリー 抽出アーカイブ

Blue Archive 日本語サーバー (Yostar Japan) のクライアント Excel JSON データから、剧情テキストとキャラクターデータを Markdown 形式で抽出したアーカイブ。

## 成果物

すべての日本語テキストは `ba-stories/` 配下：

| カテゴリ | ファイル数 | 行数 |
|---------|-----------|-----|
| 主線 | 310 | 30,829 |
| グループストーリー | 53 | 4,387 |
| イベント | 492 | 31,846 |
| 絆ストーリー | 694 | 42,790 |
| ミニストーリー | 5 | 496 |
| モモトーク | 223 | 12,821 msgs |
| キャラクターデータ | 245 | profiles + dialog |
| **合計** | **2,022** | **110,348+** |

→ [`ba-stories/README.md`](./ba-stories/README.md) に詳細統計・ディレクトリ構造・角色名一覧

## パイプライン構造

```
ba-story/
├── raw-data/                    # electricgoat/ba-data @ jp branch (sparse: Excel only)
├── ba-json -> raw-data/Excel    # symlink
├── utils/
│   ├── field_mapping.json       # Excel 表字段マッピング
│   ├── group_rules.json         # GroupId 分類ルール
│   ├── manifest.json            # 全 GroupId の分類済みリスト
│   ├── load_data.py             # JSON / 角色名 / 章節メタデータ ローダー
│   ├── parse_dialogue.py        # ScriptKr + TextJp → 構造化対話流
│   ├── format_markdown.py       # 対話流 → Markdown 変換
│   ├── character_info.py        # キャラクターデータ集約
│   ├── generate_all.py          # 7 カテゴリ 一括生成
│   ├── build_manifest.py        # manifest.json 生成
│   ├── build_readme.py          # README と集計
│   └── _smoke_test.py           # 動作確認
├── ba-stories/                  # 最終成果物 (Markdown)
├── PLAN.md                      # 実施計画
└── README.md                    # 本ファイル
```

## 再生成方法

```bash
# データ更新
cd raw-data && git pull origin jp

# 再生成
python3 -m utils.build_manifest   # 必要に応じて manifest 再構築
python3 -m utils.generate_all     # 全カテゴリ生成
python3 -m utils.build_readme     # README 再生成
```

## データソース

- [electricgoat/ba-data @ jp branch](https://github.com/electricgoat/ba-data/tree/jp)
- 380 個の Excel JSON ファイル（Yostar Japan 版 v1.68.x）
- ライセンス: MIT（コード）／オリジナル著作権は Yostar 株式会社

## 品質保証

- ランダム 5 ファイル抽出確認済み（frontmatter / 日本語 / 選択肢 / ナレーション）
- Ruby 表記 `[ruby=かな]漢字[/ruby]` → `漢字（かな）` に展開
- 色タグ `[FF6666]…[-]` 除去
- 未解決 Korean 話者名はサブストリング回避フォールバック（"통신아로나" → "アロナ" 等）
- 解決できない話者は `NPC_<id>` 扱い、既知エラーは `ba-stories/errors.log` に記録

## 注意

本アーカイブは研究・学習目的のみ。Blue Archive のゲーム内データを無断で商用利用することは、Yostar 株式会社の著作権を侵害する可能性があります。
