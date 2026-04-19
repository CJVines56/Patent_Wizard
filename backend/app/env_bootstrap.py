from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[2]

_LOADED = False


def load_project_env() -> None:
    global _LOADED
    if _LOADED:
        return

    orchestrator_dir = REPO_ROOT / "backend" / "orchestrator"
    for env_path in (orchestrator_dir / ".env", orchestrator_dir / "env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)

    _LOADED = True


def coerce_path_string(raw: str | None, *, base_dir: Path | None = None) -> Path | None:
    value = str(raw or "").strip()
    if not value:
        return None

    if len(value) >= 3 and value[1] == ":" and value[2] in {"\\", "/"}:
        drive = value[0].lower()
        suffix = value[2:].replace("\\", "/").lstrip("/")
        return Path(f"/mnt/{drive}/{suffix}").resolve()

    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()

    anchor = base_dir or REPO_ROOT
    return (anchor / path).resolve()
