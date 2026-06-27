#!/usr/bin/env python3
"""
Security Filter — scrubs API keys, tokens, and credentials from README content.
Replaces matches with [REDACTED:<type>] placeholders.
Never blocks README generation — always returns safe content.
"""
import re
import sys
from pathlib import Path
from typing import Tuple

# Patterns: (label, regex) — ordered most-specific to most-general
SECRET_PATTERNS = [
    ("anthropic_key",  re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}")),
    ("openai_key",     re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("aws_access_key", re.compile(r"AKIA[A-Z0-9]{16}")),
    ("aws_secret",     re.compile(r"(?i)aws.{0,20}secret.{0,5}['\"]([A-Za-z0-9/+=]{40})['\"]")),
    ("gh_pat",         re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("gh_oauth",       re.compile(r"gho_[A-Za-z0-9]{36}")),
    ("gh_token",       re.compile(r"github_pat_[A-Za-z0-9_]{82}")),
    ("bearer_token",   re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_.~+/]{20,}")),
    ("generic_secret", re.compile(r"(?i)(api[_\-]?key|secret[_\-]?key|auth[_\-]?token)\s*[:=]\s*['\"]?([A-Za-z0-9\-_.]{20,})['\"]?")),
    ("private_key",    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("password_field", re.compile(r"(?i)password\s*[:=]\s*['\"]([^'\"]{8,})['\"]")),
]

# Suppress false positives — these are known safe patterns
SAFE_PATTERNS = [
    re.compile(r"sk-ant-example"),
    re.compile(r"sk-example"),
    re.compile(r"AKIA_EXAMPLE"),
    re.compile(r"\[REDACTED"),
    re.compile(r"<your[_\-]?"),
    re.compile(r"YOUR_API_KEY"),
    re.compile(r"placeholder"),
]


def _is_safe_match(line: str, start: int, end: int) -> bool:
    context = line[max(0, start - 10):end + 10]
    return any(p.search(context) for p in SAFE_PATTERNS)


def scrub_readme(content: str) -> Tuple[str, list]:
    """
    Scrub secrets from README content.

    Returns:
        (cleaned_content, redacted_list)
        redacted_list: list of strings like "anthropic_key at line 12"
    """
    redacted = []
    clean_lines = []

    for line_num, line in enumerate(content.split("\n"), start=1):
        clean_line = line
        for label, pattern in SECRET_PATTERNS:
            while True:
                match = pattern.search(clean_line)
                if not match:
                    break
                if _is_safe_match(clean_line, match.start(), match.end()):
                    break
                clean_line = (
                    clean_line[:match.start()]
                    + f"[REDACTED:{label}]"
                    + clean_line[match.end():]
                )
                redacted.append(f"{label} at line {line_num}")
        clean_lines.append(clean_line)

    return "\n".join(clean_lines), redacted


def is_clean(content: str) -> bool:
    """Quick check — True if no secrets detected."""
    _, found = scrub_readme(content)
    return len(found) == 0


if __name__ == "__main__":
    text = sys.stdin.read() if not sys.stdin.isatty() else "key: sk-ant-abc12345678901234567890"
    clean, found = scrub_readme(text)
    print(f"Redacted {len(found)} item(s): {found}")
    if found:
        print(f"Cleaned: {clean[:200]}")
