""" Contains GameVersion class, which represents a game version """

import re
from bisect import bisect_left
from functools import total_ordering
from typing import Collection, Self

VERSION_RE = re.compile(r"\d+(\.\d+)+")


__all__ = ["GameVersion"]


@total_ordering
class GameVersion:
    """Represents a game version"""

    _subversions: tuple[int, ...]

    def __init__(self, version: "str | GameVersion | tuple[int, ...]"):
        match version:
            case str():
                if version.startswith("v"):
                    version = version[1:]
                self._subversions = tuple(int(v) for v in version.split("."))
            case GameVersion():
                self._subversions = version._subversions
            case tuple():
                self._subversions = version

    @classmethod
    def match(cls, s: str) -> Self | None:
        """Convert string to GameVersion, return None if not possible"""
        if s.startswith("v"):
            s = s[1:]
        if VERSION_RE.match(s) is None:
            return None
        return cls(s)

    def get_matching_version(
        self, versions: "Collection[GameVersion]"
    ) -> "GameVersion | None":
        """
        If this version in `version`, return this version.
        Otherwise, returns maximum version lower than this, or None if none available.
        """
        versions = list(sorted(versions))
        return (
            self
            if self in versions
            else versions[x - 1] if (x := bisect_left(versions, self)) else None
        )

    def __hash__(self) -> int:
        return hash(self._subversions)

    def __str__(self) -> str:
        return ".".join(map(str, self._subversions))

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, GameVersion):
            return False
        return self._subversions == __value._subversions

    def __lt__(self, __value: object) -> bool:
        if not isinstance(__value, GameVersion):
            raise NotImplementedError()
        for this, other in zip(self._subversions, __value._subversions):
            if this < other:
                return True
        return len(self._subversions) < len(__value._subversions)
