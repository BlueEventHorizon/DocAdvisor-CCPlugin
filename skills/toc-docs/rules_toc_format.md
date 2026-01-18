# rules_toc.yaml フォーマット定義

## 目的

`rules/rules_toc.yaml` は **rules-advisor Subagent** がタスクに必要な文書を特定するための**唯一の情報源**です。

このファイルの品質がタスク実行の成否を決定します。**情報の漏れは絶対に許容されません**。

**このファイルはSingle Source of Truthとして、フォーマット定義・中間ファイルスキーマを一元管理します。**

---

## 重要原則 [MANDATORY]

- 全ルール・ワークフロー・フォーマット文書を漏れなく記載
- キーワードでタスク説明とのマッチングを支援
- 疑わしきは含める（見逃し厳禁）
- **キー形式**: `rules/` プレフィックスなし（例: `core/architecture_rule.md`）

### YAML記述ルール

- **インデント**: 2スペース（タブ禁止）
- **コロン後**: 必ずスペース1つ（`key: value`）
- **配列**: ハイフン + スペース（`- item`）
- **null禁止**: 全フィールドを必ず埋める
- **空配列禁止**: `[]` は許容されない（最低1項目）
- **インライン配列禁止**: `[a, b]` 形式は使用しない。必ずリスト形式で記述
- **マルチライン禁止**: `|` や `>` は使用しない。1行で記述
- **日本語**: コメント・説明は日本語で記述

---

## スキャン対象 [Single Source of Truth]

```
rules/core/**/*.md
rules/layer/**/*.md
rules/workflow/**/*.md
rules/format/**/*.md
rules/refactoring/**/*.md
```

**除外**:
- `rules/rules_toc.yaml`（自身）
- `rules/.toc_work/`（作業ディレクトリ）
- `rules/**/reference/`（参考資料）

---

## 変更検出方式 [Single Source of Truth]

incremental モードでは、ファイル内容のハッシュ値を記録し、変更検出に使用する。

### チェックサムファイル

```yaml
# rules/.toc_checksums.yaml（Git追跡対象）
checksums:
  core/architecture_rule.md: a1b2c3d4e5f6...
  core/coding_rule.md: b2c3d4e5f6a1...
  # ... 全対象ファイル分
```

### 処理フロー

```
1. 対象ファイルをスキャン（Glob）
2. 各ファイルのハッシュを計算（shasum -a 256）
3. 既存 .toc_checksums.yaml と比較:
   - ハッシュ不一致 → 変更あり → pending YAML 生成
   - 新規ファイル → 追加 → pending YAML 生成
   - checksums にあるがファイル不在 → 削除対象
4. サブエージェントで処理
5. マージ後、.toc_checksums.yaml を更新
```

### メリット

- 内容変更の正確な検出（偽陽性/偽陰性なし）
- Git非依存（コミット状態に左右されない）
- `.toc_checksums.yaml` はGit追跡対象（別マシンでもincremental判定可能）

---

## 中間ファイルスキーマ [Single Source of Truth]

個別エントリファイル方式で使用する作業ファイルの構造定義。

### ファイル配置

```
rules/.toc_work/                    # 作業ディレクトリ（.gitignore対象）
├── core_architecture_rule.yaml
├── core_coding_rule.yaml
├── layer_domain_domain_core.yaml
└── ...（処理対象ファイル分）
```

### ファイル名生成ルール

ルール文書パスからYAMLファイル名を生成:

```
core/architecture_rule.md → core_architecture_rule.yaml
layer/domain/domain_core.md → layer_domain_domain_core.yaml
workflow/plan/design_workflow.md → workflow_plan_design_workflow.yaml
```

変換ルール: `/` → `_`, `.md` → `.yaml`

### エントリYAML構造

```yaml
# rules/.toc_work/core_architecture_rule.yaml

_meta:
  source_file: core/architecture_rule.md    # ルール文書パス（rules/からの相対）
  status: pending                           # pending | completed
  updated_at: null                          # 完了時刻（ISO 8601形式）

# 以下、rules_toc.yaml のエントリ形式（キーは source_file の値を使用）
title: null
purpose: null
content_details: []
applicable_tasks: []
keywords: []
```

### _meta フィールド説明

