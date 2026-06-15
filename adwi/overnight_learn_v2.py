#!/usr/bin/env python3
"""
overnight_learn_v2.py — Differential, parallel knowledge-indexing loop.

Key improvements over v1:
  1. Differential scanning  — skips unchanged files via mtime + content hash
     (ManifestStore in ingest_manifest.py). First run is slow, subsequent runs
     index only changed files.
  2. Parallel embedding     — ThreadPoolExecutor(max_workers=EMBED_WORKERS)
     issues concurrent embedding calls to Ollama, saturating the HTTP API.
  3. Parallel Q&A           — ThreadPoolExecutor(max_workers=QA_WORKERS) runs
     multiple Q&A generation calls concurrently (bounded to avoid OOM).
  4. Resumable              — on interrupt, completed files are already written
     to the manifest. Restart picks up exactly where it left off.
  5. Same DB schema         — fully backward-compatible with knowledge.db from v1.

Approximate timings (M4 Max, 64 GB RAM, adwi:latest):
  v1 (sequential):         ~7 hours for 1,565 files
  v2 (differential, warm): ~2 minutes  (only changed files)
  v2 (differential, cold): ~45–60 minutes (all files, parallel)

Usage:
    python3 overnight_learn_v2.py [--workers N] [--qa-workers N] [--force]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# ── venv injection ────────────────────────────────────────────────────────────
_VENV_SITE = (
    Path.home()
    / "SuneelWorkSpace"
    / "adwi"
    / ".venv"
    / "lib"
    / f"python{sys.version_info.major}.{sys.version_info.minor}"
    / "site-packages"
)
if _VENV_SITE.exists() and str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))

try:
    from markitdown import MarkItDown as _MarkItDown
    _MARKITDOWN = _MarkItDown()
    MARKITDOWN_OK = True
except Exception:
    _MARKITDOWN = None
    MARKITDOWN_OK = False

# ── Manifest import ───────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE.parent))
from adwi.ingest_manifest import ManifestStore  # noqa: E402

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

WORKSPACE_DIR     = Path.home() / "SuneelWorkSpace"
OLLAMA_URL        = "http://127.0.0.1:11434"
QA_MODEL          = "adwi:latest"
EMBED_MODEL       = "nomic-embed-text"
FAST_MODEL        = "qwen3:0.6b"

DB_PATH           = WORKSPACE_DIR / "adwi" / "knowledge.db"
MANIFEST_PATH     = WORKSPACE_DIR / "adwi" / ".ingest_manifest.json"
DESKTOP           = Path.home() / "Desktop"
LOG_PATH          = Path("/tmp/overnight-learn-v2.log")

QUESTIONS_PER_CHUNK = 3
CHUNK_CHARS         = 2400
CHUNK_OVERLAP       = 150
MAX_FILE_BYTES      = 180_000
MIN_FILE_BYTES      = 80

# Concurrency — tuned for M4 Max (16-core) + 64 GB unified RAM
# Embedding calls are IO-bound (HTTP → Ollama, ~100 ms each)
DEFAULT_EMBED_WORKERS = 8
# Q&A calls are compute-bound on GPU; 3 concurrent prevents OOM
DEFAULT_QA_WORKERS    = 3
# How often to flush manifest to disk
FLUSH_EVERY_N_FILES   = 25

TARGET_EXTS = {
    ".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".h",
    ".rb", ".swift", ".kt", ".sh", ".bash", ".zsh",
    ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini",
    ".html", ".css", ".sql",
}
RICH_EXTS = {".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".epub", ".zip"}

SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".venv", "venv", "env",
    "dist", "build", ".idea", ".vscode", "open-webui-data", "n8n-data",
    "qdrant-data", "searxng-data", "ollama-blobs", ".npm", "models",
    "rag-db", "training-data", ".pytest_cache", "coverage", ".mypy_cache",
}

# ── Logging setup ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_PATH), encoding="utf-8"),
    ],
)
log = logging.getLogger("overnight_learn_v2")


# ── SQLite schema (identical to v1 for backward compat) ───────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,
    file_path   TEXT    NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text  TEXT    NOT NULL,
    chunk_hash  TEXT    NOT NULL UNIQUE,
    embedding   TEXT
);
CREATE TABLE IF NOT EXISTS qa_pairs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,
    file_path   TEXT    NOT NULL,
    chunk_id    INTEGER,
    question    TEXT    NOT NULL,
    answer      TEXT    NOT NULL,
    qa_hash     TEXT    NOT NULL UNIQUE,
    embedding   TEXT
);
CREATE INDEX IF NOT EXISTS idx_chunk_fp  ON chunks(file_path);
CREATE INDEX IF NOT EXISTS idx_chunk_h   ON chunks(chunk_hash);
CREATE INDEX IF NOT EXISTS idx_qa_fp     ON qa_pairs(file_path);
CREATE INDEX IF NOT EXISTS idx_qa_cid    ON qa_pairs(chunk_id);
CREATE INDEX IF NOT EXISTS idx_qa_hash   ON qa_pairs(qa_hash);
"""


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()


