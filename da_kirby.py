#!/usr/bin/env python3

import sys
import re
from lxml import etree
from pyaml import dump_all

replace_square_brackets = re.compile(r"\\\[ *([^\\]+)\\\]")
end_spaces = re.compile(r" +$")
spaces = re.compile(r"[ \n]+")
invalid_var_characters = re.compile(r"[^A-Za-z0-9_]+")
digit_start = re.compile(r"^[0-9]+")
newlines = re.compile(r"\n")
remove_u = re.compile(r"^u")

def parse_inline(inline_elem):
  text = inline_elem.text or ""
  for child in inline_elem:
    if child.tag.lower() in ["strong", "b"]:
      text += f"**{child.text}**"
    elif child.tag.lower() in ["em", "i"]:
      text += f"*{child.text}*"
    elif child.tag.lower() in ["a"]:
      text += f"[{parse_inline(child)}]({child.get('HREF') or child.get('href')})"
    elif child.tag.lower() in ["u"]:
      text += parse_inline(child)
    else: # intentional: skip FONT
      text += (child.text or "")
    text += (child.tail or "")
  return text.replace("\n", " ").replace("           ", " ")

def parse_paragraph(para_elem):
  return parse_inline(para_elem) + "\n\n"

# TODO(brycew): keep track of `%%`, convert to var name and mako ${ }.
def parse_text(text_elem):
  text = text_elem.text
  for html_elem in text_elem:
    if html_elem.tag.lower() == "p":
      text += parse_paragraph(html_elem)
    elif html_elem.tag.lower() == "ul":
      for list_item in html_elem:
        text += f"* {parse_inline(list_item)}\n"
      text += "\n"
    elif html_elem.tag.lower() == "ol":
      for idx, list_item in enumerate(html_elem):
        text += f"{idx}. {parse_inline(list_item)}\n"
      text += "\n"
    else:
      text += html_elem.text + "\n"
  return text + text_elem.tail


class PageNode:

  def __init__(self, page_elem):
    self.parent = None # need to update this later
    self.text = None
    self.learn = None
    self.help = None
    self.helpimage = None
    self.buttons = []
    self.fields = []
    self.children_names = set()
    self.codeafter = None
    self.codebefore = None

    self.name = page_elem.get("NAME")
    self.page_type = page_elem.get("TYPE")
    self.step = page_elem.get("STEP")
    # ? Have no idea what these are used for
    self.map_x = page_elem.get("MAPX")
    self.map_y = page_elem.get("MAPY")

    for page_child in page_elem:
      if page_child.tag.lower() == "text":
        self.text = parse_text(page_child).strip()
      elif page_child.tag.lower() == "help":
        self.help = parse_text(page_child)
      elif page_child.tag.lower() == "learn":
        self.learn = parse_text(page_child)
      elif page_child.tag.lower() == "helpimage":
        self.helpimage = page_child.text
      elif page_child.tag.lower() == "buttons":
        self.buttons = self.parse_buttons(page_child)
      elif page_child.tag.lower() == "fields":
        self.fields = self.parse_fields(page_child)
      elif page_child.tag.lower() == "codebefore":
        self.codebefore = page_child.text
      elif page_child.tag.lower() == "codeafter":
        self.codeafter = page_child.text

  def __str__(self):
    return f"parent: {self.parent}, text: {self.text}, learn: {self.learn}, help: {self.help}, buttons: {self.buttons}, fields: {self.fields}"


  def parse_buttons(self, buttons_elem):
    buttons = []
    for button_elem in buttons_elem:
      button = {}
      button["next"] = button_elem.get("NEXT") or button_elem.get("next")
      if button["next"] and button["next"].lower() != "fail":
        self.children_names.add(button["next"])
      elif button["next"] == "fail":
        button["exit url"] = button_elem.get("URL") or button_elem.get("url")
      for button_attr in button_elem:
        if button_attr.tag.lower() == "label":
          button["label"] = button_attr.text
        elif button_attr.tag.lower() == "name":
          button["var"] = button_attr.text
        elif button_attr.tag.lower() == "value":
          button["value"] = button_attr.text
        else:
          print(f"Unknown button attr: {field_attr.tag}")
    return buttons

  def parse_fields(self, fields_elem):
    fields = []
    for field_elem in fields_elem:
      field = {}
      field["type"] = field_elem.get("TYPE")
      # ? idk bout this one
      field["order"] = field_elem.get("ORDER")
      field["required"] = field_elem.get("required")
      field["min"] = field_elem.get("min")
      field["max"] = field_elem.get("max")
      # idk how to use this one, but hand onto it
      field["calculator"] = field_elem.get("calculator")
      for field_attr in field_elem:
        if field_attr.tag.lower() == "name":
          field["var"] = field_attr.text
        elif field_attr.tag.lower() == "label":
          field["label"] = field_attr.text
        elif field_attr.tag.lower() == "value":
          field["value"] = field_attr.text
        elif field_attr.tag.lower() == "invalidprompt":
          field["invalid prompt"] = field_attr.text
        elif field_attr.tag.lower() == "listdata":
          field["listdata"] = field_attr
        # TODO(brycew): read this in, everything goes in list data
        elif field_attr.tag.lower() == "listsrc":
          field["listsrc"] = field_attr
        else:
          print(f"Unknown field attr: {field_attr.tag}")
    
  def to_yaml(self):
    # TODO(brycew): step, help, learn, helpimage, buttons, fields, codebefore, codeafter
    block = {
      "id": varname(self.name),
      "question": (self.text or "").split("\n")[0],
      "subquestion": self.text,
      "continue button field": varname(self.name),
    }
    return block



