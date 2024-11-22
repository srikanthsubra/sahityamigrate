import datetime
import os.path
import sys

from pyparsing import *
from pprint import pprint


# ====================== StanzaList ======================

# --- StanzaList: Grammar ----

# Stanza: Define structure
stanza_start = Literal("<stanza>").suppress()
details_start = Literal("-details-").suppress()
meaning_start = Literal("-meaning-").suppress()
stanza_end = Literal("</stanza>").suppress()

# Stanza: Define content 
sahityam_content =  SkipTo(Literal("-details-")) | SkipTo(Literal("-meaning-")) | SkipTo(Literal("</stanza>")) 
details_content = SkipTo(Literal("-meaning-")) | SkipTo(Literal("</stanza>")) 
meaning_content = SkipTo(Literal("</stanza>")) 

# Stanza: Put it all together
stanza = Group(
    stanza_start +
    sahityam_content("sahityam") +
    Optional(details_start + details_content("words")) +
    Optional(meaning_start + meaning_content("translation")) +
    stanza_end
)

stanza_list = ZeroOrMore(stanza)

# ---- StanzaList: Object Representation ----

TEMPL_STANZA = """\
{{{{<stanza>}}}}
{}-details-
{}-meaning-
{}{{{{</stanza>}}}}
{}
"""

class Stanza:
    def __init__(self, tokens):
        token = tokens[0] # Since Group() was used in stanza grammar def
        self.sahityam = token.get("sahityam", "")
        self.words = token.get("words", "")
        self.translation = token.get("translation", "")
        self.appendix = []

    def append(self, line):
        self.appendix.append(line)

    def get_line(self, index):
        return self.sahityam.splitlines()[index]

    def __repr__(self):
        return "<Stanza>:" + str(self.__dict__)
        
    def to_new(self):
        self.sahityam = self.sahityam.replace('<sup>', '[').replace('</sup>', ']') \
            .replace('\n', '   \n')
        self.words = self.words.replace('((', '![') \
            .replace('))', ')').replace(' "', '](means "') \
            .replace('<sup>', '[').replace('</sup>', ']') \
            .replace('\n', '   \n')  if self.words else ""
        return TEMPL_STANZA.format(self.sahityam, self.words, self.translation, "\n".join(self.appendix))

class StanzaList:
    def __init__(self, tokens):
        self.stanzas = tokens.as_list()

    def append(self, index, line):
        self.stanzas[index].append(line)

    def get_line(self, stanza, index):
        return self.stanzas[stanza].get_line(index)

    def __repr__(self):
        return "<StanzaList>:" + repr(self.stanzas)

    def to_new(self):
        return "".join([s.to_new() for s in self.stanzas])


stanza.set_parse_action(Stanza)
stanza_list.set_parse_action(StanzaList)

# ====================== LyricSectionList ======================

# --- LyricSectionList: Grammar ----
section_header = Literal("===").suppress() + Word(alphanums+" ")("header") + Literal("===").suppress()
lyric_section = Group(section_header + stanza_list)

lyric_section_list = OneOrMore(lyric_section)

# --- LyricSectionList: Object Representation ----

TEMPL_LYRICSECTION = """\
### {}
{}
"""

class LyricSection:
    def __init__(self, tokens):
        token = tokens[0] # Since Group() was used in lyric_section grammar def
        self.header = token.as_list()[0]
        self.stanza_list = token.as_list()[1]

    def __repr__(self):
        return str(self.__dict__)

    def append(self, stanza, line):
        self.stanza_list.append(stanza, line)

    def get_line(self, stanza, index):
        return self.stanza_list.get_line(stanza, index)

    def to_new(self):
        return TEMPL_LYRICSECTION.format(self.header, self.stanza_list.to_new())
        

class LyricSectionList:
    def __init__(self, tokens):
        self.sections = tokens.as_list()

    def __repr__(self):
        return ",".join([repr(s) for s in self.sections])

    def append(self, section, stanza, line):
        self.sections[section].append(stanza, line)

    def get_line(self, section, stanza, index):
        return self.sections[section].get_line(stanza, index)

    def to_new(self):
        self.append(0, 0, "<!--more-->")
        return "".join([s.to_new() for s in self.sections])

lyric_section.set_parse_action(LyricSection)
lyric_section_list.set_parse_action(LyricSectionList)

# ====================== ProseSectionList ======================

# --- ProseSection: Grammar ----
category = Literal("[[Category:").suppress() + Word(alphanums)("category") + Literal("]]").suppress()

prose_header = Literal("==").suppress() + Word(alphanums)("header") + Literal("==").suppress()
prose_section = prose_header + Group(SkipTo(prose_header) | SkipTo(category))("prose_content") 
prose_section_list = OneOrMore(prose_section)

# --- ProseSection: Object Representation ----
TEMPL_PROSESECTION = """\
## {}
{}
"""

