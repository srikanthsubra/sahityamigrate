from pyparsing import *

# --- Renditions section ---

pat_sahityam_header = Literal("## Sahityam")
pat_prose_header = Group(Literal("##") + Word(alphanums+" "))
pat_renditions_header = Literal("## Renditions").suppress()

pat_head = SkipTo(pat_sahityam_header)
pat_sahityam_section = pat_sahityam_header.suppress() + (SkipTo(Literal("## Variations")) | SkipTo(Literal("## Commentary")))
pat_middle = SkipTo(pat_renditions_header) | SkipTo(StringEnd())
pat_renditions_section = pat_renditions_header + Group(SkipTo(pat_prose_header) | SkipTo(StringEnd()))("renditions")
pat_tail = Optional(SkipTo(StringEnd()))("tail")

##`pat_song = Group(pat_head) + Group(pat_sahityam_section)("sahityam") + pat_renditions_section + Group(pat_tail)("tail")
pat_song = Group(pat_head)("head") + Group(pat_sahityam_section)("sahityam") + Optional(Group(pat_middle))("middle") + pat_renditions_section

class Song:
    def __init__(self, head, sahityam, middle, renditions, tail):
        self.head = head
        self.obj_head = Head.from_string(head)
        self.sahityam = sahityam
        self.middle = middle
        self.renditions = renditions
        self.tail = tail

    def raga(self, normalized=True):
        r = self.obj_head.rAga
        return r.replace("z", "s").lower() if normalized else r

    @classmethod
    def from_tokens(cls, tokens):
        parsed = tokens.as_dict()
        return cls(parsed.get("head")[0], "".join(parsed.get("sahityam")), parsed.get("middle")[0][0], parsed.get("renditions"), "")

    def is_valid(self):
        return "{{<youtube" in self.renditions

    def set_renditions(self, updated):
        self.renditions = updated

    def to_new(self):
        return """{}
## Sahityam

{}
## Renditions
{}
{}
{}\n""".format(self.head, self.sahityam, self.renditions, self.middle, self.tail)

pat_song.set_parse_action(lambda t: Song.from_tokens(t))

class Head:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def from_string(cls, string):
        kvp = {}
        for line in string.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                kvp[k] = v

        return cls(**kvp)


def parse(file_path):
    with open(file_path) as f:
        text = f.read()
        song = pat_song.parse_string(text)
        return song
