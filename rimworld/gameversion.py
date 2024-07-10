from dataclasses import dataclass
from functools import total_ordering
from typing import Self


@dataclass(frozen=True)
@total_ordering
class GameVersion:
    subversions: tuple[int]

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls(tuple(int(v) for v in value.split('.')))

    def __str__(self) -> str:
        return '.'.join(map(str, self.subversions))

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

