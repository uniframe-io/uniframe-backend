import pandas as pd
import pytest
from pandas.testing import assert_series_equal

from server.nm_algo.preprocessing import (
    abbreviations_to_words,
    accents_unicode_normalize_series,
    insert_space_around_punctuation_series,
    legal_abbreviations_to_words,
    lower_series,
    map_shorthands,
    remove_extra_space_series,
    strip_punctuation_series,
    strip_series,
)


@pytest.fixture
def test_series() -> pd.Series:
    return pd.Series(["Amsterdam", "Utrecht"])


@pytest.mark.parametrize(
    "name, expected",
    [
        (
            pd.Series(["Amsterdam", "Utrecht"]),
            pd.Series(["amsterdam", "utrecht"]),
        )
    ],
)
def test_lower_series(name: pd.Series, expected: pd.Series) -> None:
    assert_series_equal(lower_series(name), expected, check_names=False)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("b. v.", "bv"),
        ("b.v.", "bv"),
        ("b v", "bv"),
        ("b v ", "bv"),
        ("n.v.", "nv"),
        ("v.o.f.", "vof"),
        ("b.v.b.a.", "bvba"),
    ],
)
def test_legal_abbreviations_to_words(name: str, expected: str) -> None:
    assert legal_abbreviations_to_words(name) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Z. S.", "ZS"),
        ("Z.S.", "ZS"),
        ("Z S", "ZS"),
    ],
)
def test_abbreviations_to_words(name: str, expected: str) -> None:
    assert abbreviations_to_words(name) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        # (pd.Series(['ä']), pd.Series(['A\xa4'])),
        (pd.Series(["ä"]), pd.Series(["a"])),
    ],
)
def test_handle_accents_unicode_to_ascii(
    name: pd.Series, expected: pd.Series
) -> None:
    assert_series_equal(
        accents_unicode_normalize_series(name), expected, check_names=False
    )


@pytest.mark.parametrize(
    "name, expected",
    [
        (pd.Series(["    abc   "]), pd.Series(["abc"])),
    ],
)
def test_strip_series(name: pd.Series, expected: pd.Series) -> None:
    assert_series_equal(strip_series(name), expected, check_names=False)


@pytest.mark.parametrize(
    "name, expected",
    [
        (pd.Series(["abc    abc"]), pd.Series(["abc abc"])),
    ],
)
def test_remove_extra_space_series(
    name: pd.Series, expected: pd.Series
) -> None:
    assert_series_equal(
        remove_extra_space_series(name), expected, check_names=False
    )


@pytest.mark.parametrize(
    "name, expected",
    [
        ("vereniging van eigenaren zaandam", "vve zaandam"),
        ("stichting", "stg"),
        ("straat", "str"),
    ],
)
def test_map_shorthands(name: str, expected: str) -> None:
    assert map_shorthands(name) == expected


@pytest.mark.parametrize(
    "name, expected",
    [
        (pd.Series(["abc,abc"]), pd.Series(["abc abc"])),
        (pd.Series(["abc!abc"]), pd.Series(["abc abc"])),
        (pd.Series(["$abc!abc#"]), pd.Series([" abc abc "])),
    ],
)
def test_strip_punctuation_series(name: pd.Series, expected: pd.Series) -> None:
    assert_series_equal(
        strip_punctuation_series(name), expected, check_names=False
    )


@pytest.mark.parametrize(
    "name, expected",
    [
        (pd.Series(["abc,abc"]), pd.Series(["abc , abc"])),
        (pd.Series(["abc!abc"]), pd.Series(["abc ! abc"])),
        (pd.Series(["$abc!abc#"]), pd.Series([" $ abc ! abc # "])),
    ],
)
def test_insert_space_around_punctuation_series(
    name: pd.Series, expected: pd.Series
) -> None:
    assert_series_equal(
        insert_space_around_punctuation_series(name),
        expected,
        check_names=False,
    )
