import json
import traceback
from typing import Any, BinaryIO, TextIO, Union

import yaml

from server.core.exception import EXCEPTION_LIB


def load_yaml(yaml_f: str) -> dict:
    """Load yaml file from a given name

    :param yaml_f: yaml file name
    :type yaml_f: str
    :raises EXCEPTION_LIB.IO__DEFAULT_GLOBAL_CFG_FILE_CANNOT_OPEN.value: [description]
    :raises EXCEPTION_LIB.IO__DEFAULT_GLOBAL_CFG_FILE_CANNOT_OPEN.value: [description]
    :return: parsed dictionary
    :rtype: dict
    """
    try:
        with open(yaml_f) as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    except yaml.MarkedYAMLError as exc:
        msg = "An error occurred during YAML parsing."
        if hasattr(exc, "problem_mark"):
            msg += " Error position: ({0}:{1})".format(
                exc.problem_mark.line + 1, exc.problem_mark.column + 1  # type: ignore
            )
        raise EXCEPTION_LIB.IO__YMAL_FILE_CANNOT_PARSE.value(msg)

    except (OSError, IOError):
        traceback.print_exc()
        raise EXCEPTION_LIB.IO__YAML_FILE_NOT_EXIST.value(
            f"Cannot open file {yaml_f}"
        )


def safe_load_yaml_io(stream: Union[bytes, str, BinaryIO, TextIO]) -> Any:
    """Like yaml.safe_load, but use the C libyaml for speed where we can"""
    # delay import until use.
    from yaml import load as orig

    try:
        from yaml import CSafeLoader as SafeLoader
    except ImportError:
        from yaml import SafeLoader  # type: ignore[no-redef]

    return orig(stream, SafeLoader)


def load_json(json_f: str) -> dict:
    """Load json file from a given name

    :param json_f: yaml file name
    :type json_f: str
    :raises EXCEPTION_LIB.IO__DEFAULT_GLOBAL_CFG_FILE_CANNOT_OPEN.value: [description]
    :raises EXCEPTION_LIB.IO__DEFAULT_GLOBAL_CFG_FILE_CANNOT_OPEN.value: [description]
    :return: parsed dictionary
    :rtype: dict
    """
    try:
        with open(json_f) as f:
            return json.load(f)

    except json.decoder.JSONDecodeError:
        raise EXCEPTION_LIB.IO__JSON_FILE_CANNOT_PARSE.value(
            f"File {json_f} could not be converted to JSON"
        )
