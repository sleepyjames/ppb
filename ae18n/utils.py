import re

"""

Some utilities for string conversion and custom escaping.

"""

# Control characters to escape mapped to their escaped values
ESCAPES = {
    '\n': r'\\n',
    '\t': r'\\t',
}

ESCAPE_ITEMS = ESCAPES.items()


def escape(string):
    """Strings to be translated sometimes contain control characters (e.g. '\n')
    that translators need to translate around, in order to preserve whitespace.
    For that reason, we don't want them to be interpreted literally and must
    escape them so that they are preserved in the raw string.

    E.g.:

        msgid ""
        "\n"
        "Translate this"

    The "\n" should be preserved in the string to be translated and not turned
    into an actual newline character.
    """
    for e, v in ESCAPE_ITEMS:
        s = re.sub(e, v, string)
    return s


def unescape(string):
    """Unescape escaped control characters."""
    for e, v in ESCAPE_ITEMS:
        s = re.sub(v, e, string)
    return s


def bool2str(true_or_false, empty_for_false=False):
    """Casts a Python value to True or False and then stringifies that. If
    `empty_for_false` is True, if `true_or_false` evaluates to False, an empty
    string will be returned instead of 'n'.
    """
    # TODO: don't assume 'y/n'
    bool_strs = {
        True: 'y',
        False: 'n',
    }
    if empty_for_false:
        del bool_strs[False]
    return bool_strs.get(bool(true_or_false), '')


def str2bool(y_or_n):
    """Reverse of bool2str"""
    # TODO: don't assume 'y/n'
    str_bools = {
        'y': True,
        'n': False,
    }
    return str_bools.get(y_or_n.lower(), False)


