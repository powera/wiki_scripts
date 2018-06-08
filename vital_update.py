#!/usr/bin/python3

import parser
import util

import urllib.parse
import urllib.request

CAT = [
    "People",
    "History",
    "Geography",
    "Arts",
    "Philosophy and religion",
    "Everyday life",
    "Society and social sciences",
    "Biology and health sciences",
    "Physical sciences",
    "Technology",
    "Mathematics",
]

topic_for_cat = {
    "People": "People",
    "History": "History",
    "Geography": "Geography",
    "Arts": "Art",
    "Philosophy and religion": "Philosophy",
    "Everyday life": "Life",  # or "Everyday life"
    "Society and social sciences": "Society",  # or language
    "Biology and health sciences": "Biology",
    "Physical sciences": "Science",
    "Technology": "Technology",
    "Mathematics": "Mathematics",
}

L5_GEOGRAPHY = {
    "Physical": "Physical geography",
    "Countries": "Countries",
    "Cities": "Cities",
}

def make_template(kind, params):
    param_text = [parser.TextBlock(k + "=" + v) for (k, v) in params.items() if v is not None]
    param_text = sum([[parser.TextBlock("|"), x] for x in param_text], [])
    sub_blocks = [parser.TextBlock(kind)] + param_text
    return parser.TemplateBlock(sub_blocks=sub_blocks)

def _get_article_class(pagename, t):
    for section in t.parsed_data.sub_blocks:
        if isinstance(section, parser.TemplateBlock) and section.has_param("class"):
            return section.get_param("class").strip()
        if isinstance(section, parser.TemplateBlock):  # too many synonyms of WPBS to list
            for subsection in section.sub_blocks:
                if (isinstance(subsection, parser.TemplateBlock) and
                        subsection.has_param("class")):
                    return subsection.get_param("class").strip()
    # Not found, consider it start class
    print("No class found for " + pagename)
    return "Start"

def get_article_class(pagename, t):
    """Validate class."""
    g = _get_article_class(pagename, t)
    if g in ["Start", "Stub", "GA", "FA"]:
        return g
    return g.split()[0].capitalize()

def update_link(pagename, session, token, target_level,
                topic=None, subpage=None):
    if not pagename.startswith("Talk:"):  # wrong namespace
        print("Doing nothing for " + pagename)
        return

    try:
        base_ts, base_content = util.read_for_edit(pagename, session, token)
    except Exception:
        print("page read failed on %s" % pagename)
        return

    t = parser.WikiTokenizer(pagename)
    t.tokenize(base_content)
    
    try:
        util.bot_check(pagename, session, token)
    except Exception:
        print("Bot check failed on %s, no action taken." % pagename)
        return

    try:
        article_class = get_article_class(pagename, t)
    except Exception:
        print("Article class failed on %s" % pagename)
        return
    if t.parsed_data.has_template_of_kind("Vital article"):
        block = t.parsed_data.get_first_template_of_kind("Vital article")
        block.set_param("topic", topic)
        block.set_param("level", str(target_level))
        block.set_param("subpage", subpage)
        new_content = t.parsed_data.wiki()
        util.edit(pagename, session, token, base_ts,
                  message="Updating vital article template",
                  new_content=new_content, old_content=base_content)
        return

    vital_block = make_template("Vital article", params={
        "class": article_class, "topic": topic,
        "level": str(target_level), "subpage": subpage})

    if t.parsed_data.has_template_of_kind("WPBS"):
        parent = t.parsed_data.get_first_template_of_kind("WPBS")
        if parent.sub_blocks[-1] != "\n":
            parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.parse()
    elif t.parsed_data.has_template_of_kind("WikiProjectBannerShell"):
        parent = t.parsed_data.get_first_template_of_kind("WikiProjectBannerShell")
        if parent.sub_blocks[-1] != "\n":
            parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.parse()
    elif t.parsed_data.has_template_of_kind("WikiProject banner shell"):
        parent = t.parsed_data.get_first_template_of_kind("WikiProject banner shell")
        if parent.sub_blocks[-1] != "\n":
            parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.parse()
    elif t.parsed_data.has_template_of_kind("Banner holder"):
        parent = t.parsed_data.get_first_template_of_kind("Banner holder")
        if parent.sub_blocks[-1] != "\n":
            parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.parse()
    elif t.parsed_data.has_template_of_kind("WikiProjectBanners"):
        parent = t.parsed_data.get_first_template_of_kind("WikiProjectBanners")
        if parent.sub_blocks[-1] != "\n":
            parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.parse()
    else:
        t.parsed_data.sub_blocks.append(parser.DebugBlock("\n"))
        t.parsed_data.sub_blocks.append(vital_block)

    new_content = t.parsed_data.wiki()
    util.edit(pagename, session, token, base_ts,
              message="Adding vital article level-%s template" % target_level,
              new_content=new_content, old_content=base_content)


