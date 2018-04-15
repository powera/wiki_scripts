# Copyright 2017

import functools
import itertools

class LatexRenderState(object):
    def __init__(self):
        self.math_mode = False


class ParseBlock(object):
    def __init__(self, sub_blocks=None, short=False, tokenizer=None):
        if sub_blocks:
            self.sub_blocks = sub_blocks
        else:
            self.sub_blocks = []
        if tokenizer:
            self.tokenizer = tokenizer
        self.is_open = False
        self.short = short

    def weighted_links(self, subcall=False):
        if isinstance(self, LinkBlock):
            return [(self.anchor(), 1)]
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            links = [x.weighted_links(subcall=True) for x in self.sub_blocks
                     if hasattr(x, "weighted_links")]
            links = functools.reduce(lambda x,y:x+y, links, [])
            if isinstance(self, ReferenceBlock):  # Note: Most refblocks are in {{cite}}
                links = [(x[0], x[1]/2) for x in links]
            if isinstance(self, TemplateBlock):
                links = [(x[0], x[1]/2) for x in links]
            if not subcall:
                cutoff = int(len(links) / 4)
                links = ([(x[0], x[1] * 1.5) for x in links[:cutoff] ] + links[cutoff:-cutoff] +
                         [(x[0], x[1] * 0.7) for x in links[-cutoff:] ])
            return links
        return []

    def links(self):
        if isinstance(self, LinkBlock):
            if self.anchor() != "":
                return [self.anchor()]
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            links = [x.links() for x in self.sub_blocks if hasattr(x, "links")]
            return functools.reduce(lambda x,y:x+y, links, [])
        return []

    def has_template_of_kind(self, kind):
        kind = kind[0].upper() + kind[1:]
        if isinstance(self, TemplateBlock):
            if self.kind() == kind:
                return True
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            for s in self.sub_blocks:
                if isinstance(s, ParseBlock) and s.has_template_of_kind(kind):
                    return True
        return False

    def get_first_template_of_kind(self, kind):
        template_list = self.get_templates_of_kind(kind)
        if not template_list:
            return None
        return template_list[0]

    def get_templates_of_kind(self, kind):
        template_list = []
        if isinstance(self, TemplateBlock):
            if self.kind() == kind:
                template_list.append(self)
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            for s in self.sub_blocks:
                if isinstance(s, ParseBlock):
                    template_list.extend(s.get_templates_of_kind(kind))
        return template_list

    def remove_templates_of_kind(self, kind):
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            for s in self.sub_blocks[:]:
                if isinstance(s, TemplateBlock) and s.kind() == kind:
                    self.sub_blocks.remove(s)
                elif isinstance(s, ParseBlock):
                    s.remove_templates_of_kind(kind)

    def add_block(self, block):
        if self.sub_blocks and self.sub_blocks[-1].is_open:
            return self.sub_blocks[-1].add_block(block)

        # NOTE: HTML tag handling in Wikitext can be done in multiple ways.
        # The best approach varies depending on the situation.  When parsing
        # for LaTeX, unknown tags should generally just be hidden.  When
        # attempting to re-create the Wikitext, they should generally just
        # be repeated.  Some amount of detection of hostile tags is necessary.
        # 
        # TLDR: For LaTex, you should uncomment everything.
        if block == "&nbsp;":
            self.sub_blocks.append(TextBlock(" "))
        #elif block in ("<br>", "<br />", "<br/>"):
        #    self.sub_blocks.append(DebugBlock("\n\n"))
        elif isinstance(block, ParseBlock):
            self.sub_blocks.append(block)
        elif block.startswith("<ref"):
            self.sub_blocks.append(ReferenceBlock(block))
        elif block.startswith("<!--"):
            self.sub_blocks.append(CommentBlock(block))
        elif block in ("<sub>", "</sub>", "<sup>", "</sup>", "<math>", "</math>"):
            self.sub_blocks.append(HTMLTagBlock(block))
        #elif block in ("<noinclude>", "</noinclude>", "<small>", "</small>"):
        #    pass
        elif block == "{|":
            self.sub_blocks.append(TableBlock())
            self.sub_blocks[-1].is_open = True
        elif block == "[[":
            self.sub_blocks.append(LinkBlock())
            self.sub_blocks[-1].is_open = True
        elif block == "{{":
            self.sub_blocks.append(TemplateBlock())
            self.sub_blocks[-1].is_open = True
        elif block == "'''":
            self.sub_blocks.append(BoldBlock())
        elif block == "''":
            self.sub_blocks.append(ItalicBlock())
        elif block == "'''''":
            self.sub_blocks.append(BoldItalicBlock())
        elif block.startswith("=="):
            self.sub_blocks.append(HeadingBlock(block))
        elif block == " ":  # CLEANUP: make all words textblock
            self.sub_blocks.append(TextBlock(block))
        else:
            self.sub_blocks.append(DebugBlock(block))

    def __repr__(self):
        if not self.sub_blocks:
            return ""
        return ''.join([repr(x) for x in self.sub_blocks])

    def wiki(self):
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            return ''.join([x.wiki() for x in self.sub_blocks])
        elif hasattr(self, "text"):
            return self.text
        else:
            print("Possible error, blank section.")
            return ""

    def wigfmt(self):
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            return ''.join([x.wigfmt() for x in self.sub_blocks])
        else:
            return self.wiki()

    def to_text(self):
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            return ''.join([x.to_text() for x in self.sub_blocks])
        elif hasattr(self, "text"):
            return self.text
        print("Error on type ", type(self))
        raise "Unhandled Text"

    def latex(self, state=None):
        if state is None:
            state = LatexRenderState()
        if hasattr(self, "sub_blocks") and self.sub_blocks:
            return ''.join([x.latex(state) for x in self.sub_blocks])
        elif hasattr(self, "text"):
            return self.text
        print("Error on type ", type(self))
        raise "Unhandled Text"


