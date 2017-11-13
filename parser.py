# Copyright 2017

from parse_blocks import *

class WikiTokenizer():
    def __init__(self, page_name):
        self.page_name = page_name
        self.current_token = ""
        self.tokens = []
        self.parsed_data = None
        self.debug_set = set()

    def clear_token(self):
        if self.current_token:
            if self.current_token.isalpha():
                self.tokens.append(TextBlock(self.current_token))
            else:
                self.tokens.append(self.current_token)
        self.current_token = ""

    def tokenize(self, text):
        in_text = False
        in_tag = False
        in_table = False
        in_comment = False

        for c in text:
            if in_table and c in "|-}":  # special handling of |- and |}
                if self.current_token == "|" and c == "-":
                    self.current_token += c
                    self.clear_token()
                    continue
                if self.current_token == "|" and c == "}":
                    self.current_token += c
                    self.clear_token()
                    in_table = False
                    continue
                if c == "|":
                    self.clear_token()
                    self.current_token += c
                    continue
            if in_table and self.current_token == "|":  # regular pipe in a table
                self.clear_token()
            if in_tag:
                if in_comment:
                    if c == ">" and self.current_token.endswith("--"):
                        # end of comment
                        self.current_token += c
                        self.clear_token()
                        in_tag = False
                        in_comment = False
                        continue
                    else:
                        self.current_token += c
                        continue
                if self.current_token == "<!--":  # HTML comment
                    in_comment = True
                    self.current_token += c
                    continue
                if c != ">":
                    self.current_token += c
                    continue
                #  else c == ">":
                self.current_token += c
                in_tag = False
                self.clear_token()
                continue
            elif c.isalpha() or c.isnumeric() or c in ("/", ".", ",", ":", "-", "(", ")"):
                if in_text:
                    self.current_token += c
                else:  # (not in_text)
                    self.clear_token()
                    self.current_token += c
                    in_text = True
                continue
            elif c == ";":
                # Special because of &nbsp; and the like.
                if in_text and self.current_token[0] == "&":
                    self.current_token += c
                    self.clear_token()
                    in_text = False
                else:
                    self.clear_token()
                    self.tokens.append(";")
                    in_text = False
                continue
            elif c == "&":
                # Clear current text, ascii after can be included.
                self.clear_token()
                self.current_token += c
                in_text = True
            elif c == "<":
                # Start tag
                if in_tag:
                    raise("Nested tags on " + self.page_name)
                self.clear_token()
                in_text = False
                in_tag = True
                self.current_token += c
            elif c == "|":
                if self.current_token == "{":
                    # Table starts {|
                    self.current_token += c
                    self.clear_token()
                    in_table = True
                else:
                    # Always separate
                    self.clear_token()
                    self.tokens.append("|")
                    in_text = False
            elif c in ("]", "}"):
                # Group up to two of these in a row
                if self.current_token and self.current_token == c:
                    self.current_token += c
                else:
                    self.clear_token()
                    self.current_token += c
                    in_text = False
            elif c in ("[", "{", "=", "\n", "'"):
                # Group all of these in a row
                if self.current_token and self.current_token[0] == c:
                    self.current_token += c
                else:
                    self.clear_token()
                    self.current_token += c
                    in_text = False
            elif c == " ":
                if in_text:
                    self.clear_token()
                    in_text = False
                    self.tokens.append(c)
                else:
                    self.clear_token()
                    self.tokens.append(c)
            else:  # Unhandled, keep as single characters
                self.debug_set.add(c)
                self.clear_token()
                self.tokens.append(c)
                in_text = False
        # finally
        self.clear_token()
        self.parsed_data = DocumentBlock(tokenizer=self)
        for token in self.tokens:
            self.parsed_data.add_block(token)
        return self.parsed_data


def get_lede(tokenizer):
    assert isinstance(tokenizer, WikiTokenizer)  # CLEANUP: migration
    sub_sections = []
    for section in tokenizer.parsed_data.sub_blocks:
        if isinstance(section, HeadingBlock):
            break
        if isinstance(section, TemplateBlock):
            if section.kind() not in RAW_TEMPLATES:
                continue
        if isinstance(section, ReferenceBlock):
            continue
        sub_sections.append(section)
    if not sub_sections:
        return None
    return DocumentBlock(sub_sections, tokenizer=tokenizer, short=True)

def get_infobox(tokenizer):
    assert isinstance(tokenizer, WikiTokenizer)  # CLEANUP: migration
    for section in tokenizer.parsed_data.sub_blocks:
        if isinstance(section, TemplateBlock):
            kind = section.kind()
            if kind.startswith("infobox"):
                return section
            if kind == "subspeciesbox":
                return section
            if kind == "speciesbox":
                return section
            if kind == "taxobox":
                return section
    return None
