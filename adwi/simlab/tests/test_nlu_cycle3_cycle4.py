"""
NLU Cycle 3 & 4 regression tests.
Covers all patterns added in the reliability push (Cycles 3-4).
Run with: python3 -m unittest adwi/simlab/tests/test_nlu_cycle3_cycle4.py
"""
import re
import sys
import unittest

# ── Minimal inline regex_prefilter (mirrors eval harness logic) ──────────────
sys.path.insert(0, "/Users/MAC/SuneelWorkSpace")
from adwi.adwi_cli import _REGEX_INTENTS  # noqa: E402


def _route(text: str) -> str | None:
    for pat, intent in _REGEX_INTENTS:
        if pat.search(text):
            return intent
    return None


class TestCycle3MemoryRecall(unittest.TestCase):
    """CYCLE-3: memory_recall guard before gmail_followup_reminder"""

    def test_remind_me_know_docker(self):
        self.assertEqual(_route("remind me what I know about docker networking"), "memory_recall")

    def test_remind_me_about_project(self):
        self.assertEqual(_route("remind me about the project"), "memory_recall")

    def test_remind_me_about_background(self):
        self.assertEqual(_route("remind me about the background context"), "memory_recall")

    def test_remind_me_what_i_said(self):
        self.assertEqual(_route("remind me what I said about this"), "memory_recall")

    def test_remind_me_about_git(self):
        self.assertEqual(_route("remind me about git"), "memory_recall")

    def test_remind_me_about_adwi(self):
        self.assertEqual(_route("remind me about adwi"), "memory_recall")

    def test_normal_follow_up_still_works(self):
        # "remind me if no reply" should still be gmail_followup_reminder
        self.assertEqual(_route("remind me if they haven't replied"), "gmail_followup_reminder")

    def test_what_context_do_you_have(self):
        self.assertEqual(_route("what context do you have about me"), "memory_recall")

    def test_what_context_stored(self):
        self.assertEqual(_route("what context have you stored about my system"), "memory_recall")

    def test_what_do_you_know_about_me(self):
        self.assertEqual(_route("what do you know about my setup"), "memory_recall")

    def test_what_do_you_remember_about_project(self):
        self.assertEqual(_route("what do you remember about my project"), "memory_recall")


class TestCycle3GmailSummarize(unittest.TestCase):
    """CYCLE-3: gmail_summarize — what does this email say / brief me / what's in this email"""

    def test_what_does_this_email_say(self):
        self.assertEqual(_route("what does this email say"), "gmail_summarize")

    def test_what_does_that_message_say(self):
        self.assertEqual(_route("what does that message say"), "gmail_summarize")

    def test_brief_me_on_this_email(self):
        self.assertEqual(_route("brief me on this email"), "gmail_summarize")

    def test_brief_me_on_the_thread(self):
        self.assertEqual(_route("brief me on the thread"), "gmail_summarize")

    def test_whats_in_this_email(self):
        self.assertEqual(_route("what's in this email"), "gmail_summarize")

    def test_whats_in_the_message(self):
        self.assertEqual(_route("what's in the message"), "gmail_summarize")

    def test_what_does_email_contain(self):
        self.assertEqual(_route("what does the email contain"), "gmail_summarize")

    def test_what_does_this_thread_contain(self):
        self.assertEqual(_route("what does this thread contain"), "gmail_summarize")


class TestCycle3GmailConfirm(unittest.TestCase):
    """CYCLE-3: gmail_confirm — go ahead / proceed / yes go ahead"""

    def test_go_ahead(self):
        self.assertEqual(_route("go ahead"), "gmail_confirm")

    def test_yes_go_ahead(self):
        self.assertEqual(_route("yes go ahead"), "gmail_confirm")

    def test_yes_confirm(self):
        self.assertEqual(_route("yes confirm"), "gmail_confirm")

    def test_proceed(self):
        self.assertEqual(_route("proceed"), "gmail_confirm")

    def test_go_for_it(self):
        self.assertEqual(_route("go for it"), "gmail_confirm")

    def test_yeah_do_it(self):
        self.assertEqual(_route("yeah, do it"), "gmail_confirm")


class TestCycle3GitStatus(unittest.TestCase):
    """CYCLE-3: git_status — untracked files / are there any changes / any changes to push"""

    def test_untracked_files(self):
        self.assertEqual(_route("untracked files"), "git_status")

    def test_any_untracked_files(self):
        self.assertEqual(_route("any untracked files?"), "git_status")

    def test_are_there_uncommitted_changes(self):
        self.assertEqual(_route("are there any uncommitted changes"), "git_status")

    def test_are_there_unstaged_files(self):
        self.assertEqual(_route("are there any unstaged files"), "git_status")

    def test_any_changes_to_push(self):
        self.assertEqual(_route("any changes to push"), "git_status")

    def test_changes_to_commit(self):
        self.assertEqual(_route("any changes to commit"), "git_status")

    def test_files_not_committed(self):
        self.assertEqual(_route("any files not committed"), "git_status")


class TestCycle3FixError(unittest.TestCase):
    """CYCLE-3: fix_error — httpx / aiohttp / JSONDecodeError pastes"""

    def test_httpx_connect_error(self):
        self.assertEqual(_route("httpx.ConnectError: [Errno 111] Connection refused"), "fix_error")

    def test_httpx_timeout(self):
        self.assertEqual(_route("getting httpx.ReadTimeout on every request"), "fix_error")

    def test_aiohttp_connector_error(self):
        self.assertEqual(_route("aiohttp.ClientConnectorError connecting to localhost"), "fix_error")

    def test_requests_connection_error(self):
        self.assertEqual(_route("requests.ConnectionError: HTTPConnectionPool"), "fix_error")

    def test_json_decode_error_paste(self):
        self.assertEqual(_route("JSONDecodeError: Expecting value at line 1 column 1"), "fix_error")

    def test_json_decoder_full(self):
        self.assertEqual(_route("json.decoder.JSONDecodeError while parsing response"), "fix_error")


