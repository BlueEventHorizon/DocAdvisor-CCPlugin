#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ToC自動生成機構 共通ユーティリティ

merge-rules-toc, merge-specs-toc, create-toc-checksums から共通利用される関数群。
標準ライブラリのみ使用。
"""

import re
import shutil
from pathlib import Path


def get_project_root():
    """
    プロジェクトルートを検出（.git または .claude ディレクトリを探す）

    Returns:
        Path: プロジェクトルートのパス

    Raises:
        RuntimeError: プロジェクトルートが見つからない場合
    """
    current = Path(__file__).parent.absolute()

    # 最大10階層まで遡る
    for _ in range(10):
        if (current / ".git").exists() or (current / ".claude").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    raise RuntimeError("プロジェクトルートが見つかりません（.git または .claude ディレクトリが必要）")


def load_config(target=None):
    """
    config.yaml を読み込み、設定辞書を返す

    Args:
        target: 'rules' または 'specs'。指定時はそのセクションのみ返す

    Returns:
        dict: 設定辞書
    """
    config_path = Path(__file__).parent / "config.yaml"

    if not config_path.exists():
        # デフォルト設定を返す
        defaults = _get_default_config()
        if target:
            return defaults.get(target, {})
        return defaults

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    config = _parse_config_yaml(content)

    if target:
        return config.get(target, {})
    return config


def _get_default_config():
    """デフォルト設定を返す"""
    return {
        'rules': {
            'root_dir': 'rules/',
            'toc_file': 'rules_toc.yaml',
            'checksums_file': '.toc_checksums.yaml',
            'work_dir': '.toc_work/',
            'patterns': {
                'target_glob': '**/*.md',
                'exclude': ['.toc_work', 'rules_toc.yaml', 'reference']
            },
            'output': {
                'header_comment': 'rules-advisor Subagent用 開発ドキュメント検索インデックス',
                'metadata_name': '開発ドキュメント検索インデックス'
            }
        },
        'specs': {
            'root_dir': 'specs/',
            'toc_file': 'specs_toc.yaml',
            'checksums_file': '.toc_checksums.yaml',
            'work_dir': '.toc_work/',
            'patterns': {
                'target_dirs': ['requirements', 'design'],
                'exclude': ['.toc_work', '.toc_checksums.yaml', 'specs_toc.yaml', 'reference', '/info/']
            },
            'output': {
                'header_comment': 'specs-advisor Subagent用 要件定義書・設計書検索インデックス',
                'metadata_name': '要件定義書・設計書検索インデックス'
            }
        },
        'common': {
            'parallel': {
                'max_workers': 5,
                'fallback_to_serial': True
            }
        }
    }


def _parse_config_yaml(content):
    """
    config.yaml をパース（シンプルなYAMLパーサー）
    """
    result = {}
    current_section = None
    current_subsection = None
    current_subsubsection = None
    current_list = None

    for line in content.split('\n'):
        stripped = line.strip()

        # コメントと空行をスキップ
        if not stripped or stripped.startswith('#'):
            continue

        # インデントレベルを計算
        indent = len(line) - len(line.lstrip())

        if ':' in stripped:
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip()

            if indent == 0:
                # トップレベルセクション
                current_section = key
                result[key] = {}
                current_subsection = None
                current_subsubsection = None
                current_list = None
            elif indent == 2 and current_section:
                # サブセクション
                current_subsection = key
                if value:
                    result[current_section][key] = _parse_value(value)
                else:
                    result[current_section][key] = {}
                current_subsubsection = None
                current_list = None
            elif indent == 4 and current_section and current_subsection:
                # サブサブセクション
                current_subsubsection = key
                if value:
                    result[current_section][current_subsection][key] = _parse_value(value)
                else:
                    result[current_section][current_subsection][key] = []
                    current_list = result[current_section][current_subsection][key]
        elif stripped.startswith('- ') and current_list is not None:
            item = stripped[2:].strip().strip('"\'')
            current_list.append(item)

    return result


def _parse_value(value):
    """値をパース（文字列、数値、真偽値）"""
    value = value.strip().strip('"\'')

    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False

    try:
        return int(value)
    except ValueError:
        pass

    return value


def parse_simple_yaml(content):
    """
    シンプルなYAMLパーサー（エントリファイル用）

    _meta セクションと通常のエントリを分離して返す。

    Args:
        content: YAMLファイルの内容

    Returns:
        tuple: (meta_dict, entry_dict)
    """
    result = {}
    current_key = None
    current_list = None
    in_meta = False
    meta = {}

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        if stripped == '_meta:':
            in_meta = True
            i += 1
            continue

        if in_meta:
            if line.startswith('  ') and ':' in stripped:
                key, _, value = stripped.partition(':')
                meta[key.strip()] = value.strip().strip('"\'')
            elif not line.startswith(' '):
                in_meta = False
            else:
                i += 1
                continue

        if not line.startswith(' ') and ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()

            if value:
                result[key] = value.strip('"\'')
                current_key = None
                current_list = None
            else:
                current_key = key
                current_list = []
                result[key] = current_list
            i += 1
            continue

        if current_list is not None and stripped.startswith('- '):
            item = stripped[2:].strip().strip('"\'')
            current_list.append(item)
            i += 1
            continue

        i += 1

    return meta, result


def load_entry_file(filepath):
    """
    エントリファイルを読み込みパース

    Args:
        filepath: ファイルパス（str または Path）

    Returns:
        tuple: (meta_dict, entry_dict)

    Raises:
        IOError: ファイル読み込みに失敗した場合
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return parse_simple_yaml(content)
    except (IOError, OSError, PermissionError) as e:
        raise IOError(f"エントリファイル読み込みエラー: {filepath} - {e}") from e


