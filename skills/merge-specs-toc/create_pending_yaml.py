#!/usr/bin/env python3
"""
specs/.toc_work/ にpending YAMLテンプレートを生成するスクリプト

Usage:
    python3 .claude/skills/merge-specs-toc/create_pending_yaml.py [--full]

Options:
    --full    全ファイルを対象にする（デフォルト: 変更ファイルのみ）

実行ディレクトリ: プロジェクトルート
"""

import os
import sys
import hashlib
import re
from pathlib import Path

# 共通モジュールのパスを追加
COMMON_DIR = Path(__file__).parent.parent / "toc-common"
sys.path.insert(0, str(COMMON_DIR))

from toc_utils import get_project_root, load_config, should_exclude, extract_id_from_filename

# 設定読み込み
CONFIG = load_config('specs')
PROJECT_ROOT = get_project_root()
SPECS_DIR = PROJECT_ROOT / CONFIG.get('root_dir', 'specs').rstrip('/')
TOC_WORK_DIR = SPECS_DIR / CONFIG.get('work_dir', '.toc_work').rstrip('/')
CHECKSUMS_FILE = SPECS_DIR / CONFIG.get('checksums_file', '.toc_checksums.yaml')
SPECS_TOC_FILE = SPECS_DIR / CONFIG.get('toc_file', 'specs_toc.yaml')
PATTERNS_CONFIG = CONFIG.get('patterns', {})
TARGET_DIRS = PATTERNS_CONFIG.get('target_dirs', ['requirements', 'design'])
EXCLUDE_PATTERNS = PATTERNS_CONFIG.get('exclude', ['.toc_work', '.toc_checksums.yaml', 'specs_toc.yaml', 'reference', '/info/'])

# pending YAMLテンプレート（要件定義書用）
PENDING_SPEC_TEMPLATE = """_meta:
  source_file: {source_file}
  doc_type: spec
  status: pending
  updated_at: null

id: {id}
feature: null
category: null
title: null
summary: null
keywords: []
file: null
"""

# pending YAMLテンプレート（設計書用）
PENDING_DESIGN_TEMPLATE = """_meta:
  source_file: {source_file}
  doc_type: design
  status: pending
  updated_at: null

id: {id}
feature: null
category: 設計書
layer: null
title: null
summary: null
keywords: []
file: null
"""


def is_target_dir(filepath):
    """対象ディレクトリ配下かどうかを判定"""
    rel_path = str(filepath.relative_to(SPECS_DIR))
    parts = rel_path.split('/')
    if len(parts) >= 2:
        return parts[1] in TARGET_DIRS
    return False


def get_all_md_files():
    """対象の.mdファイル一覧を取得"""
    md_files = []

    for filepath in SPECS_DIR.rglob("*.md"):
        if should_exclude(filepath, SPECS_DIR, EXCLUDE_PATTERNS):
            continue
        if not is_target_dir(filepath):
            continue
        md_files.append(filepath)

    md_files.sort()
    return md_files


def calculate_file_hash(filepath):
    """
    ファイルのSHA256ハッシュを計算

    Returns:
        str: ハッシュ値、エラー時はNone
    """
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except (IOError, OSError, PermissionError) as e:
        print(f"⚠️ ファイル読み込みエラー: {filepath} - {e}")
        return None


def load_checksums():
    """既存のチェックサムファイルを読み込み（標準ライブラリのみ）"""
    if not CHECKSUMS_FILE.exists():
        return {}

    checksums = {}
    with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
        in_checksums = False
        for line in f:
            stripped = line.strip()
            if stripped == "checksums:":
                in_checksums = True
                continue
            if in_checksums and stripped and not stripped.startswith("#"):
                match = re.match(r"^\s+(.+?):\s*([a-f0-9]+)\s*$", line)
                if match:
                    filepath = match.group(1)
                    hash_val = match.group(2)
                    checksums[filepath] = hash_val

    return checksums


def get_source_file_path(md_file):
    """specs/からの相対パスを取得"""
    return str(md_file.relative_to(SPECS_DIR))


def get_doc_type(source_file):
    """パスからdoc_typeを判定"""
    if "/requirements/" in source_file:
        return "spec"
    elif "/design/" in source_file:
        return "design"
    return None


