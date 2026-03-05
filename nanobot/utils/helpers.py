"""Utility functions for nanobot."""

import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from loguru import logger


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_data_path() -> Path:
    """Get the nanobot data directory (~/.nanobot)."""
    return ensure_dir(Path.home() / ".nanobot")


def get_workspace_path(workspace: str | None = None) -> Path:
    """
    Get the workspace path.
    
    Args:
        workspace: Optional workspace path. Defaults to ~/.nanobot/workspace.
    
    Returns:
        Expanded and ensured workspace path.
    """
    if workspace:
        path = Path(workspace).expanduser()
    else:
        path = Path.home() / ".nanobot" / "workspace"
    return ensure_dir(path)


def get_sessions_path() -> Path:
    """Get the sessions storage directory."""
    return ensure_dir(get_data_path() / "sessions")


def get_skills_path(workspace: Path | None = None) -> Path:
    """Get the skills directory within the workspace."""
    ws = workspace or get_workspace_path()
    return ensure_dir(ws / "skills")


def timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def truncate_string(s: str, max_len: int = 100, suffix: str = "...") -> str:
    """Truncate a string to max length, adding suffix if truncated."""
    if len(s) <= max_len:
        return s
    return s[: max_len - len(suffix)] + suffix


def safe_filename(name: str) -> str:
    """Convert a string to a safe filename."""
    # Replace unsafe characters
    unsafe = '<>:"/\\|?*'
    for char in unsafe:
        name = name.replace(char, "_")
    return name.strip()


def parse_session_key(key: str) -> tuple[str, str]:
    """
    Parse a session key into channel and chat_id.
    
    Args:
        key: Session key in format "channel:chat_id"
    
    Returns:
        Tuple of (channel, chat_id)
    """
    parts = key.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid session key: {key}")
    return parts[0], parts[1]


def get_bridge_dir() -> Path:
    """Get the bridge directory, setting it up if needed."""
    # User's bridge location
    user_bridge = Path.home() / ".nanobot" / "bridge"

    # Check if already built in user dir
    if (user_bridge / "dist" / "index.js").exists():
        return user_bridge

    # Find source bridge: first check package data, then source dir
    pkg_bridge = Path(__file__).parent.parent / "bridge"  # nanobot/bridge (installed)
    src_bridge = Path(__file__).parent.parent.parent / "bridge"  # repo root/bridge (dev)

    source = None
    if (pkg_bridge / "package.json").exists():
        source = pkg_bridge
    elif (src_bridge / "package.json").exists():
        source = src_bridge

    if not source:
        raise RuntimeError("WhatsApp bridge source not found. Try reinstalling: pip install --force-reinstall nanobot")

    # If source is already built (e.g. in Docker), just use it
    if (source / "dist" / "index.js").exists():
        return source

    # Check for npm
    if not shutil.which("npm"):
        raise RuntimeError("npm not found. Please install Node.js >= 18.")

    logger.info("Setting up WhatsApp bridge...")

    # Copy to user directory
    user_bridge.parent.mkdir(parents=True, exist_ok=True)
    if user_bridge.exists():
        shutil.rmtree(user_bridge)
    shutil.copytree(source, user_bridge, ignore=shutil.ignore_patterns("node_modules", "dist"))

    # Install and build
    try:
        logger.info("  Installing bridge dependencies...")
        subprocess.run(["npm", "install"], cwd=user_bridge, check=True, capture_output=True)

        logger.info("  Building bridge...")
        subprocess.run(["npm", "run", "build"], cwd=user_bridge, check=True, capture_output=True)

        logger.info("WhatsApp bridge ready")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        raise RuntimeError(f"WhatsApp bridge build failed: {stderr[:500]}")

    return user_bridge
