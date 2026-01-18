#!/usr/bin/env python3
"""
rules/.toc_work/ にpending YAMLテンプレートを生成するスクリプト

Usage:
    python3 .claude/skills/merge-rules-toc/create_pending_yaml.py [--full]

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

from toc_utils import get_project_root, load_config, should_exclude

# 設定読み込み
CONFIG = load_config('rules')
PROJECT_ROOT = get_project_root()
RULES_DIR = PROJECT_ROOT / CONFIG.get('root_dir', 'rules').rstrip('/')
TOC_WORK_DIR = RULES_DIR / CONFIG.get('work_dir', '.toc_work').rstrip('/')
CHECKSUMS_FILE = RULES_DIR / CONFIG.get('checksums_file', '.toc_checksums.yaml')
RULES_TOC_FILE = RULES_DIR / CONFIG.get('toc_file', 'rules_toc.yaml')
PATTERNS_CONFIG = CONFIG.get('patterns', {})
EXCLUDE_PATTERNS = PATTERNS_CONFIG.get('exclude', ['.toc_work', 'rules_toc.yaml', 'reference'])

# pending YAMLテンプレート
PENDING_TEMPLATE = """_meta:
  source_file: {source_file}
  status: pending
  updated_at: null

title: null
purpose: null
content_details: []
applicable_tasks: []
keywords: []
"""


def get_all_md_files():
    """対象の.mdファイル一覧を取得"""
    md_files = []
    target_glob = PATTERNS_CONFIG.get('target_glob', '**/*.md')

    for filepath in RULES_DIR.glob(target_glob):
        if should_exclude(filepath, RULES_DIR, EXCLUDE_PATTERNS):
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
    """rules/からの相対パスを取得"""
    return str(md_file.relative_to(RULES_DIR))


def get_yaml_filename(source_file):
    """source_fileからYAMLファイル名を生成"""
    return source_file.replace("/", "_").replace(".md", ".yaml")


def create_pending_yaml(source_file):
    """
    pending YAMLファイルを作成

    Returns:
        Path: 作成したファイルのパス、エラー時はNone
    """
    yaml_name = get_yaml_filename(source_file)
    yaml_path = TOC_WORK_DIR / yaml_name

    try:
        with open(yaml_path, "w") as f:
            f.write(PENDING_TEMPLATE.format(source_file=source_file))
        return yaml_path
    except (IOError, OSError, PermissionError) as e:
        print(f"⚠️ ファイル書き込みエラー: {yaml_path} - {e}")
        return None


def main():
    # オプション解析
    full_mode = "--full" in sys.argv

    # rules_toc.yaml が存在しない場合はfullモードを強制
    if not RULES_TOC_FILE.exists():
        full_mode = True
        print("rules_toc.yaml が存在しないため、fullモードで実行します")

    # checksums が存在しない場合もfullモードを強制
    if not full_mode and not CHECKSUMS_FILE.exists():
        full_mode = True
        print(".toc_checksums.yaml が存在しないため、fullモードで実行します")

    # 対象ファイル取得
    all_files = get_all_md_files()

    if full_mode:
        # fullモード: 全ファイルを対象
        target_files = all_files
        deleted_files = []
        print(f"fullモード: {len(target_files)}件のファイルを処理")
    else:
        # incrementalモード: 変更ファイルのみ
        old_checksums = load_checksums()
        current_files = {get_source_file_path(f): f for f in all_files}

        target_files = []

        # 新規・変更ファイルを検出
        for source_file, full_path in current_files.items():
            current_hash = calculate_file_hash(full_path)
            if current_hash is None:
                continue  # ハッシュ計算失敗はスキップ
            old_hash = old_checksums.get(source_file)

            if old_hash is None:
                print(f"  [新規] {source_file}")
                target_files.append(full_path)
            elif current_hash != old_hash:
                print(f"  [変更] {source_file}")
                target_files.append(full_path)

        # 削除ファイルを検出
        deleted_files = [
            sf for sf in old_checksums.keys()
            if sf not in current_files
        ]
        for sf in deleted_files:
            print(f"  [削除] {sf}")

        if not target_files and not deleted_files:
            print("変更なし - rules_toc.yaml は最新です")
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
    for md_file in target_files:
        source_file = get_source_file_path(md_file)
        yaml_path = create_pending_yaml(source_file)
        if yaml_path is None:
            failed_count += 1
            continue
        created_files.append(source_file)

    if failed_count > 0:
        print(f"\n⚠️ {failed_count}件のファイル作成に失敗しました")

    print(f"\n{len(created_files)}件のpending YAMLを作成しました:")
    for sf in created_files:
        print(f"  - {sf}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