class DocumentBlock(ParseBlock):
    """Entry point."""
    pass

class DebugBlock(ParseBlock):
    def __init__(self, text):
        self.text = text
        self.is_open = False

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        if self.text == other:
            return True
        return False

    def to_text(self):
        return self.text

    def latex(self, state):
        if self.text == "&":
            return "\\&"
        if self.text == "#":
            return "\\#"
        if self.text == "$":
            return "\\$"
        if self.text == "%":
            return "\\%"
        if self.text == '"':
            return "\\texttt{\"}"
        if self.text == "–":  # non-ascii hyphen
            return "-"
        if not state.math_mode:
            if self.text == "_":
                return "\\_"
            if self.text == "~":
                return "\\textasciitilde{}"
            if self.text == "^":
                return "\\textasciicircum{}"
            if self.text == "\\":
                return "\\textbackslash{}"
        return self.text


class TextBlock(ParseBlock):
    def __init__(self, text):
        self.text = text
        self.is_open = False
        self.sub_blocks = None

    def __repr__(self):
        return self.text

    def __eq__(self, other):
        if self.text == other:
            return True
        return False

    def to_text(self):
        return self.text

    def latex(self, state):
        if self.text == "&ndash;" or self.text == "&mdash;" or self.text == "&minus;":
            return "-"
        if self.text == "&sdot;":
            return "$\\cdot{}$"
        if self.text == "&times;":
            return "*"
        if self.text == "&deg;":
            if state.math_mode:
                return "^{\circ}"
            else:
                return "\\textdegree{}"
        if self.text.startswith("&"):
            if self.text.endswith(";"):
                print("Must handle:", self.text)
            return "\\" + self.text
        return self.text


class HTMLTagBlock(ParseBlock):
    def __init__(self, text):
        self.text = text
        self.is_open = False

    def __repr__(self):
        return self.text
    def wiki(self):
        return self.text
    def wigfmt(self):
        return self.text
    def to_text(self):
        return self.text

    def latex(self, state):
        if self.text == "<sub>":
            return "\\textsubscript{"
        elif self.text == "</sub>":
            return "}"
        elif self.text == "<sup>":
            return "\\textsuperscript{"
        elif self.text == "</sup>":
            return "}"
        elif self.text == "<math>":
            state.math_mode = True 
            return "$"
        elif self.text == "</math>":
            state.math_mode = False
            return "$"
        else:
            print(self.text)
            raise("Unhandled tag")


