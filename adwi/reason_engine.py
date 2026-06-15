"""
reason_engine.py — Stateful multi-agent reasoning graph for /reason <task>.

Architecture (LangGraph-inspired, stdlib-only state machine):

  PlannerAgent  → produces JSON step array
  ExecutorAgent → runs each step via Adwi's internal tools
  CriticAgent   → reviews output, triggers retry on error footprint
  SafetyGateway → blocks high-risk steps; prompts terminal confirmation

Graph state flows:
  PLAN → EXECUTE (step N) → CRITIQUE → (pass) EXECUTE (step N+1) or DONE
                                      → (retry < 3) EXECUTE (step N) again
                                      → (max retries) DONE with partial result

All LLM calls go through Ollama (adwi:latest or cloud fallback).
No external dependencies beyond stdlib + what adwi_cli.py already has.
"""

import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Optional

OLLAMA_URL    = "http://127.0.0.1:11434"
MODEL_MAIN    = "adwi:latest"
MODEL_FAST    = "llama3.1:8b"
WORKSPACE     = Path.home() / "SuneelWorkSpace"
MAX_RETRIES   = 3

# ── Safety classification ────────────────────────────────────────────────────

_BLOCKED_PATTERNS = re.compile(
    r"(rm\s+-rf|git\s+push\s+--force|DROP\s+TABLE|truncate\s+table"
    r"|shutdown|reboot|format\s+disk|diskutil\s+erase"
    r"|/etc/|/private/|/System/|~/.ssh|~/.aws|secrets/)",
    re.I,
)

_REVIEW_PATTERNS = re.compile(
    r"(git\s+commit|git\s+push|docker\s+compose\s+down|brew\s+uninstall"
    r"|pip\s+uninstall|rm\s+-r(?!f)|mv\s+.*\s+/|launchctl\s+(un)?load"
    r"|chmod|chown|pkill|killall)",
    re.I,
)


def classify_risk(step_action: str) -> str:
    """Return BLOCKED | REVIEW-REQUIRED | SAFE."""
    if _BLOCKED_PATTERNS.search(step_action):
        return "BLOCKED"
    if _REVIEW_PATTERNS.search(step_action):
        return "REVIEW-REQUIRED"
    return "SAFE"


# ── Ollama helpers ────────────────────────────────────────────────────────────

def _ollama_chat(
    prompt: str,
    system: Optional[str] = None,
    model: str = MODEL_MAIN,
    timeout: int = 180,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": "/no_think\n" + prompt})
    payload = json.dumps(
        {"model": model, "messages": messages, "stream": False,
         "options": {"temperature": 0.2, "num_predict": 2048}}
    ).encode()
    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat", data=payload, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except Exception as e:
        return f"[LLM error: {e}]"


def _cloud_chat(prompt: str, model: str = "models/gemini-2.5-flash") -> str:
    """Fallback to Gemini via Open WebUI /api/chat/completions."""
    try:
        import os
        key = os.environ.get("OPENWEBUI_API_KEY", "")
        if not key:
            return _ollama_chat(prompt)
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:3000/api/chat/completions", data=payload,
            method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return _ollama_chat(prompt)


# ── Agent: Planner ────────────────────────────────────────────────────────────

_PLANNER_SYSTEM = """You are Adwi's Planner Agent.

Given a complex task from Suneel, produce a strict JSON array of steps.
Each step must be an object with exactly these fields:
  "id":          integer starting at 1
  "title":       short step name (≤ 8 words)
  "action_type": one of: "shell" | "file_read" | "file_write" | "memory_query" | "web_search" | "llm_reason" | "obsidian_write"
  "action":      the actual command, path, query, or prompt
  "depends_on":  list of step ids that must complete first ([] for first steps)
  "success_criteria": one sentence describing what a passing result looks like

Rules:
- Never include actions on secrets/, .ssh, .aws, credentials, or tokens.
- Prefer read-only steps first; batch writes last.
- Maximum 8 steps per plan.
- Output ONLY the JSON array. No markdown, no explanation.
"""


def planner_agent(task: str) -> list[dict]:
    prompt = f"Task: {task}\n\nProduce the execution plan as a JSON array:"
    raw = _ollama_chat(prompt, system=_PLANNER_SYSTEM, timeout=120)

    # Extract JSON array even if model wraps in markdown
    m = re.search(r"\[.*\]", raw, re.S)
    if not m:
        return [{"id": 1, "title": "Direct reasoning", "action_type": "llm_reason",
                 "action": task, "depends_on": [], "success_criteria": "Coherent answer produced"}]
    try:
        steps = json.loads(m.group(0))
        if not isinstance(steps, list):
            raise ValueError("not a list")
        return steps
    except Exception:
        return [{"id": 1, "title": "Direct reasoning", "action_type": "llm_reason",
                 "action": task, "depends_on": [], "success_criteria": "Coherent answer produced"}]


# ── Agent: Executor ───────────────────────────────────────────────────────────

def _exec_shell(cmd: str, timeout: int = 30) -> tuple[bool, str]:
    env = {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(Path.home()),
    }
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(WORKSPACE), env=env,
        )
        out = (r.stdout + r.stderr).strip()
        return r.returncode == 0, out[:2000]
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s"
    except Exception as e:
        return False, str(e)


