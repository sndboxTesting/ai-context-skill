"""
path_validator.py — Robust path validation for Adwi.

Problem with string-prefix and regex-based guards:
  - "/etc/passwd" passes a check for "~/.ssh" prefix
  - "../../../etc/passwd" resolves outside workspace but looks local
  - Symlinks can escape any string-based check

This module uses pathlib.Path.resolve() to canonicalize ALL paths before any
comparison, then uses Path.relative_to() for containment checks — the only
correct way to verify that a path resides inside an allowed root.

Public API:
    validator = PathValidator(allowed_roots=[...], blocked_roots=[...])
    clean_path = validator.validate("/some/path")   # raises PathViolation on failure
    ok, reason = validator.check("/some/path")      # non-raising version

Design invariants:
  1. ALL inputs are canonicalized with .expanduser().resolve() before comparison.
  2. Blocked roots are checked BEFORE allowed roots (deny-first).
  3. Path containment uses relative_to(), never string prefix matching.
  4. Symlinks are resolved: a symlink pointing outside allowed roots is blocked.
  5. Nonexistent paths are accepted if must_exist=False (can validate before creation).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


# ── Exception ─────────────────────────────────────────────────────────────────


class PathViolation(Exception):
    """Raised when a path fails any security check."""

    def __init__(self, reason: str, path: Optional[str] = None) -> None:
        self.reason = reason
        self.path   = path
        super().__init__(f"PathViolation: {reason}" + (f" ({path!r})" if path else ""))


# ── Validator ─────────────────────────────────────────────────────────────────


class PathValidator:
    """
    Reusable path security gate.

    Parameters
    ----------
    allowed_roots : list[Path]
        If non-empty, validated paths must reside under at least ONE of these
        roots (after both roots and target are resolved).
        Pass [] to allow any path not explicitly blocked.
    blocked_roots : list[Path]
        Paths that are ALWAYS rejected regardless of allowed_roots.
        Checked first; overlaps with allowed_roots are always blocked.
    """

    def __init__(
        self,
        allowed_roots: list[Path],
        blocked_roots: list[Path],
    ) -> None:
        self._allowed: list[Path] = self._resolve_list(allowed_roots)
        self._blocked: list[Path] = self._resolve_list(blocked_roots)

    # ── Public API ────────────────────────────────────────────────────────────

    def validate(self, path: str | Path, must_exist: bool = False) -> Path:
        """
        Return the canonicalized path if it passes all checks.

        Raises PathViolation if:
          - the path cannot be resolved (OSError in resolve)
          - the path is under any blocked root
          - the path is not under any allowed root (when allowed_roots != [])
          - must_exist=True and the path does not exist on disk
        """
        canonical = self._canonicalize(path)

        # Blocked roots: deny-first
        for blocked in self._blocked:
            if _is_inside_or_equal(canonical, blocked):
                raise PathViolation(
                    f"path is inside blocked root {blocked}",
                    str(canonical),
                )

        # Allowed roots: if specified, the path must be in at least one
        if self._allowed:
            if not any(_is_inside_or_equal(canonical, root) for root in self._allowed):
                raise PathViolation(
                    "path is outside all allowed roots",
                    str(canonical),
                )

        if must_exist and not canonical.exists():
            raise PathViolation("path does not exist", str(canonical))

        return canonical

    def check(self, path: str | Path, must_exist: bool = False) -> tuple[bool, str]:
        """
        Non-raising version of validate().
        Returns (True, "") on success, (False, reason_string) on failure.
        """
        try:
            self.validate(path, must_exist=must_exist)
            return True, ""
        except PathViolation as exc:
            return False, exc.reason
        except Exception as exc:
            return False, str(exc)

    def is_blocked(self, path: str | Path) -> bool:
        """True if `path` resolves to inside any blocked root."""
        try:
            canonical = self._canonicalize(path)
        except PathViolation:
            return True
        return any(_is_inside_or_equal(canonical, b) for b in self._blocked)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _canonicalize(self, path: str | Path) -> Path:
        """
        Expand ~ and resolve symlinks.
        Uses strict=False so nonexistent paths are still canonicalized
        (their parents are resolved and the final component is kept as-is).
        """
        try:
            p = Path(path).expanduser()
            # resolve(strict=False) follows symlinks for all *existing* components
            # and lexically resolves .. for the rest — prevents .. traversal.
            return p.resolve()
        except (OSError, ValueError) as exc:
            raise PathViolation(f"cannot canonicalize path: {exc}", str(path)) from exc

    @staticmethod
    def _resolve_list(paths: list[Path]) -> list[Path]:
        out: list[Path] = []
        for p in paths:
            try:
                out.append(Path(p).expanduser().resolve())
            except Exception:
                pass  # skip unresolvable roots at init time
        return out


# ── Containment check ─────────────────────────────────────────────────────────


def _is_inside_or_equal(child: Path, parent: Path) -> bool:
    """
    Returns True if `child` is `parent` itself or is contained within `parent`.

    Uses relative_to() which raises ValueError if child is NOT under parent.
    This is the ONLY correct containment check — string prefix matching breaks
    on path components of different lengths ("/tmp" vs "/tmpfoo").
    """
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


# ── Pre-configured validators ─────────────────────────────────────────────────


def make_workspace_validator(
    workspace: Optional[Path] = None,
    extra_allowed: Optional[list[Path]] = None,
) -> PathValidator:
    """
    Return a validator pre-configured with Adwi's security policy:
      - Blocked: all credential/system paths from HARD_BLOCKED
      - Allowed: workspace + optional extra roots

    This is the recommended single validator to import into adwi_cli.py
    and memory.py to replace the current safe_to_read() / is_hard_blocked().
    """
    home = Path.home()
    ws   = workspace or (home / "SuneelWorkSpace")

    hard_blocked = [
        ws / "secrets",
        home / ".ssh",
        home / ".gnupg",
        home / ".aws",
        home / ".kube",
        home / ".config" / "gcloud",
        home / ".npmrc",
        home / ".netrc",
        home / "Library" / "Keychains",
        home / "Library" / "Passwords",
        Path("/etc"),
        Path("/private"),
        Path("/System"),
        Path("/usr/lib"),
    ]

    allowed = [ws, home / "Desktop", home / "Documents", home / "Downloads"]
    if extra_allowed:
        allowed.extend(extra_allowed)

    return PathValidator(allowed_roots=allowed, blocked_roots=hard_blocked)
