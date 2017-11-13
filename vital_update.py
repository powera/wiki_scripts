#!/usr/bin/python3

import parser
import util

import difflib
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
    "Everyday life": "Life",
    "Society and social sciences": "Society",  # or language
    "Biology and health sciences": "Science",
    "Physical sciences": "Science",
    "Technology": "Technology",
    "Mathematics": "Mathematics",
}
subpage_param_for_cat = {
    "Biology and health sciences": "Biology",
    "Physical sciences": "Physics",
}

def make_template(kind, params):
    param_text = [parser.TextBlock(k + "=" + v) for (k, v) in params.items() if v is not None]
    param_text = sum([[parser.TextBlock("|"), x] for x in param_text], [])
    sub_blocks = [parser.TextBlock(kind)] + param_text
    return parser.TemplateBlock(sub_blocks=sub_blocks)

def get_article_class(pagename, t):
    for section in t.parsed_data.sub_blocks:
        if isinstance(section, parser.TemplateBlock) and section.has_param("class"):
            return section.get_param("class").strip()
        if (isinstance(section, parser.TemplateBlock) and
                section.kind() in ("WikiProjectBannerShell", "WPBS", "Banner holder")):
            for subsection in section.sub_blocks:
                if (isinstance(subsection, parser.TemplateBlock) and
                        subsection.has_param("class")):
                    return subsection.get_param("class").strip()
    # Not found, consider it start class
    print("No class found for " + pagename)
    return "Start"

def update_link(pagename, session, token, target_level,
                topic=None, subpage=None):
    if not pagename.startswith("Talk:"):  # wrong namespace
        print("Doing nothing for " + pagename)
        return

    base_ts, base_content = util.read_for_edit(pagename, session, token)

    t = parser.WikiTokenizer(pagename)
    t.tokenize(base_content)
    
    try:
        util.bot_check(pagename, session, token)
    except Exception:
        print("Bot check failed on %s, no action taken." % pagename)
        return

    article_class = get_article_class(pagename, t)
    if t.parsed_data.has_template_of_kind("Vital article"):
        block = t.parsed_data.get_first_template_of_kind("Vital article")
        block.set_param("topic", topic)
        block.set_param("level", str(target_level))
        if subpage:
            block.set_param("subpage", subpage)
        new_content = t.parsed_data.wiki()
        print(pagename)
        print(" ".join(difflib.ndiff(base_content.splitlines(keepends=True),
                                     new_content.splitlines(keepends=True))))
        # util.edit(pagename, session, token, base_ts, new_content)
        return

    vital_block = make_template("Vital article", params={
        "class": article_class, "topic": topic,
        "level": str(target_level), "subpage": subpage})

    if t.parsed_data.has_template_of_kind("WPBS"):
        parent = t.parsed_data.get_first_template_of_kind("WPBS")
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
    elif t.parsed_data.has_template_of_kind("WikiProjectBannerShell"):
        parent = t.parsed_data.get_first_template_of_kind("WikiProjectBannerShell")
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
    elif t.parsed_data.has_template_of_kind("Banner holder"):
        parent = t.parsed_data.get_first_template_of_kind("Banner holder")
        parent.sub_blocks.append(parser.TextBlock("\n"))
        parent.sub_blocks.append(vital_block)
        parent.sub_blocks.append(parser.TextBlock("\n"))
    else:
        t.parsed_data.sub_blocks.append(parser.DebugBlock("\n"))
        t.parsed_data.sub_blocks.append(vital_block)

    new_content = t.parsed_data.wiki()
    print(pagename)
    print(" ".join(difflib.ndiff(base_content.splitlines(keepends=True),
                                 new_content.splitlines(keepends=True))))
    # util.edit(pagename, session, token, base_ts, new_content)


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
    print("Old: " + base_content)
    print("New: " + new_content)
    # util.edit(pagename, session, token, base_ts, new_content)


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
    links_for_cat = util.get_links_from_page("Wikipedia:Vital articles/Expanded/" + category)

    level4_talk_pages_for_cat = set(["Talk:" + x for x in (links_for_cat - links3)])

    # These are "talk" page links.
    current = util.get_category_members(
        "Category:Wikipedia level-4 vital articles in " + topic_for_cat[category],
        session, token)

    extra = current - level4_talk_pages_for_cat
    missing = level4_talk_pages_for_cat - current
    for link in missing:
        subpage = subpage_param_for_cat[category] if category in subpage_param_for_cat else None
        update_link(link, session, token, target_level=4,
                    topic=topic_for_cat[category], subpage=subpage)
    for link in extra:
        remove_link(link, session, token)


def bulk_update():
    session, token = util.init_session_with_token()
    for cat in ["People", "History", "Geography", "Arts",
                "Philosophy and religion", "Everyday life",
                "Technology", "Mathematics"]:
        update_level4_cat(cat, session, token)
