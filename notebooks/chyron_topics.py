"""How often each cable network's WNBA chyrons touch the piece's topics.

The same vocabulary as the outlet charts (data/topic_terms.csv, via topics.py)
applied to the WNBA banners in data/chyron_matches.tsv. A banner is one line
of a chyron stack; the same line repeated minute after minute counts once per
day and channel. Writes src/data/chyron_topics.json:

    {"years": [...], "networks": [...],
     "topics": {"polrace": {"Fox News": {"2020": {"n": 40, "hits": 9}, ...}, ...}, ...}}

    python3 notebooks/chyron_topics.py
"""
import csv, json, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from topics import patterns

ROOT = Path(__file__).resolve().parents[1]
CHANNEL = {"FOXNEWSW": "Fox News", "CNNW": "CNN", "MSNBCW": "MSNBC", "MSNOW": "MSNBC"}   # MS NOW = MSNBC renamed, Nov 2025
# a banner counts as WNBA when it names the league or one of its people
# (the same terms as notebooks/08-chyrons.ipynb)
WNBA = re.compile("|".join([r"\bwnba\b", "caitlin clark", "angel reese", "brittney griner",
    r"\bgriner\b", "sophie cunningham", "paige bueckers", r"a'?ja wilson", "diana taurasi",
    "sue bird", "candace parker", "sabrina ionescu", "breanna stewart", "napheesa collier",
    "kelsey plum", "maya moore", "skylar diggins", "aliyah boston", "cameron brink",
    "dijonai carrington", "kamilla cardoso", "chennedy carter", "indiana fever",
    "chicago sky", "atlanta dream"]), re.I)
PATS = patterns()
TOPICS = {
    "polrace": re.compile(PATS["politics or race"], re.I),
    "lgbtq": re.compile(PATS["LGBTQ or trans"], re.I),
}

seen = set()
counts = {t: defaultdict(lambda: defaultdict(lambda: {"n": 0, "hits": 0})) for t in TOPICS}
with open(ROOT / "data" / "chyron_matches.tsv") as fh:
    for row in csv.DictReader(fh, delimiter="\t"):
        network = CHANNEL.get(row["channel"])
        if not network:
            continue
        day, year = row["date_time_utc"][:10], row["date_time_utc"][:4]
        for line in row["text"].split("\\n"):
            text = " ".join(line.split()).strip(" .-")
            if len(text) < 8 or not WNBA.search(text):
                continue
            key = (network, day, text.lower())
            if key in seen:
                continue
            seen.add(key)
            for topic, rx in TOPICS.items():
                cell = counts[topic][network][year]
                cell["n"] += 1
                cell["hits"] += bool(rx.search(text))

years = sorted({y for t in counts.values() for c in t.values() for y in c})
out = {"years": years, "networks": list(CHANNEL.values()),
       "topics": {t: {n: dict(c) for n, c in by.items()} for t, by in counts.items()}}
(ROOT / "src" / "data" / "chyron_topics.json").write_text(json.dumps(out))
for topic, by in counts.items():
    print(topic)
    for network in CHANNEL.values():
        cells = by[network]
        n, h = sum(c["n"] for c in cells.values()), sum(c["hits"] for c in cells.values())
        print(f"  {network:10} {n:5} banners  {h:4} on topic ({100 * h / max(n, 1):.0f}%)  "
              + " ".join(f"{y[2:]}:{cells[y]['hits']}/{cells[y]['n']}" for y in years if y in cells))
