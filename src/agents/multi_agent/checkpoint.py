"""Durable, restart-safe LangGraph checkpointer, with no new dependency.

AD-6's mandated fallback (00-EXECUTIVE-SUMMARY.md): *"if
langgraph-checkpoint-sqlite proves fragile, persist the full graph state as
JSON ... same observable behaviour, no new dependency."* This worktree
never had that package to begin with -- it is not in requirements.txt and
WS-8 does not own that file -- so this *is* the fallback, not a downgrade
from it. See docs/implementation/integration-requests/WS-8.md.

`InMemorySaver` (bundled with `langgraph` core) already implements the
correct checkpoint algorithm -- versioning, pending writes, delta-channel
history. Reimplementing that from the abstract `BaseCheckpointSaver`
interface from scratch, for a "highest risk" stream, would be exactly the
kind of subtle-bug surface a durable-interrupt claim cannot afford. So this
class changes nothing about the algorithm: it wraps `InMemorySaver`'s three
plain dict/defaultdict structures (`storage`, `writes`, `blobs` -- already
just string/bytes/tuple values, nothing exotic) and pickles them to disk
after every write, reloading them in `__init__`. A second process
constructing this class against the same path sees every prior checkpoint,
which is the one property a real restart test can actually verify.
"""
import pickle
import time
import threading
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver


class DurableFileSaver(InMemorySaver):
    """A file-persisted `InMemorySaver`. Same algorithm, durable storage."""

    def __init__(self, path: str):
        super().__init__()
        self._path = Path(path)
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        with open(self._path, "rb") as f:
            data = pickle.load(f)
        for thread_id, ns_map in data.get("storage", {}).items():
            for ns, checkpoints in ns_map.items():
                self.storage[thread_id][ns] = checkpoints
        self.writes.update(data.get("writes", {}))
        self.blobs.update(data.get("blobs", {}))

    def _flush(self) -> None:
        payload = {
            "storage": {tid: dict(ns_map) for tid, ns_map in self.storage.items()},
            "writes": dict(self.writes),
            "blobs": dict(self.blobs),
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(f"{self._path.suffix}.{id(self)}.tmp")
        with open(tmp, "wb") as f:
            pickle.dump(payload, f)
        # Windows can transiently deny a same-directory rename right after a
        # write (antivirus / indexer holding a brief read handle on the just
        # -closed file) -- a real, observed failure mode in this repo's own
        # test runs, not a hypothetical one. Retry a few times before giving
        # up; this is the only place that risk is handled, deliberately, so
        # a durable-interrupt claim does not rest on a flush that sometimes
        # silently loses a checkpoint.
        last_err = None
        for attempt in range(5):
            try:
                tmp.replace(self._path)  # atomic on the same filesystem
                return
            except PermissionError as e:
                last_err = e
                time.sleep(0.05 * (attempt + 1))
        raise last_err

    def put(self, config, checkpoint, metadata, new_versions):
        with self._lock:
            result = super().put(config, checkpoint, metadata, new_versions)
            self._flush()
            return result

    def put_writes(self, config, writes, task_id, task_path=""):
        with self._lock:
            super().put_writes(config, writes, task_id, task_path)
            self._flush()
