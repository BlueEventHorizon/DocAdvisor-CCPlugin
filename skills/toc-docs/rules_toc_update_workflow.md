---
name: rules_toc_update_workflow
description: rules_toc.yaml 更新ワークフロー（個別エントリファイル方式）
applicable_when:
  - rules-toc-updater Agentとして実行する
  - /create-rules_toc コマンドを実行する
  - ルール・ワークフロー・フォーマット文書の追加・変更・削除後
---

# rules_toc.yaml 更新ワークフロー

## 概要

`rules/rules_toc.yaml` を更新するワークフロー。**個別エントリファイル方式**を採用し、各ルール文書を独立したサブエージェントで処理します。

## アーキテクチャ

### 設計思想

- **1ファイル = 1サブエージェント**: 各ルール文書を個別に処理
- **成果物の永続化**: 各サブエージェントの出力がファイルとして残る
- **再開可能**: 中断時も完了分は保持され、未完了分から再開

### ディレクトリ構造

```
rules/
├── rules_toc.yaml              # 最終成果物（マージ後）
└── .toc_work/                  # 作業ディレクトリ（.gitignore対象）
    ├── core_architecture_rule.yaml
    ├── core_coding_rule.yaml
    └── ...（処理対象ファイル分）
```

---

## 重要原則 [MANDATORY]

- **Single Source of Truth**: `rules_toc_format.md` がフォーマット定義・中間ファイルスキーマの唯一の情報源
- **全項目必須**: フォーマット定義の全てのフィールドを必ず埋めること。**省略禁止**
- **キーワード抽出**: 各ファイルを実際に読み、内容からキーワードを抽出すること（配列形式）
- **YAML構文**: インデント・コロン・ハイフンを正しく使用すること
- **キー形式**: `rules/` プレフィックスなし（例: `core/architecture_rule.md`）

---

## ワークフロー全体像

```
/create-rules_toc 実行
    ↓
フェーズ1: 初期化（オーケストレーター）
    ↓
フェーズ2: 処理（並列サブエージェント）
    ↓
フェーズ3: マージ（オーケストレーター）
    ↓
クリーンアップ
```

---

## フェーズ1: 初期化（オーケストレーター）

### Step 1.1: .toc_work/ の状態確認

```bash
test -d rules/.toc_work && echo "EXISTS" || echo "NOT_EXISTS"
```

### Step 1.2: モード判定と処理分岐

| 条件 | 処理 |
|------|------|
| `--full` オプション指定 | .toc_work/ を削除 → full モードで新規処理 |
| .toc_work/ が存在する | 継続モード（既存のpending YAMLを処理） |
| .toc_work/ が存在しない + rules_toc.yaml が存在しない | full モードで新規処理 |
| .toc_work/ が存在しない + rules_toc.yaml が存在する | incremental モード |

### Step 1.3: 対象ファイルの特定

- **full モード**: スキャン対象の全ファイルを取得
- **incremental モード**: ハッシュ方式で変更ファイルを検出

### Step 1.4: pending YAML テンプレート生成

各対象ファイルに対して `.toc_work/` にテンプレートを生成。

---

## フェーズ2: 並列処理（サブエージェント）

### Step 2.1: pending YAML の特定

`.toc_work/*.yaml` を読み込み、`_meta.status: pending` のファイルを特定

### Step 2.2: サブエージェント並列起動

**並列数**: 5並列

```
# オーケストレーターが1メッセージで複数Task toolを呼び出し
Task(subagent_type: rules-toc-updater, prompt: "entry_file: rules/.toc_work/xxx.yaml")
Task(subagent_type: rules-toc-updater, prompt: "entry_file: rules/.toc_work/yyy.yaml")
...（最大5件同時）
```

### Step 2.3: サブエージェントの処理内容

各サブエージェント（rules-toc-updater）が実行:

1. `entry_file` を Read
2. `_meta.source_file` からルール文書パスを取得
3. ルール文書（`rules/{source_file}`）を Read
4. `rules_toc_format.md` の「各項目の記載ガイドライン」に従い情報抽出・フィールド設定
5. `_meta.status: completed`, `_meta.updated_at` を設定
6. Write で保存

### Step 2.4: 繰り返し

全ての pending YAML が completed になるまで Step 2.1-2.3 を繰り返し

---

## フェーズ3: マージ

### Step 3.1: 完了判定

各 `.toc_work/*.yaml` が以下を満たすか確認:
- `_meta.status == completed`
- `title != null`
- `purpose != null`

**未完了があれば**: 警告を出力し、ユーザーに確認

### Step 3.2: マージ処理

**full モード**:
1. `.toc_work/*.yaml` を全て読み込み
2. `_meta` を除外して `docs` セクションに変換
3. `metadata`（generated_at, file_count）を設定
4. `rules/rules_toc.yaml` に Write

**incremental モード**:
1. 既存 `rules/rules_toc.yaml` を読み込み
2. `.toc_checksums.yaml` に記録されているがファイルが存在しないエントリを削除
3. `.toc_work/*.yaml` のエントリで上書き/追加（`_meta` 除外）
4. `metadata.generated_at`, `metadata.file_count` を更新
5. `rules/rules_toc.yaml` に Write
6. `.toc_checksums.yaml` を更新（`/create-toc-checksums` スキルを実行）

### Step 3.3: クリーンアップ

```bash
rm -rf rules/.toc_work
```

---

## バリデーション

マージ前に確認:

1. **YAML構文チェック**:
   - インデント、コロン、ハイフンの正確性
   - 引用符のエスケープ

2. **必須フィールドチェック**:
   - metadata: name, generated_at, file_count
   - docs: 各エントリに title, purpose, content_details, applicable_tasks, keywords

3. **ファイル存在チェック**:
   - docs に記載された全ファイルが実際に存在する

---

## 関連ファイル

- `rules_toc_format.md` - フォーマット定義（YAMLスキーマ）
- `agents/rules-toc-updater.md` - 1ファイル処理サブエージェント
- `commands/create-rules_toc.md` - オーケストレーターコマンド
- `agents/rules-advisor.md` - 検索Subagent