def create_pending_yaml(source_file, doc_id, doc_type):
    """
    pending YAMLファイルを作成

    Returns:
        Path: 作成したファイルのパス、エラー時はNone
    """
    yaml_name = f"{doc_id}.yaml"
    yaml_path = TOC_WORK_DIR / yaml_name

    if doc_type == "design":
        template = PENDING_DESIGN_TEMPLATE
    else:
        template = PENDING_SPEC_TEMPLATE

    try:
        with open(yaml_path, "w") as f:
            f.write(template.format(source_file=source_file, id=doc_id))
        return yaml_path
    except (IOError, OSError, PermissionError) as e:
        print(f"⚠️ ファイル書き込みエラー: {yaml_path} - {e}")
        return None


def main():
    # オプション解析
    full_mode = "--full" in sys.argv

    # specs_toc.yaml が存在しない場合はfullモードを強制
    if not SPECS_TOC_FILE.exists():
        full_mode = True
        print("specs_toc.yaml が存在しないため、fullモードで実行します")

    # checksums が存在しない場合もfullモードを強制
    if not full_mode and not CHECKSUMS_FILE.exists():
        full_mode = True
        print(".toc_checksums.yaml が存在しないため、fullモードで実行します")

    # 対象ファイル取得
    all_files = get_all_md_files()

    # IDを抽出できないファイルを警告
    files_without_id = []
    valid_files = []
    for f in all_files:
        doc_id = extract_id_from_filename(str(f))
        if doc_id is None:
            files_without_id.append(f)
        else:
            valid_files.append((f, doc_id))

    if files_without_id:
        print(f"警告: {len(files_without_id)}件のファイルにIDがありません:")
        for f in files_without_id:
            print(f"  - {f}")
        print()

    if full_mode:
        # fullモード: 全ファイルを対象
        target_files = valid_files
        deleted_files = []
        print(f"fullモード: {len(target_files)}件のファイルを処理")
    else:
        # incrementalモード: 変更ファイルのみ
        old_checksums = load_checksums()
        current_files = {get_source_file_path(f): (f, doc_id) for f, doc_id in valid_files}

        target_files = []

        # 新規・変更ファイルを検出
        for source_file, (full_path, doc_id) in current_files.items():
            current_hash = calculate_file_hash(full_path)
            if current_hash is None:
                continue  # ハッシュ計算失敗はスキップ
            old_hash = old_checksums.get(source_file)

            if old_hash is None:
                print(f"  [新規] {source_file}")
                target_files.append((full_path, doc_id))
            elif current_hash != old_hash:
                print(f"  [変更] {source_file}")
                target_files.append((full_path, doc_id))

        # 削除ファイルを検出
        deleted_files = [
            sf for sf in old_checksums.keys()
            if sf not in current_files
        ]
        for sf in deleted_files:
            print(f"  [削除] {sf}")

        if not target_files and not deleted_files:
            print("変更なし - specs_toc.yaml は最新です")
            return 0

        if not target_files and deleted_files:
            print(f"\n削除ファイルのみ: {len(deleted_files)}件")
            print("マージスクリプトで --delete-only を使用してください")
            return 0

        print(f"\nincrementalモード: {len(target_files)}件の変更, {len(deleted_files)}件の削除")

    # .toc_work ディレクトリ作成
    TOC_WORK_DIR.mkdir(parents=True, exist_ok=True)

    # pending YAML生成
    created_files = []
    failed_count = 0
    for md_file, doc_id in target_files:
        source_file = get_source_file_path(md_file)
        doc_type = get_doc_type(source_file)
        if doc_type is None:
            print(f"警告: doc_type判定不可 - {source_file}")
            continue
        yaml_path = create_pending_yaml(source_file, doc_id, doc_type)
        if yaml_path is None:
            failed_count += 1
            continue
        created_files.append((doc_id, source_file))

    if failed_count > 0:
        print(f"\n⚠️ {failed_count}件のファイル作成に失敗しました")

    print(f"\n{len(created_files)}件のpending YAMLを作成しました:")
    for doc_id, sf in created_files:
        print(f"  - {doc_id}: {sf}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