class ProseSection:
    def __init__(self, tokens):
        self.header = tokens.header
        self.content = tokens.prose_content

    def __repr__(self):
        ##return "%s: %s" % (self.header, self.prose_content)
        return "\n" + ", ".join(["{}: {}".format(str(k), str(v)) for k, v in self.__dict__.items()])

    def to_new(self):
        content = "\n".join([p.replace('<sup>', '{{<sup ') \
                           .replace('</sup>', '>}}') \
                           .replace('**', '  * ') \
                           .replace('<lipi>', '{{<lipi>}}') \
                           .replace('</lipi>', '{{</lipi>}}') \
                           .replace('\\t', ' ') for p in self.content])
        return TEMPL_PROSESECTION.format(self.header, content)

class ProseSectionList:
    def __init__(self, tokens):
        self.sections = tokens.as_list()

    def __repr__(self):
        return ",".join([repr(s) for s in self.sections])

    def to_new(self):
        return "".join([s.to_new() for s in self.sections])

prose_section.set_parse_action(ProseSection)
prose_section_list.set_parse_action(ProseSectionList)

# ====================== CategoryList ======================

# --- CategoryList: Grammar ----
category_list = OneOrMore(category)
notoc = Literal("__NOTOC__").suppress()
footer = category_list + notoc

# --- CategoryList: Object Representation ----
TEMPL_HEADER = """\
---
title: {title}
date: {date}
rAga: {raga}
tAla: {tala}
composer: {composer}
language: {language}
composition: {composition}
---
"""

map_hk = {
    "Tyagaraja": "tyAgarAja",
    "Kriti": "kRti",
    "Telugu": "telugu",
    "Rupakam": "rUpaka",
}

def to_hk(val):
    return map_hk.get(val, val.lower())

class CategoryList:
    def __init__(self, tokens):
        self.categories = tokens.as_list()
        if len(self.categories) < 5:
            raise ValueError("Too few categories")
        self.raga = self.categories[0]
        self.tala = self.categories[1]
        self.composer = self.categories[2]
        self.language = self.categories[3]
        self.format = self.categories[4]
        self.title = ""

    def set_title(self, title):
        self.title = title

    def __repr__(self):
        return str(self.__dict__)

    def to_new(self):
        return TEMPL_HEADER.format(**{
            "title": self.title,
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "raga": self.raga.lower(),
            "tala": to_hk(self.tala),
            "composer": to_hk(self.composer),
            "language": to_hk(self.language),
            "composition": to_hk(self.format),
        })

category_list.set_parse_action(CategoryList)

# ====================== Song ======================
song = Literal("==Lyrics==").suppress() + lyric_section_list("lyrics_area") + prose_section_list("prose_area") + category_list("header_area") + notoc

TEMPL_SONG ="""\
{header_area}
{lyrics_area}{prose_area}
"""

class Song:
    def __init__(self, tokens):
        parsed = tokens.as_dict()
        self.header_area = parsed.get("header_area")
        self.lyrics_area = parsed.get("lyrics_area")
        self.prose_area = parsed.get("prose_area")
        self.old_file = ""
        self.new_file = ""
        self.title = ""

    def set_old_filename(self, filename):
        self.old_file = filename
        self.new_file = self.old_file.replace('_', '-').lower()[:-4]

    def form_title(self):
        first_line = self.lyrics_area.get_line(0, 0, 0)
        self.title = form_title(self.new_file, first_line)
        self.header_area.set_title(self.title)
        
    def __repr__(self):
        return "\n".join(["{}: {}".format(k, v) for k, v in self.__dict__.items()])

    def to_new(self):
        self.form_title()
        return TEMPL_SONG.format(**{
            "header_area": self.header_area.to_new(),
            "lyrics_area": self.lyrics_area.to_new(),
            "prose_area": self.prose_area.to_new(),
        })

song.set_parse_action(Song)


def form_title(filename, first_line):
    return first_line[:len(filename)]


# - Tests - 

def test_stanza_list(data):
    result = stanza_list.parse_string(data)
    pprint(result.as_list())
    print(result[0].to_new())

data_lyrics = """
===Pallavi===
<stanza>
nAdOpAsanacE<sup>1</sup> zaGkara 
nArAyaNa vidhulu velasiri O manasA
-details-
((nAdOpAsanacE "by worship of Nada"))<sup>1</sup> zaGkara nArAyaNa ((vidhulu "and Brahma")) ((velasiri "became effulgent")) O ((manasA "Mind"))
-meaning-
By meditation on Nada, the Trinity became effulgent, O Mind.
</stanza>

===Anupallavi===
<stanza>
vEdOddhArulu vEdAtItulu 
vizwamella niNDiyuNDE vAralu
-details-
vEda ((uddhArulu "upholders")) vEda ((atItulu "those beyond")) 
((vizwamu-ella "in the whole universe")) ((niNDiyuNDE-vAralu "present throughout"))
-meaning-
(By meditation... became) upholders of the Vedas and
those beyond the Vedas, and are present throughout the whole universe.
</stanza>
"""

def test_lyrics_section_list(data):
    result = lyric_section_list.parse_string(data)
    ##pprint(result.as_list())
    print(result[0].to_new())

