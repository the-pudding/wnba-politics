"""Monthly topic counts per outlet (the yearly ones are notebook 05's
outlet_topics.csv), for the small multiples
"""
import csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "notebooks"))
from outlets import OUTLETS
import topics
csv.field_size_limit(10 ** 9)
pats = topics.patterns()
# the race panels: race terms only, BLM among them
PATTERNS = {"polrace": re.compile(pats["race / racism"], re.I),
            "lgbtq": re.compile(pats["LGBTQ or trans"], re.I),
            "fouls": re.compile(pats["fouls"], re.I),
            "protect": re.compile(pats["protect"], re.I)}
PAIRS = [("fouls", "protect"), ("polrace", "lgbtq")]
# each of the fouls topic's words on its own, so a chart can name the word
# behind each spike
FOUL_TERMS = {"hip-check": r"hip-?check", "poke": r"\bpoke[ds]?\b",
              "punch": r"\bpunch(?:ed|es|ing)?\b", "throat": r"\bthroat\b"}
assert list(FOUL_TERMS.values()) == topics.OVERRIDES["fouls"], "the fouls words changed in topics.py"
FOUL_RX = {w: re.compile(p, re.I) for w, p in FOUL_TERMS.items()}
term_records = []
records = []
for key, label, *_ in OUTLETS:
    months = {t: defaultdict(Counter) for t in list(PATTERNS) + [f"{a}&{b}" for a, b in PAIRS]}
    terms = {w: Counter() for w in FOUL_TERMS}
    for r in csv.DictReader((HERE / "data" / f"{key}.csv").open()):
        d, body = (r.get("date") or "")[:7], r.get("body") or ""
        if len(d) < 7 or d < "2019-01" or len(body.split()) <= 80:
            continue
        text = (r.get("headline") or "") + " " + body
        hits = {}
        for t, rx in PATTERNS.items():
            months[t][d]["n"] += 1
            hits[t] = bool(rx.search(text))
            if hits[t]:
                months[t][d]["hit"] += 1
        # the overlap of two topics, for a stack that splits them without
        # double counting ("fouls&protect": articles with both)
        for a, b in PAIRS:
            months[f"{a}&{b}"][d]["n"] += 1
            if hits[a] and hits[b]:
                months[f"{a}&{b}"][d]["hit"] += 1
        if hits["fouls"]:
            for w, rx in FOUL_RX.items():
                if rx.search(text):
                    terms[w][d] += 1
    for t in months:
        for m, v in sorted(months[t].items()):
            records.append((t, "body", label, m, v["n"], v["hit"]))
    for w, c in terms.items():
        for m, k in sorted(c.items()):
            term_records.append((label, w, m, k))
out = HERE / "src/data/outlet_topics_monthly.csv"
with out.open("w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["topic", "method", "outlet", "period", "articles", "hits"]); w.writerows(records)
print(f"{len(records)} rows -> {out.name}")
tout = HERE / "src/data/foul_terms_monthly.csv"
with tout.open("w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["outlet", "term", "period", "hits"]); w.writerows(term_records)
print(f"{len(term_records)} rows -> {tout.name}")
