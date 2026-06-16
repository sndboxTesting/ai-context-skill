"""
adwi/simlab/tests/test_nlu_regex.py

Focused regression tests for _REGEX_INTENTS in adwi/adwi_cli.py.
Tests every confirmed bug from the 2026-06-15 NLU eval master report
plus all Phase B new-intent patterns.

Run: python3 -m unittest adwi/simlab/tests/test_nlu_regex.py -v
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: extract _REGEX_INTENTS without importing the full adwi_cli module
# (avoids triggering Ollama, Qdrant, or hardware checks at test time).
# ---------------------------------------------------------------------------

_CLI_PATH = Path(__file__).resolve().parents[3] / "adwi" / "adwi_cli.py"

def _load_regex_intents():
    src = _CLI_PATH.read_text()
    start = src.index("_REGEX_INTENTS = [")
    end   = src.index("\ndef _regex_prefilter")
    ns: dict = {}
    exec(src[start:end], {"re": re}, ns)   # noqa: S102
    return ns["_REGEX_INTENTS"]

_REGEX_INTENTS = _load_regex_intents()


def _classify(text: str) -> str | None:
    """Replicate _regex_prefilter from adwi_cli.py."""
    for pattern, intent in _REGEX_INTENTS:
        if pattern.search(text):
            return intent
    return None


# ---------------------------------------------------------------------------
# Bug 1 — Status regex word-boundary false positives
# ---------------------------------------------------------------------------

class TestBug1StatusWordBoundary(unittest.TestCase):
    """Regex word boundaries prevent 'is'/'are'/'down'/'up' matching as
    substrings inside longer words (list→is, downloads→down, backup→up)."""

    def test_list_files_downloads_no_status(self):
        # Previously "l[is]t files...down[loads]" triggered status.
        result = _classify("list files in my downloads folder")
        self.assertNotEqual(result, "status",
            "'list files in my downloads folder' must NOT route to status")

    def test_downloads_word_no_status(self):
        result = _classify("this downloads fine")
        self.assertNotEqual(result, "status",
            "'this downloads fine' must NOT route to status via 'is'+'down'")

    def test_backup_up_no_status(self):
        # 'back[up]' contains 'up' — must not trigger status.
        result = _classify("is my backup recent")
        self.assertNotEqual(result, "status",
            "'backup' contains 'up' but must NOT trigger status")

    def test_real_status_is_running(self):
        self.assertEqual(_classify("is everything running"), "status")

    def test_real_status_are_services_up(self):
        self.assertEqual(_classify("are services up"), "status")

    def test_real_status_ollama_running(self):
        self.assertEqual(_classify("is ollama running"), "status")

    def test_real_status_is_down(self):
        self.assertEqual(_classify("is the stack down"), "status")


# ---------------------------------------------------------------------------
# Bug 2 — large_files must win over disk_usage
# ---------------------------------------------------------------------------

class TestBug2LargeFilesOrdering(unittest.TestCase):
    """disk_usage previously swallowed 'biggest/largest files' prompts because
    its regex appeared first with a superset pattern."""

    def test_biggest_files(self):
        self.assertEqual(_classify("what are the biggest files"), "large_files")

    def test_largest_files_home(self):
        self.assertEqual(_classify("largest files in my home directory"), "large_files")

    def test_top_n_biggest(self):
        self.assertEqual(_classify("top 10 biggest files"), "large_files")

    def test_huge_files(self):
        self.assertEqual(_classify("show me the huge files"), "large_files")

    def test_files_over_size(self):
        self.assertEqual(_classify("files over 500MB"), "large_files")

    def test_heaviest_on_disk_still_disk_usage(self):
        # "heaviest stuff on disk" — no 'files' object → disk_usage wins
        self.assertEqual(_classify("what's the heaviest stuff on disk"), "disk_usage")

    def test_disk_usage_still_works(self):
        self.assertEqual(_classify("how much disk space do I have"), "disk_usage")

    def test_check_disk(self):
        self.assertEqual(_classify("check my disk"), "disk_usage")

    def test_disk_analysis(self):
        self.assertEqual(_classify("disk space analysis"), "disk_usage")


# ---------------------------------------------------------------------------
# Bug 3 — self_heal must beat status for service-error prompts
# ---------------------------------------------------------------------------

class TestBug3SelfHealBeforeStatus(unittest.TestCase):
    """Status regex fired first on 'docker is not working' because self_heal
    appeared after it and only handled verb-first ordering."""

    def test_docker_not_working_repair(self):
        # Subject-first ordering: docker (subject) + not working (verb)
        self.assertEqual(_classify("docker is not working repair"), "self_heal")

    def test_adwi_isnt_working(self):
        # "isn't" contraction variation
        self.assertEqual(_classify("adwi isn't working properly"), "self_heal")

    def test_ollama_is_broken(self):
        self.assertEqual(_classify("ollama is broken"), "self_heal")

    def test_fix_docker_service(self):
        # Verb-first: fix ... service
        self.assertEqual(_classify("fix the docker service"), "self_heal")

    def test_stack_crashing(self):
        self.assertEqual(_classify("the stack is crashing"), "self_heal")


# ---------------------------------------------------------------------------
# Bug 4 — obsidian_daily must not be swallowed by obsidian_search
# ---------------------------------------------------------------------------

class TestBug4ObsidianDailyGuard(unittest.TestCase):
    """obsidian_search regex '(open|read|show).{0,10}note' previously fired
    on daily-note queries before any obsidian_daily pattern existed."""

    def test_daily_note(self):
        self.assertEqual(_classify("read my daily note"), "obsidian_daily")

    def test_open_todays_note(self):
        self.assertEqual(_classify("open today's note"), "obsidian_daily")

    def test_obsidian_daily_explicit(self):
        self.assertEqual(_classify("open my obsidian daily"), "obsidian_daily")

    def test_obsidian_search_still_works(self):
        # Generic vault search must still reach obsidian_search
        self.assertIn(
            _classify("search my obsidian vault for meeting notes"),
            ("obsidian_search", "rag_search"),
        )

    def test_open_obsidian_notes_is_search(self):
        self.assertEqual(_classify("open my obsidian notes"), "obsidian_search")


# ---------------------------------------------------------------------------
# Bug 7 — git_status regex broadened
# ---------------------------------------------------------------------------

class TestBug7GitStatusBroadened(unittest.TestCase):
    """git_status only caught 'git <subcommand>' and 3 literal phrases;
    11 common git queries routed to chat/memory/disk."""

    def test_show_recent_commits(self):
        self.assertEqual(_classify("show recent commits"), "git_status")

    def test_uncommitted_changes(self):
        self.assertEqual(_classify("are there uncommitted changes"), "git_status")

    def test_current_branch(self):
        self.assertEqual(_classify("what's the current branch"), "git_status")

    def test_unstaged_changes(self):
        self.assertEqual(_classify("show unstaged changes"), "git_status")

    def test_is_repo_clean(self):
        self.assertEqual(_classify("is the repo clean"), "git_status")

    def test_git_stat(self):
        self.assertEqual(_classify("git stat"), "git_status")

    def test_staged_files(self):
        self.assertEqual(_classify("show staged files"), "git_status")

    def test_explicit_git_status_still_works(self):
        self.assertEqual(_classify("run git status"), "git_status")

    def test_git_log(self):
        self.assertEqual(_classify("git log"), "git_status")


# ---------------------------------------------------------------------------
# Phase B — New intent patterns
# ---------------------------------------------------------------------------

class TestPhaseB_Nightly(unittest.TestCase):
    def test_nightly_status(self):
        self.assertEqual(_classify("nightly status"), "nightly_status")

    def test_when_nightly_ran(self):
        self.assertEqual(_classify("when did nightly last run"), "nightly_status")

    def test_show_nightly_log(self):
        self.assertEqual(_classify("show nightly log"), "nightly_status")

    def test_run_nightly(self):
        self.assertEqual(_classify("run nightly"), "nightly_run")

    def test_trigger_nightly_maintenance(self):
        self.assertEqual(_classify("trigger nightly maintenance"), "nightly_run")


class TestPhaseB_ModelSwitching(unittest.TestCase):
    def test_what_model_am_i_using(self):
        self.assertEqual(_classify("what model am I using"), "model_status")

    def test_which_model_active(self):
        self.assertEqual(_classify("which model is active"), "model_status")

    def test_show_model_status(self):
        self.assertEqual(_classify("show model status"), "model_status")

    def test_switch_to_local_model(self):
        self.assertEqual(_classify("switch to local model"), "use_local")

    def test_use_local_llm(self):
        self.assertEqual(_classify("use local llm"), "use_local")

    def test_use_qwen(self):
        self.assertEqual(_classify("use qwen"), "use_local")

    def test_switch_to_cloud(self):
        self.assertEqual(_classify("switch to cloud"), "use_cloud")

    def test_use_gemini(self):
        self.assertEqual(_classify("use gemini"), "use_cloud")


class TestPhaseB_Voice(unittest.TestCase):
    def test_voice_input(self):
        self.assertEqual(_classify("listen to my voice input"), "voice_in")

    def test_start_voice_recording(self):
        self.assertEqual(_classify("start voice recording"), "voice_in")

    def test_text_to_speech(self):
        self.assertEqual(_classify("text to speech"), "voice_out")

    def test_read_this_aloud(self):
        self.assertEqual(_classify("read this aloud"), "voice_out")

    def test_say_out_loud(self):
        self.assertEqual(_classify("say this out loud"), "voice_out")


class TestPhaseB_BackupOps(unittest.TestCase):
    def test_backup_status(self):
        self.assertEqual(_classify("backup status"), "backup_status")

    def test_last_backup_time(self):
        self.assertEqual(_classify("when was the last backup"), "backup_status")

    def test_is_backup_recent(self):
        self.assertEqual(_classify("is my backup recent"), "backup_status")

    def test_show_backup_log(self):
        self.assertEqual(_classify("show backup log"), "backup_log")

    def test_backup_history(self):
        self.assertEqual(_classify("backup history"), "backup_log")


class TestPhaseB_FileOps(unittest.TestCase):
    def test_list_files_downloads(self):
        # This was the Bug1 victim; now correctly → file_list
        self.assertEqual(_classify("list files in my downloads folder"), "file_list")

    def test_ls_documents(self):
        self.assertEqual(_classify("ls my documents folder"), "file_list")

    def test_what_files_in_tmp(self):
        self.assertEqual(_classify("what files are in /tmp"), "file_list")

    def test_read_py_file(self):
        self.assertEqual(_classify("read adwi_cli.py"), "file_read")

    def test_show_contents(self):
        self.assertEqual(_classify("show me the contents of .gitignore"), "file_read")

    def test_search_for_files(self):
        self.assertEqual(_classify("search for python files in my workspace"), "file_search")

    def test_find_all_yaml(self):
        self.assertEqual(_classify("find all yaml files"), "file_search")

    def test_locate_config(self):
        self.assertEqual(_classify("find files named config.yaml"), "file_search")


class TestPhaseB_EvalTest(unittest.TestCase):
    def test_eval_routing(self):
        self.assertEqual(_classify("run routing tests"), "eval_routing")

    def test_test_adwi(self):
        self.assertEqual(_classify("run adwi tests"), "test_adwi")

    def test_eval_adwi(self):
        self.assertEqual(_classify("evaluate adwi performance"), "eval_adwi")


# ---------------------------------------------------------------------------
# Regressions — patterns that must not change after patching
# ---------------------------------------------------------------------------

class TestRegressions(unittest.TestCase):
    """Guard against fixes that accidentally break previously working routes."""

    def test_disk_usage_basic(self):
        self.assertEqual(_classify("check my disk"), "disk_usage")

    def test_disk_usage_how_much(self):
        self.assertEqual(_classify("how much disk space do I have"), "disk_usage")

    def test_disk_usage_storage(self):
        self.assertEqual(_classify("storage usage breakdown"), "disk_usage")

    def test_generate_image(self):
        self.assertEqual(_classify("generate an image of a cat"), "generate_image")

    def test_generate_image_draw(self):
        self.assertEqual(_classify("draw me a picture of a sunset"), "generate_image")

    def test_git_status_explicit(self):
        self.assertEqual(_classify("run git status"), "git_status")

    def test_git_log(self):
        self.assertEqual(_classify("git log"), "git_status")

    def test_gmail_check(self):
        self.assertEqual(_classify("check my email"), "gmail")

    def test_web_search(self):
        self.assertEqual(_classify("search the web for llama3 benchmarks"), "web_search")

    def test_memory_recall(self):
        self.assertEqual(_classify("what do you remember about my setup?"), "memory_recall")

    def test_old_files(self):
        self.assertEqual(_classify("files I haven't opened in a year"), "old_files")

    def test_obsidian_search(self):
        self.assertEqual(_classify("search my obsidian notes for python"), "obsidian_search")

    def test_run_code(self):
        self.assertEqual(_classify("run this python script"), "run_code")

    def test_doctor_full_health_check(self):
        self.assertEqual(_classify("run a full health check"), "doctor")

    def test_doctor_deep_diagnostic(self):
        self.assertEqual(_classify("deep diagnostic please"), "doctor")


if __name__ == "__main__":
    unittest.main(verbosity=2)
