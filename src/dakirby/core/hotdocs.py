#!/usr/bin/env python3

from lxml import etree
from lxml.etree import QName
from .common import varname, PageNode
import glob

from typing import TypedDict

class DialogElement(TypedDict):
  name: str
  caption: str | None
  web_link: str | None

def parse_display_text(text):
  # TODO(brycew): handle .w, vars, etc.
  if not text:
    return ""
  text = text.replace("«.b»", "**").replace("«.be»", "**")
  text = text.replace("«.i»", "*").replace("«.ie»", "*")
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
    return {
      "label": label,
      "field": self.da_name,
      "datatype": self.get_datatype()
    }

class TextVariable(Variable):
  help: str | None
  area: bool

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
  options: list

  def __init__(self, name, prompt=None, style=None, options=None):
    super().__init__(name, prompt)
    self.style = style
    self.options = options if options else []

  def get_datatype(self):
    if self.style == "dropDownList":
      return "dropdown"
    else:
      return "radio"

  def get_field(self):
    field = super().get_field()
    field["choices"] = [{tup1: tup2} if tup1 != tup2 else tup1 for tup1, tup2 in self.options]
    return field


class HotDocsInterview:

  xml_namespace = "http://www.hotdocs.com/schemas/component_library/2009"

  @classmethod
  def xml_ns(cls, arg):
    """Returns the full URL of an XML namespaced tag"""
    return QName(cls.xml_namespace, arg).text

  def __init__(self, input_dirname):
    self.metadata = {}
    self.setup_info = {}
    self.page_map: dict[str, PageNode] = {}
    self.dialogs: dict[str, dict] = {}
    self.variable_map: dict[str, Variable] = {}

    # HotDoc specific things that might be useful
    self.preferences = {}
    self.code_blocks = {}
    self.dialog_elements: dict[str, DialogElement] = {}

    self.master_cmp = None
    for cmp_file in glob.iglob(input_dirname + "/*cmp"):
      # print(cmp_file)
      with open(cmp_file, "r") as f:
        doc = etree.parse(f)
        # print(doc.getroot().tag)
        if doc.getroot().tag == self.xml_ns("componentLibrary"):
          self.master_cmp = input_dirname + "/" + doc.getroot().get("pointedToFile", cmp_file)
          break

    if self.master_cmp:
      self.parse_master_cmp()

    self.main_order_script = self.preferences.get("CUSTOM_INTERVIEW")

  def __str__(self):
    return f"{self.master_cmp=}, {self.metadata=}, {self.setup_info=}, {self.variable_map=}"
  
  def __repr__(self):
    return str(self)
    
  def parse_master_cmp(self):
    with open(self.master_cmp, "r") as f:
      doc = etree.parse(f)
      for elem in doc.getroot():
        if elem.tag.lower() == self.xml_ns("preferences"):
          self.parse_preferences(elem)
        elif elem.tag.lower() == self.xml_ns("components"):
          for component in elem:
            tag = component.tag
            if tag == self.xml_ns("text"):
              self.parse_text_var(component)
            elif tag == self.xml_ns("number"):
              self.parse_number_var(component)
            elif tag == self.xml_ns("trueFalse"):
              self.parse_tf_var(component)
            elif tag == self.xml_ns("multipleChoice"):
              self.parse_mc_var(component)
            elif tag == self.xml_ns("computation"):
              self.parse_computation(component)
            elif tag == self.xml_ns("dialogElement"):
              self.parse_dialog_element(component)
            elif tag == self.xml_ns("dialog"):
              self.parse_dialog(component)
            # All other top levels are text formats, number formats, etc. Idk what to do with those.

  def parse_preferences(self, prefs):
    for pref in prefs:
      name = pref.get("name")
      self.preferences[name] = pref.text

  def parse_text_var(self, text_elem):
    if len(text_elem) == 0: # If no prompt, likely set by a script somewhere?
      return
    name = text_elem.get("name")
    prompt = None
    help = None
    area = False
    for elem in text_elem:
      if elem.tag == self.xml_ns("prompt"):
        prompt = elem.text
      elif elem.tag == self.xml_ns("resource"):
        help = elem[0].text
      elif elem.tag == self.xml_ns("multiLine"):
        area = True
      # Ignore fieldWidth, columnWidth. Idk what to do with defMergeProps?
    # Also warnIfUnanswered?
    self.variable_map[name] = TextVariable(name, prompt=prompt, help=help, area=area)

  def parse_number_var(self, number_elem):
    if len(number_elem) == 0: # If no prompt, likely set by a script somewhere?
      return
    name = number_elem.get("name")
    decimal_places = number_elem.get("decimalPlaces", 0)
    currency_symbol = number_elem.get("currencySymbol")
    prompt = None
    help = None
    def_format = None
    for elem in number_elem:
      if elem.tag == self.xml_ns("prompt"):
        prompt = elem.text
      elif elem.tag == self.xml_ns("resource"):
        help = elem[0].text
      elif elem.tag == self.xml_ns("defFormat"):
        def_format = elem.text
    # TODO: Also warnIfUnanswered?
    self.variable_map[name] = NumberVariable(name, prompt, help, decimal_places, currency_symbol, def_format)

  def parse_tf_var(self, tf_elem):
    if len(tf_elem) == 0: # If no prompt, likely set by a script somewhere?
      return
    name = tf_elem.get("name")
    yes_no = tf_elem.get("yesNoOnSameLine")
    prompt = None
    help = None
    for elem in tf_elem:
      if elem.tag == self.xml_ns("prompt"):
        prompt = elem.text
      elif elem.tag == self.xml_ns("resource"):
        help = elem[0].text
    # Also warnIfUnanswered?
    self.variable_map[name] = TrueFalseVariable(name, prompt, help, yes_no)

  def parse_mc_var(self, mc_elem):
    """Multiple choice variable copmonent element"""
    if len(mc_elem) == 0: # If no prompt, likely set by a script somewhere?
      return
    name = mc_elem.get("name")
    style = None # dropDownList or buttonGrid
    prompt = None
    options = []
    for elem in mc_elem:
      if elem.tag == self.xml_ns("prompt"):
        prompt = elem.text
      elif elem.tag == self.xml_ns("options"):
        for opt in elem:
          val = opt.get("name")
          disp_label = next(iter(opt_elem for opt_elem in opt if opt_elem.tag == self.xml_ns("ptompt")), None)
          options.append((disp_label or val, val))
      elif elem.tag == self.xml_ns("singleSelection"):
        style = elem.get("style")
    # TODO(brycew): defMergeProps, fieldWidth
    # TODO(brycew): conslidate different variables with the same options; should go in a different var somewhere
    self.variable_map[name] = MultipleChoiceVariable(name, prompt, style, options)

  def parse_computation(self, computation):
    name = computation.get("name")
    result_type = computation.get("resultType")
    script = ""
    for elem in computation:
      if elem.tag == self.xml_ns("script"):
        script = elem.text
    # TODO(brycew): parse Hotdocs script, for things with result, when it would return,
    # set the value to this.
    # Alternate: make everything functions? Looks like hot docs re-evals
    # everything when it can
    self.code_blocks[name] = {
      "name": name,
      "result_type": result_type,
      "script": script
    }


  def parse_dialog_element(self, dialog_element):
    name = dialog_element.get("name")
    caption = None
    for elem in dialog_element:
      if elem.tag == self.xml_ns("caption"):
        caption = elem.text
    self.dialog_elements[name] = {
      "name": name,
      "caption": parse_display_text(caption),
    }

  def parse_dialog(self, dialog):
    name = dialog.get("name")
    link_vars = dialog.get("linkVariables")
    title = None
    contents = []
    for elem in dialog:
      if elem.tag == self.xml_ns("title"):
        title = elem.text
      elif elem.tag == self.xml_ns("contents"):
        for item in elem:
          contents.append({"name": item.get("name"), "on_previous_line": item.get("onPreviousLine")})
    self.dialogs[name] = {
      "name": name,
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

  def to_yaml_objs(self):
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
      dialogs.append(question)
    variables = {
      "variables": self.variable_map
    }
    computations = [
      {
        "id": v["name"],
        "code": v['script']
      }
       for v in self.code_blocks.values()
    ]
    return [metadata] + dialogs # , variables] # + computations



