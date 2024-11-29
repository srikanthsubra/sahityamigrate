import datetime
import re
import os.path
import sys

from pyparsing import *
from pprint import pprint


# ====================== StanzaList ======================

# --- StanzaList: Grammar ----

# Stanza: Define structure
pat_number = Word(nums)
stanza_start = Literal("<stanza>").suppress() | Suppress(Literal("<stanza") + Literal("num=") + Optional("\"") + Optional(pat_number) + Optional ("\"") + Literal(">"))
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

re_numeric = re.compile(r'^\d+\.\s*')
def paras(text):
    clean = lambda p: re_numeric.sub("", p.strip() + "\n")
    return [clean(p) for p in text.split("\n\n")]

def replace_sup(text):
    pat_sup_open = Suppress("<sup>")
    pat_sup_close = Suppress("</sup>")
    pat_word = Word(alphas)

    # Define a pattern for <sup>number</sup> followed by a word
    pat_bad_sup = Combine(pat_sup_open + pat_number("num") + pat_sup_close + pat_word("word"))
    pat_good_sup = Combine(pat_word("word") + pat_sup_open + pat_number("num") + pat_sup_close)
    pat_sup = pat_bad_sup | pat_good_sup

    # Define how to replace the matched pattern
    def replace_sup_to_brackets(tokens):
        return f"{tokens.word}[{tokens.num}]"

    # Set parse action
    pat_sup.set_parse_action(replace_sup_to_brackets)

    # Process the whole string to replace all occurrences
    result = pat_sup.transform_string(text)
    return result

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

    def is_translated(self):
        return bool(self.translation.strip())

    def __repr__(self):
        return "<Stanza>:" + str(self.__dict__)

    @classmethod
    def from_text(cls, sahityam, words, translation):
        return cls([{
            "sahityam": sahityam,
            "words": words,
            "translation": translation,
        }])


    def to_new(self):
        if len(paras(self.sahityam)) > 1 and len(paras(self.words)) > 1:
            # Convert into a StanzaList
            stanlist = StanzaList.from_text(self.sahityam, self.words, self.translation)
            return stanlist.to_new()

        self.sahityam = replace_sup(self.sahityam)
        self.sahityam = self.sahityam.replace('\n', '   \n')
        ## replace('<sup>', '[').replace('</sup>', ']') \
        self.words = replace_sup(self.words)
        self.words = self.words.replace('((', '![') \
            .replace('))', ')').replace(' "', '](means "') \
            .replace('\n', '   \n')  if self.words else ""
            ##.replace('<sup>', '[').replace('</sup>', ']') \
        return TEMPL_STANZA.format(self.sahityam, self.words, self.translation, "\n".join(self.appendix))

class AsLister:
    def __init__(self, mylist):
        self.list = mylist

    def as_list(self):
        return self.list

class StanzaList:
    def __init__(self, tokens):
        self.stanzas = tokens.as_list()

    def append(self, index, line):
        self.stanzas[index].append(line)

    def get_line(self, stanza, index):
        return self.stanzas[stanza].get_line(index)

    def is_translated(self):
        return any(s.is_translated() for s in self.stanzas)

    def __repr__(self):
        return "<StanzaList>:" + repr(self.stanzas)

    def to_new(self):
        return "".join([s.to_new() for s in self.stanzas])

    @classmethod
    def from_text(cls, sahityam, words, translation):
        stanlist = []
        for s, w, t in zip(paras(sahityam), paras(words), paras(translation)):
            stanlist.append(Stanza.from_text(s, w, t))
        return cls(AsLister(stanlist))


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

    def is_translated(self):
        return self.stanza_list.is_translated()

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

    def is_translated(self):
        return any(sec.is_translated() for sec in self.sections)

    def to_new(self):
        self.append(0, 0, "<!--more-->")
        return "".join([s.to_new() for s in self.sections])

lyric_section.set_parse_action(LyricSection)
lyric_section_list.set_parse_action(LyricSectionList)

# ====================== ProseSectionList ======================

# --- ProseSection: Grammar ----
category = Literal("[[Category:").suppress() + Word(alphanums+" ")("category") + Literal("]]").suppress()

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