def _cosine(a: list, b: list) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na  = math.sqrt(sum(x * x for x in a))
    nb  = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


# ── Thread-safe KnowledgeDB ───────────────────────────────────────────────────


class KnowledgeDB:
    """
    Thread-safe wrapper around the SQLite knowledge store.
    Uses a per-thread connection pool (check_same_thread=False is insufficient
    for concurrent writes; we serialize inserts with a lock instead).
    """

    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._local = threading.local()
        # Initialize schema using a fresh connection
        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.executescript(_SCHEMA)
        conn.commit()
        conn.close()

    def _conn(self) -> sqlite3.Connection:
        """Get (or create) a per-thread connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.path), check_same_thread=False
            )
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    # ── Write helpers (all use the per-thread conn + a write lock) ────────────

    def chunk_exists(self, h: str) -> bool:
        cur = self._conn().execute(
            "SELECT 1 FROM chunks WHERE chunk_hash=?", (h,)
        )
        return cur.fetchone() is not None

    def insert_chunk(
        self, file_path: str, idx: int, text: str, emb: list
    ) -> int:
        h        = _sha(text)
        emb_json = json.dumps(emb) if emb else None
        ts       = datetime.now(timezone.utc).isoformat()
        with self._lock:
            try:
                cur = self._conn().execute(
                    "INSERT INTO chunks (ts,file_path,chunk_index,chunk_text,chunk_hash,embedding)"
                    " VALUES (?,?,?,?,?,?)",
                    (ts, file_path, idx, text, h, emb_json),
                )
                self._conn().commit()
                return cur.lastrowid  # type: ignore[return-value]
            except sqlite3.IntegrityError:
                # Already exists; return existing row id
                row = self._conn().execute(
                    "SELECT id FROM chunks WHERE chunk_hash=?", (h,)
                ).fetchone()
                return row[0] if row else -1

    def qa_exists(self, h: str) -> bool:
        cur = self._conn().execute(
            "SELECT 1 FROM qa_pairs WHERE qa_hash=?", (h,)
        )
        return cur.fetchone() is not None

    def insert_qa(
        self, file_path: str, chunk_id: int, q: str, a: str, emb: list
    ) -> None:
        h        = _sha(q + a)
        emb_json = json.dumps(emb) if emb else None
        ts       = datetime.now(timezone.utc).isoformat()
        with self._lock:
            try:
                self._conn().execute(
                    "INSERT INTO qa_pairs (ts,file_path,chunk_id,question,answer,qa_hash,embedding)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (ts, file_path, chunk_id, q, a, h, emb_json),
                )
                self._conn().commit()
            except sqlite3.IntegrityError:
                pass

    def stats(self) -> dict:
        c = self._conn().execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        q = self._conn().execute("SELECT COUNT(*) FROM qa_pairs").fetchone()[0]
        f = self._conn().execute(
            "SELECT COUNT(DISTINCT file_path) FROM chunks"
        ).fetchone()[0]
        return {"chunks": c, "qa_pairs": q, "files": f}

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# ── Ollama helpers ────────────────────────────────────────────────────────────


def _post(endpoint: str, payload: dict, timeout: int = 240) -> dict:
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        f"{OLLAMA_URL}{endpoint}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def ollama_ok() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=4)
        return True
    except Exception:
        return False


def wait_for_ollama(max_wait: int = 90) -> bool:
    for _ in range(max_wait // 3):
        if ollama_ok():
            return True
        time.sleep(3)
    return False


def embed_text(text: str, retries: int = 3) -> list:
    """Embed a single text chunk. Called from worker threads."""
    for attempt in range(retries):
        try:
            resp = _post(
                "/api/embeddings",
                {"model": EMBED_MODEL, "prompt": text[:4000]},
                timeout=25,
            )
            v = resp.get("embedding", [])
            if v:
                return v
        except Exception as exc:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                log.debug("embed_text failed after %d attempts: %s", retries, exc)
    return []


def generate_qa(chunk_text: str, file_path: str, n: int = QUESTIONS_PER_CHUNK) -> list:
    """Generate Q&A pairs for one chunk. Called from worker threads."""
    ext  = Path(file_path).suffix.lstrip(".")
    lang = {
        "py": "Python", "js": "JavaScript", "ts": "TypeScript",
        "go": "Go", "rs": "Rust", "java": "Java", "cpp": "C++",
        "c": "C", "rb": "Ruby", "swift": "Swift", "kt": "Kotlin",
        "sh": "Shell script", "bash": "Bash", "sql": "SQL",
        "md": "Markdown documentation", "yaml": "YAML config",
        "toml": "TOML config", "json": "JSON config",
    }.get(ext, "source code")

    prompt = (
        f"You are a principal engineer doing a deep code review of this {lang} file.\n"
        f"FILE: {Path(file_path).name}\n\n"
        f"```{ext}\n{chunk_text[:2600]}\n```\n\n"
        f"Generate exactly {n} advanced technical Q&A pairs that a senior engineer "
        f"would want to know. Focus on non-obvious design decisions, edge cases, "
        f"performance, security, and system interactions.\n\n"
        f"Return ONLY a JSON array — no prose, no markdown fences:\n"
        f'[{{"q":"...","a":"..."}}]'
    )
    for attempt in range(3):
        try:
            resp = _post(
                "/api/generate",
                {
                    "model": QA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.75,
                        "num_predict": 2200,
                        "top_p": 0.92,
                        "repeat_penalty": 1.1,
                    },
                },
                timeout=200,
            )
            raw = resp.get("response", "").strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
            raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)
            m = re.search(r"\[[\s\S]*\]", raw)
            if not m:
                objs = re.findall(r'\{[^{}]+\}', raw)
                raw  = "[" + ",".join(objs) + "]" if objs else "[]"
            else:
                raw  = m.group(0)
            pairs = json.loads(raw)
            valid = [
                p for p in pairs
                if isinstance(p, dict)
                and isinstance(p.get("q"), str) and len(p["q"]) > 20
                and isinstance(p.get("a"), str) and len(p["a"]) > 40
            ]
            if valid:
                return valid[:n]
        except (json.JSONDecodeError, ValueError) as exc:
            log.debug("QA parse error (attempt %d/3): %s", attempt + 1, exc)
            time.sleep(3)
        except urllib.error.URLError as exc:
            log.debug("Ollama timeout (attempt %d/3): %s", attempt + 1, exc)
            time.sleep(8)
        except Exception as exc:
            log.debug("generate_qa error (attempt %d/3): %s", attempt + 1, exc)
            if attempt < 2:
                time.sleep(5)
    return []


# ── File scanning & chunking ──────────────────────────────────────────────────


def crawl_workspace(root: Path) -> list[Path]:
    all_exts = TARGET_EXTS | (RICH_EXTS if MARKITDOWN_OK else set())
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        if path.suffix.lower() not in all_exts:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        max_bytes = 5_000_000 if path.suffix.lower() in RICH_EXTS else MAX_FILE_BYTES
        if size < MIN_FILE_BYTES or size > max_bytes:
            continue
        files.append(path)
    return files


def read_file_content(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in RICH_EXTS and MARKITDOWN_OK and _MARKITDOWN:
        try:
            result = _MARKITDOWN.convert(str(file_path))
            md = result.text_content if hasattr(result, "text_content") else str(result)
            if md and len(md.strip()) > 40:
                return md
        except Exception as exc:
            log.debug("markitdown failed for %s: %s", file_path.name, exc)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str) -> list[tuple[int, str]]:
    chunks: list[tuple[int, str]] = []
    idx   = 0
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        if end < len(text):
            nl = text.rfind("\n", start + CHUNK_CHARS // 2, end)
            if nl > 0:
                end = nl + 1
        piece = text[start:end].strip()
        if piece:
            chunks.append((idx, piece))
            idx += 1
        next_start = end - CHUNK_OVERLAP
        if next_start <= start:
            next_start = start + 1
        if next_start >= len(text) - 40:
            break
        start = next_start
    return chunks


# ── Per-file worker (runs in ThreadPoolExecutor) ──────────────────────────────


def process_file(
    file_path: Path,
    db: KnowledgeDB,
    embed_executor: ThreadPoolExecutor,
    qa_executor: ThreadPoolExecutor,
) -> tuple[int, int]:
    """
    Index one file: chunk → embed (parallel) → Q&A (parallel) → store.
    Returns (chunks_added, qa_pairs_added).
    Exceptions propagate to the caller (the main loop) so they can be caught
    and the file marked as failed in the manifest.
    """
    try:
        raw = read_file_content(file_path)
    except Exception as exc:
        raise RuntimeError(f"read failed: {exc}") from exc

    chunks = chunk_text(raw)
    if not chunks:
        return 0, 0

    fp_str = str(file_path)
    chunks_added  = 0
    qa_pairs_added = 0

    # ── Stage 1: Embed all chunks in parallel ─────────────────────────────
    embed_futures: dict[Future, tuple[int, str]] = {
        embed_executor.submit(embed_text, chunk_text_): (idx, chunk_text_)
        for idx, chunk_text_ in chunks
    }

    chunk_ids: dict[tuple[int, str], int] = {}   # (idx, text) → db row id

    for future in as_completed(embed_futures):
        idx, text = embed_futures[future]
        try:
            emb = future.result()
        except Exception as exc:
            log.debug("embed error for chunk %d of %s: %s", idx, file_path.name, exc)
            emb = []

        if not db.chunk_exists(_sha(text)):
            row_id = db.insert_chunk(fp_str, idx, text, emb)
            chunk_ids[(idx, text)] = row_id
            chunks_added += 1
        else:
            # Chunk already in DB; look up its id for Q&A association
            cur = db._conn().execute(
                "SELECT id FROM chunks WHERE chunk_hash=?", (_sha(text),)
            )
            row = cur.fetchone()
            chunk_ids[(idx, text)] = row[0] if row else -1

    # ── Stage 2: Generate Q&A in parallel, embed answers concurrently ────
    qa_futures: dict[Future, tuple[int, str, int]] = {
        qa_executor.submit(generate_qa, text, fp_str): (idx, text, chunk_ids.get((idx, text), -1))
        for idx, text in chunks
    }

    for future in as_completed(qa_futures):
        idx, text, chunk_id = qa_futures[future]
        try:
            pairs = future.result()
        except Exception as exc:
            log.debug("qa error for chunk %d of %s: %s", idx, file_path.name, exc)
            pairs = []

        for pair in pairs:
            q, a = pair.get("q", ""), pair.get("a", "")
            if not q or not a:
                continue
            if db.qa_exists(_sha(q + a)):
                continue
            # Embed Q+A for semantic retrieval
            qa_emb = embed_text(f"Q: {q}\nA: {a}")
            db.insert_qa(fp_str, chunk_id, q, a, qa_emb)
            qa_pairs_added += 1

    return chunks_added, qa_pairs_added


# ── Main ──────────────────────────────────────────────────────────────────────


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Overnight differential knowledge indexer")
    parser.add_argument("--workers",    type=int, default=DEFAULT_EMBED_WORKERS,
                        help="Embedding worker threads (default: 8)")
    parser.add_argument("--qa-workers", type=int, default=DEFAULT_QA_WORKERS,
                        help="Q&A generation worker threads (default: 3)")
    parser.add_argument("--force",      action="store_true",
                        help="Re-index all files even if unchanged")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Only process files marked as failed in manifest")
    args = parser.parse_args(argv)

    log.info("=" * 64)
    log.info("  OVERNIGHT LEARN v2 — differential parallel indexer")
    log.info("  Workspace : %s", WORKSPACE_DIR)
    log.info("  embed workers: %d  |  QA workers: %d", args.workers, args.qa_workers)
    log.info("=" * 64)

    if not wait_for_ollama(90):
        log.error("Ollama not reachable on :11434 — is it running?")
        sys.exit(1)
    log.info("Ollama is up ✓")

    # Warm up embedding model
    test_emb = embed_text("warmup")
    if not test_emb:
        log.error("%s not responding — run: ollama pull %s", EMBED_MODEL, EMBED_MODEL)
        sys.exit(1)
    log.info("Embedding model OK — %d dimensions ✓", len(test_emb))

    db       = KnowledgeDB(DB_PATH)
    manifest = ManifestStore(MANIFEST_PATH)

    # Determine which files to process
    log.info("Crawling workspace...")
    all_files = crawl_workspace(WORKSPACE_DIR)
    log.info("Found %d eligible files", len(all_files))

    if args.retry_failed:
        todo = manifest.failed_files()
        log.info("Retry mode: %d previously failed files", len(todo))
    elif args.force:
        todo = all_files
        log.info("Force mode: indexing all %d files", len(todo))
    else:
        todo = manifest.changed_files(all_files)
        skipped = len(all_files) - len(todo)
        log.info(
            "%d files changed/new  |  %d unchanged (skipped)",
            len(todo), skipped,
        )

    if not todo:
        log.info("Nothing to do — knowledge base is up to date.")
        db_stats = db.stats()
        log.info("DB: %d chunks  %d Q&A pairs  %d files", **db_stats)
        return

    start     = time.monotonic()
    processed = 0
    total_chunks = 0
    total_qa     = 0
    failed_count = 0

    with (
        ThreadPoolExecutor(max_workers=args.workers,    thread_name_prefix="embed") as embed_pool,
        ThreadPoolExecutor(max_workers=args.qa_workers, thread_name_prefix="qa")    as qa_pool,
    ):
        for i, file_path in enumerate(todo, 1):
            try:
                rel = file_path.relative_to(WORKSPACE_DIR)
            except ValueError:
                rel = file_path

            log.info("[%d/%d] %s", i, len(todo), rel)
            t0 = time.monotonic()

            try:
                n_chunks, n_qa = process_file(
                    file_path, db, embed_pool, qa_pool
                )
                manifest.mark(file_path, chunks=n_chunks, qa_pairs=n_qa)
                total_chunks += n_chunks
                total_qa     += n_qa
                processed    += 1
                elapsed       = time.monotonic() - t0
                log.info(
                    "  ✓ %d chunks  %d Q&A  (%.1fs)", n_chunks, n_qa, elapsed
                )
            except Exception as exc:
                log.warning("  ✗ FAILED %s: %s", rel, exc)
                manifest.mark_failed(file_path)
                failed_count += 1

            # Periodic manifest flush
            if i % FLUSH_EVERY_N_FILES == 0:
                manifest.flush()
                log.debug("Manifest flushed at file %d", i)

    # Final flush
    manifest.flush()

    elapsed_total = time.monotonic() - start
    db_stats      = db.stats()
    mstats        = manifest.stats()

    log.info("=" * 64)
    log.info("DONE  elapsed=%.1fs  (%.1f min)", elapsed_total, elapsed_total / 60)
    log.info(
        "This run:  %d files processed  %d chunks  %d Q&A  %d failed",
        processed, total_chunks, total_qa, failed_count,
    )
    log.info(
        "DB total:  %d chunks  %d Q&A pairs  %d files",
        db_stats["chunks"], db_stats["qa_pairs"], db_stats["files"],
    )
    log.info("Manifest:  %d tracked  %d ok  %d failed", **{
        k: mstats[k] for k in ("total_tracked", "ok", "failed")
    })
    log.info("=" * 64)

    db.close()


if __name__ == "__main__":
    main()
