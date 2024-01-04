#!/usr/bin/env python3
"""Common functions and regexes used in different parsers / outputs"""

import re

replace_square_brackets = re.compile(r"\\\[ *([^\\]+)\\\]")
end_spaces = re.compile(r" +$")
spaces = re.compile(r"[ \n]+")
invalid_var_characters = re.compile(r"[^A-Za-z0-9_]+")
digit_start = re.compile(r"^[0-9]+")
newlines = re.compile(r"\n")
remove_u = re.compile(r"^u")

# Expanded from ALWeaver
def varname(var_name: str) -> str:
    if var_name:
        var_name = var_name.strip()
        var_name = spaces.sub(r"_", var_name)
        var_name = invalid_var_characters.sub(r"", var_name)
        var_name = digit_start.sub(r"", var_name)
        if var_name.endswith("_TE"):
          var_name = var_name[:-3]
        var_name = var_name.lower()
        return var_name
    return var_name

class PageNode:

  def to_yaml():
    pass
