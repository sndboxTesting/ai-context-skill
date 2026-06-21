"""
tests/test_validate_env.py — Unit tests for adwi/scripts/validate_adwi_env.py.

Tests are fully hermetic: no real config/.env is read, no live network calls are
made, no secrets are touched. All I/O is mocked via unittest.mock.

Run:
    python3 -m unittest adwi/tests/test_validate_env.py

Safety note: these tests assert the *output classification* of each check
function. They do not assert any secret values (secret presence is checked
via "is non-empty and non-placeholder" logic; the value itself is never
asserted or printed).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── Load module without executing main() ──────────────────────────────────────
_SCRIPT = Path(__file__).parent.parent / "scripts" / "validate_adwi_env.py"
_spec = importlib.util.spec_from_file_location("validate_adwi_env", _SCRIPT)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)                 # type: ignore[union-attr]
venv = _mod


# ── Helpers ───────────────────────────────────────────────────────────────────

def _urlopen_returning(body: bytes, code: int = 200):
    """Return a mock context-manager response for urllib.request.urlopen."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=BytesIO(body))
    cm.__exit__ = MagicMock(return_value=False)
    cm.read = MagicMock(return_value=body)
    return cm


def _http_error(code: int):
    raise urllib.error.HTTPError(url="", code=code, msg="", hdrs=None, fp=None)


# ── 1. .gitignore safety check ────────────────────────────────────────────────

class TestGitignoreSafety(unittest.TestCase):
    """chk_gitignore_secrets must fail when critical patterns are absent."""

    REQUIRED = ["secrets/", "config/.env", "**/.env", "**/*token*"]

    def _run_with_content(self, content: str) -> tuple[str, str]:
        fake_workspace = MagicMock(spec=Path)
        gi = MagicMock(spec=Path)
        gi.exists.return_value = True
        gi.read_text.return_value = content
        fake_workspace.__truediv__ = MagicMock(return_value=gi)
        with patch.object(venv, "WORKSPACE", fake_workspace):
            return venv.chk_gitignore_secrets()

    def test_all_patterns_present_returns_pass(self):
        content = "\n".join(self.REQUIRED) + "\n*.pyc\n"
        status, detail = self._run_with_content(content)
        self.assertEqual(status, "pass")

    def test_missing_secrets_pattern_returns_fail(self):
        content = "\n".join(p for p in self.REQUIRED if p != "secrets/")
        status, detail = self._run_with_content(content)
        self.assertEqual(status, "fail")
        self.assertIn("secrets/", detail)

    def test_missing_env_pattern_returns_fail(self):
        content = "\n".join(p for p in self.REQUIRED if p != "config/.env")
        status, detail = self._run_with_content(content)
        self.assertEqual(status, "fail")
        self.assertIn("config/.env", detail)

    def test_missing_token_pattern_returns_fail(self):
        content = "\n".join(p for p in self.REQUIRED if p != "**/*token*")
        status, detail = self._run_with_content(content)
        self.assertEqual(status, "fail")
        self.assertIn("**/*token*", detail)

    def test_empty_gitignore_returns_fail(self):
        status, detail = self._run_with_content("")
        self.assertEqual(status, "fail")

    def test_missing_gitignore_file_returns_fail(self):
        fake_workspace = MagicMock(spec=Path)
        gi = MagicMock(spec=Path)
        gi.exists.return_value = False
        fake_workspace.__truediv__ = MagicMock(return_value=gi)
        with patch.object(venv, "WORKSPACE", fake_workspace):
            status, detail = venv.chk_gitignore_secrets()
        self.assertEqual(status, "fail")


# ── 2. Local control-plane secret check ───────────────────────────────────────

