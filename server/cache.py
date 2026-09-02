"""Small thread-safe cache of recently rendered screen artifacts."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class ScreenArtifact:
    version: str
    png: bytes


class ArtifactCache:
    def __init__(self, max_versions: int = 2) -> None:
        if max_versions < 1:
            raise ValueError("Cache must retain at least one version")
        self.max_versions = max_versions
        self._artifacts: OrderedDict[str, ScreenArtifact] = OrderedDict()
        self._lock = Lock()

    def get(self, version: str) -> ScreenArtifact | None:
        with self._lock:
            artifact = self._artifacts.get(version)
            if artifact is not None:
                self._artifacts.move_to_end(version)
            return artifact

    def put(self, artifact: ScreenArtifact) -> None:
        with self._lock:
            self._artifacts[artifact.version] = artifact
            self._artifacts.move_to_end(artifact.version)
            while len(self._artifacts) > self.max_versions:
                self._artifacts.popitem(last=False)

    def latest(self) -> ScreenArtifact | None:
        with self._lock:
            if not self._artifacts:
                return None
            return next(reversed(self._artifacts.values()))

    def clear(self) -> None:
        with self._lock:
            self._artifacts.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._artifacts)
