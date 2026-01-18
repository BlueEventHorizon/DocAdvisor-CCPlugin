#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rules_toc.yaml マージスクリプト（標準ライブラリのみ版）

rules/.toc_work/*.yaml から全エントリを読み込み、
_meta セクションを除去してマージし、rules/rules_toc.yaml を生成する。

使用方法:
    python3 merge_rules_toc.py [--cleanup] [--mode full|incremental]

オプション:
    --cleanup   マージ成功後に .toc_work/ を削除
    --mode      full（デフォルト）: 新規生成、incremental: 差分マージ
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# 共通モジュールのパスを追加
COMMON_DIR = Path(__file__).parent.parent / "toc-common"
sys.path.insert(0, str(COMMON_DIR))

from toc_utils import (
    get_project_root,
    load_config,
    load_entry_file,
    yaml_escape,
    backup_existing_file,
    load_checksums,
    cleanup_work_dir,
    should_exclude,
)

# 設定読み込み
CONFIG = load_config('rules')
PROJECT_ROOT = get_project_root()
RULES_DIR = PROJECT_ROOT / CONFIG.get('root_dir', 'rules').rstrip('/')
TOC_WORK_DIR = RULES_DIR / CONFIG.get('work_dir', '.toc_work').rstrip('/')
OUTPUT_FILE = RULES_DIR / CONFIG.get('toc_file', 'rules_toc.yaml')
CHECKSUMS_FILE = RULES_DIR / CONFIG.get('checksums_file', '.toc_checksums.yaml')
OUTPUT_CONFIG = CONFIG.get('output', {})
PATTERNS_CONFIG = CONFIG.get('patterns', {})
EXCLUDE_PATTERNS = PATTERNS_CONFIG.get('exclude', ['.toc_work', 'rules_toc.yaml', 'reference'])


def load_existing_toc(toc_path):
    """既存の rules_toc.yaml を読み込み"""
    if not toc_path.exists():
        return {}

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    docs = {}
    current_file = None
    current_entry = {}
    current_list = None
    in_docs = False

    for line in content.split('\n'):
        stripped = line.strip()

        if stripped.startswith('#') or not stripped:
            continue

        if stripped == 'docs:':
            in_docs = True
            continue

        if not in_docs:
            continue

        # ファイルパスの検出（2スペースインデントで : で終わる）
        if line.startswith('  ') and not line.startswith('    ') and stripped.endswith(':'):
            if current_file and current_entry:
                docs[current_file] = current_entry
            current_file = stripped.rstrip(':')
            current_entry = {}
            current_list = None
        elif line.startswith('    ') and ':' in stripped and not stripped.startswith('-'):
            if current_file:
                key, _, val = stripped.partition(':')
                key = key.strip()
                val = val.strip().strip('"\'')
                if val:
                    current_entry[key] = val
                else:
                    current_list = []
                    current_entry[key] = current_list
        elif stripped.startswith('- ') and current_list is not None:
            item = stripped[2:].strip().strip('"\'')
            current_list.append(item)

    if current_file and current_entry:
        docs[current_file] = current_entry

    return docs


def get_existing_files():
    """現在存在するファイル一覧を取得"""
    files = set()
    target_glob = PATTERNS_CONFIG.get('target_glob', '**/*.md')
    for filepath in RULES_DIR.glob(target_glob):
        if should_exclude(filepath, RULES_DIR, EXCLUDE_PATTERNS):
            continue
        rel_path = str(filepath.relative_to(RULES_DIR))
        files.add(rel_path)
    return files


