""" Contains GameVersion class, which represents a game version """

import re
from bisect import bisect_left
from dataclasses import dataclass
from functools import total_ordering
from typing import Collection, Self

VERSION_RE = re.compile(r"v?(?P<version>\d(\.\d+)+)(?P<adds> *[A-Za-z\d ]+)*$")


__all__ = ["GameVersion"]


@total_ordering
@dataclass(frozen=True)
class GameVersion:
    """Represents a game version"""

    subversions: tuple[int, ...]
    adds: tuple[str, ...] | None = None

    @classmethod
    def new(cls, version: "str | GameVersion ") -> Self:
        """Create a new GameVersion instance

        Either parses a string or creates a copy of the provided GameVersion
        """
        match version:
            case str():
                return cls.from_string(version)
            case GameVersion():
                return cls(version.subversions, version.adds)

    @classmethod
    def from_string(cls, source: str) -> Self:
        """Create a GameVersion instance from string"""
        match = VERSION_RE.match(source)
        if not match:
            raise ValueError(f"{source[:100]} is not a version string")
        version_part = match.group("version")
        adds_part = match.group("adds")
        version_tuple = tuple(map(int, version_part.split(".")))
        adds_tuple = tuple(adds_part.strip().split(" ")) if adds_part else None
        return cls(version_tuple, adds_tuple)

    @classmethod
    def match(cls, source: str) -> Self | None:
        """Convert string to GameVersion, return None if not possible"""
        try:
            return cls.from_string(source)
        except ValueError:
            return None

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
        return hash((self.subversions, self.adds))

    def __str__(self) -> str:
        result = ".".join(map(str, self.subversions))
        if self.adds:
            adds_substring = " ".join(self.adds)
            result = f"{result} {adds_substring}"
        return result

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, GameVersion):
            return False
        return self.subversions == __value.subversions

    def __lt__(self, __value: object) -> bool:
        if not isinstance(__value, GameVersion):
            raise NotImplementedError()
        for this, other in zip(self.subversions, __value.subversions):
            if this < other:
                return True
        return len(self.subversions) < len(__value.subversions)
