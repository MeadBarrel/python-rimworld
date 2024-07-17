""" Tests for rimworld.gameversion """

import pytest

from rimworld.gameversion import GameVersion


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("1.5", GameVersion((1, 5))),
        ("v1.5", GameVersion((1, 5))),
        ("0.9.41", GameVersion((0, 9, 41))),
        ("1.5.4104 rev435", GameVersion((1, 5, 4104), ("rev435",))),
    ],
)
def test_from_string(source: str, expected: GameVersion):
    """Test string to GameVersion conversion"""
    assert GameVersion.new(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("1.5", GameVersion((1, 5))),
        ("v0.9.41", GameVersion((0, 9, 41))),
        ("1.5.4104 rev435", GameVersion((1, 5, 4104), ("rev435",))),
        ("1.5.4104 rev435!", None),
        ("this is not a version", None),
    ],
)
def test_match(source: str, expected: GameVersion):
    """Test GameVersion.match"""
    assert GameVersion.match(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    (
        ("1.5", "1.5"),
        ("v1.3", "1.3"),
        ("1.9 rev435", "1.9 rev435"),
        ("1.9 rev435 beta", "1.9 rev435 beta"),
        ("v1.9 rev435 beta", "1.9 rev435 beta"),
    ),
)
def test_to_string(source: str, expected: str):
    """Test GameVersion to string conversion"""
    assert str(GameVersion.from_string(source)) == expected


@pytest.mark.parametrize(
    ("this", "other"),
    [
        ("1.5", "3.9"),
        ("1.5 rev435", "3.9"),
    ],
)
def test_le(this: str, other: str):
    """Test gameversion comparison"""
    assert GameVersion.new(this) < GameVersion.new(other)


@pytest.mark.parametrize(
    ("this", "other"),
    [
        ("3.9", "1.5"),
        ("3.9", "1.5 rev435"),
    ],
)
def test_ge(this: str, other: str):
    """Test gameversion comparison"""
    assert GameVersion.new(this) > GameVersion.new(other)


@pytest.mark.parametrize(
    ("this", "other"),
    [
        ("3.9", "3.9"),
        ("3.9", "3.9 rev435"),
        ("3.9 rev435 beta", "3.9 rev435"),
        ("3.9 rev435 beta", "3.9"),
    ],
)
def test_eq(this: str, other: str):
    """Test gameversion comparison"""
    assert GameVersion.new(this) == GameVersion.new(other)
