#!/usr/bin/env python3

from lxml import etree
from .common import varname, PageNode

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


class A2JPage(PageNode):

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
          print(f"Unknown button attr: {button_attr.tag}")
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


class A2JInterview:

  def __init__(self, input_filename):
    self.metadata = {}
    # Things like maintainer email, version, etc.
    self.setup_info = {}
    self.page_map: dict[str, A2JPage] = {}
    self.first_page_name = None
    self.changelog = ""
    self.sections: dict[int, str] = {}
    self.variable_map: dict[str, str] = {} # map from A2J varname to valid DA varname

    self.parse_dict = {
      "authors": self.parse_authors,
      "description": self.set_description,
      "notes": self.set_changelog,
      "emailcontact": self.set_author_email,
      "title": self.set_title,
      "firstpage": self.set_firstpage
    }

    with open(input_filename, "r") as f:
      doc = etree.parse(f)
      self.parse_from_xml(doc)

  def parse_from_xml(self, doc):
    for elem in doc.getroot():
      if elem.tag.lower() == "info":
        for info_child in elem:
          if info_child.tag.lower() in self.parse_dict:
            self.parse_dict[info_child.tag.lower()](info_child)
      elif elem.tag.lower() == "steps":
        for step_child in elem:
          self.sections[int(step_child.get("NUMBER"))] = step_child[0].text
      elif elem.tag.lower() == "pages":
        for page_child in elem:
          self.add_page(page_child)

  def parse_authors(self, authors_elem):
    authors = []
    for author_elem in authors_elem:
      author = {}
      for author_attr in author_elem:
        author[author_attr.tag.lower()] = author_attr.text
      authors.append(author)
    self.metadata["authors"] = authors

  def set_description(self, description_elem):
    self.metadata["description"] = description_elem.text

  def set_changelog(self, elem):
    self.changelog = elem.text

  def set_author_email(self, elem):
    self.setup_info["author_email"] = elem.text

  def set_title(self, elem):
    self.metadata["title"] = elem.text

  def set_firstpage(self, elem):
    self.first_page_name = elem.text

  def add_page(self, page_elem):
    page = A2JPage(page_elem)
    if not self.first_page_name:
      self.first_page_name = page.name
    self.page_map[page.name] = page

  def to_yaml_objs(self):
    metadata = { 
      "metadata": self.metadata
    }
    sections = {
      "sections": [{val: varname(val)} for val in self.sections.values()]
    }
    all_pages = [page.to_yaml() for page in self.page_map.values()]
    return [metadata, sections] + all_pages