class TestCycle4ExtractIdeas(unittest.TestCase):
    """CYCLE-4: extract_ideas — pull/extract ideas/insights"""

    def test_extract_key_points(self):
        self.assertEqual(_route("extract the key points from this"), "extract_ideas")

    def test_pull_insights(self):
        self.assertEqual(_route("pull out the insights from this document"), "extract_ideas")

    def test_get_key_takeaways(self):
        self.assertEqual(_route("get the key takeaways from this article"), "extract_ideas")

    def test_key_takeaways_from(self):
        self.assertEqual(_route("key takeaways from this meeting"), "extract_ideas")

    def test_key_takeaways(self):
        self.assertEqual(_route("key takeaways from this conversation"), "extract_ideas")

    def test_main_insights(self):
        self.assertEqual(_route("main insights from this document"), "extract_ideas")


class TestCycle4ImplementIdea(unittest.TestCase):
    """CYCLE-4: implement_idea — implement this feature/idea"""

    def test_implement_this_idea(self):
        self.assertEqual(_route("implement this idea"), "implement_idea")

    def test_implement_the_feature(self):
        self.assertEqual(_route("implement the feature"), "implement_idea")

    def test_build_this_feature(self):
        self.assertEqual(_route("build this feature"), "implement_idea")

    def test_build_out_the_concept(self):
        self.assertEqual(_route("build out the concept"), "implement_idea")

    def test_develop_this_plan(self):
        self.assertEqual(_route("develop this plan"), "implement_idea")


class TestCycle4ModelStatus(unittest.TestCase):
    """CYCLE-4: model_status — model performance patterns"""

    def test_model_performing(self):
        self.assertEqual(_route("is the model performing well"), "model_status")

    def test_model_performance_report(self):
        self.assertEqual(_route("model performance report"), "model_status")

    def test_how_is_model_performing(self):
        self.assertEqual(_route("how is the model performing"), "model_status")

    def test_how_well_is_llm_performing(self):
        self.assertEqual(_route("how well is the llm performing today"), "model_status")


class TestCycle4EvalAdwi(unittest.TestCase):
    """CYCLE-4: eval_adwi — bare 'eval' and 'generate eval scenarios'"""

    def test_bare_eval(self):
        self.assertEqual(_route("eval"), "eval_adwi")

    def test_generate_eval_scenarios(self):
        self.assertEqual(_route("generate eval scenarios for adwi"), "eval_adwi")

    def test_generate_new_eval_scenarios(self):
        self.assertEqual(_route("generate new eval scenarios"), "eval_adwi")


class TestCycle4VoiceIn(unittest.TestCase):
    """CYCLE-4: voice_in — bare 'voice' and 'voice in'"""

    def test_bare_voice(self):
        self.assertEqual(_route("voice"), "voice_in")

    def test_voice_in(self):
        self.assertEqual(_route("voice in"), "voice_in")


class TestCycle4RunCode(unittest.TestCase):
    """CYCLE-4: run_code — generate code for X / bare 'run'"""

    def test_generate_code_for(self):
        self.assertEqual(_route("generate code for a web scraper"), "run_code")

    def test_generate_python_code(self):
        self.assertEqual(_route("generate python code for sorting a list"), "run_code")

    def test_bare_run(self):
        self.assertEqual(_route("run"), "run_code")


class TestCycle4WebSearch(unittest.TestCase):
    """CYCLE-4: web_search — bare 'search' and 'find information about'"""

    def test_bare_search(self):
        self.assertEqual(_route("search"), "web_search")

    def test_find_information_about(self):
        self.assertEqual(_route("find information about Python 3.12"), "web_search")

    def test_find_information_about_ollama(self):
        self.assertEqual(_route("find information about ollama"), "web_search")


class TestCycle4Status(unittest.TestCase):
    """CYCLE-4/5: status — is the model slow/unresponsive (diagnostic, not advisory)"""

    def test_is_the_model_slow(self):
        self.assertEqual(_route("is the model slow"), "status")

    def test_why_is_adwi_sluggish_is_chat(self):
        # "why is X slow" = advisory question → chat (CYCLE-5 moved this from status)
        self.assertEqual(_route("why is adwi sluggish"), "chat")

    def test_is_ollama_unresponsive(self):
        self.assertEqual(_route("is ollama unresponsive"), "status")

    def test_hows_my_ai_doing(self):
        self.assertEqual(_route("how's my ai doing"), "status")


class TestNoRegressionHardened(unittest.TestCase):
    """Verify previously-hardened patterns still work"""

    def test_memory_recall_still_works(self):
        self.assertEqual(_route("what do you remember about docker"), "memory_recall")

    def test_gmail_followup_no_bleed(self):
        result = _route("set a follow-up reminder for this thread")
        self.assertEqual(result, "gmail_followup_reminder")

    def test_web_search_still_works(self):
        self.assertIn(_route("search the web for llama3 news"), ["web_search"])

    def test_git_status_still_works(self):
        self.assertEqual(_route("git status"), "git_status")

    def test_fix_error_still_works(self):
        self.assertEqual(_route("getting TypeError: unhashable type"), "fix_error")

    def test_model_status_still_works(self):
        self.assertEqual(_route("what model is currently loaded"), "model_status")


if __name__ == "__main__":
    unittest.main(verbosity=2)
