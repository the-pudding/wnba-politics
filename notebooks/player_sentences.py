"""
Every sentence that names one of the featured players, from Fox News and the
comparison outlets (ESPN, CBS Sports, USA Today, Just Women's Sports, The
Athletic). Headlines count as sentences too.

Output: data/player_sentences.csv with one row per (sentence, player):
    outlet, date, url, player, in_headline, sentence

A sentence naming two players appears twice, once per player. Matching is by
name (full name, or an unambiguous surname or first name); pronouns are not
resolved here — see 09-player-words.ipynb for the parsed attachments.

    python3 notebooks/player_sentences.py
"""

import csv
import html
import re
import sys
from pathlib import Path

import spacy

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "player_sentences.csv"

SOURCES = {
    "Fox News": "fox_wnba.csv",
    "ESPN": "espn.csv",
    "CBS Sports": "cbs_sports.csv",
    "USA Today": "usa_today.csv",
    "Just Women's Sports": "just_womens_sports.csv",
    "The Athletic": "the_athletic.csv",
}

ALIASES = {
    "Caitlin Clark": ["caitlin clark", "clark"],
    "Angel Reese": ["angel reese", "reese"],
    "Brittney Griner": ["brittney griner", "griner"],
    "Sophie Cunningham": ["sophie cunningham", "cunningham"],
    "DiJonai Carrington": ["dijonai carrington", "carrington", "dijonai"],
    "Paige Bueckers": ["paige bueckers", "bueckers"],
    "A'ja Wilson": ["a'ja wilson", "aja wilson", "a’ja wilson"],
    "Alyssa Thomas": ["alyssa thomas"],
    "Sue Bird": ["sue bird"],
    "Breanna Stewart": ["breanna stewart", "stewie"],
    "Diana Taurasi": ["diana taurasi", "taurasi"],
    "Chennedy Carter": ["chennedy carter", "chennedy"],
    "Aliyah Boston": ["aliyah boston"],
    "Sabrina Ionescu": ["sabrina ionescu", "ionescu"],
    "Napheesa Collier": ["napheesa collier", "collier", "napheesa"],
    "Natasha Cloud": ["natasha cloud"],
    "Kelsey Plum": ["kelsey plum", "plum"],
    "Candace Parker": ["candace parker"],
    "Kelsey Mitchell": ["kelsey mitchell"],
    "Jonquel Jones": ["jonquel jones", "jonquel"],
    "DeWanna Bonner": ["dewanna bonner", "dewanna", "bonner"],
    "Chelsea Gray": ["chelsea gray"],
    "Arike Ogunbowale": ["arike ogunbowale", "ogunbowale", "arike"],
    "Cameron Brink": ["cameron brink"],
    "Nneka Ogwumike": ["nneka ogwumike", "nneka"],
    "Marina Mabrey": ["marina mabrey", "mabrey"],
    "Jewell Loyd": ["jewell loyd", "loyd"],
    "Lexie Hull": ["lexie hull"],
    "Courtney Vandersloot": ["courtney vandersloot", "vandersloot"],
    "Kahleah Copper": ["kahleah copper", "kahleah"],
}
LOOKUP = {alias: name for name, aliases in ALIASES.items() for alias in aliases}
NAME_RE = re.compile(
    r"\b(" + "|".join(sorted(map(re.escape, LOOKUP), key=len, reverse=True)) + r")\b",
    re.I,
)
# Fox staples promo lines mid-paragraph; the all-caps run defeats the splitter
BOILERPLATE = re.compile(r"CLICK HERE[^a-z]*(?=[A-Z][a-z]|$)")


def clean(text):
    t = html.unescape(str(text or "")).replace("\xa0", " ")
    t = BOILERPLATE.sub(" ", t)
    return re.sub(r"\s+", " ", t).strip()


# a surname shared with someone else in the corpus: when the look-alike is
# named anywhere in the article and the player's own first name is not, a
# bare surname in that article is not her ("Taurasi re-signs in Phoenix
# while Clark heads to Washington" is Alysha Clark)
LOOKALIKES = {
    "Caitlin Clark": (re.compile(r"alysha\W{0,3}clark", re.I), re.compile(r"caitlin", re.I)),
    "Brittney Griner": (re.compile(r"cherelle\W{0,3}griner", re.I), re.compile(r"brittney", re.I)),
    "Napheesa Collier": (re.compile(r"charli\W{0,3}collier", re.I), re.compile(r"napheesa", re.I)),
    "Sophie Cunningham": (re.compile(r"cade\W{0,3}cunningham", re.I), re.compile(r"sophie", re.I)),
    "Breanna Stewart": (re.compile(r"isaiah\W{0,3}stewart", re.I), re.compile(r"breanna", re.I)),
    "Angel Reese": (re.compile(r"arvell\W{0,3}reese", re.I), re.compile(r"angel", re.I)),
}


def ambiguous_in(article_text):
    return {name for name, (lookalike, required) in LOOKALIKES.items()
            if lookalike.search(article_text) and not required.search(article_text)}


def players_in(sentence, ambiguous=frozenset()):
    text = sentence.replace("’", "'")
    found = set()
    for m in NAME_RE.finditer(text):
        alias = m.group(1).lower()
        name = LOOKUP[alias]
        # in an ambiguous article only the full name counts; and a sentence
        # that names the look-alike herself is hers even in a clear article
        if " " not in alias:
            if name in ambiguous:
                continue
            rule = LOOKALIKES.get(name)
            if rule and rule[0].search(text) and not rule[1].search(text):
                continue
        found.add(name)
    return sorted(found)


def main():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    nlp.max_length = 3_000_000
    csv.field_size_limit(10**9)

    rows_out = 0
    with OUT.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["outlet", "date", "url", "player", "in_headline", "sentence"])
        for outlet, file in SOURCES.items():
            path = DATA / file
            if not path.exists():
                print(f"  (no {file})", file=sys.stderr)
                continue
            rows = list(csv.DictReader(path.open()))
            print(f"{outlet}: {len(rows):,} articles", file=sys.stderr)
            seen = set()
            heads, bodies, meta = [], [], []
            for r in rows:
                if r.get("url") in seen:
                    continue
                seen.add(r.get("url"))
                heads.append(clean(r.get("headline")))
                bodies.append(clean(r.get("body")))
                meta.append((r.get("date", ""), r.get("url", "")))
            amb = [ambiguous_in(h + " " + b) for h, b in zip(heads, bodies)]
            # headlines are one sentence each
            for (date, url), head, a in zip(meta, heads, amb):
                for player in players_in(head, a):
                    writer.writerow([outlet, date, url, player, 1, head])
                    rows_out += 1
            for (date, url), doc, a in zip(meta, nlp.pipe(bodies, batch_size=64), amb):
                for sent in doc.sents:
                    text = sent.text.strip()
                    if len(text) < 15:
                        continue
                    for player in players_in(text, a):
                        writer.writerow([outlet, date, url, player, 0, text])
                        rows_out += 1
    print(f"wrote {OUT.relative_to(ROOT)} ({rows_out:,} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
