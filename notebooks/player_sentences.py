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
    "NaLyssa Smith": ["nalyssa smith", "nalyssa"],
    "Jonquel Jones": ["jonquel jones", "jonquel"],
    "Cameron Brink": ["cameron brink"],
    "Sheryl Swoopes": ["sheryl swoopes", "swoopes"],
    "DeWanna Bonner": ["dewanna bonner", "dewanna", "bonner"],
    "JuJu Watkins": ["juju watkins", "juju"],
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


def players_in(sentence):
    text = sentence.replace("’", "'")
    return sorted({LOOKUP[m.group(1).lower()] for m in NAME_RE.finditer(text)})


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
            # headlines are one sentence each
            for (date, url), head in zip(meta, heads):
                for player in players_in(head):
                    writer.writerow([outlet, date, url, player, 1, head])
                    rows_out += 1
            for (date, url), doc in zip(meta, nlp.pipe(bodies, batch_size=64)):
                for sent in doc.sents:
                    text = sent.text.strip()
                    if len(text) < 15:
                        continue
                    for player in players_in(text):
                        writer.writerow([outlet, date, url, player, 0, text])
                        rows_out += 1
    print(f"wrote {OUT.relative_to(ROOT)} ({rows_out:,} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
