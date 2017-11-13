#!/usr/bin/python3

import parser
import vital_update

import unittest

def test_article_class(pagename, expected_class):
    filename = "testdata/" + pagename.lower().replace(" ", "_") + ".dat"
    with open(filename) as f:
        t = parser.WikiTokenizer(pagename)
        t.tokenize(f.read())
        assert vital_update.get_article_class(pagename, t) == expected_class

    return True

test_article_class("Pennsylvania", "C")  # also a delisted good article
test_article_class("Economics", "B")  # also a former featured article
test_article_class("Bob Dylan", "FA")
test_article_class("Fried plantain", "Start")

class IntegrationTest(unittest.TestCase):
  def test_add_and_remove(self):
    filename = "testdata/bob_dylan.dat"
    with open(filename) as f:
        t = parser.WikiTokenizer("Bob Dylan")
        t.tokenize(f.read())
    block = t.parsed_data.get_first_template_of_kind("Vital article")
    block.set_param("level", "3")
    block.set_param("topic", "Biographies")
    result = t.parsed_data.wiki()

    result_file = "testdata/results/dylan_change_attr.dat"
    #with open(result_file, "w") as g:
    #    g.write(result)
    with open(result_file) as g:
        assert g.read() == result

    t.parsed_data.remove_templates_of_kind("Vital article")
    result2= t.parsed_data.wiki()
    result_file2 = "testdata/results/dylan_remove.dat"
    #with open(result_file2, "w") as h:
    #    h.write(result2)
    with open(result_file2) as h:
        self.assertEqual(h.read(), result2)

if __name__ == '__main__':
    unittest.main()
