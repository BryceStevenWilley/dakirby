#! /usr/bin/env python3

import sys
import os

from .core.a2jauthor import A2JInterview
from .core.hotdocs import HotDocsInterview
from .core.docassemble import to_yaml

def main():
  input_path = sys.argv[1]
  if input_path.endswith("Guide.xml"):
    input_interview = A2JInterview(input_path)
  elif os.path.isdir(input_path):
    # Assuming Hotdocs for now
    input_interview = HotDocsInterview(input_path)
  else:
    print("Don't recognize the input file type: {input_filename}")
    exit(2)

  print(to_yaml(input_interview.to_yaml_objs()))

# TODO(brycew): next steps:
# * build the page graph and make the mandatory code block
# * add fields to the question blocks
# * get more control of YAML output (force things to be "|", or flow, depending on the attr)
# * Better Question headers (at least don't repeat the exact thing from the subquestion)
# * helpimages
# * learn more
# * codebefore and after into mandatory block
if __name__ == "__main__":
  main()