class WikiBlock(ParseBlock):
    """Only for documenting inheritence."""
    pass

class HeadingBlock(WikiBlock):
    def __init__(self, block):
        self.sub_blocks = []
        self.is_open = True
        self.level = len(block)

    def add_block(self, block):
        if self.sub_blocks and isinstance(self.sub_blocks[-1], ParseBlock) and self.sub_blocks[-1].is_open:
            return self.sub_blocks[-1].add_block(block)

        if block == ("=" * (self.level)):
            self.is_open = False
            return
        else:
            super().add_block(block)

    def wiki(self):
        tag = "=" * self.level
        return tag + ''.join([x.wiki() for x in self.sub_blocks]) + tag

    def wigfmt(self):
        tag = "=" * self.level
        return tag + ''.join([x.wigfmt() for x in self.sub_blocks]) + tag

    def to_text(self):
        tag = "=" * self.level
        return tag + ''.join([x.to_text() for x in self.sub_blocks]) + tag


class LinkBlock(WikiBlock):
    def add_block(self, block):
        if block == "\n\n":  # Mal-formed; close block at paragraph break
            self.is_open = False
            self.malformed = True
            return
        if self.sub_blocks and isinstance(self.sub_blocks[-1], ParseBlock) and self.sub_blocks[-1].is_open:
            return self.sub_blocks[-1].add_block(block)

        if block == "]]":
            self.is_open = False
            return
        else:
            super().add_block(block)

    def __repr__(self):
        return "[[%s]]" % ''.join([repr(x) for x in self.sub_blocks])

    def anchor(self):
        if "|" in self.sub_blocks:
            idx = self.sub_blocks.index("|")
            anchor = "".join([str(x) for x in self.sub_blocks[:idx]])
        else:
            anchor = "".join([str(x) for x in self.sub_blocks])
        if len(anchor) == 0:  # CLEANUP: should return "None" and be handled by callers
            return ""
        anchor = anchor[0].upper() + anchor[1:]
        return anchor

    def linktext(self):
        if len(self.sub_blocks) == 1:
            return str(self.sub_blocks[0])
        if "|" not in self.sub_blocks:
            text = "".join([str(x) for x in self.sub_blocks])
            return text
        idx = self.sub_blocks.index("|")
        linktext = "".join([str(x) for x in self.sub_blocks[idx+1:]])
        return linktext

    def wiki(self):
        return "[[" + ''.join([x.wiki() for x in self.sub_blocks]) + "]]"

    def wigfmt(self):
        return "[[" + ''.join([x.wigfmt() for x in self.sub_blocks]) + "]]"

    def to_text(self):
        if str(self.sub_blocks[0]).startswith("File:"):
            return ""
        if str(self.sub_blocks[0]).startswith("Image:"):
            return ""
        elif len(self.sub_blocks) == 1:
            if isinstance(self.sub_blocks[0], ParseBlock):
                return self.sub_blocks[0].to_text()
            else:
                return self.sub_blocks[0]
        else:
            if "|" not in self.sub_blocks:
                text = "".join([str(x) for x in self.sub_blocks])
                return text
            idx = self.sub_blocks.index("|")
            linktext = "".join([str(x) for x in self.sub_blocks[idx+1:]])
            return linktext

    def latex(self, state):
        if str(self.sub_blocks[0]).startswith("File:"):
            return ""
        if str(self.sub_blocks[0]).startswith("Image:"):
            return ""
        if len(self.sub_blocks) == 1:
            linktext = strtex(self.sub_blocks[0], state)
        elif "|" not in self.sub_blocks:
            linktext = "".join([strtex(x, state) for x in self.sub_blocks])
        else:
            idx = self.sub_blocks.index("|")
            linktext = "".join([strtex(x, state) for x in self.sub_blocks[idx+1:]])
        return "\emph{" + linktext + "}"


