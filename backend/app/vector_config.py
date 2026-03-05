from __future__ import annotations

import os
from pathlib import Path


ALLOWED_TOKEN_DTYPES = {"float16", "float32"}
ALLOWED_VARIANTS = {"128_f16", "128_f32"}


def _as_bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _parse_variants(raw: str) -> set[str]:
    value = (raw or "").strip().lower()
    if value in {"all", "*"}:
        return set(ALLOWED_VARIANTS)
    parsed = {v.strip().lower() for v in value.split(",") if v.strip()}
    return parsed


TOKEN_VECTOR_DIM = int(os.environ.get("TOKEN_VECTOR_DIM", "128"))
PROJECTION_MODE = os.environ.get("PROJECTION_MODE", "trained").strip().lower()
PROJECTION_PATH_RAW = os.environ.get("PROJECTION_PATH", "").strip()
TOKEN_VECTOR_DTYPE = os.environ.get("TOKEN_VECTOR_DTYPE", "float16").strip().lower()
COLBERT_VARIANTS_RAW = os.environ.get("COLBERT_VARIANTS", "128_f16")
WEAVIATE_NAMED_VECTOR = os.environ.get("WEAVIATE_NAMED_VECTOR", "colbert").strip() or "colbert"
DEBUG_VECTOR_COMPARE = _as_bool(os.environ.get("DEBUG_VECTOR_COMPARE", "0"))


if TOKEN_VECTOR_DIM != 128:
    raise ValueError(
        f"TOKEN_VECTOR_DIM must be exactly 128. Got {TOKEN_VECTOR_DIM}. "
        "768-d mode is forbidden by configuration."
    )

if PROJECTION_MODE != "trained":
    raise ValueError(
        f"PROJECTION_MODE must be exactly 'trained'. Got '{PROJECTION_MODE}'. "
        "Random/PCA/runtime fallback projection modes are forbidden."
    )

if TOKEN_VECTOR_DTYPE not in ALLOWED_TOKEN_DTYPES:
    raise ValueError(
        f"TOKEN_VECTOR_DTYPE must be one of {sorted(ALLOWED_TOKEN_DTYPES)}. "
        f"Got '{TOKEN_VECTOR_DTYPE}'."
    )

if not PROJECTION_PATH_RAW:
    raise ValueError(
        "PROJECTION_PATH is required and must point to trained projection weights on disk."
    )

PROJECTION_PATH = Path(PROJECTION_PATH_RAW).expanduser().resolve()
if not PROJECTION_PATH.exists():
    raise FileNotFoundError(
        f"PROJECTION_PATH does not exist: {PROJECTION_PATH}. "
        "Cannot continue without trained projection weights."
    )

ENABLED_COLBERT_VARIANTS = _parse_variants(COLBERT_VARIANTS_RAW)
if not ENABLED_COLBERT_VARIANTS:
    raise ValueError(
        "COLBERT_VARIANTS resolved to empty set. "
        "Expected one of: 128_f16, 128_f32."
    )
if any("768" in v for v in ENABLED_COLBERT_VARIANTS):
    raise ValueError(
        f"768 variants are forbidden. Requested variants: {sorted(ENABLED_COLBERT_VARIANTS)}"
    )
unknown = ENABLED_COLBERT_VARIANTS.difference(ALLOWED_VARIANTS)
if unknown:
    raise ValueError(
        f"Unknown COLBERT_VARIANTS: {sorted(unknown)}. "
        f"Allowed: {sorted(ALLOWED_VARIANTS)}."
    )

PRIMARY_COLBERT_VARIANT = "128_f16" if TOKEN_VECTOR_DTYPE == "float16" else "128_f32"
if PRIMARY_COLBERT_VARIANT not in ENABLED_COLBERT_VARIANTS:
    raise ValueError(
        f"Primary variant '{PRIMARY_COLBERT_VARIANT}' is missing from COLBERT_VARIANTS={sorted(ENABLED_COLBERT_VARIANTS)}."
    )


def assert_128_variant(variant: str, *, context: str = "") -> str:
    v = str(variant or "").strip().lower()
    if "768" in v:
        raise ValueError(
            f"768 variant '{variant}' is forbidden"
            + (f" ({context})" if context else "")
            + "."
        )
    if v not in ALLOWED_VARIANTS:
        raise ValueError(
            f"Unsupported variant '{variant}'"
            + (f" ({context})" if context else "")
            + f". Allowed: {sorted(ALLOWED_VARIANTS)}."
        )
    return v

