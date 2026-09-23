"""
In-memory LRU-style cache for neuPrint query results.

Purpose:
  Repeated requests for the same neuron or neighborhood must not
  re-query the remote neuPrint service unnecessarily.

Scope:
  Cache is provider-instance-scoped (not process-wide).
  Maximum cache size is bounded to prevent uncontrolled memory growth.
  We do NOT cache the entire connectome — only explicitly requested records.

Cache keys:
  Neuron record   : "neuron:{body_id}"
  Connections     : "connections:{body_id}"
  Neighbors       : "neighbors:{body_id}:{hops}"
  Cell-type query : "cell_type:{cell_type}"
  Region query    : "region:{region}"
"""
import threading
from collections import OrderedDict
from typing import Any, Optional


class LRUCache:
    """Thread-safe bounded LRU cache."""

    def __init__(self, max_size: int = 512) -> None:
        self._max_size = max_size
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self._max_size:
                # Evict least recently used
                self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    # ------------------------------------------------------------------
    # Convenience key builders
    # ------------------------------------------------------------------

    @staticmethod
    def neuron_key(body_id: str) -> str:
        return f"neuron:{body_id}"

    @staticmethod
    def connections_key(body_id: str) -> str:
        return f"connections:{body_id}"

    @staticmethod
    def neighbors_key(body_id: str, hops: int) -> str:
        return f"neighbors:{body_id}:{hops}"

    @staticmethod
    def cell_type_key(cell_type: str) -> str:
        return f"cell_type:{cell_type}"

    @staticmethod
    def region_key(region: str) -> str:
        return f"region:{region}"