class TemplateBlock(WikiBlock):
    """Templates.

    Templates consist of a name, followed by a series of pipe (the "|" character)
    separated arguments.  These are sometimes of the key=value type, and sometimes
    are positional arguments.
    """
    def __init__(self, *args, **kwargs):
        self._kind = None
        self._kind_was_lowercase = False
        self._kind_trailing_whitespace = ""
        self.arguments = []
        self.is_parsed = False
        self.rewrite = False
        super(TemplateBlock, self).__init__(*args, **kwargs)

    def add_block(self, block):
        if (self.sub_blocks and isinstance(self.sub_blocks[-1], ParseBlock)
                and self.sub_blocks[-1].is_open):
            return self.sub_blocks[-1].add_block(block)

        if block == "}}":
            self.is_open = False
            return
        else:
            super().add_block(block)
        if not self.is_open:
            self.parse()

    def parse(self):
        if self.is_open:
            raise Exception("Template block incorrectly open.")

        # Split the block by "|"
        blocks = [list(g) for k, g in itertools.groupby(self.sub_blocks, lambda x: x=="|")
                  if not k]

        # We upper-case the first letter, keep the rest as written.
        self._kind = "".join(str(x) for x in blocks[0])
        if self._kind[0] != self._kind[0].upper():
            self._kind_was_lowercase = True
        if len(self._kind) != len(self._kind.rstrip()):
            self._kind_trailing_whitespace = self._kind[len(self._kind.rstrip()):]
        self._kind = self._kind[0].upper() + self._kind[1:]
        self._kind = self._kind.strip()
        self.arguments = blocks[1:]
        self.arg_dict = {}
        self.positional_args = []
        for x in self.arguments:
            if "=" in x:
                idx = x.index("=")
                key = "".join(str(xx) for xx in x[:idx]).strip()
                value = x[idx+1:]
                self.arg_dict[str(key)] = value
            else:
                # positional argument
                self.positional_args.append(x)
        self.is_parsed = True

    def has_param(self, key):
        if not self.is_parsed:
            self.parse()
        return key in self.arg_dict

    def get_param(self, key):
        if not self.is_parsed:
            self.parse()
        return "".join(str(x) for x in self.arg_dict[key])  # or raise KeyError

    def set_param(self, key, value):
        if value is None:
            if key in self.arg_dict:
                del self.arg_dict[key]
        else:
            self.arg_dict[key] = [TextBlock(value)]
        self.rewrite = True

    def remove_templates_of_kind(self, kind):
        for k, v in self.arg_dict.items():
            for sub_block in v[:]:
                if isinstance(sub_block, TemplateBlock):
                    if sub_block.kind() == kind:
                        v.remove(sub_block)
                        self.rewrite = True
                    else:
                        self.rewrite = sub_block.remove_templates_of_kind(kind)
        for block_group in self.positional_args:
            for sub_block in block_group[:]:
                if isinstance(sub_block, TemplateBlock):
                    if sub_block.kind() == kind:
                        block_group.remove(sub_block)
                        self.rewrite = True
                    else:
                        self.rewrite = sub_block.remove_templates_of_kind(kind)
        return self.rewrite

    def sections(self):
        if self.is_parsed:
            return self.arguments
        self.parse()
        return self.arguments

    def kind(self):
        if self.is_parsed:
            return self._kind
        self.parse()
        return self._kind

    def to_text(self):
        if self.rewrite:
            raise Exception("set_param not yet compatible with latex")
        return "{{" + ''.join([x.to_text() for x in self.sub_blocks]) + "}}"

    def wiki(self):
        if not self.is_parsed:
            self.parse()
        out = "{{"
        if self._kind_was_lowercase:
            out += self._kind[0].lower() + self._kind[1:]
        else:
            out += self._kind
        out += self._kind_trailing_whitespace
        if self.rewrite:
            # Use arg_dict
            for key, value in self.arg_dict.items():
                out += "|" + key + "=" + "".join([x.wiki() for x in value])
            for block in self.positional_args:
                out += "|" + "".join([x.wiki() for x in block])
        else:
            if self.arguments:
                out += "|"
                out += "|".join([''.join([y.wiki() for y in x]) for x in self.arguments])
        out += "}}"
        return out

    def wigfmt(self):
        if self.rewrite:
            raise Exception("set_param not yet compatible with latex")
        return "{{" + ''.join([x.wigfmt() for x in self.sub_blocks]) + "}}"

    def latex(self, state):
        if self.rewrite:
            raise Exception("set_param not yet compatible with latex")
        joined_body = "".join([strtex(x, state) for x in self.sub_blocks])
        split_body = joined_body.split("|")
        if self.kind() == "Lang":
            return split_body[2]
        if self.kind() == "Nihongo":
            return "%s (%s)" % (split_body[1], split_body[2])
        if self.kind() == "Convert":
            # handle "2 to 4"
            if split_body[2] == "to":
                return "%s-%s %s" % (split_body[1], split_body[3], split_body[4])
            else:
                return "%s %s" % (split_body[1], split_body[2])
        if self.kind() == "As of":
            return "as of %s" % split_body[1]
        if self.kind() == "Sc" and len(split_body) == 2:
            return "\textsc{%s}" % split_body[1]
        return ''.join([x.latex(state) for x in self.sub_blocks])


