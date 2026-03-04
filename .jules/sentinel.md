## 2025-02-12 - [Critical Path Traversal in Filesystem Tools]
**Vulnerability:** Use of `str.startswith()` on resolved paths for sandbox restriction was flawed. A directory named `workspace_secret` would incorrectly match a restriction to `workspace`.
**Learning:** Path-based security checks must be component-aware, not just string-based.
**Prevention:** Use `Path.is_relative_to(allowed_dir)` (available since Python 3.9) instead of `str(resolved).startswith(str(allowed_dir))`.
