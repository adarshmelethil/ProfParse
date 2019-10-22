import os
import json
import re
import requests
import urllib
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from bs4 import UnicodeDammit


uofc_schulich_url = "https://schulich.ucalgary.ca"

def printFailed(cur_prof_name, addr):
  addr = urllib.parse.urljoin(uofc_schulich_url, addr)
  print(f"FAILED: {cur_prof_name}: {addr}")


if not os.path.exists("profs_list.json"):
  if not os.path.exists("faculty-members.html"):
    profs_list_url = urllib.parse.urljoin(uofc_schulich_url, "/electrical-computer/faculty-members")
    print(f"Making request '{profs_list_url}'")
    res = requests.get(profs_list_url)
    if res.status_code != 200:
      print(f"failed to get page: {profs_list_url}")
      exit(1)
    
    with open(os.path.join("data", "faculty-members.html"), "w+") as fp:
      fp.write(str(res.content))

    page_content = res.content
  else:
    print(f"Loading request form file 'faculty-members.html'")
    with open(os.path.join("data", "faculty-members.html"), "r") as fp:
      page_content = fp.read()

  profs_page = BeautifulSoup(page_content, 'html.parser')

  prof_ps = profs_page.find("div", {"class": "col-sm-12 two-col"}).find_all("p")

  profs = {}
  for prof_p in prof_ps:
    prof_body = UnicodeDammit(str(prof_p)).unicode_markup
    if prof_body == "":
      print("empty")
    patterns = ["<p>", "</p>", "<span>", "</span>", "\\\\xc2", "\\\\xa0"]

    cleaned = re.sub("|".join(patterns), "", prof_body)
    profs_datas = cleaned.split("<br/>")
    prof_name_title = profs_datas[0].split(",")

    prof_name = prof_name_title[0].strip()
    prof_title = prof_name_title[1].strip()
    prof_email = BeautifulSoup(profs_datas[1]).text
    prof_details = BeautifulSoup(profs_datas[2]).a['href']

    profs[prof_name] = {
      "title": prof_title,
      "email": prof_email,
      "address": prof_details
    }
  
  with open(os.path.join("data", 'profs_list.json'), 'w+') as f:
    json.dump(profs, f, indent=2)
else:
  print("Loaded profs")
  with open(os.path.join("data", 'profs_list.json'), 'r') as f:
    profs = json.load(f)


profs_dir = "profs"
if not os.path.exists(profs_dir):
  os.makedirs(profs_dir)


for cur_prof_name, _ in profs.items():
  print(f"Processing '{cur_prof_name}'")
  prof_detail_dirname = os.path.join("data", profs_dir, cur_prof_name.replace(" ", ""))
  if not os.path.isdir(prof_detail_dirname):
    os.makedirs(prof_detail_dirname)

  prof_detail_filename = os.path.join(prof_detail_dirname, "details.html")
  if not os.path.exists(prof_detail_filename):
    prof_detail_url = urllib.parse.urljoin(uofc_schulich_url, profs[cur_prof_name]["address"])
    res = requests.get(prof_detail_url)
    if res.status_code != 200: 
      print(f"failed to get page: {prof_detail_url}")
      exit(1)
    with open(prof_detail_filename, "w+") as fp:
      fp.write(str(res.content))

    prof_detail_html = res.content
  else:
    print(f"Loading info for '{cur_prof_name}'")
    with open(prof_detail_filename, "r") as fp:
      prof_detail_html = fp.read()

  prof_detail = BeautifulSoup(prof_detail_html, "html.parser")
  

  if prof_detail is None:
    printFailed(cur_prof_name, profs[cur_prof_name]["address"])
    continue
  prof_infos = prof_detail.find("div", {"class": "ucws-profiles"})
  if not prof_infos:
    printFailed(cur_prof_name, profs[cur_prof_name]["address"])
    continue
  prof_infos = prof_infos.find("div", {"class": "container"})
  if not prof_infos:
    printFailed(cur_prof_name, profs[cur_prof_name]["address"])
    continue
  prof_infos = prof_infos.find("div", {"class": "content"})
  if not prof_infos:
    printFailed(cur_prof_name, profs[cur_prof_name]["address"])
    continue
  prof_infos = prof_infos.find_all("div")
  if not prof_infos:
    printFailed(cur_prof_name, profs[cur_prof_name]["address"])
    continue

  prof_contact_method = None
  prof_biography = None
  prof_pubs = []
  prof_awards = []
  prof_researchs = []
  prof_courses = []
  for prof_info in prof_infos:
    if prof_info.find("div", {"class": "divider"}) is None:
      prof_info_text = prof_info.getText()
      if "Preferred method of communication" in prof_info_text:
        prof_contact_method = prof_info.find("p").getText()
      if "Biography" in prof_info_text:
        prof_biography = prof_info.find("p").getText().strip()
      if "Publications" in prof_info_text:
        prof_pubs = [pubs.getText().strip() for pubs in prof_info.find_all("p")]
      if "Awards" in prof_info_text:
        prof_awards = [award.getText().strip() for award in prof_info.find_all("p")]
      if "Research areas" in prof_info_text:
        prof_researchs = [r.getText().strip() for r in prof_info.find("ul").find_all("li")]

  prof_detail_courses = prof_detail.find("div", {"class": "courses-text"})
  if prof_detail_courses is not None:
    prof_courses = [c.getText().strip() for c in prof_detail_courses.find_all("p")]

  profs[cur_prof_name]["courses"] = prof_courses
  profs[cur_prof_name]["researchs"] = prof_researchs
  profs[cur_prof_name]["contact_method"] = prof_contact_method
  profs[cur_prof_name]["biography"] = prof_biography
  profs[cur_prof_name]["publications"] = prof_pubs
  profs[cur_prof_name]["awards"] = prof_awards

with open(os.path.join("data", "profs_details.json"), "w+") as fp:
  json.dump(profs, fp, indent=2)
