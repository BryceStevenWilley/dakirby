"""Contains the scanner / parser for HotDocs scripts"""

from enum import Enum, auto


# TODO(brycew):
# * newlines are important, ignore what HotDocs says (it's ambigious otherwise)
#    * (alt: they aren't important, and they replace var names with something else)
# * they show up at the end of IF / ELSE IF / WHILE instructions
# * you just need an infinite lookahead until you reach new line or some other keyword (all caps?) or syntax

# https://help.hotdocs.com/preview/help/HotDocs_Scripting_Language_Overview.htm
# says suprisingly little. Please never explain a programming language to me in
# New lines don't matter; can be on multiple lines or one.
# instructinos, functions, and ops must be in ALL CAPS
# 

# Interesting idea: attempt to parse like INFORM? https://ganelson.github.io/inform/words-module/3-lxr.html#SP27
# Might be too difficult. Can also stick to parsing a large amount of look ahead.

# Just a lexer is ambigious;
# since new lines don't matter, we can have something like:
# ```
# IF Child lives with plaintiff CO
#     Plaintiff address confidential or res CO
# ELSE IF Child lives with defendant CO`
# ```
# Multiple things wrong here:
# * a variable followed directly by a variable.
# * WITH and OR in the variable names (I guess that's because keywords have to be all caps)
# By normal rules, we can't distinguish them. So we have to rely on fields ending in CO, TF, etc.






# terms of english again.
# Statements are either:
# * instruction + other key words followed by components / values

# From examples in the file:
# SET <var name> TO <value>
# IF <var name> <value> END
# DEBUG (? idk what it does)
# IF <var name> OR (<var name > AND <varname> = 0)
# ENDIF used sometimes too?
# (<var name> AND !<var name>) OR ...
# INCREMENT <var name>
# ELSE IF
# ELSE
# ASK
# MONTHS FROM( <var name>, TODAY)
# FALSE
# TRUE
# REPEAT <var name>
# END REPEAT
# END IF
# IF <var name> CONTAINS
# HIDE
# SHOW

# In a template, can only use
# IF
# REPEAT
# ASSEMBLE

# How to parse IFs: https://help.hotdocs.com/preview/help/Conditional_Region_Overview.htm


# Full list online: https://help.hotdocs.com/preview/help/Full_List_of_Instructions,_Functions_and_Operators.htm
dialog_instructions = [
  "GRAY", # i.e. enable / disable
  "GRAY ALL",
  "HIDE",
  "HIDE ALL",
  "LIMIT",
  "REQUIRE",
  "REQUIRE ALL",
  "SHOW",
  "SHOW ALL",
  "UNGRAY",
  "UNGRAY ALL"
]

nondialog_instructions = [
  "ADD",
  "ASK",
  "ASSEMBLE",
  "CLEAR", # removes all current options from specified multiple choice
  "INSERT", # insert contents of specified file at that location during assembly
  "REPEAT",
]

general_instructions = [
  "DECREMENT",
  "DEFAULT",
  "ERASE",
  "IF",
  "ELSE IF",
  "ELSE",
  "END IF",
  "INCREMENT",
  "QUIT",
  "SET",
  "WHILE",
  "END WHILE",
]

# TODO(brycew): also https://help.hotdocs.com/preview/help/HotDocs_Scripting_Language_Keywords.htm
class TokenType(Enum):
  EOF = auto()
  LEFT_PAREN = auto()
  RIGHT_PAREN = auto()
  LEFT_SQUARE = auto()
  RIGHT_SQUARE = auto()
  DOT = auto()
  COMMA = auto()
  MINUS = auto()
  PLUS = auto()
  SLASH = auto()
  STAR = auto()
  BANG = auto()
  BANG_EQUAL = auto()
  EQUAL = auto()
  GREATER = auto()
  GREATER_EQUAL = auto()
  LESS = auto()
  LESS_EQUAL = auto()
  IDENTIFIER = auto()
  STRING = auto()

  # TODO(bryce): date literals
  
  # TODO(brycew): all keywords
  GRAY = auto()
  HIDE = auto()
  REQUIRE = auto()
  LIMIT = auto()
  SHOW = auto()
  UNGRAY = auto()
  ALL = auto()
  ADD = auto()
  ASK = auto()
  ASSEMBLE = auto()
  CLEAR = auto()
  DECREMENT = auto()
  DEFAULT = auto()
  ERASE = auto()
  IF = auto()
  ELSE = auto()
  END = auto()
  INCREMENT = auto()
  INSERT = auto()
  QUIT = auto()
  REPEAT = auto()
  ASCEND = auto()
  DESCEND = auto()
  FILTER = auto()
  FORMAT = auto()
  SET = auto()
  WHILE = auto()

  # Functions?
  MONTHS = auto()
  OF = auto()
  FROM = auto()

  # ops?
  AND = auto()
  OR = auto()
  NOT = auto()
  STARTS = auto()
  WITH = auto()
  CONTAINS = auto()
  ENDS = auto()
  

class Token:
  def __init__(self, token_type, lexeme, literal):
    self.token_type = token_type
    self.lexeme = lexeme
    self.literal = literal

class Scanner:
  def __init__(self, script):
    self.script = script
    self.start = 0
    self.current = 0

  def scan_tokens(self):
    """Return a list of Tokens"""
    tokens = []
    while (self.current < len(self.script)):
      self.start = self.current
      tokens.append(self.scanToken())
    tokens.append(Token(TokenType.EOF, "", None))