data_prose_section = """\
==Variations==
* <sup>2</sup><lipi>manvatramulennO kala vAralu – mantramulenni kala vAralu</lipi>
* <sup>3</sup><lipi>vilOlulu – vilOluru</lipi>
==References==
* The following websites may be visited to find fuller information about ‘Nadopasana’ – [[http://www.ipnatlanta.net/camaga/vidyarthi/Music_Salvation.htm Nadopasana1]] : [[http://www.svbf.org/sringeri/journal/vol1no2/nada.html Nadopasana2] : [[http://www.atributetohinduism.com/Hindu_Music.htm Nadopasana3]]
==Commentary==
* <sup>1</sup><lipi>upAsana - yathA yathA upAsate tathA bhavati</lipi>  - “As you contemplate, so you become.” Please refer to discourse on Brhadaranyaka Upanishad, Chapter 1, 5th Brahmana by Swami Krishnananda – [[http://www.swami-krishnananda.org/brdup_audio/brdup-40.pdf upasana]]
==Renditions==
[[Category:Begada]]
"""

def test_prose_section_list(data):
    result = prose_section_list.parse_string(data)
    print(result[0].to_new())

data_category_list = """\
[[Category:Begada]]
[[Category:Adi]]
[[Category:Tyagaraja]]
[[Category:Telugu]]
[[Category:Kriti]]
"""

def test_category_list(data):
    result = category_list.parse_string(data)
    print(result[0].to_new())

data_song = """
==Lyrics==
===Pallavi===
<stanza>
nAdOpAsanacE<sup>1</sup> zaGkara 
nArAyaNa vidhulu velasiri O manasA
-details-
((nAdOpAsanacE "by worship of Nada"))<sup>1</sup> zaGkara nArAyaNa ((vidhulu "and Brahma")) ((velasiri "became effulgent")) O ((manasA "Mind"))
-meaning-
By meditation on Nada, the Trinity became effulgent, O Mind.
</stanza>

===Anupallavi===
<stanza>
vEdOddhArulu vEdAtItulu 
vizwamella niNDiyuNDE vAralu
-details-
vEda ((uddhArulu "upholders")) vEda ((atItulu "those beyond")) 
((vizwamu-ella "in the whole universe")) ((niNDiyuNDE-vAralu "present throughout"))
-meaning-
(By meditation... became) upholders of the Vedas and
those beyond the Vedas, and are present throughout the whole universe.
</stanza>

===Charanam===
<stanza>
mantrAtmulu yantra tantrAtmulu mari 
manvantramulennO<sup>2</sup> gala vAralu
tantrI laya swara rAga vilOlulu<sup>3</sup> 
tyAgarAja vandyulu swatantrulu
-details-
((mantra-Atmulu "Indwellers of mantras")) ((yantra-tantra-Atmulu "Indwellers of Yantra and Tantra")) ((mari "and")) 
((manvantramulu "aeons"))-((ennO "many"))<sup>2</sup> ((gala-vAralu "having")) 
((tantrI "Chord Instruments")) ((laya "percussion")) swara rAga ((vilOlulu "experts in"))<sup>3</sup>
tyAgarAja ((vandyulu "saluted")) ((swatantrulu "independent - self-regulated"))
-meaning-
(By meditation... became) the Indwellers of mantra, yantra and tantra  
those spanning many aeons, connoisseurs of musical instruments, 
rhythm, swara and raga, 
those saluted by Thyagaraja and self-regulated.
</stanza>

==Variations==
* <sup>2</sup><lipi>manvatramulennO kala vAralu – mantramulenni kala vAralu</lipi>
* <sup>3</sup><lipi>vilOlulu – vilOluru</lipi>
==References==
* The following websites may be visited to find fuller information about ‘Nadopasana’ – [[http://www.ipnatlanta.net/camaga/vidyarthi/Music_Salvation.htm Nadopasana1]] : [[http://www.svbf.org/sringeri/journal/vol1no2/nada.html Nadopasana2] : [[http://www.atributetohinduism.com/Hindu_Music.htm Nadopasana3]]
==Commentary==
* <sup>1</sup><lipi>upAsana - yathA yathA upAsate tathA bhavati</lipi>  - “As you contemplate, so you become.” Please refer to discourse on Brhadaranyaka Upanishad, Chapter 1, 5th Brahmana by Swami Krishnananda – [[http://www.swami-krishnananda.org/brdup_audio/brdup-40.pdf upasana]]
==Renditions==

[[Category:Begada]]
[[Category:Adi]]
[[Category:Tyagaraja]]
[[Category:Telugu]]
[[Category:Kriti]]
__NOTOC__
"""

def test_song(data):
    result = song.parse_string(data)
    obj_song = result.as_list()[0]
    obj_song.set_old_filename("Nadopasanace.txt")
    print(obj_song.to_new())

def parse_and_convert(file_path):
    filename = file_path.rsplit("/")[-1]
    with open(file_path) as f:
        old = f.read()
        result = song.parse_string(old)
        obj_song = result.as_list()[0]
        obj_song.set_old_filename(filename)

        return obj_song.to_new()

if __name__ == '__main__':
    ##test_song(data_song)
    filename = sys.argv[-1]
    base_path = "/Users/srikanth/Code/sahityam/songs/"
    file_path = os.path.join(base_path, filename)
    print(parse_and_convert(file_path))