def parse_authors(authors_elem, da_interview):
  authors = []
  for author_elem in authors_elem:
    author = {}
    for author_attr in author_elem:
      author[author_attr.tag.lower()] = author_attr.text
    authors.append(author)
  da_interview.metadata["authors"] = authors
  return da_interview

def parse_description(description_elem, da_interview):
  da_interview.metadata["description"] = description_elem.text
  return da_interview

def parse_notes(elem, da_interview):
  da_interview.changelog = elem.text
  return da_interview

def parse_emailcontact(elem, da_interview):
  da_interview.setup_info["author_email"] = elem.text
  return da_interview

def parse_title(elem, da_interview):
  da_interview.metadata["title"] = elem.text
  return da_interview

def parse_firstpage(elem, da_interview):
  da_interview.first_page_name = elem.text
  return da_interview

parse_dict = {
  "authors": parse_authors,
  "description": parse_description,
  "notes": parse_notes,
  "emailcontact": parse_emailcontact,
  "title": parse_title,
  "firstpage": parse_firstpage
}


# From ALWeaver
def varname(var_name: str) -> str:
    if var_name:
        var_name = var_name.strip()
        var_name = spaces.sub(r"_", var_name)
        var_name = invalid_var_characters.sub(r"", var_name)
        var_name = digit_start.sub(r"", var_name)
        return var_name
    return var_name


class DAInterview:

  def __init__(self):
    self.metadata = {}
    # Things like maintainer email, version, etc.
    self.setup_info = {}
    self.page_map: dict[str, PageNode] = {}
    self.first_page_name = None
    self.changelog = ""
    self.steps: dict[int, str] = {}
    self.variable_map: dict[str, str] = {} # map from A2J varname to valid DA varname

  def add_page(self, page_elem):
    page = PageNode(page_elem)
    if not self.first_page_name:
      self.first_page_name = page.name
    self.page_map[page.name] = page

  def to_yaml(self):
    metadata = { 
      "metadata": self.metadata
    }
    sections = {
      "sections": [{val: varname(val)} for val in self.steps.values()]
    }
    all_pages = [page.to_yaml() for page in self.page_map.values()]
    return dump_all([metadata, sections] + all_pages, string_val_style="|", sort_keys=False)

def main():
  da_interview = DAInterview()
  with open(sys.argv[1], "r") as f:
    doc = etree.parse(f)
    for elem in doc.getroot():
      if elem.tag.lower() == "info":
        for info_child in elem:
          if info_child.tag.lower() in parse_dict:
            parse_dict[info_child.tag.lower()](info_child, da_interview)
      elif elem.tag.lower() == "steps":
        for step_child in elem:
          da_interview.steps[int(step_child.get("NUMBER"))] = step_child[0].text
      elif elem.tag.lower() == "pages":
        for page_child in elem:
          da_interview.add_page(page_child)
  print(da_interview.to_yaml())


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
