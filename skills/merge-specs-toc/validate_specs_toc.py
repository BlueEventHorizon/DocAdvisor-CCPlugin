#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
specs_toc.yaml 検査スクリプト

生成された specs_toc.yaml の整合性を検査する。

使用方法:
    python3 validate_specs_toc.py [--file PATH]

オプション:
    --file    検査対象ファイル（デフォルト: specs/specs_toc.yaml）

検査項目:
    1. YAML構文検査
    2. 必須フィールド検査
    3. ファイル参照検査
    4. 重複ID検査
"""

import sys
import re
from pathlib import Path

# 共通モジュールのパスを追加
COMMON_DIR = Path(__file__).parent.parent / "toc-common"
sys.path.insert(0, str(COMMON_DIR))

from toc_utils import get_project_root, load_config

# 設定読み込み
CONFIG = load_config('specs')
PROJECT_ROOT = get_project_root()
SPECS_DIR = PROJECT_ROOT / CONFIG.get('root_dir', 'specs').rstrip('/')
DEFAULT_TOC_FILE = SPECS_DIR / CONFIG.get('toc_file', 'specs_toc.yaml')


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


def validate_toc(toc_path):
    """
    生成された toc ファイルを検査する
    - YAML構文検査
    - 必須フィールド検査
    - ファイル参照検査
    - 重複ID検査
    """
    print("=" * 50)
    print("specs_toc.yaml 検査")
    print("=" * 50)
    print(f"対象: {toc_path}")
    print()

    errors = []

    # 1. YAML構文検査（ファイルが読み込めるか）
    try:
        with open(toc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print("✓ YAML構文検査: OK（ファイル読み込み成功）")
    except Exception as e:
        errors.append(f"YAML構文検査: ファイル読み込み失敗 - {e}")
        print(f"\n❌ 検査失敗: {len(errors)} 件のエラー")
        for err in errors:
            print(f"  - {err}")
        return False

    # パース
    features, specs, designs = load_existing_toc(toc_path)

    # 2. 必須フィールド検査
    spec_required = ['feature', 'title', 'file']
    design_required = ['feature', 'title', 'file']
    field_errors = []

    for doc_id, entry in specs.items():
        for field in spec_required:
            if not entry.get(field):
                field_errors.append(f"必須フィールド欠落: specs/{doc_id} に '{field}' がありません")

    for doc_id, entry in designs.items():
        for field in design_required:
            if not entry.get(field):
                field_errors.append(f"必須フィールド欠落: designs/{doc_id} に '{field}' がありません")

    if not field_errors:
        print(f"✓ 必須フィールド検査: OK（specs: {len(specs)}件, designs: {len(designs)}件）")
    else:
        print(f"✗ 必須フィールド検査: {len(field_errors)}件のエラー")
        errors.extend(field_errors)

    # 3. ファイル参照検査
    file_errors = []
    for doc_id, entry in specs.items():
        filepath = entry.get('file')
        if filepath:
            full_path = SPECS_DIR / filepath
            if not full_path.exists():
                file_errors.append(f"ファイル不在: specs/{doc_id} の file '{filepath}' が存在しません")

    for doc_id, entry in designs.items():
        filepath = entry.get('file')
        if filepath:
            full_path = SPECS_DIR / filepath
            if not full_path.exists():
                file_errors.append(f"ファイル不在: designs/{doc_id} の file '{filepath}' が存在しません")

    if not file_errors:
        print(f"✓ ファイル参照検査: OK（全ファイルが存在）")
    else:
        print(f"✗ ファイル参照検査: {len(file_errors)}件のエラー")
        errors.extend(file_errors)

    # 4. 重複ID検査
    all_ids = list(specs.keys()) + list(designs.keys())
    seen = set()
    duplicates = []
    for doc_id in all_ids:
        if doc_id in seen:
            duplicates.append(f"重複ID: '{doc_id}' が複数回定義されています")
        seen.add(doc_id)

    if not duplicates:
        print(f"✓ 重複ID検査: OK（{len(all_ids)}件のユニークID）")
    else:
        print(f"✗ 重複ID検査: {len(duplicates)}件の重複")
        errors.extend(duplicates)

    # 結果サマリー
    print()
    if errors:
        print(f"❌ 検査失敗: {len(errors)} 件のエラー")
        print("-" * 40)
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print(f"✅ 検査完了: 全チェックOK")
        return True


def main():
    # --file オプションの処理
    toc_path = DEFAULT_TOC_FILE
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            toc_path = Path(sys.argv[idx + 1])

    if not toc_path.exists():
        print(f"エラー: ファイルが存在しません: {toc_path}")
        return 1

    success = validate_toc(toc_path)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
