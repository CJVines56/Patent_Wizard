from __future__ import annotations

import re
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET


DEFAULT_CPC_SCHEME_ZIP = Path(__file__).resolve().parents[2] / "CPCSchemeXML202601.zip"
_CODE_PATTERN = re.compile(r"[A-HY]\s*\d{2}\s*[A-Z](?:\s*\d+(?:\s*/\s*\d+)?)?", re.IGNORECASE)
_WHITESPACE_PATTERN = re.compile(r"\s+")


def _clean_text(text: str) -> str:
    return _WHITESPACE_PATTERN.sub(" ", text).strip(" ;,\n\t")


def _normalize_symbol(raw: Any) -> str:
    if raw is None:
        return ""
    compact = _WHITESPACE_PATTERN.sub("", str(raw).upper())
    return compact.strip(" ;,.\n\t")


def extract_cpc_codes(value: Any) -> List[str]:
    """Extract normalized CPC symbols from free-form text, strings, or lists."""
    candidates: List[str] = []

    if value is None:
        return candidates

    if isinstance(value, str):
        for match in _CODE_PATTERN.findall(value):
            symbol = _normalize_symbol(match)
            if symbol:
                candidates.append(symbol)
        if not candidates:
            fallback = _normalize_symbol(value)
            if re.match(r"^[A-HY]\d{2}[A-Z]", fallback):
                candidates.append(fallback)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            candidates.extend(extract_cpc_codes(item))
    else:
        candidates.extend(extract_cpc_codes(str(value)))

    deduped: List[str] = []
    seen = set()
    for symbol in candidates:
        if symbol and symbol not in seen:
            seen.add(symbol)
            deduped.append(symbol)
    return deduped


def _extract_item_title(item: ET.Element) -> str:
    parts: List[str] = []

    for title_part in item.findall("./class-title/title-part"):
        text = _clean_text(" ".join(title_part.itertext()))
        if text:
            parts.append(text)

    if not parts:
        class_title = item.find("./class-title")
        if class_title is not None:
            fallback = _clean_text(" ".join(class_title.itertext()))
            if fallback:
                parts.append(fallback)

    deduped: List[str] = []
    seen = set()
    for part in parts:
        if part not in seen:
            seen.add(part)
            deduped.append(part)

    return "; ".join(deduped)


@lru_cache(maxsize=2)
def _load_cpc_title_index(zip_path_str: str) -> Dict[str, str]:
    zip_path = Path(zip_path_str)
    if not zip_path.exists():
        return {}

    index: Dict[str, str] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if not member.lower().endswith(".xml"):
                continue
            with archive.open(member) as fh:
                try:
                    root = ET.parse(fh).getroot()
                except ET.ParseError:
                    continue

            for item in root.iter("classification-item"):
                symbol_el = item.find("./classification-symbol")
                if symbol_el is None or not symbol_el.text:
                    continue
                symbol = _normalize_symbol(symbol_el.text)
                if not symbol:
                    continue

                title = _extract_item_title(item)
                if not title:
                    continue

                existing = index.get(symbol)
                if existing is None or len(title) > len(existing):
                    index[symbol] = title

    return index


def _candidate_symbols(symbol: str) -> List[str]:
    normalized = _normalize_symbol(symbol)
    if not normalized:
        return []

    candidates: List[str] = [normalized]

    if "/" in normalized:
        prefix, subgroup = normalized.split("/", 1)
        subgroup_digits = re.sub(r"\D", "", subgroup)
        if subgroup_digits:
            for width in range(len(subgroup_digits) - 1, 0, -1):
                candidates.append(f"{prefix}/{subgroup_digits[:width]}")
        candidates.append(f"{prefix}/00")
    else:
        if re.match(r"^[A-HY]\d{2}[A-Z]\d+$", normalized):
            candidates.append(f"{normalized}/00")

    if re.match(r"^[A-HY]\d{2}[A-Z]", normalized):
        candidates.append(normalized[:4])  # subclass
        candidates.append(normalized[:3])  # class
        candidates.append(normalized[:1])  # section

    deduped: List[str] = []
    seen = set()
    for code in candidates:
        if code and code not in seen:
            seen.add(code)
            deduped.append(code)
    return deduped


def get_cpc_title(symbol: str, zip_path: Optional[Path] = None) -> Optional[str]:
    """Return a human-readable title for a CPC symbol, with hierarchical fallback."""
    path = str(zip_path or DEFAULT_CPC_SCHEME_ZIP)
    index = _load_cpc_title_index(path)

    for candidate in _candidate_symbols(symbol):
        title = index.get(candidate)
        if title:
            return title
    return None


def describe_cpc_symbol(symbol: str, zip_path: Optional[Path] = None) -> Dict[str, Any]:
    """Return normalized CPC symbol metadata with best-match and hierarchy context."""
    normalized = _normalize_symbol(symbol)
    path = str(zip_path or DEFAULT_CPC_SCHEME_ZIP)
    index = _load_cpc_title_index(path)

    matched_code: Optional[str] = None
    matched_title: Optional[str] = None
    for candidate in _candidate_symbols(normalized):
        title = index.get(candidate)
        if title:
            matched_code = candidate
            matched_title = title
            break

    hierarchy: List[Dict[str, str]] = []
    if normalized and re.match(r"^[A-HY]\d{2}[A-Z]", normalized):
        level_candidates = [normalized[:1], normalized[:3], normalized[:4]]

        if "/" in normalized:
            level_candidates.append(f"{normalized.split('/', 1)[0]}/00")
        elif re.match(r"^[A-HY]\d{2}[A-Z]\d+$", normalized):
            level_candidates.append(f"{normalized}/00")

        if matched_code:
            level_candidates.append(matched_code)

        seen = set()
        for code in level_candidates:
            if code in seen:
                continue
            seen.add(code)
            title = index.get(code)
            if title:
                hierarchy.append({"code": code, "title": title})

    return {
        "input": symbol,
        "normalized": normalized,
        "matched_code": matched_code,
        "topic": matched_title,
        "hierarchy": hierarchy,
    }


def describe_cpc_codes(value: Any, zip_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Describe one or more CPC symbols from free-form input."""
    out: List[Dict[str, Any]] = []
    for symbol in extract_cpc_codes(value):
        out.append(describe_cpc_symbol(symbol, zip_path=zip_path))
    return out
