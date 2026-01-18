---
name: specs_toc_update_workflow
description: specs_toc.yaml 更新ワークフロー（個別エントリファイル方式）
applicable_when:
  - specs-toc-updater Agentとして実行する
  - /create-specs_toc コマンドを実行する
  - 要件定義書・設計書の追加・変更・削除後
---

# specs_toc.yaml 更新ワークフロー

## 概要

`specs/specs_toc.yaml` を更新するワークフロー。中断耐性を持つ**個別エントリファイル方式**を採用し、各要件定義書・設計書を並列処理します。

## アーキテクチャ

### 設計思想

1. **1ファイル = 1サブエージェント**: 各要件定義書・設計書を個別に処理
2. **成果物の永続化**: 各サブエージェントの出力がファイルとして残る
3. **再開可能**: 中断時も完了分は保持され、未完了分から再開
4. **Single Source of Truth**: フォーマット定義を `specs_toc_format.md` に集約

### ディレクトリ構造

```
specs/
├── specs_toc.yaml              # 最終成果物（マージ後）
└── .toc_work/                  # 作業ディレクトリ（.gitignore対象）
    ├── APP-001.yaml
    ├── SCR-001.yaml
    ├── DES-001.yaml
    └── ...（処理対象ファイル分）
```

---

## 重要原則 [MANDATORY]

- **フォーマット定義**: `specs_toc_format.md` に従う（中間ファイルスキーマ、ID体系マスター、Feature判定ルール含む）
- **全項目必須**: フォーマット定義の全てのフィールドを必ず埋めること。**省略禁止**
- **キーワード抽出**: 各ファイルを実際に読み、内容からキーワードを抽出すること（5-10語）
- **YAML構文**: インデント・コロン・ハイフンを正しく使用すること

---

## ワークフロー全体像

```
/create-specs_toc 実行
    ↓
.toc_work/ の存在確認
    ↓
【存在しない場合】新規処理
    ├─ full: 全ファイル分のpending YAMLを生成
    └─ incremental: git diff の A/M ファイル分のpending YAMLを生成
    ↓
【存在する場合】継続処理
    └─ 既存のpending YAMLを特定して処理継続
    ↓
サブエージェント並列処理（5並列）
    ↓
全完了後マージ
    ├─ full: .toc_work/*.yaml から specs_toc.yaml を新規生成
    └─ incremental: 既存 specs_toc.yaml + .toc_work/*.yaml 合成 + D削除
    ↓
.toc_work/ を削除（クリーンアップ）
```

---

## フェーズ1: 初期化（オーケストレーター）

### Step 1.1: .toc_work/ の存在確認

```bash
test -d specs/.toc_work && echo "EXISTS" || echo "NOT_EXISTS"
```

### Step 1.2: 存在しない場合の処理

#### モード判定

| 条件 | モード | 処理内容 |
|------|--------|---------|
| `--full` オプション指定 | full | 全ファイルスキャン |
| specs_toc.yaml が存在しない | full | 全ファイルスキャン |
| それ以外 | incremental | 変更ファイルのみ処理 |

#### full モード時の初期化

1. `.toc_work/` ディレクトリを作成
2. Glob で対象ファイルを取得:
   ```
   specs/{feature}/requirements/**/*.md
   specs/{feature}/design/**/*.md
   ```
3. 各ファイルに対して pending YAML をテンプレート生成

#### incremental モード時の初期化（ハッシュ方式）

1. `.toc_work/` ディレクトリを作成
2. ハッシュ方式で変更ファイルを検出
3. 変更・新規ファイル → pending YAML をテンプレート生成
4. 削除ファイル → マージ時に自動検出（merge_specs_toc.py がチェックサム比較で検出）

### Step 1.3: 存在する場合の処理（継続モード）

1. `.toc_work/*.yaml` から `_meta.status == pending` のファイルを特定
2. 未完了ファイルがあれば処理を継続
3. 全て completed であればマージフェーズへ

---

## フェーズ2: 並列処理（サブエージェント）

### 処理単位

**1つのサブエージェントが1つのYAMLファイルを担当**

### 並列数

