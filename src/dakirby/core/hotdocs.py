#!/usr/bin/env python3

from lxml import etree
from lxml.etree import QName
from .common import varname, PageNode
import glob

import re

# w in text like that is a link, essentially <a href=""...>
web_chevron = re.compile(r'«.w "([^»]+)"»([^«]+)«.we»')

from typing import TypedDict

xml_namespace = "http://www.hotdocs.com/schemas/component_library/2009"

def xml_ns(arg):
  """Returns the full URL of an XML namespaced tag"""
  return QName(xml_namespace, arg).text

class DialogElement(TypedDict):
  name: str
  caption: str | None
  web_link: str | None

def parse_display_text(text):
  """Note: does not parse variables and scripts (since we can't fully replace them yet)."""
  if not text:
    return ""
  text = text.replace("«.b»", "**").replace("«.be»", "**")
  # Treat underlines the same as bold (underlines are harder to read)
  text = text.replace("«.u»", "**").replace("«.ue»", "**")
  text = text.replace("«.i»", "*").replace("«.ie»", "*")
  text = text.replace("«.lq»", '"').replace("«.rq»", '"')
  text = web_chevron.sub(r"[\2](\1)", text)
  # TODO: ask brett about «.lb, «.c», and «.z»
  text = text.replace("«.c»", '').replace("«.z»", '').replace("«.ze»", '').replace("«.lb»", '')
  return text

class Variable:
  name: str
  da_name: str
  prompt: str | None

  def __init__(self, name, prompt=None):
    self.name = name
    self.da_name = varname(name)
    self.prompt = parse_display_text(prompt)

  def get_datatype():
    return "text"
  
  def get_field(self):
    label = self.prompt or self.name
    label = label.strip()
    field = {
      "label": label,
      "field": self.da_name,
      "datatype": self.get_datatype()
    }
    if "\n" in label:
      field["label above field"] = True
    return field

class TextVariable(Variable):
  help: str | None
  area: bool

  # TODO: get maxChars
  def __init__(self, name, prompt=None, help=None, area=False):
    super().__init__(name, prompt)
    self.help = parse_display_text(help)
    self.area = area

  def get_datatype(self):
    return "text"

class NumberVariable(Variable):
  decimal_places: int | None
  currency_symbol: str | None
  def_format: str | None
  help: str | None

  def __init__(self, name, prompt=None, help=None, decimal_places=0, currency_symbol=None, def_format=None):
    super().__init__(name, prompt)
    self.help = parse_display_text(help)
    self.decimal_places = decimal_places
    self.currency_symbol = currency_symbol
    self.def_format = def_format

  def get_datatype(self):
    if self.currency_symbol:
      return "currency"
    elif self.decimal_places > 0:
      return "number"
    else:
      return "integer"

class TrueFalseVariable(Variable):
  help: str | None
  yes_no: str | None

  def __init__(self, name, prompt=None, help=None, yes_no=None):
    super().__init__(name, prompt)
    self.help = parse_display_text(help)
    self.yes_no = yes_no

  def get_datatype(self):
    # TODO: depend on self.yes_no?
    return "yesnoradio"

class MultipleChoiceVariable(Variable):
  style: str | None
  options: list | str # either full choices, or reference choices var elsewhere

  def __init__(self, mc_elem):
    """Multiple choice variable copmonent element"""
    self.name = mc_elem.get("name")
    self.style = None # dropDownList or buttonGrid
    self.prompt = None
    self.options = []
    for elem in mc_elem:
      if elem.tag == xml_ns("prompt"):
        self.prompt = elem.text
      elif elem.tag == xml_ns("options"):
        for opt in elem:
          val = opt.get("name")
          disp_label = next(iter(opt_elem.text for opt_elem in opt if opt_elem.tag == xml_ns("prompt")), None)
          if disp_label is None:
            self.options.append((val, val))
          else:
            self.options.append((disp_label, val))
      elif elem.tag == xml_ns("singleSelection"):
        self.style = elem.get("style")
    super().__init__(self.name, self.prompt)
    # TODO(brycew): defMergeProps, fieldWidth
    # TODO(brycew): conslidate different variables with the same options; should go in a different var somewhere

  def get_datatype(self):
    if self.style == "dropDownList":
      return "dropdown"
    else:
      return "radio"

  def get_field(self):
    field = super().get_field()
    if isinstance(self.options, list):
      field["choices"] = [{tup1: tup2} if tup1 != tup2 else tup1 for tup1, tup2 in self.options]
    else:
      field["code"] = self.options
    return field