class TestLocalSecret(unittest.TestCase):
    """chk_local_secret must never expose secret value; must warn when missing."""

    def _run(self, keys: dict) -> tuple[str, str]:
        with patch.object(venv, "_read_env_keys", return_value=keys):
            return venv.chk_local_secret()

    def test_secret_configured_returns_pass(self):
        status, detail = self._run({"ADWI_LOCAL_SECRET": "a-real-secret-value"})
        self.assertEqual(status, "pass")

    def test_secret_value_never_in_detail(self):
        secret = "super-secret-12345"
        _, detail = self._run({"ADWI_LOCAL_SECRET": secret})
        self.assertNotIn(secret, detail, "Secret value must never appear in detail output")

    def test_missing_secret_returns_warn(self):
        status, detail = self._run({})
        self.assertEqual(status, "warn")

    def test_replace_me_placeholder_returns_warn(self):
        status, detail = self._run({"ADWI_LOCAL_SECRET": "REPLACE_ME"})
        self.assertEqual(status, "warn")

    def test_empty_string_secret_returns_warn(self):
        status, detail = self._run({"ADWI_LOCAL_SECRET": ""})
        self.assertEqual(status, "warn")


# ── 3. Telegram bridge config check ───────────────────────────────────────────

class TestTelegramConfig(unittest.TestCase):
    """chk_telegram_config covers all 4 states of the token/UID/secret matrix."""

    def _run(self, keys: dict) -> tuple[str, str]:
        with patch.object(venv, "_read_env_keys", return_value=keys):
            return venv.chk_telegram_config()

    def test_no_token_configured_is_pass(self):
        # Bridge is optional; absent config is a valid state
        status, _ = self._run({})
        self.assertEqual(status, "pass")

    def test_token_without_uid_is_fail(self):
        status, detail = self._run({"TELEGRAM_BOT_TOKEN": "1234:real-token"})
        self.assertEqual(status, "fail")
        self.assertIn("TELEGRAM_ALLOWED_USER_ID", detail)

    def test_token_plus_uid_without_secret_is_warn(self):
        status, detail = self._run({
            "TELEGRAM_BOT_TOKEN": "1234:real-token",
            "TELEGRAM_ALLOWED_USER_ID": "987654321",
        })
        self.assertEqual(status, "warn")

    def test_all_three_configured_is_pass(self):
        status, _ = self._run({
            "TELEGRAM_BOT_TOKEN": "1234:real-token",
            "TELEGRAM_ALLOWED_USER_ID": "987654321",
            "ADWI_LOCAL_SECRET": "a-real-secret",
        })
        self.assertEqual(status, "pass")

    def test_token_placeholder_treated_as_absent(self):
        # REPLACE_ME is treated as "not configured"
        status, _ = self._run({"TELEGRAM_BOT_TOKEN": "REPLACE_ME"})
        self.assertEqual(status, "pass")


# ── 4. Ollama model list check ────────────────────────────────────────────────

class TestOllamaModels(unittest.TestCase):
    """chk_ollama must validate both adwi:latest and llama3.1:8b."""

    def _run_with_models(self, model_names: list[str]) -> tuple[str, str]:
        body = json.dumps({
            "models": [{"name": n} for n in model_names]
        }).encode()
        cm = _urlopen_returning(body)
        with patch("urllib.request.urlopen", return_value=cm):
            return venv.chk_ollama()

    def test_both_required_models_present_returns_pass(self):
        status, _ = self._run_with_models(["llama3.1:8b", "adwi:latest", "nomic-embed-text"])
        self.assertEqual(status, "pass")

    def test_missing_adwi_latest_returns_warn(self):
        status, detail = self._run_with_models(["llama3.1:8b", "qwen3:0.6b"])
        self.assertEqual(status, "warn")
        self.assertIn("adwi:latest", detail)

    def test_missing_llama_returns_warn(self):
        status, detail = self._run_with_models(["adwi:latest", "qwen3:0.6b"])
        self.assertEqual(status, "warn")
        self.assertIn("llama3.1:8b", detail)

    def test_both_missing_returns_warn_with_both_names(self):
        status, detail = self._run_with_models(["qwen3:0.6b", "nomic-embed-text"])
        self.assertEqual(status, "warn")
        self.assertIn("adwi:latest", detail)
        self.assertIn("llama3.1:8b", detail)

    def test_empty_model_list_returns_warn(self):
        status, detail = self._run_with_models([])
        self.assertEqual(status, "warn")

    def test_ollama_unreachable_returns_fail(self):
        with patch("urllib.request.urlopen", side_effect=Exception("connection refused")):
            status, detail = venv.chk_ollama()
        self.assertEqual(status, "fail")
        self.assertIn("11434", detail)

    def test_partial_name_match_accepted(self):
        # e.g. "adwi:latest" in "adwi:latest" — checks `m in n` substring logic
        status, _ = self._run_with_models(["llama3.1:8b", "adwi:latest"])
        self.assertEqual(status, "pass")


