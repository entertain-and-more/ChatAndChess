#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manage_translations.py - Multi-Language Translation Manager & CI Gate.

Manages, validates, and audits locales/translations.json according to
Policy P-006 Tier-2 (DE, EN, ES, ZH, JA, RU) for ChatAndChess.

Commands:
- Strict 6-language parity check (--check) for CI / automated gates (Exit 0/1)
- Formatted statistics table (--stats) with key counts and coverage per language
- Source scanner (--scan) detecting UI string usage across python files
- Atomic persistence with fsync and staging file (.tmp.<pid>)
"""

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Defensive UTF-8 console output for Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

SUPPORTED_LANGUAGES: List[str] = ["de", "en", "es", "zh", "ja", "ru"]
REFERENCE_LANGUAGE: str = "de"

LANGUAGE_LABELS: Dict[str, str] = {
    "de": "Deutsch (DE) - Referenz",
    "en": "English (EN)",
    "es": "Español (ES)",
    "zh": "简体中文 (ZH)",
    "ja": "日本語 (JA)",
    "ru": "Русский (RU)",
}


def get_default_catalog_path(base_dir: Optional[Path] = None) -> Path:
    """Resolve default path to translations.json."""
    root = base_dir or Path(__file__).resolve().parent
    return root / "locales" / "translations.json"


def load_translations(catalog_path: Path) -> Dict[str, Dict[str, str]]:
    """Load translations catalog JSON safely."""
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Translations file not found: {catalog_path}")
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Invalid format: root must be a JSON object")
    catalog: Dict[str, Dict[str, str]] = {}
    for lang in SUPPORTED_LANGUAGES:
        catalog[lang] = {}
        if lang in data and isinstance(data[lang], dict):
            catalog[lang] = {str(k): str(v) for k, v in data[lang].items()}
    return catalog


def atomic_save_translations(catalog_path: Path, data: Dict[str, Dict[str, str]]) -> None:
    """Save translations atomically using staging file and fsync."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = catalog_path.with_name(f"{catalog_path.name}.tmp.{os.getpid()}")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

        # Ensure target file is writable if it exists
        if catalog_path.exists():
            try:
                catalog_path.chmod(stat.S_IWRITE | stat.S_IREAD)
            except Exception:
                pass

        os.replace(temp_path, catalog_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


def audit_parity(catalog: Dict[str, Dict[str, str]]) -> Tuple[bool, Dict[str, List[str]], Dict[str, List[str]]]:
    """Audit translations for parity against reference language.

    Returns:
        (is_valid, missing_per_lang, empty_per_lang)
    """
    ref_keys = set(catalog.get(REFERENCE_LANGUAGE, {}).keys())
    missing_per_lang: Dict[str, List[str]] = {}
    empty_per_lang: Dict[str, List[str]] = {}
    is_valid = True

    if not ref_keys:
        return False, {"all": ["Reference language 'de' has no keys"]}, {}

    for lang in SUPPORTED_LANGUAGES:
        lang_keys = set(catalog.get(lang, {}).keys())
        missing = sorted(list(ref_keys - lang_keys))
        if missing:
            missing_per_lang[lang] = missing
            is_valid = False

        empty = [k for k, v in catalog.get(lang, {}).items() if not v or not str(v).strip()]
        if empty:
            empty_per_lang[lang] = sorted(empty)
            is_valid = False

    return is_valid, missing_per_lang, empty_per_lang


def print_stats(catalog: Dict[str, Dict[str, str]]) -> None:
    """Print formatted statistics table."""
    ref_keys = set(catalog.get(REFERENCE_LANGUAGE, {}).keys())
    total_ref = len(ref_keys)

    print("=" * 72)
    print("ChatAndChess - Multi-Language Translation Statistics (Policy P-006 Tier-2)")
    print("=" * 72)
    print(f"{'Sprache / Language':<28} | {'Total':<6} | {'Gefüllt':<8} | {'Fehlend':<8} | {'Deckung'}")
    print("-" * 72)

    for lang in SUPPORTED_LANGUAGES:
        label = LANGUAGE_LABELS.get(lang, lang)
        cur_dict = catalog.get(lang, {})
        filled = sum(1 for k in ref_keys if cur_dict.get(k, "").strip())
        missing = total_ref - filled
        pct = (filled / total_ref * 100.0) if total_ref > 0 else 0.0
        print(f"{label:<28} | {total_ref:<6} | {filled:<8} | {missing:<8} | {pct:6.1f}%")

    print("=" * 72)


def scan_source_keys(base_dir: Path) -> Set[str]:
    """Scan Python sources for translation keys used via tr(...) or t(...)."""
    found_keys: Set[str] = set()
    patterns = [
        re.compile(r'\b(?:tr|t)\(\s*["\']([a-zA-Z0-9_-]+)["\']'),
        re.compile(r'\b(?:tr|t)\(\s*key\s*=\s*["\']([a-zA-Z0-9_-]+)["\']'),
    ]

    for py_file in base_dir.glob("*.py"):
        if py_file.name in ("manage_translations.py",):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            for pat in patterns:
                for match in pat.finditer(content):
                    found_keys.add(match.group(1))
        except Exception:
            pass

    for py_file in (base_dir / "tests").glob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            for pat in patterns:
                for match in pat.finditer(content):
                    found_keys.add(match.group(1))
        except Exception:
            pass

    return found_keys


def main() -> int:
    """CLI entry point for manage_translations."""
    parser = argparse.ArgumentParser(
        description="ChatAndChess Translation Manager & CI Parity Gate (Policy P-006)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check 100% translation parity across all 6 Tier-2 languages (CI Gate).",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display translation coverage statistics.",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan python source files for used translation keys.",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Specify project root directory (default: script parent directory).",
    )

    args = parser.parse_args()
    base_dir = Path(args.dir).resolve() if args.dir else Path(__file__).resolve().parent
    catalog_path = get_default_catalog_path(base_dir)

    try:
        catalog = load_translations(catalog_path)
    except Exception as e:
        sys.stderr.write(f"ERROR: Could not load translations: {e}\n")
        return 1

    if args.check:
        is_valid, missing, empty = audit_parity(catalog)
        if not is_valid:
            print("Translation Parity Gate: FAILED", file=sys.stderr)
            for lang, keys in missing.items():
                print(f"  Missing in [{lang}] ({len(keys)} keys): {', '.join(keys[:10])}", file=sys.stderr)
            for lang, keys in empty.items():
                print(f"  Empty in [{lang}] ({len(keys)} keys): {', '.join(keys[:10])}", file=sys.stderr)
            return 1
        print("Translation Parity Gate: PASS (100% parity across all 6 languages)")
        return 0

    if args.scan:
        used_keys = scan_source_keys(base_dir)
        catalog_keys = set(catalog.get(REFERENCE_LANGUAGE, {}).keys())
        missing_in_catalog = sorted(list(used_keys - catalog_keys))
        unused_in_catalog = sorted(list(catalog_keys - used_keys))

        print(f"Source Scan: {len(used_keys)} keys detected in code.")
        print(f"Catalog contains: {len(catalog_keys)} keys in reference '{REFERENCE_LANGUAGE}'.")
        if missing_in_catalog:
            print(f"WARNING: {len(missing_in_catalog)} keys used in code but missing in catalog:")
            for k in missing_in_catalog:
                print(f"  - {k}")
        else:
            print("All code-referenced keys exist in translation catalog.")
        if unused_in_catalog:
            print(f"Info: {len(unused_in_catalog)} catalog keys not directly matched via simple regex scan.")
        return 0

    # Default action if neither --check nor --scan is explicitly passed: show stats
    print_stats(catalog)
    is_valid, _, _ = audit_parity(catalog)
    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
