"""
This module contains NM algorithm preprocessing model
"""

import re
import string
import unicodedata
from typing import Any

from pandas.core.frame import DataFrame
from pandas.core.series import Series
from sklearn.base import BaseEstimator, TransformerMixin

from server.apps.nm_task import schemas


def lower_series(name_col: Series) -> Series:
    """string series to lower case"""
    return name_col.str.lower()


def legal_abbreviations_to_words(name: str) -> str:
    """
    Maps all the abbreviations to the same format (B. V.= B.V. = B V = BV)
    """
    # a legal form list contains most important words
    legal_form_abbr_list = [
        "bv",
        "nv",
        "vof",  # netherlands
        "bvba",
        "vzw",
        "asbl",
        "vog",
        "snc",
        "scs",
        "sca",
        "sa",
        "sprl",
        "cvba",
        "scrl",  # Belgium
        "gmbh",
        "kgaa",
        "ag",
        "ohg",  # Germeny
        "ska",
        "spzoo",  # Poland
    ]
    abbr_finder_punc = re.compile(
        r"(?:^|\s)((?:\w(?:\.\s|$|\s|\.))+|(?:\w+(?:\.\s|$|\.))+)", re.UNICODE
    )
    all_abbreviations = abbr_finder_punc.findall(name)
    for abbreviation in all_abbreviations:
        re_abbr_separator = re.compile(r"(\s|\.)+", re.UNICODE)
        new_form = re_abbr_separator.sub("", abbreviation)
        if new_form in legal_form_abbr_list:
            name = name.replace(abbreviation, new_form)
    return name


def legal_abbreviations_to_words_series(name_col: Series) -> Series:
    return name_col.apply(legal_abbreviations_to_words)


# ABBR_FINDER_PUNC: one character with a separator followed by one or more one-char words with the same separator
# the character before the abbreviation should be ^ or \s so that we dont split words accidentially
ABBR_FINDER_PUNC = re.compile(
    r"(?:^|\s)((?:\w(\.\s|\s|\.))(?:\w\2)+)", re.UNICODE
)
# RE_ABBR_SEPARATOR: abbreviation separators
RE_ABBR_SEPARATOR = re.compile(r"(\s|\.)", re.UNICODE)


def abbreviations_to_words(name: str) -> str:
    """
    Maps all the abbreviations to the same format (Z. S.= Z.S. = Z S = ZS)
    """
    name += " "
    all_abbreviations = [x[0] for x in ABBR_FINDER_PUNC.findall(name + " ")]
    for abbreviation in all_abbreviations:
        new_form = RE_ABBR_SEPARATOR.sub("", abbreviation) + " "
        name = name.replace(abbreviation, new_form)
    return name.strip()


def abbreviations_to_words_series(name_col: Series) -> Series:
    return name_col.apply(abbreviations_to_words)


def extract_initial_letter(name: str) -> str:
    # TODO: better nr word algorithm?
    word_l = name.split()
    nr_words = len(word_l)

    if nr_words > 1:
        init_letter_str = "".join([word[0] for word in word_l])
        return name + " " + (" ".join([init_letter_str] * nr_words))

    return name


def extract_initial_letter_series(name_col: Series) -> Series:
    return name_col.apply(extract_initial_letter)


def insert_space_around_punctuation_series(name_col: Series) -> Series:
    """
    Insert space around all punctuation characters, e.g., H&M => H & M; H.M. => H . M .
    """
    return name_col.str.replace(
        rf"([{string.punctuation}])", r" \1 ", regex=True
    )


def strip_punctuation(name: str) -> str:
    """
    Replace all punctuation characters (e.g. '.', '-', '_', ''', ';') with spaces
    """
    translator = str.maketrans(
        string.punctuation, " " * len(string.punctuation)
    )

    return name.translate(translator)


def strip_punctuation_series(name_col: Series) -> Series:
    return name_col.apply(strip_punctuation)


def handle_accents_unicode_to_ascii(unicode_str: str) -> str:
    return (
        unicodedata.normalize("NFKD", unicode_str)
        .encode("ascii", "ignore")
        .decode("utf-8")
    )