# ── 5. Safe Command API static check ─────────────────────────────────────────

class TestSafeCommandApiStatic(unittest.TestCase):
    """chk_safe_command_api must fail statically if server.py binds to 0.0.0.0."""

    def _run_with_server_content(self, server_content: str, env_keys: dict | None = None) -> tuple[str, str]:
        env_keys = env_keys or {}
        fake_adwi = MagicMock(spec=Path)
        server_py = MagicMock(spec=Path)
        server_py.exists.return_value = True
        server_py.read_text.return_value = server_content
        # ADWI / "services" / "command-api" / "server.py"
        fake_adwi.__truediv__ = MagicMock(return_value=MagicMock(
            __truediv__=MagicMock(return_value=MagicMock(
                __truediv__=MagicMock(return_value=server_py)
            ))
        ))
        with patch.object(venv, "ADWI", fake_adwi), \
             patch.object(venv, "_read_env_keys", return_value=env_keys), \
             patch("urllib.request.urlopen", side_effect=Exception("not running")):
            return venv.chk_safe_command_api()

    def test_loopback_binding_is_not_flagged(self):
        content = 'host = "127.0.0.1"\nSECRET = ""\n'
        status, detail = self._run_with_server_content(content)
        # Should not fail due to binding; may warn because server not running
        self.assertNotIn("0.0.0.0", detail.lower() + detail)

    def test_any_interface_binding_returns_fail(self):
        content = 'host = "0.0.0.0"\nSECRET = ""\n'
        status, detail = self._run_with_server_content(content)
        self.assertEqual(status, "fail")
        self.assertIn("0.0.0.0", detail)

    def test_static_check_beats_runtime_check(self):
        # Even if server were running, 0.0.0.0 bind must fail first
        content = 'host = "0.0.0.0"\nSECRET = "abc"\n'
        status, _ = self._run_with_server_content(content, env_keys={"ADWI_LOCAL_SECRET": "abc"})
        self.assertEqual(status, "fail")

    def test_alternative_binding_form_also_caught(self):
        # Regression guard: ThreadingHTTPServer(("0.0.0.0", port)) form must be caught.
        # If this test fails, the strengthened check was weakened — fix the check, not the test.
        content = 'server = ThreadingHTTPServer(("0.0.0.0", 5055), Handler)\n'
        status, detail = self._run_with_server_content(content)
        self.assertEqual(status, "fail",
                         "ThreadingHTTPServer((\"0.0.0.0\", ...)) form must be caught by static check")
        self.assertIn("0.0.0.0", detail)


# ── 6. Safe Command API runtime auth check ───────────────────────────────────

