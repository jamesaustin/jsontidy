#!/usr/bin/env python3
from json import load as json_load
from argparse import ArgumentParser
from re import compile as re_compile

# Taken from https://github.com/python/cpython/blob/master/Lib/json/encoder.py
ESCAPE_RE = re_compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
ESCAPE_DICT = {"\\": "\\\\", '"': '\\"', "\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t"}
for i in range(0x20):
    ESCAPE_DICT.setdefault(chr(i), "\\u{0:04x}".format(i))


def encode_basestring(s):
    def replace(match):
        return ESCAPE_DICT[match.group(0)]

    return '"' + ESCAPE_RE.sub(replace, s) + '"'


# Configure the output rules.
EMPTY = True
LIST_SINGLES = True
LIST_OF_NUMBERS = True
LIST_OF_BOOLS = True
LIST_OF_LISTS_OF = False
DICT_OF_NUMBERS = True
DICT_OF_BOOLS = True
DICT_MAX_ELEMENTS = 5  # allows RGBA or XYZW or RGBLr style dicts
FLOAT_FORMAT = "{:g}"  # limits precision to ~6dp


def dump(data, stream, indent):
    def tab(d):
        return " " * (indent * d)

    def config_list(o, d):
        if (
            (LIST_OF_NUMBERS and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in o))
            or (LIST_OF_BOOLS and all(isinstance(x, bool) for x in o))
            or (LIST_OF_LISTS_OF and all(isinstance(x, list) and can_compact_list(x) for x in o))
            or (LIST_SINGLES and len(o) == 1)
            or (EMPTY and len(o) == 0)
        ):
            return ("[", ", ", "]", False, d)
        else:
            return ("[\n", ",\n", "\n" + tab(d) + "]", True, d + 1)

    def config_dict(o, d):
        if (DICT_MAX_ELEMENTS >= len(o)) and (
            (DICT_OF_NUMBERS and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in o))
            or (DICT_OF_BOOLS and all(isinstance(x, bool) for x in o))
            or (EMPTY and len(o) == 0)
        ):
            return ("{", '"{}": ', ", ", "}")
        else:
            return ("{\n", tab(d + 1) + '"{}": ', ",\n", "\n" + tab(d) + "}")

    def encode(o, requires_indent=True, depth=0):
        if requires_indent:
            yield tab(depth)

        if isinstance(o, (list, tuple)):
            (start, comma, end, next_indent, next_depth) = config_list(o, depth)
            yield start
            for n, v in enumerate(o):
                yield from encode(v, next_indent, next_depth)
                if n < len(o) - 1:
                    yield comma
            yield end
        elif isinstance(o, dict):
            (start, key, comma, end) = config_dict(o.values(), depth)
            yield start
            for n, (k, v) in enumerate(o.items()):
                yield key.format(k)
                yield from encode(v, False, depth + 1)
                if n < len(o) - 1:
                    yield comma
            yield end
        elif o is True:
            yield "true"
        elif o is False:
            yield "false"
        elif o is None:
            yield "null"
        elif isinstance(o, int):
            yield str(o)
        elif isinstance(o, float):
            yield FLOAT_FORMAT.format(o)
        elif isinstance(o, str):
            yield encode_basestring(o)
        else:
            print(f"ERROR: {o}")

    stream.writelines(encode(data))
    stream.write("\n")


parser = ArgumentParser(description="Tidy JSON files in-place.")
parser.add_argument("files", metavar="FILE", type=str, nargs="+", help="file to tidy")
parser.add_argument("-i", "--indent", type=int, default=4, help="number of spaces per depth")
args = parser.parse_args()

for filename in args.files:
    with open(filename) as f:
        data = json_load(f)
    with open(filename, "w") as f:
        dump(data, f, args.indent)