class HotDocsInterview:

  def __init__(self, input_dirname):
    self.metadata = {}
    self.setup_info = {}
    self.page_map: dict[str, PageNode] = {}
    self.dialogs: dict[str, dict] = {}
    self.variable_map: dict[str, Variable] = {}

    # HotDoc specific things that might be useful
    self.preferences = {}
    self.code_blocks = {}
    self.dup_choices = {}
    self.dialog_elements: dict[str, DialogElement] = {}

    self.master_cmp = None
    for cmp_file in glob.iglob(input_dirname + "/*cmp"):
      # print(cmp_file)
      with open(cmp_file, "r") as f:
        doc = etree.parse(f)
        # print(doc.getroot().tag)
        if doc.getroot().tag == xml_ns("componentLibrary"):
          self.master_cmp = input_dirname + "/" + doc.getroot().get("pointedToFile", cmp_file)
          break

    if self.master_cmp:
      self.parse_master_cmp()

    self.main_order_script = self.preferences.get("CUSTOM_INTERVIEW")

    for var in self.variable_map.values():
      if var.prompt:
        var.prompt = self.sub_all_vars(var.prompt)
    for elem in self.dialog_elements.values():
      elem["caption"] = self.sub_all_vars(elem["caption"])
    for dialog in self.dialogs.values():
      if dialog["title"]:
        dialog["title"] = self.sub_all_vars(dialog["title"])

  def __str__(self):
    return f"{self.master_cmp=}, {self.metadata=}, {self.setup_info=}, {self.variable_map=}"
  
  def __repr__(self):
    return str(self)

  vars_re = re.compile("«([^».]+)»")

  def sub_all_vars(self, text):
    def sub_vars(match):
      hd_name = match.group(1)
      if hd_name.startswith("IF "):
        if hd_name[3:] in self.code_blocks:
          return "\n% if " + varname(hd_name[3:]) + "():\n"
        else:
          return "\n% if " + varname(hd_name[3:]) + ":\n"
      elif hd_name.startswith("ELSE IF "):
        if hd_name[8:] in self.code_blocks:
          return "\n% elif " + varname(hd_name[8:]) + "():\n"
        else:
          return "\n% elif " + varname(hd_name[8:]) + ":\n"
      elif hd_name == "END IF":
        return "\n% endif\n"
      elif hd_name in self.code_blocks:
        return "${ " + self.code_blocks[hd_name]["da_func_name"] + "() }"
      elif hd_name in self.variable_map:
        return "${ " + self.variable_map[hd_name].da_name + " }"
      # TODO(brycew): add to errors somewhere?
      return varname(hd_name)

    return self.vars_re.subn(sub_vars, text)[0]

  def parse_master_cmp(self):
    with open(self.master_cmp, "r") as f:
      doc = etree.parse(f)
      for elem in doc.getroot():
        if elem.tag.lower() == xml_ns("preferences"):
          self.parse_preferences(elem)
        elif elem.tag.lower() == xml_ns("components"):
          for component in elem:
            tag = component.tag
            if tag == xml_ns("text"):
              self.parse_text_var(component)
            elif tag == xml_ns("number"):
              self.parse_number_var(component)
            elif tag == xml_ns("trueFalse"):
              self.parse_tf_var(component)
            elif tag == xml_ns("multipleChoice"):
              self.parse_mc_var(component)
            elif tag == xml_ns("computation"):
              self.parse_computation(component)
            elif tag == xml_ns("dialogElement"):
              self.parse_dialog_element(component)
            elif tag == xml_ns("dialog"):
              self.parse_dialog(component)
            # All other top levels are text formats, number formats, etc. Idk what to do with those.

  def parse_preferences(self, prefs):
    for pref in prefs:
      name = pref.get("name")
      self.preferences[name] = pref.text

  def parse_text_var(self, text_elem):
    name = text_elem.get("name")
    # If no prompt, likely set by a script somewhere?
    prompt = None
    help = None
    area = False
    for elem in text_elem:
      if elem.tag == xml_ns("prompt"):
        prompt = elem.text
      elif elem.tag == xml_ns("resource"):
        help = elem[0].text
      elif elem.tag == xml_ns("multiLine"):
        area = True
      # Ignore fieldWidth, columnWidth. Idk what to do with defMergeProps?
    # Also warnIfUnanswered?
    self.variable_map[name] = TextVariable(name, prompt=prompt, help=help, area=area)

  def parse_number_var(self, number_elem):
    # If no prompt, likely set by a script somewhere?
    name = number_elem.get("name")
    decimal_places = number_elem.get("decimalPlaces", 0)
    currency_symbol = number_elem.get("currencySymbol")
    prompt = None
    help = None
    def_format = None
    for elem in number_elem:
      if elem.tag == xml_ns("prompt"):
        prompt = elem.text
      elif elem.tag == xml_ns("resource"):
        help = elem[0].text
      elif elem.tag == xml_ns("defFormat"):
        def_format = elem.text
    # TODO: Also warnIfUnanswered?
    self.variable_map[name] = NumberVariable(name, prompt, help, decimal_places, currency_symbol, def_format)

  def parse_tf_var(self, tf_elem):
    # If no prompt, likely set by a script somewhere?
    name = tf_elem.get("name")
    yes_no = tf_elem.get("yesNoOnSameLine")
    prompt = None
    help = None
    for elem in tf_elem:
      if elem.tag == xml_ns("prompt"):
        prompt = elem.text
      elif elem.tag == xml_ns("resource"):
        help = elem[0].text
    # Also warnIfUnanswered?
    self.variable_map[name] = TrueFalseVariable(name, prompt, help, yes_no)

  def parse_mc_var(self, mc_elem):
    """Multiple choice variable copmonent element"""
    if len(mc_elem) == 0: # If no prompt, likely set by a script somewhere?
      return
    mc_var = MultipleChoiceVariable(mc_elem)
    self.variable_map[mc_var.name] = mc_var

  def parse_computation(self, computation):
    name = computation.get("name")
    result_type = computation.get("resultType")
    script = ""
    for elem in computation:
      if elem.tag == xml_ns("script"):
        script = elem.text
    # TODO(brycew): parse Hotdocs script, for things with result, when it would return,
    # set the value to this.
    # Alternate: make everything functions? Looks like hot docs re-evals
    # everything when it can
    self.code_blocks[name] = {
      "name": name,
      "da_func_name": varname(name),
      "result_type": result_type,
      "script": script
    }


  def parse_dialog_element(self, dialog_element):
    name = dialog_element.get("name")
    caption = None
    for elem in dialog_element:
      if elem.tag == xml_ns("caption"):
        caption = elem.text
    self.dialog_elements[name] = {
      "name": name,
      "caption": parse_display_text(caption),
    }

  def parse_dialog(self, dialog):
    name = dialog.get("name")
    da_name = varname(name)
    link_vars = dialog.get("linkVariables")
    title = None
    contents = []
    for elem in dialog:
      if elem.tag == xml_ns("title"):
        title = elem.text
      elif elem.tag == xml_ns("contents"):
        for item in elem:
          contents.append({"name": item.get("name"), "on_previous_line": item.get("onPreviousLine")})
    self.dialogs[name] = {
      "name": name,
      "da_name": da_name,
      "title": title,
      "contents": contents,
    }

  def to_question_screen(self, name):
    if name in self.dialog_elements:
      return self.dialog_elements[name]
    if name in self.variable_map:
      return self.variable_map[name]
    # print(f"No thing with {name}?")
    return {}


  def merge_choices(self):
    if self.dup_choices:
      # Don't try to merge more than once
      return
    mcs = [var for _, var in self.variable_map.items() if isinstance(var, MultipleChoiceVariable)]
    # TODO(brycew): O(n^2) could be better
    self.dup_choices = {}
    for idx, mc in enumerate(mcs):
      # If these choices are already duplicates, don't need to check again
      if isinstance(mc.options, str):
        continue
      mc_sorted = list(sorted(mc.options))
      has_dup = False
      for mc2 in mcs[idx+1:]:
        if not isinstance(mc2.options, str) and mc_sorted == list(sorted(mc2.options)):
          has_dup = True
          dup_name = mc.da_name + "_choices"
          self.dup_choices[dup_name] = mc_sorted
          mc2.options = dup_name
      if has_dup:
        mc.options = dup_name


  def to_yaml_objs(self):
    self.merge_choices()
    metadata = {
      "metadata": self.metadata
    }
    dialogs = []
    for dialog_name, dialog in self.dialogs.items():
      dialog_items = [self.to_question_screen(dialog_item["name"]) for dialog_item in dialog["contents"]]
      subquestion = ""
      fields = []
      seen_variable = False
      for idx, dialog_item in enumerate(dialog_items):
        if isinstance(dialog_item, dict) and dialog_item and dialog_item["caption"].strip():
          capt = dialog_item["caption"].strip()
          if not seen_variable:
            subquestion += f"{capt}\n\n"
          else:
            fields.append({"note": capt})
        elif isinstance(dialog_item, Variable):
          seen_variable = True
          fields.append(dialog_item.get_field())
      question = {
          "id": dialog_name,
          "question": dialog["title"],
          "subquestion": subquestion.rstrip(),
        }
      if fields:
        question["fields"] = fields
      else:
        question["continue button field"] = dialog["da_name"]
      # NOTE: TEMP for testing
      question["mandatory"] = True
      dialogs.append(question)
    choices = [
      {"variable name": dup_name } | {"data": [{val : disp} if disp != val else val for disp, val in dup_opts]}
      for dup_name, dup_opts in self.dup_choices.items()
    ]
    variables = [
      {
        "id": v.name,
        "code": f"{v.da_name} = False"
      }
      for v in self.variable_map.values() if v.prompt == ""
    ]
    computations = [
      {
        "id": v["name"],
        "code": f"def {v['da_func_name']}():\n  return '''tmp for code {v['name']}'''",
      }
       for v in self.code_blocks.values()
    ]
    return [metadata] + choices + dialogs + computations + variables


# TODO: to focus on:
# * getting PDF output correct (or at least renaming vars, getting attachment block)
# * getting show if working correctly, script stuff, etc.
# * what to change about the general structure of HotDocs interviews when converting to
#   docassemble?


