#!/usr/bin/python3

URL = ("https://en.wikipedia.org/w/api.php?action=query&list=logevents&"
       "letype=rights&leaction=rights/rights&lelimit=50&format=json&ledir=newer")

import datetime
import json
import requests

rights_dict = {}

def get_data(start=None):
    if not start:
        start = datetime.datetime.now() - datetime.timedelta(days=28)
    start_url = URL + "&lestart=" + start.strftime("%Y%m%d%H%M%S")
    lecontinue = ""
    while True:
        page = requests.get(start_url + lecontinue)
        results = page.json()
        for logevent in results["query"]["logevents"]:
            user = logevent["title"]
            rights_dict.setdefault(user, {"old": logevent["params"]["oldgroups"]})
            rights_dict[user]["new"] = logevent["params"]["newgroups"]
        if "continue" in results:
            lecontinue = "&lecontinue=" + results["continue"]["lecontinue"]
        else:
            break
    for right in ["extendedmover", "reviewer", "patroller", "templateeditor"]:
        print("\n'''" + right + "'''")
        for user in sorted(rights_dict.keys()):
            if right in rights_dict[user]["new"] and right not in rights_dict[user]["old"]:
                print("* " + user)

get_data()
