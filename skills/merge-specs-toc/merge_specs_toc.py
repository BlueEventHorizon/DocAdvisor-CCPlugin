#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
specs_toc.yaml マージスクリプト（標準ライブラリのみ版）

specs/.toc_work/*.yaml から全エントリを読み込み、
_meta セクションを除去してマージし、specs/specs_toc.yaml を生成する。

使用方法:
    python3 merge_specs_toc.py [--cleanup] [--mode full|incremental]

オプション:
    --cleanup   マージ成功後に .toc_work/ を削除
    --mode      full（デフォルト）: 新規生成、incremental: 差分マージ
"""

import sys
import re
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
    extract_id_from_filename,
)

# 設定読み込み
CONFIG = load_config('specs')
PROJECT_ROOT = get_project_root()
SPECS_DIR = PROJECT_ROOT / CONFIG.get('root_dir', 'specs').rstrip('/')
TOC_WORK_DIR = SPECS_DIR / CONFIG.get('work_dir', '.toc_work').rstrip('/')
OUTPUT_FILE = SPECS_DIR / CONFIG.get('toc_file', 'specs_toc.yaml')
CHECKSUMS_FILE = SPECS_DIR / CONFIG.get('checksums_file', '.toc_checksums.yaml')
OUTPUT_CONFIG = CONFIG.get('output', {})
PATTERNS_CONFIG = CONFIG.get('patterns', {})
TARGET_DIRS = PATTERNS_CONFIG.get('target_dirs', ['requirements', 'design'])
EXCLUDE_PATTERNS = PATTERNS_CONFIG.get('exclude', ['.toc_work', '.toc_checksums.yaml', 'specs_toc.yaml', 'reference', '/info/'])


def extract_feature_from_path(source_file):
    """パスから Feature名 を抽出"""
    # main/requirements/... → main
    parts = source_file.split('/')
    if len(parts) >= 1:
        return parts[0]
    return 'unknown'


def write_yaml_output(features_dict, specs, designs, output_path):
    """
    YAMLファイルを出力

    Returns:
        bool: 成功時True、失敗時False
    """
    lines = []

    # ファイルヘッダーコメント
    header_comment = OUTPUT_CONFIG.get('header_comment', 'specs-advisor Subagent用 要件定義書・設計書検索インデックス')
    metadata_name = OUTPUT_CONFIG.get('metadata_name', '要件定義書・設計書検索インデックス')

    lines.append("# specs/specs_toc.yaml")
    lines.append(f"# {header_comment}")
    lines.append("")

    lines.append("metadata:")
    lines.append(f"  name: {metadata_name}")
    lines.append(f"  generated_at: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append(f"  file_count: {len(specs) + len(designs)}")
    lines.append("")

    # features セクション
    lines.append("features:")
    for name, info in sorted(features_dict.items()):
        lines.append(f"  - name: {name}")
        lines.append(f"    status: {info.get('status', '完了')}")
        lines.append(f"    directory: {name}/")
        lines.append(f"    description: {info.get('description', f'{name} 機能')}")
    lines.append("")

    # specs セクション
    lines.append("specs:")
    for doc_id, entry in sorted(specs.items()):
        lines.append(f"  {doc_id}:")
        for key in ['feature', 'category', 'title', 'summary']:
            if key in entry:
                lines.append(f"    {key}: {yaml_escape(entry[key])}")
        if 'keywords' in entry and entry['keywords']:
            lines.append("    keywords:")
            for kw in entry['keywords']:
                lines.append(f"      - {yaml_escape(kw)}")
        if 'file' in entry:
            lines.append(f"    file: {entry['file']}")
    lines.append("")

    # designs セクション
    lines.append("designs:")
    for doc_id, entry in sorted(designs.items()):
        lines.append(f"  {doc_id}:")
        for key in ['feature', 'category', 'layer', 'title', 'summary']:
            if key in entry and entry[key]:
                lines.append(f"    {key}: {yaml_escape(entry[key])}")
        if 'keywords' in entry and entry['keywords']:
            lines.append("    keywords:")
            for kw in entry['keywords']:
                lines.append(f"      - {yaml_escape(kw)}")
        if 'file' in entry:
            lines.append(f"    file: {entry['file']}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        return True
    except (IOError, OSError, PermissionError) as e:
        print(f"エラー: ファイル書き込み失敗: {output_path} - {e}")
        return False


def load_existing_toc(toc_path):
    """既存の specs_toc.yaml を読み込み"""
    if not toc_path.exists():
        return {}, {}, {}

    with open(toc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    features = {}
    specs = {}
    designs = {}
    current_section = None
    current_id = None
    current_entry = {}
    current_list = None

    for line in content.split('\n'):
        stripped = line.strip()

        if stripped.startswith('#') or not stripped:
            continue

        if stripped == 'features:':
            current_section = 'features'
            continue
        elif stripped == 'specs:':
            current_section = 'specs'
            continue
        elif stripped == 'designs:':
            current_section = 'designs'
            continue
        elif stripped.startswith('metadata:'):
            current_section = 'metadata'
            continue

        if current_section == 'features' and stripped.startswith('- name:'):
            name = stripped.split(':', 1)[1].strip()
            features[name] = {'status': '完了', 'description': f'{name} 機能'}
        elif current_section == 'features' and ':' in stripped:
            key, _, val = stripped.partition(':')
            key = key.strip()
            val = val.strip().strip('"\'')
            if features:
                last_feature = list(features.keys())[-1]
                features[last_feature][key] = val

        elif current_section in ('specs', 'designs'):
            if re.match(r'^[A-Z]+-\d+:', stripped):
                if current_id and current_entry:
                    if current_section == 'specs':
                        specs[current_id] = current_entry
                    else:
                        designs[current_id] = current_entry
                current_id = stripped.rstrip(':')
                current_entry = {}
                current_list = None
            elif line.startswith('    ') and ':' in stripped and not stripped.startswith('-'):
                if current_id:
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

    if current_id and current_entry:
        if current_section == 'specs':
            specs[current_id] = current_entry
        else:
            designs[current_id] = current_entry

    return features, specs, designs


def is_target_dir(filepath):
    """対象ディレクトリ配下かどうかを判定"""
    rel_path = str(filepath.relative_to(SPECS_DIR))
    parts = rel_path.split('/')
    if len(parts) >= 2:
        return parts[1] in TARGET_DIRS
    return False


def get_existing_files():
    """現在存在するファイル一覧を取得"""
    files = set()
    for filepath in SPECS_DIR.rglob("*.md"):
        if should_exclude(filepath, SPECS_DIR, EXCLUDE_PATTERNS):
            continue
        if not is_target_dir(filepath):
            continue
        rel_path = str(filepath.relative_to(SPECS_DIR))
        files.add(rel_path)
    return files


def remove_empty_features(features_dict, specs, designs):
    """エントリのない feature を削除"""
    used_features = set()
    for entry in specs.values():
        used_features.add(entry.get('feature'))
    for entry in designs.values():
        used_features.add(entry.get('feature'))

    removed = []
    result = {}
    for name, info in features_dict.items():
        if name in used_features:
            result[name] = info
        else:
            removed.append(name)

    if removed:
        for name in removed:
            print(f"  🗑 空 feature 削除: {name}")

    return result


def delete_only_mode():
    """削除のみモード: .toc_work/ なしで削除を反映"""
    print("モード: delete-only（削除のみ）")

    if not OUTPUT_FILE.exists():
        print("エラー: specs_toc.yaml が存在しません")
        return False

    # バックアップ作成
    backup_existing_file(OUTPUT_FILE)

    # 既存データを読み込み
    features_dict, specs, designs = load_existing_toc(OUTPUT_FILE)

    # チェックサムにあるがファイルが存在しないエントリを削除
    checksum_files = load_checksums(CHECKSUMS_FILE)
    existing_files = get_existing_files()
    deleted_files = checksum_files - existing_files

    if not deleted_files:
        print("削除対象ファイルがありません")
        return True

    deleted_count = 0
    for del_file in deleted_files:
        del_id = extract_id_from_filename(del_file)
        if del_id:
            if del_id in specs:
                del specs[del_id]
                print(f"  🗑 削除: {del_id}")
                deleted_count += 1
            if del_id in designs:
                del designs[del_id]
                print(f"  🗑 削除: {del_id}")
                deleted_count += 1

    if deleted_count == 0:
        print("削除対象エントリがありません（IDが抽出できないファイルの可能性）")
        return True

    # 空 feature を削除
    features_dict = remove_empty_features(features_dict, specs, designs)

    if not write_yaml_output(features_dict, specs, designs, OUTPUT_FILE):
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
        features_dict, specs, designs = load_existing_toc(OUTPUT_FILE)
        # チェックサムにあるがファイルが存在しないエントリを削除
        checksum_files = load_checksums(CHECKSUMS_FILE)
        existing_files = get_existing_files()
        deleted_files = checksum_files - existing_files
        for del_file in deleted_files:
            del_id = extract_id_from_filename(del_file)
            if del_id:
                if del_id in specs:
                    del specs[del_id]
                    print(f"  🗑 削除: {del_id}")
                if del_id in designs:
                    del designs[del_id]
                    print(f"  🗑 削除: {del_id}")
    else:
        features_dict = {}
        specs = {}
        designs = {}

    errors = []

    for filepath in yaml_files:
        filename = filepath.name
        try:
            meta, entry = load_entry_file(filepath)
            source_file = meta.get('source_file')
            status = meta.get('status')
            doc_type = meta.get('doc_type')

            if not source_file:
                errors.append(f"{filename}: source_file が取得できない")
                continue

            if status != 'completed':
                errors.append(f"{filename}: ステータスが completed ではない（{status}）")
                continue

            doc_id = entry.get('id')
            if not doc_id:
                errors.append(f"{filename}: id が取得できない")
                continue

            # Feature抽出
            feature = entry.get('feature') or extract_feature_from_path(source_file)
            entry['feature'] = feature

            # file フィールド設定
            entry['file'] = source_file

            # features辞書に追加
            if feature not in features_dict:
                features_dict[feature] = {'status': '完了', 'description': f'{feature} 機能'}

            # doc_type で振り分け
            if doc_type == 'design':
                designs[doc_id] = entry
                print(f"  ✓ {doc_id} → designs")
            else:
                specs[doc_id] = entry
                print(f"  ✓ {doc_id} → specs")

        except Exception as e:
            errors.append(f"{filename}: {e}")

    if errors:
        print("\n警告:")
        for err in errors:
            print(f"  - {err}")

    if not specs and not designs:
        print("エラー: 有効なエントリがありません")
        return False

    # 空 feature を削除
    features_dict = remove_empty_features(features_dict, specs, designs)

    if not write_yaml_output(features_dict, specs, designs, OUTPUT_FILE):
        return False

    print(f"\n✅ 生成完了: {OUTPUT_FILE}")
    print(f"   - specs: {len(specs)}")
    print(f"   - designs: {len(designs)}")
    print(f"   - features: {len(features_dict)}")

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
    print("specs_toc.yaml マージスクリプト")
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
