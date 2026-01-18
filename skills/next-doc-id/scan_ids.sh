#!/usr/bin/env bash
# 全ブランチ（ローカル + リモート）から指定プレフィックスのIDをスキャンし、次のIDを返す
#
# 使い方:
#   ./scan_ids.sh SCR    # → SCR-016
#   ./scan_ids.sh BL     # → BL-014
#   ./scan_ids.sh DES    # → DES-016

set -euo pipefail

PREFIX="${1:-}"

# 引数チェック
if [ -z "$PREFIX" ]; then
    echo "エラー: プレフィックスを指定してください"
    echo ""
    echo "使い方: $0 <PREFIX>"
    echo ""
    echo "有効なプレフィックス:"
    echo "  APP   - アプリケーション概要"
    echo "  SCR   - 画面要件"
    echo "  CMP   - UIコンポーネント"
    echo "  FNC   - 機能要件"
    echo "  BL    - ビジネスロジック"
    echo "  NF    - 非機能要件"
    echo "  DM    - データモデル"
    echo "  EXT   - 外部インターフェース"
    echo "  NAV   - ナビゲーション"
    echo "  THEME - テーマ"
    echo "  DES   - 設計書"
    exit 1
fi

# 有効なプレフィックスかチェック
case "$PREFIX" in
    APP|SCR|CMP|FNC|BL|NF|DM|EXT|NAV|THEME|DES) ;;
    *)
        echo "エラー: 無効なプレフィックス '$PREFIX'"
        echo ""
        echo "有効なプレフィックス: APP, SCR, CMP, FNC, BL, NF, DM, EXT, NAV, THEME, DES"
        exit 1
        ;;
esac

# ベースブランチの決定（develop があれば develop、なければ main）
if git show-ref --verify --quiet refs/heads/develop 2>/dev/null; then
    BASE_BRANCH="develop"
elif git show-ref --verify --quiet refs/remotes/origin/develop 2>/dev/null; then
    BASE_BRANCH="origin/develop"
elif git show-ref --verify --quiet refs/heads/main 2>/dev/null; then
    BASE_BRANCH="main"
else
    BASE_BRANCH="origin/main"
fi

# リモートをフェッチ（最新化）
git fetch --quiet 2>/dev/null || true

# 全ブランチを取得（ローカル + リモート）
ALL_BRANCHES=$(git for-each-ref --format='%(refname:short)' refs/heads/ refs/remotes/origin/ 2>/dev/null | grep -v "HEAD" | sort -u)

# ベースブランチから派生したブランチをフィルタリング
SCAN_BRANCHES=""
for branch in $ALL_BRANCHES; do
    # ベースブランチ自体、またはベースブランチを祖先に持つブランチ
    if [ "$branch" = "$BASE_BRANCH" ] || git merge-base --is-ancestor "$BASE_BRANCH" "$branch" 2>/dev/null; then
        SCAN_BRANCHES="$SCAN_BRANCHES $branch"
    fi
done

# 一時ファイルでID管理
TMPFILE=$(mktemp)
trap "rm -f $TMPFILE" EXIT

MAX_NUM=0
BRANCH_COUNT=0

for branch in $SCAN_BRANCHES; do
    BRANCH_COUNT=$((BRANCH_COUNT + 1))

    # specs/ 配下のファイルをスキャン
    git ls-tree -r --name-only "$branch" -- specs/ 2>/dev/null | while read -r file; do
        # 指定プレフィックスのIDを抽出
        if echo "$file" | grep -qE "${PREFIX}-[0-9]+"; then
            # IDを抽出
            ID=$(echo "$file" | grep -oE "${PREFIX}-[0-9]+" | head -1)
            echo "$ID|$branch" >> "$TMPFILE"
        fi
    done
done

# 結果を集計
if [ -s "$TMPFILE" ]; then
    # 最大番号を取得
    MAX_NUM=$(cat "$TMPFILE" | cut -d'|' -f1 | grep -oE '[0-9]+' | sort -n | tail -1)
    MAX_NUM=$((10#$MAX_NUM))  # ゼロ埋め除去

    # ユニークなID数
    UNIQUE_IDS=$(cat "$TMPFILE" | cut -d'|' -f1 | sort -u | wc -l | tr -d ' ')

    # 重複検出
    DUPLICATES=$(cat "$TMPFILE" | sort | uniq -c | sort -rn | awk '$1 > 1 {print}' | while read count id_branch; do
        id=$(echo "$id_branch" | cut -d'|' -f1)
        branches=$(grep "^$id|" "$TMPFILE" | cut -d'|' -f2 | sort -u | tr '\n' ', ' | sed 's/,$//')
        echo "  $id: $branches"
    done)
else
    UNIQUE_IDS=0
fi

# 次のID
NEXT_NUM=$((MAX_NUM + 1))
NEXT_ID=$(printf "%s-%03d" "$PREFIX" "$NEXT_NUM")

# 結果出力
echo "次のID: $NEXT_ID"
echo ""
echo "スキャン結果:"
echo "  ベースブランチ: $BASE_BRANCH"
echo "  スキャンしたブランチ数: $BRANCH_COUNT"
if [ "$MAX_NUM" -gt 0 ]; then
    echo "  検出した ${PREFIX}-XXX: ${UNIQUE_IDS}件（最大: ${PREFIX}-$(printf "%03d" $MAX_NUM)）"
else
    echo "  検出した ${PREFIX}-XXX: 0件"
fi

if [ -n "$DUPLICATES" ]; then
    echo ""
    echo "⚠️  重複検出（異なるブランチで同じIDが使用されています）:"
    echo "$DUPLICATES"
fi