## Sahityam
"""

map_hk = {
    "Tyagaraja": "tyAgarAja",
    "Kriti": "kRti",
    "Telugu": "telugu",
    "Adi": "Adi",
    "Rupakam": "rUpaka",
}

def to_hk(val):
    return map_hk.get(val, val)

class CategoryList:
    def __init__(self, tokens):
        self.categories = tokens.as_list()
        if len(self.categories) < 5:
            raise ValueError("Too few categories: {}".format(self.categories))
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
            "raga": self.raga,
            "tala": self.tala,
            "composer": self.composer,
            "language": self.language,
            "composition": self.format,
        })

category_list.set_parse_action(CategoryList)

# ====================== Song ======================
pat_draft = Optional(Literal("{{draft}}"))
song = pat_draft("is_draft") + Literal("==Lyrics==").suppress() + lyric_section_list("lyrics_area") + prose_section_list("prose_area") + category_list("header_area") + notoc

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
        self.is_draft = parsed.get("is_draft")

    def set_old_filename(self, filename):
        self.old_file = filename
        self.new_file = self.old_file.replace('_', '-').lower()[:-4]
        self.form_title()

    def form_title(self):
        first_line = self.lyrics_area.get_line(0, 0, 0)
        self.title = form_title(self.new_file, first_line)

    def is_translated(self):
        return self.lyrics_area.is_translated()

    def __repr__(self):
        return "\n".join(["{}: {}".format(k, v) for k, v in self.__dict__.items()])

    def to_new(self):
        self.header_area.set_title(self.title)
        return TEMPL_SONG.format(**{
            "header_area": self.header_area.to_new(),
            "lyrics_area": self.lyrics_area.to_new(),
            "prose_area": self.prose_area.to_new(),
        })

song.set_parse_action(Song)


def form_title(filename, first_line):
    return first_line[:len(filename)].strip()


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

data_combined = """\
<stanza>
1. pavamAna sutuDu paTTu
<sup>1</sup>pAdAravindamulaku (nI)

2. paGkajAkSi nelakonna-
yaGga<sup>2</sup> yugamunaku (nI)

3. nava muktA hAramulu
naTiyiJcEyuramunaku (nI)

4. naLinAri kEru ciru
navvu gala mOmunaku (nI)

5. prahlAda nAradAdi bhaktulu
<sup>3</sup>pogaDucuNDE (nI)

6. rAjIva nayana tyAgarAja
vinutamaina (nI)
-details-
1. ((pavamAna-sutuDu "Anjaneya - son of Wind God")) ((paTTu "held")) ((pAda "feet"))-((aravindamulaku "to the Lotus")) (nI)


2. ((paGkaja-akSi "Sita - Lotus Eyed")) ((nelakonna "seated"))-((aGga "thighs - part of body - limb")) ((yugamunaku "to the pair")) (nI)


3. ((nava "new - fresh")) ((muktA "pearl")) ((hAramulu "necklaces")) ((naTiyiJcE "dangling - dancing"))-((uramunaku "to the chest - bosom")) (nI)


4. ((naLina-ari "Moon - enemy of Lotus")) ((kEru "deriding")) ((ciru-navvu-gala "smiling")) ((mOmunaku "to the face")) (nI)


5. prahlAda nArada-((Adi "and other")) ((bhaktulu "devotees")) ((pogaDucuNDE "ever extolling")) (nI)


6. ((rAjIva "Lotus")) ((nayana "Eyed")) tyAgarAja ((vinutamaina "praised by")) (nI)
-meaning-
1. May there ever be victory and prosperity – to the Lotus Feet held by Anjaneya – son of Wind God and to Your name and form!

2. May there ever be victory and prosperity - to the pair of thighs where Sita – the Lotus Eyed - is seated and to Your name and form!

3. May there ever be victory and prosperity - to Your broad chest wherein dangles new pearl necklaces and to Your name and form!

4. May there ever be victory and prosperity - to the smiling face that derides the Moon – the enemy of Lotus - and to Your name and form!

5. May there ever be victory and prosperity to Your name and form which are ever extolled by Prahlada, Narada and other devotees!

6. O Lotus Eyed! May there ever be victory and prosperity to Your name and form which are praised by this Thyagaraja!
</stanza>
"""

def test_song(data):
    result = song.parse_string(data)
    obj_song = result.as_list()[0]
    obj_song.set_old_filename("Nadopasanace.txt")
    print(obj_song.to_new())

def test_combined(data):
    result = stanza.parse_string(data)
    obj_stanza = result.as_list()[0]
    print(obj_stanza.to_new())

def parse_and_convert(file_path):
    filename = file_path.rsplit("/")[-1]
    with open(file_path) as f:
        old = f.read()
        result = song.parse_string(old)
        obj_song = result.as_list()[0]
        obj_song.set_old_filename(filename)

        return obj_song

if __name__ == '__main__':
    ##test_combined(data_combined)
    filename = sys.argv[-1]
    base_path = "/Users/srikanth/Code/sahityam/songs/"
    file_path = os.path.join(base_path, filename)
    print(parse_and_convert(file_path).to_new())
