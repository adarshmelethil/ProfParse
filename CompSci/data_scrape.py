import sys
import os
import json
import re
import requests
import urllib
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from bs4 import UnicodeDammit


uofc_science_url = "https://science.ucalgary.ca"

def printFailed(cur_prof_name, addr, add_url=uofc_science_url):
  addr = urllib.parse.urljoin(add_url, addr)
  print(f"FAILED: {cur_prof_name}: {addr}", file=sys.stderr)


faculty_members_cache = os.path.join("data", "faculty-members.html")
profs_list_cache = os.path.join("data", "profs_list.json")
if not os.path.exists(profs_list_cache):
  if not os.path.exists(faculty_members_cache):
    profs_list_url = urllib.parse.urljoin(uofc_science_url, "computer-science/contacts")
    print(f"Making request '{profs_list_url}'", file=sys.stderr)
    res = requests.get(profs_list_url)
    if res.status_code != 200:
      print(f"failed to get page: {profs_list_url}", file=sys.stderr)
      exit(1)
    
    # cache result
    with open(faculty_members_cache, "w+") as fp:
      fp.write(str(res.content))

    page_content = res.content
  else:
    print(f"Loading request form file 'faculty-members.html'", file=sys.stderr)
    with open(faculty_members_cache, "r") as fp:
      page_content = fp.read()

  profs_page = BeautifulSoup(page_content, 'html.parser')

  prof_lis = profs_page.find("ol", {"class": "section-items max-items"}).find_all("li")

  profs = {}
  for prof_li in prof_lis:
    prof_name = prof_li.find("p", {"class": "title"}).getText()
    email_a, link_a = prof_li.find_all("a")
    prof_email = email_a.getText()
    prof_details = link_a["href"]
    prof_title = prof_li.find("strong").getText().replace("\\xc2", "").replace("\\xa0", "").strip()

    profs[prof_name] = {
      "title": prof_title,
      "email": prof_email,
      "detailsURL": prof_details
    }
  
  # cache result
  with open(profs_list_cache, 'w+') as f:
    json.dump(profs, f, indent=2)
else:
  print("Loaded profs", file=sys.stderr)
  with open(profs_list_cache, 'r') as f:
    profs = json.load(f)


# *** prof specific data ***
profs_dir = os.path.join("data", "profs")
if not os.path.exists(profs_dir):
  os.makedirs(profs_dir)


def getCourses(prof_detail_dirname, addr):
  course_page_content_cache = os.path.join(prof_detail_dirname, "courses.html")
  if not os.path.exists(course_page_content_cache):
    print(f"Making request '{addr}'", file=sys.stderr)
    res = requests.get(addr)
    if res.status_code != 200:
      print(f"failed to get page: {addr}", file=sys.stderr)
      exit(1)
    # cache result
    with open(course_page_content_cache, "w+") as fp:
      fp.write(str(res.content))
    course_page_content = res.content    
  else:
    with open(course_page_content_cache, "r") as fp:
      course_page_content = fp.read()

  course_page = BeautifulSoup(course_page_content, "html.parser")
  courses = course_page.find("tbody").find_all("tr", {"class": "primary-row"})
  prof_courses = []
  for course in courses:
    course_expander_link = course.find("a", {"class": "uofc-row-expander"})
    if course_expander_link is None:
      continue
    course_name = course_expander_link.getText()
    if "LEC" in course_name:
      continue

    # print(course_name)
    season, course_code, *course_name = course_name.split(" - ")
    course_name = " - ".join(course_name)
    prof_courses.append({
      "season": season,
      "course_code": course_code,
      "course_name": course_name
    })
  return prof_courses

profs_details_cache = os.path.join("data", "profs_details.json")
if not os.path.exists(profs_details_cache):
  for cur_prof_name, cur_prof_data in profs.items():
    print(f"Processing '{cur_prof_name}'", file=sys.stderr)
    prof_detail_dirname = os.path.join(profs_dir, cur_prof_name.replace(" ", ""))
    if not os.path.isdir(prof_detail_dirname):
      os.makedirs(prof_detail_dirname)

    prof_detail_filename = os.path.join(prof_detail_dirname, "details.html")
    if not os.path.exists(prof_detail_filename):
      prof_detail_url = cur_prof_data["detailsURL"]
      res = requests.get(prof_detail_url)
      if res.status_code != 200: 
        print(f"failed to get page: {prof_detail_url}", file=sys.stderr)
        exit(1)
      with open(prof_detail_filename, "w+") as fp:
        fp.write(str(res.content))

      prof_detail_html = res.content
    else:
      print(f"Loading info for '{cur_prof_name}'", file=sys.stderr)
      with open(prof_detail_filename, "r") as fp:
        prof_detail_html = fp.read()

    prof_detail = BeautifulSoup(prof_detail_html, "html.parser")
    if prof_detail is None:
      printFailed(cur_prof_name, profs[cur_prof_name]["detailsURL"])
      continue

    # Courses
    courses_page_url = prof_detail.find("div", {"class":"unitis-profile-region-2"}).find("a")["href"]
    prof_courses = getCourses(prof_detail_dirname, courses_page_url)
    
    # contact
    profile_block_contact = prof_detail.find("div", {"id": "unitis-profile-block-contact"})
    prof_phones = [phone_li.getText()
      for phone_li in 
      profile_block_contact.find("div", {"class": "unitis-phones-list"}).find("ul").find_all("li")]
    
    website_list = profile_block_contact.find("div", {"class": "unitis-website-list"})
    if website_list:
      prof_websites = [website_li.find("a")["href"]
        for website_li in website_list.find("ul").find_all("li")]
    else:
      prof_websites = []
    
    # Area of interest
    areas_of_interest_block = prof_detail.find("div", {"id": "unitis-profile-block-profileblock_0"})
    areas_of_interests = []
    if areas_of_interest_block is not None:
      if "Areas of Interest" in areas_of_interest_block.getText():
        areas_of_interests = [x for x in areas_of_interest_block.find("div", {"class": "content"}).find("p").contents if getattr(x, 'name', None) != 'br']

    credentials_block = prof_detail.find("div", {"id": "unitis-profile-block-profileblock_1"})
    credentials = []
    if credentials_block is not None:
      if "Credentials" in credentials_block.getText():
        for x in credentials_block.find("div", {"class": "content"}).find("p").contents:
          if getattr(x, 'name', None) is None:
            credentials.append(x)


    profs[cur_prof_name]["courses_url"] = courses_page_url
    profs[cur_prof_name]["courses"] = prof_courses
    profs[cur_prof_name]["phones"] = prof_phones
    profs[cur_prof_name]["websites"] = prof_websites
    profs[cur_prof_name]["interests"] = areas_of_interests
    profs[cur_prof_name]["credentials"] = credentials

  with open(profs_details_cache, "w+") as fp:
    json.dump(profs, fp, indent=2)
else:
  with open(profs_details_cache, "r") as fp:
    profs = json.load(fp)