def _exec_file_read(path_str: str) -> tuple[bool, str]:
    p = Path(path_str).expanduser()
    blocked_prefixes = [
        Path.home() / ".ssh", Path.home() / ".aws",
        WORKSPACE / "secrets", Path("/etc"), Path("/private"),
    ]
    for blocked in blocked_prefixes:
        try:
            p.resolve().relative_to(blocked.resolve())
            return False, f"BLOCKED: path is inside protected directory {blocked}"
        except ValueError:
            pass
    if not p.exists():
        return False, f"File not found: {p}"
    try:
        content = p.read_text(encoding="utf-8", errors="replace")[:4000]
        return True, content
    except Exception as e:
        return False, str(e)


def _exec_file_write(spec: str, context: dict) -> tuple[bool, str]:
    # spec format: "path::content" or just a path (content from context)
    if "::" in spec:
        path_str, content = spec.split("::", 1)
    else:
        path_str = spec
        content = context.get("write_content", "")
    p = Path(path_str).expanduser()
    # Safety: never write to system or secret dirs
    blocked = [Path.home() / ".ssh", Path("/etc"), WORKSPACE / "secrets"]
    for b in blocked:
        try:
            p.resolve().relative_to(b.resolve())
            return False, f"BLOCKED: write to {b} is not allowed"
        except ValueError:
            pass
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return True, f"Written {len(content)} chars to {p}"
    except Exception as e:
        return False, str(e)


def _exec_memory_query(query: str) -> tuple[bool, str]:
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "memory", WORKSPACE / "adwi" / "memory.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mem = mod.AdwiMemory()
        result = mem.format_context(query, k=5)
        mem.close()
        return True, result or "No relevant memories found."
    except Exception as e:
        return False, f"Memory query failed: {e}"


