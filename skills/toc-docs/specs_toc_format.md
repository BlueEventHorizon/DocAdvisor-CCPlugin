# specs_toc.yaml フォーマット定義

## 目的

`specs/specs_toc.yaml` は **specs-advisor Subagent** がタスクに必要な要件定義書・設計書を特定するための**唯一の情報源**です。

このファイルの品質がタスク実行の成否を決定します。**情報の漏れは絶対に許容されません**。

**このファイルはSingle Source of Truthとして、フォーマット定義・ID体系マスター・中間ファイルスキーマを一元管理します。**

---

## 重要原則 [MANDATORY]

- 全Featureの全要件定義書・設計書を漏れなく記載
- キーワードでタスク説明とのマッチングを支援
- 疑わしきは含める（見逃し厳禁）

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
specs/{feature}/requirements/**/*.md
specs/{feature}/design/**/*.md
```

**除外**:
- `specs/{feature}/plan/**/*.md`（計画書）
- `specs/info/**/*.md`（情報資料）
- `specs/**/reference/**/*`（参考資料、ソースコード）

---

## 変更検出方式 [Single Source of Truth]

incremental モードでは、ファイル内容のハッシュ値を記録し、変更検出に使用する。

### チェックサムファイル

```yaml
# specs/.toc_checksums.yaml（Git追跡対象）
checksums:
  main/requirements/APP-001_app_overview_spec.md: a1b2c3d4e5f6...
  main/design/DES-001_foo_list_design.md: b2c3d4e5f6a1...
  # ... 全対象ファイル分
```

### 処理フロー

```
1. 対象ファイルをスキャン（Glob）
2. 各ファイルのハッシュを計算（shasum -a 256）
3. 既存 .toc_checksums.yaml と比較:
   - ハッシュ不一致 → 変更あり → pending YAML 生成
   - 新規ファイル → 追加 → pending YAML 生成
   - checksums にあるがファイル不在 → 削除対象（_deleted.txt に記録）
4. サブエージェントで処理
5. マージ後、.toc_checksums.yaml を更新
```

### メリット

- 内容変更の正確な検出（偽陽性/偽陰性なし）
- Git非依存（コミット状態に左右されない）
- `.toc_checksums.yaml` はGit追跡対象（別マシンでもincremental判定可能）

---

## YAMLスキーマ定義

### トップレベル構造

```yaml
metadata:
  name: string              # インデックス名（固定値: "要件定義書・設計書検索インデックス"）
  generated_at: datetime    # 生成日時（ISO 8601形式）
  file_count: integer       # 対象ファイル総数

features: array             # Feature一覧（配列）

specs: object               # 要件定義書（キー: 要件ID）

designs: object             # 設計書（キー: 設計ID）
```

---

### features（Feature一覧）

```yaml
features:
  - name: string           # Feature名（例: "main", "csv_import"）
    status: string         # ステータス（例: "完了", "開発中", "計画中"）
    directory: string      # ディレクトリ名（例: "main/"）
    description: string    # Feature説明（1行）
```

**例**:
```yaml
features:
  - name: main
    status: 完了
    directory: main/
    description: {アプリ名} メイン機能
  - name: csv_import
    status: 開発中
    directory: csv_import/
    description: CSVファイルからのデータインポート機能
```

---

### specs（要件定義書）

```yaml
specs:
  <要件ID>:                      # 要件ID（APP-XXX, SCR-XXX, BL-XXX, FNC-XXX, CMP-XXX, NF-XXX, THEME-XXX）
    feature: string              # Feature名
    category: string             # カテゴリ（"アプリケーション要件", "画面要件", "ビジネスロジック", "機能要件", "UIコンポーネント", "非機能要件", "テーマ要件"）
    title: string                # タイトル（H1から抽出）
    summary: string              # 概要（1-2行、何を・どうしたいか・目的・期待値）
    keywords: array[string]      # キーワード（5-10語）
    file: string                 # ファイルパス（specs/ からの相対パス）
```

**例**:
```yaml
specs:
  APP-001:
    feature: main
    category: アプリケーション要件
    title: {アプリ名}概要仕様書
    summary: {アプリ名}の要件定義。カテゴリ分類、アクション実行、データ同期、リアルタイム自動更新を提供
    keywords:
      - {アプリ名}
      - データ管理
      - カテゴリ機能
      - アクション実行
      - AsyncStream
    file: main/requirements/APP-001_app_overview_spec.md

  SCR-001:
    feature: main
    category: 画面要件
    title: アイテム一覧画面
    summary: アプリ内のデータを表示・管理するメイン画面。左右2分割レイアウト（カテゴリリスト/アイテムリスト）で、行タップによる展開・アクション実行を提供する
    keywords:
      - アイテム
      - カテゴリ
      - 検索
      - ソート
      - フィルタリング
    file: main/requirements/screens/SCR-001_foo_list_screen_spec.md
```

---

### designs（設計書）

```yaml
designs:
  <設計ID>:                     # 設計ID（DES-XXX）
    feature: string             # Feature名
    category: string            # カテゴリ（固定値: "設計書"）
    layer: string               # 実装層（"Domain層", "UI層", "Infrastructure層", "DI層", "Tools層", "Library層"）（オプション）
    title: string               # タイトル（H1から抽出）
    summary: string             # 概要（1-2行）
    keywords: array[string]     # キーワード（5-10語）
    file: string                # ファイルパス（specs/ からの相対パス）