def write_yaml_output(docs, output_path):
    """
    YAMLファイルを出力

    Returns:
        bool: 成功時True、失敗時False
    """
    lines = []

    # ファイルヘッダーコメント
    header_comment = OUTPUT_CONFIG.get('header_comment', 'rules-advisor Subagent用 開発ドキュメント検索インデックス')
    metadata_name = OUTPUT_CONFIG.get('metadata_name', '開発ドキュメント検索インデックス')

    lines.append("# rules/rules_toc.yaml")
    lines.append(f"# {header_comment}")
    lines.append("")

    lines.append("metadata:")
    lines.append(f"  name: {metadata_name}")
    lines.append(f"  generated_at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append(f"  file_count: {len(docs)}")
    lines.append("")

    lines.append("docs:")
    for source_file, entry in sorted(docs.items()):
        lines.append(f"  {source_file}:")

        for key in ['title', 'purpose']:
            if key in entry:
                lines.append(f"    {key}: {yaml_escape(entry[key])}")

        for key in ['content_details', 'applicable_tasks', 'keywords']:
            if key in entry and entry[key]:
                lines.append(f"    {key}:")
                for item in entry[key]:
                    lines.append(f"      - {yaml_escape(item)}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        return True
    except (IOError, OSError, PermissionError) as e:
        print(f"エラー: ファイル書き込み失敗: {output_path} - {e}")
        return False


def delete_only_mode():
    """削除のみモード: .toc_work/ なしで削除を反映"""
    print("モード: delete-only（削除のみ）")

    if not OUTPUT_FILE.exists():
        print("エラー: rules_toc.yaml が存在しません")
        return False

    # バックアップ作成
    backup_existing_file(OUTPUT_FILE)

    # 既存データを読み込み
    docs = load_existing_toc(OUTPUT_FILE)

    # チェックサムにあるがファイルが存在しないエントリを削除
    checksum_files = load_checksums(CHECKSUMS_FILE)
    existing_files = get_existing_files()
    deleted_files = checksum_files - existing_files

    if not deleted_files:
        print("削除対象ファイルがありません")
        return True

    deleted_count = 0
    for del_file in deleted_files:
        if del_file in docs:
            del docs[del_file]
            print(f"  🗑 削除: {del_file}")
            deleted_count += 1

    if deleted_count == 0:
        print("削除対象エントリがありません")
        return True

    if not write_yaml_output(docs, OUTPUT_FILE):
        return False

    print(f"\n✅ 削除完了: {deleted_count}件のエントリを削除")
    return True


def merge_toc_files(mode='full'):
    yaml_files = sorted(TOC_WORK_DIR.glob("*.yaml"))

    if not yaml_files:
        print(f"エラー: {TOC_WORK_DIR} にYAMLファイルが見つかりません")
        return False

    print(f"対象ファイル: {len(yaml_files)} 件")
    print(f"モード: {mode}")

    # バックアップ作成（全モード共通）
    backup_existing_file(OUTPUT_FILE)

    # incremental モードでは既存データを読み込み
    if mode == 'incremental':
        docs = load_existing_toc(OUTPUT_FILE)
        # チェックサムにあるがファイルが存在しないエントリを削除
        checksum_files = load_checksums(CHECKSUMS_FILE)
        existing_files = get_existing_files()
        deleted_files = checksum_files - existing_files
        for del_file in deleted_files:
            if del_file in docs:
                del docs[del_file]
                print(f"  🗑 削除: {del_file}")
    else:
        docs = {}

    errors = []

    for filepath in yaml_files:
        filename = filepath.name
        try:
            meta, entry = load_entry_file(filepath)
            source_file = meta.get('source_file')
            status = meta.get('status')

            if not source_file:
                errors.append(f"{filename}: source_file が取得できない")
                continue

            if status != 'completed':
                errors.append(f"{filename}: ステータスが completed ではない（{status}）")
                continue

            docs[source_file] = entry
            print(f"  ✓ {source_file}")

        except Exception as e:
            errors.append(f"{filename}: {e}")

    if errors:
        print("\n警告:")
        for err in errors:
            print(f"  - {err}")

    if not docs:
        print("エラー: 有効なエントリがありません")
        return False

    if not write_yaml_output(docs, OUTPUT_FILE):
        return False

    print(f"\n✅ 生成完了: {OUTPUT_FILE}")
    print(f"   - ファイル数: {len(docs)}")

    return True


def main():
    cleanup = '--cleanup' in sys.argv
    delete_only = '--delete-only' in sys.argv
    mode = 'full'
    if '--mode' in sys.argv:
        idx = sys.argv.index('--mode')
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]

    print("=" * 50)
    print("rules_toc.yaml マージスクリプト")
    print("=" * 50)

    if delete_only:
        success = delete_only_mode()
    else:
        success = merge_toc_files(mode)

    if success and cleanup:
        cleanup_work_dir(TOC_WORK_DIR)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
