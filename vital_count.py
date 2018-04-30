#!/usr/bin/python

"""Pages that contain the "Vital articles" project lists."""

import util

LEVEL1 = ["Wikipedia:Vital articles/Level/1"]
LEVEL2 = ["Wikipedia:Vital articles/Level/2"]
LEVEL3 = ["Wikipedia:Vital articles"]
LEVEL4 = [
    "Wikipedia:Vital articles/Expanded/People",
    "Wikipedia:Vital articles/Expanded/History",
    "Wikipedia:Vital articles/Expanded/Geography",
    "Wikipedia:Vital articles/Expanded/Arts",
    "Wikipedia:Vital articles/Expanded/Philosophy and religion",
    "Wikipedia:Vital articles/Expanded/Everyday life",
    "Wikipedia:Vital articles/Expanded/Society and social sciences",
    "Wikipedia:Vital articles/Expanded/Biology and health sciences",
    "Wikipedia:Vital articles/Expanded/Physical sciences",
    "Wikipedia:Vital articles/Expanded/Technology",
    "Wikipedia:Vital articles/Expanded/Mathematics",
]
LEVEL5 = [
    "Wikipedia:Vital articles/Level/5/People/Writers and journalists",
    "Wikipedia:Vital articles/Level/5/People/Artists, musicians, and composers",
    "Wikipedia:Vital articles/Level/5/People/Entertainers, directors, producers, and screenwriters",
    "Wikipedia:Vital articles/Level/5/People/Philosophers, historians, political and social scientists",
    "Wikipedia:Vital articles/Level/5/People/Religious figures",
    "Wikipedia:Vital articles/Level/5/People/Politicians and leaders",
    "Wikipedia:Vital articles/Level/5/People/Military leaders, revolutionaries, and activists",
    "Wikipedia:Vital articles/Level/5/People/Explorers and businesspeople",
    "Wikipedia:Vital articles/Level/5/People/Scientists, inventors, and mathematicians",
    "Wikipedia:Vital articles/Level/5/People/Sports figures",
    "Wikipedia:Vital articles/Level/5/People/Jurists, law enforcement, and criminals",
    "Wikipedia:Vital articles/Level/5/History",
    "Wikipedia:Vital articles/Level/5/Geography/Physical",
    "Wikipedia:Vital articles/Level/5/Geography/Countries",
    "Wikipedia:Vital articles/Level/5/Geography/Cities",
    "Wikipedia:Vital articles/Level/5/Arts",
    "Wikipedia:Vital articles/Level/5/Philosophy and religion",
    "Wikipedia:Vital articles/Level/5/Everyday life",
    "Wikipedia:Vital articles/Level/5/Society and social sciences",
    "Wikipedia:Vital articles/Level/5/Biological and health sciences/Biology",
    "Wikipedia:Vital articles/Level/5/Biological and health sciences/Animals",
    "Wikipedia:Vital articles/Level/5/Biological and health sciences/Plants",
    "Wikipedia:Vital articles/Level/5/Biological and health sciences/Health",
    "Wikipedia:Vital articles/Level/5/Physical sciences/Basics and measurement",
    "Wikipedia:Vital articles/Level/5/Physical sciences/Astronomy",
    "Wikipedia:Vital articles/Level/5/Physical sciences/Chemistry",
    "Wikipedia:Vital articles/Level/5/Physical sciences/Earth science",
    "Wikipedia:Vital articles/Level/5/Physical sciences/Physics",
    "Wikipedia:Vital articles/Level/5/Technology",
    "Wikipedia:Vital articles/Level/5/Mathematics",
]

def links_for_rank(rank=3):
    """Returns a map of (page name) -> (list of links)."""
    RANK_MAP = {1: LEVEL1, 2: LEVEL2, 3: LEVEL3, 4: LEVEL4, 5: LEVEL5}
    pages = RANK_MAP[rank]
    result_map = {}
    for page in pages:
        result_map[page] = util.get_links_from_page(page)
    return result_map