```

**例**:
```yaml
designs:
  DES-001:
    feature: main
    category: 設計書
    layer: UI層
    title: アイテム一覧設計
    summary: アイテム一覧画面の詳細設計。ViewModel、DataStore、AsyncStreamを用いた状態管理とリアルタイム更新を実現
    keywords:
      - SwiftUI
      - ViewModel
      - AsyncStream
      - FooDataStore
      - リアルタイム更新
    file: main/design/DES-001_foo_list_design.md
```

---

## ID体系マスター [Single Source of Truth]

| プレフィックス | category | doc_type | YAMLセクション |
|--------------|---------|----------|--------------|
| APP- | アプリケーション要件 | spec | specs |
| SCR- | 画面要件 | spec | specs |
| BL- | ビジネスロジック | spec | specs |
| FNC- | 機能要件 | spec | specs |
| CMP- | UIコンポーネント | spec | specs |
| NF- | 非機能要件 | spec | specs |
| THEME- | テーマ要件 | spec | specs |
| DM- | データモデル | spec | specs |
| EXT- | 外部連携 | spec | specs |
| NAV- | ナビゲーション | spec | specs |
| DES- | 設計書 | design | designs |

---

## Feature判定ルール [Single Source of Truth]

パスから Feature名 を抽出：

```
specs/main/requirements/... → Feature: main
specs/csv_import/design/... → Feature: csv_import
specs/{feature-name}/... → Feature: {feature-name}
```

**パターン**: `specs/([^/]+)/`（2番目のパスセグメント）

---

## doc_type 判定ルール [Single Source of Truth]

パスから doc_type を判定：

| パスパターン | doc_type |
|------------|----------|
| `specs/{feature}/requirements/**/*.md` | spec |
| `specs/{feature}/design/**/*.md` | design |

---

## ファイル名からIDの抽出ルール

```
SCR-001_foo_list_screen_spec.md → SCR-001
DES-001_foo_list_design.md → DES-001
APP-001_app_overview_spec.md → APP-001
```

**パターン**: `(APP|SCR|BL|FNC|CMP|NF|THEME|DM|EXT|NAV|DES)-\d+`

---

## 完全な例

```yaml
# specs/specs_toc.yaml

metadata:
  name: 要件定義書・設計書検索インデックス
  generated_at: 2026-01-03T18:30:00Z
  file_count: 63

features:
  - name: main
    status: 完了
    directory: main/
    description: {アプリ名} メイン機能
  - name: csv_import
    status: 開発中
    directory: csv_import/
    description: CSVファイルからのデータインポート機能
  - name: hagaki_print
    status: 計画中
    directory: hagaki_print/
    description: 印刷機能

specs:
  APP-001:
    feature: main
    category: アプリケーション要件
    title: {アプリ名}概要仕様書
    summary: {アプリ名}の要件定義
    keywords:
      - {アプリ名}
      - データ管理
    file: main/requirements/APP-001_app_overview_spec.md

  SCR-001:
    feature: main
    category: 画面要件
    title: アイテム一覧画面
    summary: アプリ内のデータを表示・管理するメイン画面
    keywords:
      - アイテム
      - カテゴリ
      - 検索
    file: main/requirements/screens/SCR-001_foo_list_screen_spec.md

designs:
  DES-001:
    feature: main
    category: 設計書
    layer: UI層
    title: アイテム一覧設計
    summary: アイテム一覧画面の詳細設計
    keywords:
      - SwiftUI
      - ViewModel
      - AsyncStream
    file: main/design/DES-001_foo_list_design.md
```

---

## 中間ファイルスキーマ [Single Source of Truth]

### 作業ディレクトリ

```
specs/.toc_work/          # 作業ディレクトリ（.gitignore対象）
```

### エントリYAML構造

**要件定義書（spec）用**:
```yaml
# specs/.toc_work/SCR-001.yaml

_meta:
  source_file: main/requirements/screens/SCR-001_foo_list_screen_spec.md  # specs/ からの相対パス
  doc_type: spec                    # spec | design
  status: pending                   # pending | completed
  updated_at: null                  # ISO 8601形式（completed時に設定）

id: SCR-001
feature: null                       # 処理後: main
category: null                      # 処理後: 画面要件
title: null                         # 処理後: H1から抽出
summary: null                       # 処理後: 1-2行要約
keywords: []                        # 処理後: 5-10語
file: null                          # 処理後: source_file と同値
```

**設計書（design）用**:
```yaml
# specs/.toc_work/DES-001.yaml

_meta:
  source_file: main/design/DES-001_foo_list_design.md
  doc_type: design
  status: pending
  updated_at: null

id: DES-001
feature: null
category: 設計書                     # 固定値
layer: null                         # 処理後: Domain層/UI層/Infrastructure層 等
title: null
summary: null
keywords: []
file: null
```

### ステータス遷移

```
pending → completed（正常完了時）
```

### 完了判定条件

以下の全てを満たす場合に `completed` とする：
- `_meta.status == completed`
- `id` が null でない
- `feature` が null でない
- `category` が null でない
- `title` が null でない
- `summary` が null でない
- `keywords` が空配列でない
- `file` が null でない

### ファイル名生成ルール

要件定義書/設計書のIDをそのままファイル名として使用:

```
SCR-001_foo_list_screen_spec.md → SCR-001.yaml
DES-001_foo_list_design.md → DES-001.yaml
APP-001_app_overview_spec.md → APP-001.yaml
```