def accents_unicode_normalize_series(name_col: Series) -> Series:
    """
    Replace accented characters by their normalized representation, e.g. replace 'ä' with 'A\xa4'
    """
    return name_col.apply(handle_accents_unicode_to_ascii)


def strip_series(name_col: Series) -> Series:
    return name_col.str.strip()


def remove_extra_space_series(name_col: Series) -> Series:
    """
    remove extra space (XYZ    ABC = XYZ ABC)
    """
    return name_col.str.replace(r"""\s+""", " ", regex=True)


SHORTHANDS = [
    (
        re.compile(
            r"ver(?:eniging)? v(?:an)? (\w*)(?:eigenaren|eigenaars)", re.UNICODE
        ),
        r"vve\1",
    ),
    (re.compile(r"stichting", re.UNICODE), r"stg"),
    (re.compile(r"straat", re.UNICODE), r"str"),
]


def map_shorthands(name: str) -> str:
    """
    Map all the shorthands to the same format (stichting => stg)
    """
    for regex, shorthand in SHORTHANDS:
        name = regex.sub(shorthand, name)
    return name


def map_shorthands_series(name_col: Series) -> Series:
    return name_col.apply(map_shorthands)


class PreprocessingPipeline(BaseEstimator, TransformerMixin):
    """
    Load name matching dataset from nm task configuration
    """

    def __init__(self, algo_option: schemas.AlgorithmOption) -> None:
        """
        nm_cfg: name matching algorithm configuration
        """
        self.algo_option = algo_option

    def fit(self, X: Any, y: Any = None) -> None:
        """
        placeholder method, since it is just a transformer
        """
        return

    def transform(
        self, name_series: Any, is_gt: bool, y: Any = None
    ) -> DataFrame:
        """
        Load name matching dataset from nm task configuration
        """

        prep_option = self.algo_option.value.preprocessing_option

        prep_l = []

        # 1. Convert all upper-case characters to lower case and remove leading and trailing whitespace
        if not prep_option.case_sensitive:
            prep_l.append(lower_series)

        # 2. Map all the legal form abbreviations to the same format (B. V.= B.V. = B V = BV)
        if prep_option.company_legal_form_processing:
            prep_l.append(legal_abbreviations_to_words_series)

        # 3a. Map all the abbreviations to the same format (Z. S. = Z.S. = ZS)
        if prep_option.initial_abbr_processing:
            prep_l.append(abbreviations_to_words_series)

        # 3b. collect all initial letters (Zhe Sun ==> Zhe Sun zs zs)
        if is_gt:
            if prep_option.initial_abbr_processing:
                prep_l.append(extract_initial_letter_series)

        # 4. Merge & separated abbreviations by removing & and the spaces between them
        # "merge_&": lambda x: sf.regexp_replace(x, r"(\s|^)(\w)\s*&\s*(\w)(\s|$)", r'$1$2$3$4')
        # TODO
        # prep_l.append("???")

        # 5. punctuation
        if prep_option.punctuation_removal:
            # b) Replace all punctuation characters (e.g. '.', '-', '_', ''', ';') with spaces
            prep_l.append(strip_punctuation_series)
        else:
            # a) Insert space around all punctuation characters, e.g., H&M => H & M; H.M. => H . M .
            prep_l.append(insert_space_around_punctuation_series)

        # 6. Replace accented characters by their normalized representation, e.g. replace 'ä' with 'A\xa4'
        if prep_option.accented_char_normalize:
            prep_l.append(accents_unicode_normalize_series)

        # 7. Remove leading and trailing whitespace
        prep_l.append(strip_series)

        # 8. remove extra space (XYZ    ABC = XYZ ABC)
        prep_l.append(remove_extra_space_series)

        # 9. Map all the shorthands to the same format (stichting => stg)
        if prep_option.shorthands_format_processing:
            prep_l.append(map_shorthands_series)

        # run all preprocessing steps
        for prep_step in prep_l:
            name_series = prep_step(name_series)

        return name_series
