# -*- coding: utf-8 -*-

import parser

import difflib
import requests
import urllib.parse
import urllib.request

def init_session_with_token():
    session = requests.Session()
    username = 'PowerBOT'
    import pwdfile
    password = pwdfile.password

    api_url = 'https://en.wikipedia.org/w/api.php'
    # get login token
    r1 = session.get(api_url, params={
        'format': 'json',
        'action': 'query',
        'meta': 'tokens',
        'type': 'login',
    })
    r1.raise_for_status()

    # log in
    r2 = session.post(api_url, data={
        'format': 'json',
        'action': 'login',
        'lgname': username,
        'lgpassword': password,
        'lgtoken': r1.json()['query']['tokens']['logintoken'],
    })
    if r2.json()['login']['result'] != 'Success':
        raise RuntimeError(r2.json()['login']['reason'])

    # get edit token
    r3 = session.get(api_url, params={
        'format': 'json',
        'action': 'query',
        'meta': 'tokens',
    })
    token = r3.json()['query']['tokens']['csrftoken'],
    return session, token


def get_page(title):
    URL_FMT = "https://en.wikipedia.org/wiki/%s?action=raw"
    url = URL_FMT % (urllib.parse.quote(title))
    r = urllib.request.urlopen(url)
    return r.read().decode('utf-8')

def get_links_from_page(title, sentinel=None):
    p = parser.WikiTokenizer(title)
    page = get_page(title)
    if sentinel:
        page = page.split(sentinel)[1]
    p.tokenize(page)
    links = [x for x in p.parsed_data.links() if ":" not in x]
    return set(links)


def get_category_members(cat_name, session, token):
    api_url = 'https://en.wikipedia.org/w/api.php'
    entries = []
    cmcontinue = None
    while True:
        p1 = session.post(api_url, data={
            'format': 'json',
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': cat_name,
            'cmlimit': 250,
            'cmcontinue': cmcontinue,
            })
        entries.extend([x["title"] for x in p1.json()["query"]["categorymembers"]])
        if "continue" in p1.json():
            cmcontinue = p1.json()["continue"]["cmcontinue"]
        else:
            break
    return set(entries)

def read_for_edit(pagename, session, token):
    api_url = 'https://en.wikipedia.org/w/api.php'
    p3 = session.post(api_url, data={
        'format': 'json',
        'action': 'query',
        'titles': pagename,
        'prop': 'revisions',
        'rvprop': 'timestamp|content',
        'rvsection': 0,
        'token': token,
        })

    pages = p3.json()['query']['pages']
    page_data = next(iter(pages.values()))["revisions"][0]

    base_ts = page_data["timestamp"]
    base_content = page_data["*"]

    return base_ts, base_content

def edit(pagename, session, token, base_ts, new_content, old_content=None):
    api_url = 'https://en.wikipedia.org/w/api.php'
    if old_content:
        print(pagename)
        print(" ".join(difflib.ndiff(old_content.splitlines(keepends=True),
                                     new_content.splitlines(keepends=True))))
        print("Confirm edit?  (Y/n)")
        if input() != "Y":
            print("not confirmed, skipping")
    summary = 'Vital article categorization.'
    # save the edit
    if True:
        r4 = session.post(api_url, data={
            'basetimestamp': base_ts,
            'format': 'json',
            'action': 'edit',
            'assert': 'user',
            'section': 0,
            'text': new_content,
            'summary': summary,
            'title': pagename,
            'token': token,
        })
    else:
        print("Did not edit with new content: " + new_content)

def bot_check(pagename, session=None, token=None):  #TODO: use token or remove
    t = parser.WikiTokenizer(pagename)
    t.tokenize(get_page(pagename))

    if t.parsed_data.has_template_of_kind("Nobots"):
        print("Nobots present on " + pagename)
        return False

    bots_tpls = t.parsed_data.get_templates_of_kind("Bots")
    for tpl in bots_tpls:
        for section in tpl.sections():
            if section.startswith("allow"):
                values = section[6:].split(",")
                if "none" in values:
                    return False
                if "all" in values:
                    return True
                if "PowerBOT" in values:
                    return True
                return False
            if section.startswith("deny"):
                values = section[5:].split(",")
                if "none" in values:
                    return True
                if "all" in values:
                    return False
                if "PowerBOT" in values:
                    return False
                return True
            # unknown; log and ignore
            print(tpl)

    return True