def yaml_escape(s):
    """
    YAML出力用に文字列をエスケープ

    Args:
        s: エスケープ対象の文字列

    Returns:
        str: エスケープ済み文字列
    """
    if not s:
        return '""'

    # 特殊文字のエスケープが必要かチェック
    needs_quotes = any(c in s for c in ':#{}[]&*!|>\'"%@`\n\r\t')
    needs_quotes = needs_quotes or s.startswith('-') or s.startswith(' ')

    if needs_quotes:
        # バックスラッシュを先にエスケープ、次にダブルクォート
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        # 改行・タブをエスケープ
        escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{escaped}"'

    return s


def backup_existing_file(file_path):
    """
    既存ファイルをバックアップ（.bak 拡張子付き）

    Args:
        file_path: バックアップ対象のファイルパス（str または Path）
    """
    file_path = Path(file_path)
    if file_path.exists():
        backup_path = file_path.with_suffix('.yaml.bak')
        shutil.copy(file_path, backup_path)
        print(f"バックアップ作成: {backup_path}")


def load_checksums(checksums_file):
    """
    チェックサムファイルからファイル一覧を取得

    Args:
        checksums_file: チェックサムファイルのパス（str または Path）

    Returns:
        set: ファイルパスの集合
    """
    checksums_file = Path(checksums_file)

    if not checksums_file.exists():
        return set()

    try:
        with open(checksums_file, 'r', encoding='utf-8') as f:
            content = f.read()

        files = set()
        in_checksums = False
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped == 'checksums:':
                in_checksums = True
                continue
            if in_checksums and ':' in stripped:
                filepath = stripped.split(':')[0].strip()
                files.add(filepath)

        return files
    except Exception as e:
        print(f"警告: チェックサムファイル読み込みエラー: {e}")
        print("フォールバック: 削除検出をスキップします")
        return set()


def cleanup_work_dir(work_dir):
    """
    作業ディレクトリを削除

    Args:
        work_dir: 削除対象のディレクトリパス（str または Path）

    Returns:
        bool: 成功時True、失敗時False
    """
    work_dir = Path(work_dir)
    if work_dir.exists():
        try:
            shutil.rmtree(work_dir)
            print(f"✅ クリーンアップ完了: {work_dir}")
            return True
        except (OSError, PermissionError) as e:
            print(f"⚠️ クリーンアップ失敗: {work_dir} - {e}")
            print("   手動で削除してください")
            return False
    return True


def extract_id_from_filename(filename):
    """
    ファイル名からドキュメントIDを抽出（汎用正規表現版）

    Args:
        filename: ファイル名（パスでも可）

    Returns:
        str or None: 抽出されたID、見つからない場合はNone

    Examples:
        'SCR-001_foo.md' → 'SCR-001'
        'DES-042_bar.md' → 'DES-042'
        'CUSTOM-123_baz.md' → 'CUSTOM-123'
    """
    # パスの場合はファイル名部分のみ取得
    if '/' in filename:
        filename = filename.split('/')[-1]

    # [A-Z]+-\d+ パターンでマッチ
    match = re.match(r'([A-Z]+-\d+)', filename)
    if match:
        return match.group(1)
    return None


def should_exclude(filepath, root_dir, exclude_patterns):
    """
    除外対象かどうかを判定

    Args:
        filepath: チェック対象のファイルパス（Path）
        root_dir: ルートディレクトリ（Path）
        exclude_patterns: 除外パターンのリスト

    Returns:
        bool: 除外対象ならTrue
    """
    rel_path = str(filepath.relative_to(root_dir))
    for pattern in exclude_patterns:
        if pattern in rel_path:
            return True
    return False