class BoldBlock(WikiBlock):
    def wiki(self):
        return "'''"
    def wigfmt(self):
        return "'''"
    def to_text(self):
        return ""
    def latex(self, state):
        return ""

class ItalicBlock(WikiBlock):
    def wiki(self):
        return "''"
    def wigfmt(self):
        return "''"
    def to_text(self):
        return ""
    def latex(self, state):
        return ""

class BoldItalicBlock(WikiBlock):
    def wiki(self):
        return "'''''"
    def wigfmt(self):
        return "'''''"
    def to_text(self):
        return ""
    def latex(self, state):
        return ""

class CommentBlock(ParseBlock):
    def wiki(self):
        return "".join([str(x) for x in self.sub_blocks])
    def wigfmt(self):
        return ""
    def to_text(self):
        return ""
    def latex(self, state):
        return ""
    def __repr__(self):
        return "".join(self.sub_blocks)


class TableBlock(WikiBlock):
    def add_block(self, block):
        if self.sub_blocks and isinstance(self.sub_blocks[-1], ParseBlock) and self.sub_blocks[-1].is_open:
            return self.sub_blocks[-1].add_block(block)

        if block == "|}":
            self.is_open = False
            return
        else:
            super().add_block(block)

    def wiki(self):
        return "{|" + ''.join([x.wiki() for x in self.sub_blocks]) + "|}"

    def wigfmt(self):
        return "{|" + ''.join([x.wigfmt() for x in self.sub_blocks]) + "|}"


class ReferenceBlock(WikiBlock):
    def __init__(self, block):
        if block == "<ref>":
            self.is_open = True
            self.sub_blocks = []
            self.details = None
            return
        elif block.endswith("/>"):  # Single tag
            self.is_open = False
            self.details = TextBlock(block)
            self.sub_blocks = None
            return
        else:
            self.is_open = True
            self.details = TextBlock(block[5:-1])
            self.sub_blocks = []
            return

    def add_block(self, block):
        if block == "</ref>":
            self.is_open = False
            return
        if self.sub_blocks and isinstance(self.sub_blocks[-1], ParseBlock) and self.sub_blocks[-1].is_open:
            return self.sub_blocks[-1].add_block(block)
        else:
            super().add_block(block)

    def to_text(self):
        return ""

    def wiki(self, extra_line_breaks=False):
        if not self.sub_blocks:  # single-tag
            if not self.details:
                return "<ref></ref>"  # degenerate case
            return self.details.wiki()
        if self.details:
            open_tag = "<ref " + self.details.wiki() + ">"
        else:
            open_tag = "<ref>"
        body = ''.join([x.wiki() for x in self.sub_blocks])
        if extra_line_breaks:
            return open_tag + "\n" + body + "\n</ref>"
        else:
            return open_tag + body + "</ref>"

    def wigfmt(self):
        return self.wiki(extra_line_breaks=True)

    def latex(self, state):
        return ""

def strtex(x, state):
    if hasattr(x, "latex"):
        return x.latex(state)
    return str(x)