class TestSafeCommandApiRuntime(unittest.TestCase):
    """Runtime path: test auth enforcement logic when the server is reachable."""

    _GOOD_SERVER = 'host = "127.0.0.1"\nSECRET = ""\n'

    def _run_with_runtime(self, env_keys: dict, urlopen_side_effect) -> tuple[str, str]:
        fake_adwi = MagicMock(spec=Path)
        server_py = MagicMock(spec=Path)
        server_py.exists.return_value = True
        server_py.read_text.return_value = self._GOOD_SERVER
        fake_adwi.__truediv__ = MagicMock(return_value=MagicMock(
            __truediv__=MagicMock(return_value=MagicMock(
                __truediv__=MagicMock(return_value=server_py)
            ))
        ))
        with patch.object(venv, "ADWI", fake_adwi), \
             patch.object(venv, "_read_env_keys", return_value=env_keys), \
             patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
            return venv.chk_safe_command_api()

    def test_unauthenticated_200_with_secret_configured_is_fail(self):
        # Server accepted unauthenticated request even though secret is set — auth not enforced
        cm = _urlopen_returning(b'{"ok":true}')
        status, detail = self._run_with_runtime(
            {"ADWI_LOCAL_SECRET": "real-secret"},
            lambda *a, **k: cm,
        )
        self.assertEqual(status, "fail")
        self.assertIn("auth", detail.lower())

    def test_401_with_secret_configured_is_pass(self):
        # Server correctly rejected unauthenticated request
        def raise_401(*a, **k):
            _http_error(401)
        status, detail = self._run_with_runtime(
            {"ADWI_LOCAL_SECRET": "real-secret"},
            raise_401,
        )
        self.assertEqual(status, "pass")
        self.assertIn("401", detail)

    def test_server_not_running_is_warn(self):
        # Not running is a warn, not a fail (service may not be started yet)
        def raise_conn(*a, **k):
            raise Exception("connection refused")
        status, detail = self._run_with_runtime(
            {"ADWI_LOCAL_SECRET": "real-secret"},
            raise_conn,
        )
        self.assertEqual(status, "warn")
        self.assertIn("5055", detail)

    def test_non_401_http_error_is_warn(self):
        def raise_403(*a, **k):
            _http_error(403)
        status, detail = self._run_with_runtime({}, raise_403)
        self.assertEqual(status, "warn")

    def test_no_secret_plus_200_is_warn_not_fail(self):
        # Without a secret configured, an open server is a warn (not yet secured)
        cm = _urlopen_returning(b'{"ok":true}')
        status, detail = self._run_with_runtime(
            {},  # no ADWI_LOCAL_SECRET
            lambda *a, **k: cm,
        )
        self.assertEqual(status, "warn")


# ── 7. JSON output does not leak secrets ─────────────────────────────────────

class TestJsonOutputNoSecretLeak(unittest.TestCase):
    """--json output must never include secret values in detail fields."""

    def test_local_secret_not_in_json_detail(self):
        secret = "hunter2-do-not-log"
        with patch.object(venv, "_read_env_keys", return_value={"ADWI_LOCAL_SECRET": secret}):
            status, detail = venv.chk_local_secret()
        self.assertNotIn(secret, detail)

    def test_telegram_token_not_in_json_detail(self):
        # chk_telegram_config must not echo back the token value
        token = "9876543210:FakeTokenValue"
        with patch.object(venv, "_read_env_keys", return_value={
            "TELEGRAM_BOT_TOKEN": token,
            "TELEGRAM_ALLOWED_USER_ID": "111",
            "ADWI_LOCAL_SECRET": "x",
        }):
            _, detail = venv.chk_telegram_config()
        self.assertNotIn(token, detail)


# ── 8. chk_key_files — file presence check ────────────────────────────────────