**5並列**（オーケストレーターが1メッセージで5つのTask toolを呼び出し）

### サブエージェントの処理

1. 対象 YAML を Read（`_meta.source_file` を取得）
2. 要件定義書/設計書ファイルを Read
3. フォーマット定義に従い情報抽出:
   - `id`: ファイル名から抽出済み
   - `feature`: パスから判定（`specs/([^/]+)/`）
   - `category`: IDプレフィックスから判定（ID体系マスター参照）
   - `title`: H1から抽出
   - `summary`: 概要を1-2行で要約
   - `keywords`: 5-10語
   - `file`: `_meta.source_file` と同値
   - `layer`: 設計書の場合のみ
4. `_meta.status: completed`、`_meta.updated_at` を設定
5. Write で保存

### 繰り返し処理

pending ファイルが残っている限り、5並列でサブエージェントを起動し続ける

---

## フェーズ3: マージ

### Step 3.1: 完了判定

各 YAML が以下を満たすか確認:
- `_meta.status == completed`
- `id`, `feature`, `category`, `title`, `summary`, `keywords`, `file` が null でない

未完了があれば警告を出力（処理は継続）

### Step 3.2: マージ処理

#### full モードの場合

1. `.toc_work/*.yaml` を全て読み込み
2. `doc_type` で振り分け:
   - `spec` → specs セクション
   - `design` → designs セクション
3. features を自動生成（出現した feature 名を集約）
4. metadata を設定:
   - `name`: "要件定義書・設計書検索インデックス"
   - `generated_at`: 現在時刻（ISO 8601形式）
   - `file_count`: specs + designs の総数
5. `specs/specs_toc.yaml` に Write

#### incremental モードの場合

1. 既存 `specs/specs_toc.yaml` を読み込み
2. チェックサム比較で削除ファイルを検出し、対応するエントリを削除
3. `.toc_work/*.yaml` のエントリで上書き/追加
4. features を更新
5. metadata を更新
6. `specs/specs_toc.yaml` に Write
7. `.toc_checksums.yaml` を更新（`/create-toc-checksums` スキルを実行）

### Step 3.3: クリーンアップ

`.toc_work/` ディレクトリを削除:
```bash
rm -rf specs/.toc_work
```

---

## pending YAMLテンプレート生成

- 入力: ファイルパス（例: `specs/main/requirements/screens/SCR-001_foo_list_screen_spec.md`）
- 出力: `specs/.toc_work/{ID}.yaml`

---

## バリデーション

マージ前に確認:

1. **YAML構文チェック**:
   - インデント、コロン、ハイフンの正確性
   - 引用符のエスケープ

2. **必須フィールドチェック**:
   - metadata: name, generated_at, file_count
   - features: 各エントリに name, status
   - specs/designs: 各エントリに id, feature, category, title, summary, keywords, file

3. **ファイル存在チェック**:
   - specs/designs に記載された全ファイルが実際に存在する

---

## エラーハンドリング

### サブエージェントのエラー時

- エラー情報をログ出力
- `_meta.status` は `pending` のまま
- 次のバッチで再試行

### マージのエラー時

- `.toc_work/` は削除しない（再実行可能）
- エラー内容を報告
- 手動対応を促す

---

## 品質チェックリスト

生成・更新後に確認：

- [ ] 全Featureの requirements/、design/ ファイルが記載されている
- [ ] 各エントリに必須フィールド（feature, category, title, summary, keywords, file）がある
- [ ] 概要が「何を・どうしたいか・目的」を含んでいる（1-2行）
- [ ] キーワードがタスク説明とマッチしやすい用語を含んでいる（5-10語）
- [ ] YAML構文が正しい（インデント、コロン、ハイフン）
- [ ] 生成日時（metadata.generated_at）がISO 8601形式
- [ ] ファイル数（metadata.file_count）が実際のファイル数と一致

---

## 関連ファイル

- `specs_toc_format.md` - フォーマット定義（Single Source of Truth）
- `agents/specs-toc-updater.md` - 1ファイル処理サブエージェント
- `commands/create-specs_toc.md` - オーケストレーターコマンド
- `agents/specs-advisor.md` - 検索Subagent