def remove_link(pagename, session, token):
    base_ts, base_content = util.read_for_edit(pagename, session, token)

    t = parser.WikiTokenizer(pagename)
    t.tokenize(base_content)

    try:
        util.bot_check(pagename, session, token)
    except Exception:
        print("Bot check failed on %s, no action taken." % pagename)
        return

    if not t.parsed_data.has_template_of_kind("Vital article"):
        print("Template not present on " + pagename)
        return
    
    t.parsed_data.remove_templates_of_kind("Vital article")

    new_content = t.parsed_data.wiki()
    util.edit(pagename, session, token, base_ts,
              message="Removing vital article template",
              new_content=new_content, old_content=base_content)


### Update functions.  These get a list of pages which need templates ###
### to be added or removed, due to updates on the vital article lists ###

def update_vital3():
    session, token = util.init_session_with_token()

    # These are "article" page links.
    links2 = util.get_links_from_page("Wikipedia:Vital articles/Level/2")
    links3 = util.get_links_from_page("Wikipedia:Vital articles")

    level3_talk_pages = set(["Talk:" + x for x in (links3 - links2)])

    # These are "talk" page links.
    current = util.get_category_members(
        "Category:All Wikipedia level-3 vital articles", session, token)

    extra = current - level3_talk_pages
    missing = level3_talk_pages - current
    for link in missing:
        update_link(link, session, token, target_level=3, topic=None)
    for link in extra:
        # Do nothing for now.
        print(link)


def update_level4_cat(category, session=None, token=None):
    if not session:
        session, token = util.init_session_with_token()
    else:
        assert token  # must pass both

    links3 = util.get_links_from_page(
        "Wikipedia:Vital articles",
        sentinel="<!-- LIST STARTS HERE -->")
    links_for_cat = util.get_links_from_page("Wikipedia:Vital articles/Level/4/" + category)

    level4_talk_pages_for_cat = set(["Talk:" + x for x in (links_for_cat - links3)])

    # These are "talk" page links.
    current = util.get_category_members(
        "Category:Wikipedia level-4 vital articles in " + topic_for_cat[category],
        session, token)

    extra = current - level4_talk_pages_for_cat
    missing = level4_talk_pages_for_cat - current
    for link in missing:
        # subpage = subpage_param_for_cat[category] if category in subpage_param_for_cat else None
        subpage = None
        update_link(link, session, token, target_level=4,
                    topic=topic_for_cat[category], subpage=subpage)
    for link in extra:
        remove_link(link, session, token)

def update_level5_cat(category, subcat=None, *, session=None, token=None):
    if not session:
        session, token = util.init_session_with_token()
    else:
        assert token  # must pass both

    links4 = util.get_links_from_page(
        "Wikipedia:Vital articles/Level/4/" + category)
    links_for_cat = util.get_links_from_page(
        "Wikipedia:Vital articles/Level/5/" + category + ("/" + subcat if subcat else ""))

    level5_talk_pages_for_cat = set(["Talk:" + x for x in (links_for_cat - links4)])

    # These are "talk" page links.
    current = util.get_category_members(
        "Category:Wikipedia level-5 vital articles in " + topic_for_cat[category],
        session, token)

    extra = current - level5_talk_pages_for_cat
    missing = level5_talk_pages_for_cat - current
    for link in missing:
        # subpage = subpage_param_for_cat[category] if category in subpage_param_for_cat else None
        subpage = subcat
        update_link(link, session, token, target_level=5,
                    topic=topic_for_cat[category], subpage=subpage)
    for link in extra:
        remove_link(link, session, token)

def bulk_update():
    session, token = util.init_session_with_token()
    for cat in ["Technology", "History", "Geography", "Arts", "People",
                "Philosophy and religion", "Everyday life",
                "Mathematics", "Biology and health sciences", "Physical sciences"]:
        update_level4_cat(cat, session, token)