class TestKeyFiles(unittest.TestCase):
    """chk_key_files must fail precisely when any required file is absent."""

    def _run_with_tmp(self, present: list[str]) -> tuple[str, str]:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Build the directory structure the check expects
            (tmp_path / "infra" / "docker").mkdir(parents=True)
            (tmp_path / "bin").mkdir(parents=True)
            for name in present:
                (tmp_path / name).touch()
            with patch.object(venv, "ADWI", tmp_path), \
                 patch.object(venv, "WORKSPACE", tmp_path.parent):
                return venv.chk_key_files()

    _ALL = [
        "adwi_cli.py", "memory.py", "reason_engine.py",
        "nightly.py", "path_validator.py",
        "infra/docker/docker-compose.yml", "bin/adwi",
    ]

    def test_all_files_present_returns_pass(self):
        status, detail = self._run_with_tmp(self._ALL)
        self.assertEqual(status, "pass")
        self.assertIn("7", detail)

    def test_missing_adwi_cli_returns_fail(self):
        present = [f for f in self._ALL if f != "adwi_cli.py"]
        status, detail = self._run_with_tmp(present)
        self.assertEqual(status, "fail")
        self.assertIn("adwi_cli.py", detail)

    def test_missing_path_validator_returns_fail(self):
        present = [f for f in self._ALL if f != "path_validator.py"]
        status, detail = self._run_with_tmp(present)
        self.assertEqual(status, "fail")
        self.assertIn("path_validator.py", detail)

    def test_no_files_returns_fail_with_all_listed(self):
        status, detail = self._run_with_tmp([])
        self.assertEqual(status, "fail")
        self.assertIn("Missing", detail)

    def test_adwi_outside_workspace_does_not_crash(self):
        """If ADWI is outside WORKSPACE, relative_to() raises ValueError.
        chk_key_files() must not propagate it — return fail with a safe message."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # ADWI inside tmp_path, WORKSPACE is a different unrelated directory
            adwi_path = tmp_path / "adwi"
            adwi_path.mkdir()
            other_workspace = tmp_path / "other"
            other_workspace.mkdir()
            with patch.object(venv, "ADWI", adwi_path), \
                 patch.object(venv, "WORKSPACE", other_workspace):
                try:
                    status, detail = venv.chk_key_files()
                    # Either fails gracefully (no crash) or pass/warn is OK
                    self.assertIn(status, ("fail", "warn", "pass"))
                except ValueError as e:
                    self.fail(f"chk_key_files() must not propagate ValueError: {e}")


# ── 9. chk_syntax — py_compile check ─────────────────────────────────────────

class TestSyntaxCheck(unittest.TestCase):
    """chk_syntax must report pass/fail accurately via mocked subprocess.run."""

    def _make_proc(self, returncode: int, stderr: str = "") -> MagicMock:
        m = MagicMock()
        m.returncode = returncode
        m.stderr = stderr
        return m

    def _run(self, side_effects: list) -> tuple[str, str]:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name in ["adwi_cli.py", "reason_engine.py", "memory.py", "nightly.py", "path_validator.py"]:
                (tmp_path / name).touch()
            with patch.object(venv, "ADWI", tmp_path), \
                 patch("subprocess.run", side_effect=side_effects):
                return venv.chk_syntax()

    def test_all_pass_returns_pass(self):
        ok = self._make_proc(0)
        status, detail = self._run([ok] * 5)
        self.assertEqual(status, "pass")
        self.assertIn("5 files", detail)

    def test_one_syntax_error_returns_fail(self):
        ok = self._make_proc(0)
        bad = self._make_proc(1, "SyntaxError: invalid syntax")
        # First file fails, rest pass
        status, detail = self._run([bad, ok, ok, ok, ok])
        self.assertEqual(status, "fail")
        self.assertIn("SyntaxError", detail)

    def test_missing_file_reported_as_missing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Create only 4 of 5 required files — nightly.py absent
            for name in ["adwi_cli.py", "reason_engine.py", "memory.py", "path_validator.py"]:
                (tmp_path / name).touch()
            with patch.object(venv, "ADWI", tmp_path), \
                 patch("subprocess.run", return_value=self._make_proc(0)):
                status, detail = venv.chk_syntax()
        self.assertEqual(status, "fail")
        self.assertIn("nightly.py", detail)
        self.assertIn("missing", detail)

    def test_multiple_failures_all_reported(self):
        bad = self._make_proc(1, "SyntaxError: bad")
        status, detail = self._run([bad] * 5)
        self.assertEqual(status, "fail")
        # Multiple filenames should appear in the detail
        self.assertIn("adwi_cli.py", detail)

    def test_oserror_reported_as_fail(self):
        """If subprocess.run raises OSError (e.g. python3 not found), chk_syntax must fail."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name in ["adwi_cli.py", "reason_engine.py", "memory.py", "nightly.py", "path_validator.py"]:
                (tmp_path / name).touch()

            def raise_os(*a, **k):
                raise OSError("python3 not found")

            with patch.object(venv, "ADWI", tmp_path), \
                 patch("subprocess.run", side_effect=raise_os):
                status, detail = venv.chk_syntax()

        self.assertEqual(status, "fail")

    def test_timeout_reported_as_fail(self):
        """If subprocess.run raises TimeoutExpired, chk_syntax must fail gracefully."""
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for name in ["adwi_cli.py", "reason_engine.py", "memory.py", "nightly.py", "path_validator.py"]:
                (tmp_path / name).touch()

            def raise_timeout(*a, **k):
                raise subprocess.TimeoutExpired(cmd="python3", timeout=30)

            with patch.object(venv, "ADWI", tmp_path), \
                 patch("subprocess.run", side_effect=raise_timeout):
                status, detail = venv.chk_syntax()

        self.assertEqual(status, "fail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
