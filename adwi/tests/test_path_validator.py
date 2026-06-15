"""
tests/test_path_validator.py — Unit tests for PathValidator.

Run:
    python3 -m pytest adwi/tests/test_path_validator.py -v

Tests cover:
  - Normal paths inside workspace allowed
  - Dotdot traversal (../../) rejected
  - Symlink pointing outside allowed roots blocked
  - Blocked-root overlap (workspace/secrets) rejected
  - Relative paths canonicalized correctly
  - Non-existent paths accepted (must_exist=False) or rejected (must_exist=True)
  - check() returns (True, "") on success and (False, reason) on failure
  - is_blocked() convenience predicate
  - Empty allowed_roots = allow-everything-except-blocked mode
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adwi.path_validator import PathValidator, PathViolation, _is_inside_or_equal


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_validator(
    allowed: list[Path],
    blocked: list[Path],
) -> PathValidator:
    return PathValidator(allowed_roots=allowed, blocked_roots=blocked)


# ── Containment primitive ─────────────────────────────────────────────────────


class TestIsInsideOrEqual(unittest.TestCase):
    def test_child_is_inside_parent(self):
        self.assertTrue(_is_inside_or_equal(Path("/a/b/c"), Path("/a/b")))

    def test_parent_equals_child(self):
        self.assertTrue(_is_inside_or_equal(Path("/a/b"), Path("/a/b")))

    def test_sibling_is_not_inside(self):
        self.assertFalse(_is_inside_or_equal(Path("/a/c"), Path("/a/b")))

    def test_common_prefix_different_component(self):
        # /tmpfoo should NOT match /tmp
        self.assertFalse(_is_inside_or_equal(Path("/tmpfoo/bar"), Path("/tmp")))

    def test_parent_not_inside_child(self):
        self.assertFalse(_is_inside_or_equal(Path("/a"), Path("/a/b")))


# ── PathViolation exception ───────────────────────────────────────────────────


class TestPathViolation(unittest.TestCase):
    def test_str_includes_reason(self):
        exc = PathViolation("some reason", "/bad/path")
        self.assertIn("some reason", str(exc))
        self.assertIn("/bad/path", str(exc))

    def test_path_attribute(self):
        exc = PathViolation("blocked", "/x")
        self.assertEqual(exc.path, "/x")

    def test_reason_attribute(self):
        exc = PathViolation("test reason")
        self.assertEqual(exc.reason, "test reason")
        self.assertIsNone(exc.path)


# ── Validator — normal access ─────────────────────────────────────────────────


class TestNormalAccess(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.allowed = Path(self.tmpdir) / "workspace"
        self.allowed.mkdir()
        self.blocked = Path(self.tmpdir) / "secrets"
        self.blocked.mkdir()
        self.v = _make_validator(
            allowed=[self.allowed],
            blocked=[self.blocked],
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_path_inside_allowed_accepted(self):
        target = self.allowed / "file.txt"
        result = self.v.validate(target)
        self.assertEqual(result, target.resolve())

    def test_nested_path_inside_allowed_accepted(self):
        (self.allowed / "subdir").mkdir()
        target = self.allowed / "subdir" / "deep.md"
        result = self.v.validate(target)
        self.assertEqual(result, target.resolve())

    def test_must_exist_false_for_nonexistent(self):
        target = self.allowed / "nonexistent.txt"
        result = self.v.validate(target, must_exist=False)
        self.assertEqual(result.name, "nonexistent.txt")

    def test_must_exist_true_for_existing(self):
        target = self.allowed / "exists.txt"
        target.touch()
        result = self.v.validate(target, must_exist=True)
        self.assertTrue(result.exists())

    def test_must_exist_true_raises_for_missing(self):
        target = self.allowed / "ghost.txt"
        with self.assertRaises(PathViolation) as ctx:
            self.v.validate(target, must_exist=True)
        self.assertIn("does not exist", ctx.exception.reason)


# ── Validator — dotdot traversal ──────────────────────────────────────────────


class TestDotDotTraversal(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.allowed = Path(self.tmpdir) / "workspace"
        self.allowed.mkdir()
        self.v = _make_validator(allowed=[self.allowed], blocked=[])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_dotdot_one_level_rejected(self):
        attack = self.allowed / ".." / "etc" / "passwd"
        with self.assertRaises(PathViolation):
            self.v.validate(attack)

    def test_dotdot_two_levels_rejected(self):
        attack = self.allowed / ".." / ".." / "etc" / "passwd"
        with self.assertRaises(PathViolation):
            self.v.validate(attack)

    def test_dotdot_string_form_rejected(self):
        attack = str(self.allowed) + "/../../etc/passwd"
        with self.assertRaises(PathViolation):
            self.v.validate(attack)

    def test_valid_path_with_redundant_dot_accepted(self):
        # "./workspace/file.txt" relative to allowed parent should still work
        target = self.allowed / "." / "notes.md"
        result = self.v.validate(target)
        self.assertEqual(result.name, "notes.md")


# ── Validator — symlink escape ─────────────────────────────────────────────────


class TestSymlinkEscape(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.allowed = Path(self.tmpdir) / "workspace"
        self.allowed.mkdir()
        self.outside = Path(self.tmpdir) / "outside"
        self.outside.mkdir()
        self.v = _make_validator(allowed=[self.allowed], blocked=[])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_symlink_inside_pointing_inside_accepted(self):
        real = self.allowed / "real.txt"
        real.touch()
        link = self.allowed / "link.txt"
        link.symlink_to(real)
        result = self.v.validate(link)
        self.assertEqual(result.name, "real.txt")

    def test_symlink_inside_pointing_outside_rejected(self):
        outside_file = self.outside / "secret.txt"
        outside_file.touch()
        evil_link = self.allowed / "evil.txt"
        evil_link.symlink_to(outside_file)
        with self.assertRaises(PathViolation):
            self.v.validate(evil_link)

    def test_directory_symlink_escape_rejected(self):
        evil_dir = self.allowed / "escape"
        evil_dir.symlink_to(self.outside)
        attack = evil_dir / "something.txt"
        with self.assertRaises(PathViolation):
            self.v.validate(attack)


# ── Validator — blocked roots ─────────────────────────────────────────────────


class TestBlockedRoots(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.workspace = Path(self.tmpdir) / "workspace"
        self.workspace.mkdir()
        self.secrets = self.workspace / "secrets"
        self.secrets.mkdir()
        self.v = _make_validator(
            allowed=[self.workspace],
            blocked=[self.secrets],
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_blocked_root_itself_rejected(self):
        with self.assertRaises(PathViolation) as ctx:
            self.v.validate(self.secrets)
        self.assertIn("blocked root", ctx.exception.reason)

    def test_file_inside_blocked_root_rejected(self):
        with self.assertRaises(PathViolation):
            self.v.validate(self.secrets / "api_key.txt")

    def test_nested_inside_blocked_rejected(self):
        with self.assertRaises(PathViolation):
            self.v.validate(self.secrets / "sub" / "deep" / "creds.json")

    def test_sibling_of_blocked_allowed(self):
        sibling = self.workspace / "notes"
        sibling.mkdir()
        result = self.v.validate(sibling / "file.md")
        self.assertEqual(result.parent, sibling.resolve())

    def test_is_blocked_predicate(self):
        self.assertTrue(self.v.is_blocked(self.secrets / "key.pem"))
        self.assertFalse(self.v.is_blocked(self.workspace / "notes.md"))


# ── Validator — relative paths ────────────────────────────────────────────────


class TestRelativePaths(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.allowed = Path(self.tmpdir) / "workspace"
        self.allowed.mkdir()
        self.v = _make_validator(allowed=[self.allowed], blocked=[])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_relative_path_resolves_against_cwd(self):
        # CWD is NOT inside allowed — relative path like "file.txt" should be
        # rejected because cwd resolves outside allowed workspace
        original_cwd = os.getcwd()
        try:
            os.chdir(self.tmpdir)  # outside allowed
            with self.assertRaises(PathViolation):
                self.v.validate("relative_file.txt")
        finally:
            os.chdir(original_cwd)

    def test_relative_path_inside_allowed_ok(self):
        original_cwd = os.getcwd()
        try:
            os.chdir(self.allowed)  # inside allowed workspace
            (self.allowed / "test.txt").touch()
            result = self.v.validate("test.txt")
            self.assertTrue(result.is_absolute())
        finally:
            os.chdir(original_cwd)


# ── Validator — tilde expansion ───────────────────────────────────────────────


class TestTildeExpansion(unittest.TestCase):
    def setUp(self):
        self.home = Path.home()
        self.v = _make_validator(
            allowed=[self.home / "Documents"],
            blocked=[self.home / ".ssh"],
        )

    def test_tilde_ssh_blocked(self):
        with self.assertRaises(PathViolation):
            self.v.validate("~/.ssh/id_rsa")

    def test_tilde_ssh_known_hosts_blocked(self):
        with self.assertRaises(PathViolation):
            self.v.validate("~/.ssh/known_hosts")

    def test_tilde_documents_allowed(self):
        result = self.v.validate("~/Documents/notes.md")
        self.assertTrue(str(result).startswith(str(self.home / "Documents")))


# ── Validator — check() non-raising API ──────────────────────────────────────


class TestCheckApi(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.allowed = Path(self.tmpdir) / "workspace"
        self.allowed.mkdir()
        self.blocked = Path(self.tmpdir) / "blocked"
        self.blocked.mkdir()
        self.v = _make_validator(allowed=[self.allowed], blocked=[self.blocked])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_check_returns_true_empty_on_success(self):
        ok, reason = self.v.check(self.allowed / "file.txt")
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    def test_check_returns_false_with_reason_on_failure(self):
        ok, reason = self.v.check(self.blocked / "creds.txt")
        self.assertFalse(ok)
        self.assertIn("blocked root", reason)

    def test_check_does_not_raise(self):
        ok, reason = self.v.check("/etc/passwd")
        self.assertFalse(ok)
        self.assertIsInstance(reason, str)


# ── Empty allowed_roots = allow-all-except-blocked ────────────────────────────


class TestEmptyAllowedRoots(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.blocked = Path(self.tmpdir) / "secrets"
        self.blocked.mkdir()
        # allowed=[] → any path not blocked is accepted
        self.v = _make_validator(allowed=[], blocked=[self.blocked])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_arbitrary_path_allowed_when_not_blocked(self):
        result = self.v.validate("/tmp")
        self.assertEqual(result, Path("/tmp").resolve())

    def test_blocked_path_still_rejected(self):
        with self.assertRaises(PathViolation):
            self.v.validate(self.blocked / "key.pem")


# ── make_workspace_validator smoke test ───────────────────────────────────────


class TestMakeWorkspaceValidator(unittest.TestCase):
    def test_import_and_instantiate(self):
        from adwi.path_validator import make_workspace_validator
        v = make_workspace_validator()
        self.assertIsInstance(v, PathValidator)

    def test_ssh_blocked(self):
        from adwi.path_validator import make_workspace_validator
        v = make_workspace_validator()
        ok, _ = v.check(Path.home() / ".ssh" / "id_rsa")
        self.assertFalse(ok)

    def test_workspace_allowed(self):
        from adwi.path_validator import make_workspace_validator
        ws = Path.home() / "SuneelWorkSpace"
        if not ws.exists():
            self.skipTest("workspace not present on this machine")
        v = make_workspace_validator()
        ok, _ = v.check(ws / "adwi" / "adwi_cli.py")
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
