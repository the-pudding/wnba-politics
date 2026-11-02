"""Data for the cable news triangle (static/data/chyron_triangle.json, used by
ChyronTriangle.svelte): every chyron word with its uses on each network and
one example, plus the words of each topic version.

Reads notebook 08's output and the topic word lists; run after notebook 08:

    python notebooks/chyron_triangle.py
"""
import csv, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "static/data/chyron_triangle.json"

# ---------------------------------------------------------------------------
# Edit these
# ---------------------------------------------------------------------------

# each topic version: the categories of data/topic_terms.csv it lights
TOPIC_TERMS = {
    "polrace": ["race / racism", "politics / protest"],
    "lgbtq": ["LGBTQ / sexuality", "transgender / trans"],
    "fouls": ["fouls"],
}
# words a topic lights that its lists don't catch (the lists' race terms are
# phrases, "Black women"; a chyron word is one word), and words it leaves out
EXTRA = {"lgbtq": ["trans"], "polrace": ["black", "white", "privilege"]}
LEAVE_OUT = {"polrace": ["anthem"]}
# a word's example read off the broadcast itself, where the archive's text
# recognition caught only scraps of the screen (checked against the clip)
EXAMPLE_FIX = {
    # Fox, My View with Lara Trump, Aug. 23, 2026: a full-screen quote card, then the banner
    "gabby": "“I would welcome a trans athlete on my team or against my team” —Gabby Williams / "
             "ENES KANTER FREEDOM CHALLENGES TRANS AGENDA",
}

# ---------------------------------------------------------------------------

chy = json.loads((HERE / "src/data/chyrons.json").read_text())
years = json.loads((HERE / "src/data/chyron_ternary_years.json").read_text())
channels = chy["channels"]

# each network's WNBA chyron word total: the page divides by these, so a
# network that ran more WNBA text doesn't win by volume
totals = [sum(years["totals"][y][i] for y in years["years"]) for i in range(3)]

terms = []
for t in chy["ternary"]:
    ex_ch = channels.index(t["ex_ch"]) if t["ex_ch"] in channels else -1
    ex = EXAMPLE_FIX.get(t["term"], re.sub(r"\s+", " ", t["ex"]).strip())
    terms.append([t["term"], *t["counts"], ex_ch, ex])

rows = list(csv.DictReader((HERE / "data/topic_terms.csv").open()))
topics = {}
for key, cats in TOPIC_TERMS.items():
    rx = re.compile("|".join(r["term"] for r in rows if r["topic"] in cats), re.I)
    topics[key] = [t["term"] for t in chy["ternary"]
                   if (rx.search(t["term"]) or t["term"] in EXTRA.get(key, []))
                   and t["term"] not in LEAVE_OUT.get(key, [])]

OUT.write_text(json.dumps({
    "channels": channels,
    "totals": totals,
    "months": [chy["months"][0], chy["months"][-1]],
    "terms": terms,
    "topics": topics,
}, ensure_ascii=False, separators=(",", ":")))
print(f"{len(terms)} words; totals {totals}; topics", {k: len(v) for k, v in topics.items()})
