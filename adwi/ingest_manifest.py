"""
ingest_manifest.py — Persistent differential-scan state for overnight_learn.py.

Manifest schema (JSON):
{
  "version": 2,
  "ts":      "ISO-8601 of last successful run",
  "files": {
    "/abs/path/to/file.py": {
      "mtime":        1718000000.0,   # float, st_mtime at index time
      "sha256":       "abc123...",    # first-8KB content hash
      "indexed_at":   "ISO-8601",
      "chunks":       4,
      "qa_pairs":     12,
      "status":       "ok" | "failed" | "skipped"
    }
  }
}

Thread-safety: ManifestStore is NOT thread-safe for concurrent writes.
Call flush() only from the main thread after all workers complete a batch.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

MANIFEST_VERSION = 2
HASH_SAMPLE_BYTES = 8192   # read first 8 KB for fast content fingerprint


# ── File record ───────────────────────────────────────────────────────────────


@dataclass
class FileRecord:
    mtime:      float
    sha256:     str
    indexed_at: str
    chunks:     int = 0
    qa_pairs:   int = 0
    status:     str = "ok"    # "ok" | "failed" | "skipped"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "FileRecord":
        return cls(
            mtime=float(d.get("mtime", 0)),
            sha256=str(d.get("sha256", "")),
            indexed_at=str(d.get("indexed_at", "")),
            chunks=int(d.get("chunks", 0)),
            qa_pairs=int(d.get("qa_pairs", 0)),
            status=str(d.get("status", "ok")),
        )


# ── Manifest store ────────────────────────────────────────────────────────────


class ManifestStore:
    """
    Lightweight JSON manifest that tracks which files have been indexed
    and whether they have changed since last run.

    Usage:
        manifest = ManifestStore(Path("/tmp/ingest_manifest.json"))
        changed  = manifest.changed_files(all_files)
        # ... index changed_files ...
        manifest.mark(path, chunks=4, qa_pairs=12)
        manifest.flush()
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, FileRecord] = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if raw.get("version") != MANIFEST_VERSION:
                log.info("Manifest version mismatch — starting fresh")
                return
            for abs_path, rec_dict in raw.get("files", {}).items():
                try:
                    self._data[abs_path] = FileRecord.from_dict(rec_dict)
                except Exception as exc:
                    log.debug("Skipping bad manifest entry %s: %s", abs_path, exc)
            log.info("Manifest loaded: %d file records", len(self._data))
        except Exception as exc:
            log.warning("Could not load manifest (%s) — starting fresh", exc)
            self._data = {}

    def flush(self) -> None:
        """Write manifest to disk atomically (write-then-rename)."""
        tmp = self.path.with_suffix(".tmp")
        payload = {
            "version": MANIFEST_VERSION,
            "ts": datetime.now(timezone.utc).isoformat(),
            "files": {p: r.to_dict() for p, r in self._data.items()},
        }
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    # ── Querying ──────────────────────────────────────────────────────────────

    def is_changed(self, file_path: Path) -> bool:
        """
        Returns True if the file should be (re-)indexed.
        A file is considered unchanged if:
          - it has an "ok" record in the manifest
          - its on-disk mtime matches the recorded mtime
          - its first-8KB sha256 matches the recorded hash
        """
        key = str(file_path.resolve())
        rec = self._data.get(key)
        if rec is None or rec.status != "ok":
            return True
        try:
            current_mtime = file_path.stat().st_mtime
        except OSError:
            return True
        if abs(current_mtime - rec.mtime) > 0.01:  # mtime differs
            return True
        # mtime matches → quick-check content hash to catch same-second writes
        current_hash = _sha256_prefix(file_path)
        return current_hash != rec.sha256

    def changed_files(self, paths: list[Path]) -> list[Path]:
        """Filter `paths` to only those that need (re-)indexing."""
        return [p for p in paths if self.is_changed(p)]

    def failed_files(self) -> list[Path]:
        """Return paths that are marked 'failed' — useful for retry runs."""
        return [
            Path(p) for p, r in self._data.items() if r.status == "failed"
        ]

    # ── Writing ───────────────────────────────────────────────────────────────

    def mark(
        self,
        file_path: Path,
        *,
        chunks: int = 0,
        qa_pairs: int = 0,
        status: str = "ok",
    ) -> None:
        """Record a completed (or failed) indexing result for one file."""
        key = str(file_path.resolve())
        try:
            mtime  = file_path.stat().st_mtime
            sha256 = _sha256_prefix(file_path)
        except OSError:
            mtime  = 0.0
            sha256 = ""
        self._data[key] = FileRecord(
            mtime=mtime,
            sha256=sha256,
            indexed_at=datetime.now(timezone.utc).isoformat(),
            chunks=chunks,
            qa_pairs=qa_pairs,
            status=status,
        )

    def mark_failed(self, file_path: Path) -> None:
        self.mark(file_path, status="failed")

    def mark_skipped(self, file_path: Path) -> None:
        self.mark(file_path, status="skipped")

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        total  = len(self._data)
        ok     = sum(1 for r in self._data.values() if r.status == "ok")
        failed = sum(1 for r in self._data.values() if r.status == "failed")
        chunks = sum(r.chunks for r in self._data.values())
        qa     = sum(r.qa_pairs for r in self._data.values())
        return {
            "total_tracked": total,
            "ok": ok,
            "failed": failed,
            "skipped": total - ok - failed,
            "total_chunks": chunks,
            "total_qa_pairs": qa,
        }

    def __len__(self) -> int:
        return len(self._data)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _sha256_prefix(path: Path) -> str:
    """SHA-256 of the first HASH_SAMPLE_BYTES of a file. Fast and collision-resistant."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            h.update(f.read(HASH_SAMPLE_BYTES))
    except OSError:
        return ""
    return h.hexdigest()
