# Doc Advisor - Claude Code Plugin

AI を活用したドキュメント管理と自動インデックス化された目次（ToC）生成。

## 概要

Doc Advisor は、プロジェクトのドキュメントを自動的にインデックス化し、AI エージェントが必要な文書を素早く特定できるようにする Claude Code プラグインです。

### 主な機能

- **自動 ToC 生成**: ドキュメントの内容を分析し、検索可能な構造化インデックスを自動生成
- **差分更新**: 変更されたファイルのみを処理する incremental モード
- **並列処理**: 最大5並列でドキュメント処理を高速化
- **中断耐性**: 処理中断時も完了分は保持、再開可能

## インストール

### マーケットプレイスから（推奨）

```
/plugin install doc-advisor
```

### GitHub から

```
/plugin install github:BlueEventHorizon/DocAdvisor-CCPlugin
```

### ローカルから

```
/plugin install /path/to/DocAdvisor-CCPlugin/plugin
```

## セットアップ

インストール後、プロジェクトのドキュメントディレクトリに合わせてセットアップを実行します。

### 1. プラグインディレクトリに移動

```bash
cd ~/.claude/plugins/doc-advisor  # インストール先に応じて変更
```

### 2. セットアップスクリプトを実行

```bash
# デフォルト設定（rules/, specs/）
./setup.sh

# カスタムディレクトリを指定
./setup.sh --rules-dir docs/rules/ --specs-dir docs/specs/

# ヘルプを表示
./setup.sh --help
```

### セットアップオプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--rules-dir <path>` | 開発ドキュメントのディレクトリ | `rules/` |
| `--specs-dir <path>` | 要件定義書・設計書のディレクトリ | `specs/` |

### 3. ToC の初回生成

```bash
# 開発ドキュメントの ToC 生成
/doc-advisor:create-rules_toc --full

# 要件定義書・設計書の ToC 生成
/doc-advisor:create-specs_toc --full
```

## 使い方

### ToC 生成コマンド

```bash
# 開発ドキュメント（rules/）の ToC 生成
/doc-advisor:create-rules_toc          # 差分更新（変更ファイルのみ処理）
/doc-advisor:create-rules_toc --full   # 全ファイル再生成

# 要件定義書・設計書（specs/）の ToC 生成
/doc-advisor:create-specs_toc          # 差分更新
/doc-advisor:create-specs_toc --full   # 全ファイル再生成
```

### Advisor エージェント

タスクに必要なドキュメントを自動特定：

```
# Task tool で使用
Task(subagent_type: rules-advisor, prompt: "ユーザー認証機能の実装に必要な文書を特定")
Task(subagent_type: specs-advisor, prompt: "画面遷移に関する要件定義書を特定")
```

### ID 取得（新規ドキュメント作成時）

```bash
# 次の連番 ID を取得
skills/next-doc-id/scan_ids.sh SCR   # → SCR-016
skills/next-doc-id/scan_ids.sh DES   # → DES-042
```

## ディレクトリ構造

```
plugin/
├── .claude-plugin/
│   └── plugin.json          # プラグインメタデータ
├── setup.sh                 # セットアップスクリプト
├── templates/               # テンプレート（プレースホルダー付き）
│   ├── agents/
│   ├── commands/
│   └── skills/toc-common/
├── commands/                # スラッシュコマンド（setup.sh で生成）
├── agents/                  # 特化エージェント（setup.sh で生成）
├── skills/                  # ユーティリティ
│   ├── toc-common/          # 共通設定・関数
│   ├── toc-docs/            # フォーマット定義
│   ├── merge-rules-toc/     # rules マージ処理
│   ├── merge-specs-toc/     # specs マージ処理
│   ├── create-toc-checksums/# チェックサム生成
│   └── next-doc-id/         # ID 取得
└── README.md
```

## 対象ディレクトリ

### rules/ - 開発ドキュメント

```
rules/
├── core/           # アーキテクチャ、コーディング規約
├── layer/          # レイヤー別ルール
├── workflow/       # ワークフロー定義
└── rules_toc.yaml  # 生成される ToC
```

### specs/ - 要件定義書・設計書

```
specs/
├── {feature}/
│   ├── requirements/  # 要件定義書 (APP-, SCR-, BL-, etc.)
│   └── design/        # 設計書 (DES-)
└── specs_toc.yaml     # 生成される ToC
```

## ID 体系

| プレフィックス | カテゴリ |
|--------------|---------|
| APP- | アプリケーション要件 |
| SCR- | 画面要件 |
| CMP- | UI コンポーネント |
| FNC- | 機能要件 |
| BL- | ビジネスロジック |
| NF- | 非機能要件 |
| DM- | データモデル |
| EXT- | 外部連携 |
| NAV- | ナビゲーション |
| THEME- | テーマ |
| DES- | 設計書 |

## 設定のカスタマイズ

`skills/toc-common/config.yaml`（setup.sh で生成）でデフォルト設定を変更できます：

```yaml
rules:
  root_dir: rules/
  patterns:
    target_glob: "**/*.md"
    exclude:
      - ".toc_work"
      - "rules_toc.yaml"

specs:
  root_dir: specs/
  patterns:
    target_dirs:
      - requirements
      - design

common:
  parallel:
    max_workers: 5
```

## 処理モード

| モード | 説明 |
|--------|------|
| full | 全ファイルをスキャンして ToC を再生成 |
| incremental | 変更ファイルのみ処理（SHA-256 ハッシュで検出） |
| 継続 | 中断された処理を再開 |

## 必要要件

- Python 3（標準ライブラリのみ使用、pip 依存なし）
- Claude Code 1.0.0 以上

## ライセンス

MIT License