def _exec_web_search(query: str) -> tuple[bool, str]:
    try:
        import urllib.parse
        params = urllib.parse.urlencode(
            {"q": query, "format": "json", "language": "en"}
        )
        req = urllib.request.Request(
            f"http://127.0.0.1:8888/search?{params}",
            headers={"User-Agent": "Adwi-Reason/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        results = data.get("results", [])[:5]
        lines = [f"- [{r.get('title','')}]: {r.get('content','')[:200]}" for r in results]
        return True, "\n".join(lines) if lines else "No results."
    except Exception as e:
        return False, f"Search error: {e}"


def executor_agent(
    step: dict,
    context: dict,
    confirm_callback=None,
) -> tuple[bool, str]:
    """
    Execute one plan step. Returns (success, output).
    confirm_callback(step) → bool: called for REVIEW-REQUIRED steps.
    """
    action      = step.get("action", "")
    action_type = step.get("action_type", "llm_reason")

    # Safety gate
    risk = classify_risk(action)
    if risk == "BLOCKED":
        return False, f"SAFETY GATE: action blocked — matches high-risk pattern.\nAction: {action}"
    if risk == "REVIEW-REQUIRED":
        if confirm_callback:
            approved = confirm_callback(step)
            if not approved:
                return False, f"Step skipped — user declined at safety gate.\nAction: {action}"
        else:
            return False, f"SAFETY GATE: action requires manual confirmation.\nAction: {action}"

    # Dispatch
    if action_type == "shell":
        return _exec_shell(action)
    elif action_type == "file_read":
        return _exec_file_read(action)
    elif action_type == "file_write":
        return _exec_file_write(action, context)
    elif action_type == "memory_query":
        return _exec_memory_query(action)
    elif action_type == "web_search":
        return _exec_web_search(action)
    elif action_type == "obsidian_write":
        vault_path = WORKSPACE / "obsidian-vault" / action
        return _exec_file_write(
            str(vault_path) + "::" + context.get("obsidian_content", ""),
            context,
        )
    else:  # llm_reason (default)
        # Build context-enriched prompt
        ctx_block = ""
        if context.get("step_outputs"):
            prior = [f"Step {k}: {v[:500]}" for k, v in context["step_outputs"].items()]
            ctx_block = "\n\nPrior step outputs:\n" + "\n".join(prior)
        result = _ollama_chat(action + ctx_block, timeout=180)
        return bool(result) and not result.startswith("[LLM error"), result


# ── Agent: Critic ─────────────────────────────────────────────────────────────

_CRITIC_SYSTEM = """You are Adwi's Critic Agent.

Review a step's output and decide if it meets the success criteria.
Respond with ONLY valid JSON: {"verdict": "PASS" | "RETRY" | "FAIL", "reason": "one sentence"}

PASS  = output clearly satisfies success_criteria
RETRY = output has a recoverable error or is incomplete (max 3 retries allowed)
FAIL  = output has a non-recoverable error or the action was blocked
"""


def critic_agent(step: dict, output: str, attempt: int) -> dict:
    criteria = step.get("success_criteria", "Task completed without error.")
    prompt = (
        f"Step: {step.get('title','?')}\n"
        f"Action: {step.get('action','')[:200]}\n"
        f"Success criteria: {criteria}\n"
        f"Output (attempt {attempt}):\n{output[:1500]}\n\n"
        "Verdict?"
    )
    raw = _ollama_chat(prompt, system=_CRITIC_SYSTEM, model=MODEL_FAST, timeout=30)
    m = re.search(r"\{.*?\}", raw, re.S)
    if m:
        try:
            verdict = json.loads(m.group(0))
            if verdict.get("verdict") in ("PASS", "RETRY", "FAIL"):
                return verdict
        except Exception:
            pass
    # Heuristic fallback: if output starts with error marker, RETRY
    if output.startswith(("BLOCKED", "SAFETY", "[LLM error", "File not found")):
        return {"verdict": "FAIL", "reason": "Executor reported a hard error."}
    if "error" in output.lower() and attempt < MAX_RETRIES:
        return {"verdict": "RETRY", "reason": "Error detected in output."}
    return {"verdict": "PASS", "reason": "No obvious error detected."}


# ── Terminal confirmation callback ────────────────────────────────────────────

def terminal_confirm(step: dict) -> bool:
    """Prompt the user for approval of a REVIEW-REQUIRED step."""
    print(f"\n  \033[33m⚠  SAFETY GATE — review required\033[0m")
    print(f"  Step    : {step.get('title','?')}")
    print(f"  Action  : {step.get('action','?')[:120]}")
    print(f"  Proceed? [y/N] ", end="", flush=True)
    try:
        ans = input().strip().lower()
        return ans in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# ── Main graph runner ─────────────────────────────────────────────────────────

class ReasonGraph:
    def __init__(self, task: str, interactive: bool = True):
        self.task        = task
        self.interactive = interactive
        self.plan:   list[dict]       = []
        self.outputs: dict[int, str]  = {}   # step_id → output
        self.verdicts: dict[int, str] = {}   # step_id → PASS|FAIL
        self.log: list[str]           = []

    def _emit(self, msg: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.log.append(line)
        print(f"  \033[90m{line}\033[0m")

    def run(self) -> dict:
        # ── Phase 1: Plan ──────────────────────────────────────────────────
        self._emit("Planner: mapping task to execution steps …")
        self.plan = planner_agent(self.task)
        self._emit(f"Plan ready: {len(self.plan)} step(s)")
        for s in self.plan:
            self._emit(f"  [{s['id']}] {s['title']} ({s['action_type']})")

        # ── Phase 2: Execute + Critique ────────────────────────────────────
        context = {"task": self.task, "step_outputs": self.outputs}

        for step in self.plan:
            sid = step["id"]
            # Check dependencies
            deps = step.get("depends_on", [])
            dep_failed = [d for d in deps if self.verdicts.get(d) == "FAIL"]
            if dep_failed:
                self._emit(f"  [{sid}] Skipped — depends on failed step(s): {dep_failed}")
                self.verdicts[sid] = "FAIL"
                self.outputs[sid] = f"Skipped due to failed dependencies: {dep_failed}"
                continue

            attempt  = 0
            verdict  = {"verdict": "RETRY", "reason": "initial"}

            while verdict["verdict"] == "RETRY" and attempt < MAX_RETRIES:
                attempt += 1
                self._emit(f"  [{sid}] Executing (attempt {attempt}): {step['title']}")

                confirm_cb = terminal_confirm if self.interactive else None
                success, output = executor_agent(step, context, confirm_cb)

                self._emit(f"  [{sid}] {'✓' if success else '✗'} output: {output[:100].replace(chr(10),' ')}")
                verdict = critic_agent(step, output, attempt)
                self._emit(f"  [{sid}] Critic: {verdict['verdict']} — {verdict['reason']}")

                if verdict["verdict"] == "RETRY":
                    self._emit(f"  [{sid}] Retrying …")

            self.verdicts[sid] = verdict["verdict"]
            self.outputs[sid]  = output
            context["step_outputs"] = self.outputs

        # ── Phase 3: Final synthesis ───────────────────────────────────────
        passed  = [sid for sid, v in self.verdicts.items() if v == "PASS"]
        failed  = [sid for sid, v in self.verdicts.items() if v == "FAIL"]
        partial = len(failed) > 0 and len(passed) > 0

        self._emit(f"Synthesis: {len(passed)} passed, {len(failed)} failed")

        outputs_block = "\n\n".join(
            f"Step {sid} ({self.plan[sid-1]['title'] if sid <= len(self.plan) else '?'}):\n{out}"
            for sid, out in self.outputs.items()
        )
        summary_prompt = (
            f"Original task: {self.task}\n\n"
            f"Execution results:\n{outputs_block[:4000]}\n\n"
            f"{'PARTIAL COMPLETION — some steps failed.' if partial else ''}\n\n"
            "Write a concise, actionable summary of what was accomplished and what remains."
        )
        final_answer = _ollama_chat(summary_prompt, timeout=180)

        return {
            "task":         self.task,
            "plan":         self.plan,
            "outputs":      self.outputs,
            "verdicts":     self.verdicts,
            "passed":       passed,
            "failed":       failed,
            "partial":      partial,
            "final_answer": final_answer,
            "log":          self.log,
        }


def run_reason(task: str, interactive: bool = True) -> str:
    """Entry point called by adwi_cli.py /reason handler."""
    graph = ReasonGraph(task, interactive=interactive)
    result = graph.run()

    lines = [
        f"\n\033[35m\033[1m  Adwi Reason Engine — Complete\033[0m",
        f"  Steps: {len(result['plan'])} planned  ·  "
        f"{len(result['passed'])} passed  ·  {len(result['failed'])} failed",
    ]
    if result["failed"]:
        lines.append(f"  \033[33mFailed steps: {result['failed']}\033[0m")
    lines.append(f"\n{result['final_answer']}")

    return "\n".join(lines)
