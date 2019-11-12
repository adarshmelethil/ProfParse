import sys
import os
import json

data_file = os.path.join("data", "profs_details.json")
if not os.path.exists(data_file):
  print(f"missing file {data_file}, run data_scrape.py")
  exit(1)


with open(data_file, "r") as fp:
  profs = json.load(fp)

if len(sys.argv) < 2:
  print("specify action")
  print("display?")
  print("show?")
  exit(1)

action = sys.argv[1]
if action == "display" or action == "d":
  display_content = profs
  keys = []
  if len(sys.argv) > 2:
    keys = " ".join(sys.argv[2:])
    keys = keys.split("-")
    key = keys[0].strip()
    if key not in profs:
      print(f"Prof not found '{key}'")
      exit(1)
    display_content = display_content[key]

  if len(keys) > 1:
    ks = [k.strip() for k in keys[1].split()]
    temp_c = {}
    for k in ks:
      if k not in display_content:
        ks = ", ".join([ks for ks in display_content.keys()])
        print(f"{k} not found in [{ks}]")
        exit(1)
      temp_c[k] = display_content[k]
    display_content = temp_c
  print(json.dumps(display_content, indent=4))

elif action == "show" or action == "s":
  if len(sys.argv) > 2:
    key = sys.argv[2]
    vals = []
    for prof_name, prof_data in profs.items():
      if key not in prof_data:
        print(f"'{key}' not part of keys for '{prof_name}'")
      else:
        data = prof_data[key]
        if type(data) is list:
          vals.extend([(prof_name, d) for d in data])
        else:
          vals.append((prof_name, data))
    vals = set(vals)
    
    search_string = None
    if len(sys.argv) > 3:
      search_string =  " ".join(sys.argv[3:])
    for val in vals:
      if search_string:
        if search_string in val[1]:
          print(f"{val[0]}: {val[1]}")
      else:
        print(val[1])
  else:
    for first_prof in profs:
      print(", ".join(profs[first_prof].keys()))
      exit(0)
elif action == "filter" or action == "f":
  pass
else:
  print("unknown action")
  exit(1)

