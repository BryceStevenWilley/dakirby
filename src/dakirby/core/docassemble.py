#from pyaml import dump_all
import io

def nested_print(output, data, indent=0, prev_context=None):
  if isinstance(data, dict):
    if not data:
      print("{}", file=output)
      return
    if prev_context:
      indent += 2
    ind = ' ' * indent
    idx = 0
    for key in data:
      if (prev_context == "list" and idx == 0) or prev_context is None:
        print(f"{key}: ", file=output, end='')
      elif idx > 0:
        print(f"{ind}{key}: ", file=output, end='')
      else:
        print(f"\n{ind}{key}: ", file=output, end='')
      nested_print(output, data[key], indent, prev_context="dict")
      idx += 1
  elif isinstance(data, list):
    indent += 2
    ind = ' ' * indent
    for idx, item in enumerate(data):
      if prev_context == "dict" and idx == 0:
        print(f"\n{ind}- ", file=output, end='')
      else:
        print(f"{ind}- ", file=output, end='')
      nested_print(output, item, indent, prev_context="list")
  elif isinstance(data, str):
    if '\n' in data:
      indent += 2
      ind = ' ' * indent
      data = data.replace("\n", f"\n{ind}")
      print(f"|\n{ind}{data}", file=output)
    else:
      ind = ' ' * indent
      print(f"\"{data}\"", file=output)
  elif isinstance(data, int) or isinstance(data, float):
    ind = ' ' * indent
    print(f"{data}", file=output)
  else:
    ind = ' ' * indent
    print(f"{data}", file=output)

def to_yaml(objs):
  # TODO(brycew): do smarter things, like `|` vs inline for certain keys,
  # matching docassemble YAML style, etc.
  # return dump_all(objs, string_val_style="|", sort_keys=False)

  output = io.StringIO()
  for obj in objs:
    print("---", file=output)
    nested_print(output, obj, indent=0)
  return output.getvalue()