| フィールド | 型 | 説明 |
|-----------|------|------|
| `source_file` | string | 処理対象のルール文書パス（rules/からの相対） |
| `status` | enum | `pending`（未処理）または `completed`（完了） |
| `updated_at` | datetime/null | 完了時刻（ISO 8601形式）、未完了時は `null` |

---

## YAMLスキーマ定義（最終出力）

### トップレベル構造

```yaml
metadata:
  name: string              # インデックス名（固定値: "開発ドキュメント検索インデックス"）
  generated_at: datetime    # 生成日時（ISO 8601形式）
  file_count: integer       # 対象ファイル総数

docs: object                # 文書エントリ（キー: ファイルパス）
```

---

### docs（文書エントリ）

```yaml
docs:
  <ファイルパス>:                 # rules/ からの相対パス（例: "core/architecture_rule.md"）※rules/プレフィックスなし
    title: string                # タイトル（H1から抽出）
    purpose: string              # 目的（1-2行、何を定義するか）
    content_details: array[string] # 内容詳細（5項目以上、主要なルール・制約・パターン）
    applicable_tasks: array[string] # 適用タスク（このファイルが必要なタスク種別）
    keywords: array[string]       # キーワード（タスク説明とのマッチング用語、5-10語）
```

**例**:
```yaml
docs:
  core/architecture_rule.md:
    title: アーキテクチャルール
    purpose: アーキテクチャの全体構造・レイヤー設計・レイヤー間連携を定義
    content_details:
      - ディレクトリ構成
      - レイヤー依存関係
      - App/Domain/Infrastructure/DI/Tools/Library層の責務
      - レイヤー間連携パターン
      - Factory流れ
      - データフロー設計
      - AsyncStream設計原則
    applicable_tasks:
      - アーキテクチャ確認
      - レイヤー違反検出
      - 新層導入
      - 全体設計見直し
      - 既存コード理解
    keywords:
      - アーキテクチャ
      - レイヤー
      - Clean Architecture
      - DI
      - Factory
      - Protocol-based
      - AsyncStream
      - StreamManager
```

---

## 各項目の記載ガイドライン

### purpose（目的）

- ファイルの役割を1-2文で簡潔に
- 「〜のルールを定義」「〜のワークフローを規定」など

### content_details（内容詳細）

- ファイル内の**具体的なルール・制約・パターン**を列挙
- Subagentがファイルを読まなくても概要を把握できる詳細さ
- 重要な制約は必ず含める
- 5-10項目程度

### applicable_tasks（適用タスク）

- このファイルが**必要となるタスク種別**を具体的に列挙
- 曖昧な表現は避け、具体的なタスク名で記載
- 「〜実装」「〜作成」「〜修正」など動作を含める

### keywords（キーワード）

- タスク説明文との**マッチング用語**
- 技術用語、概念名、略語を含める
- 5-10語程度

---

## 完全な例

```yaml
# rules/rules_toc.yaml

metadata:
  name: 開発ドキュメント検索インデックス
  generated_at: 2026-01-11T12:00:00Z
  file_count: 25

docs:
  core/architecture_rule.md:
    title: アーキテクチャルール
    purpose: アーキテクチャの全体構造・レイヤー設計・レイヤー間連携を定義
    content_details:
      - ディレクトリ構成
      - レイヤー依存関係
      - App/Domain/Infrastructure/DI/Tools/Library層の責務
      - データフロー設計
      - AsyncStream設計原則
    applicable_tasks:
      - アーキテクチャ確認
      - レイヤー違反検出
      - 全体設計見直し
    keywords:
      - アーキテクチャ
      - レイヤー
      - Clean Architecture
      - DI
      - Factory

  layer/infrastructure/repository_rule.md:
    title: Repository実装ルール
    purpose: Repository実装の即時反応 + 最終同期パターンを定義
    content_details:
      - Repository層の責務
      - 即時反応 + 最終同期パターン
      - Create/Update/Delete への適用方法
      - アンチパターン
    applicable_tasks:
      - Repository実装
      - Infrastructure層実装
      - CRUD操作実装
    keywords:
      - Repository
      - 即時反応
      - 最終同期
      - キャッシュ更新
      - forceBroadcast
```
