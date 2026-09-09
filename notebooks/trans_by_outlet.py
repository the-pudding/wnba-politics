"""WNBA articles that mention trans athletes, per outlet and year, for the
trans-section bar chart ({.SimpleBars} source: trans).

An article counts when its headline or body matches a term in the
"transgender / trans" group of data/topic_terms.csv. Fox is data/fox_wnba.csv
(after notebooks/fox_corpus_filter.py); the sports outlets are their own CSVs.
Writes src/data/trans_by_outlet.json.

    python3 notebooks/trans_by_outlet.py
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA, OUT = HERE / "data", HERE / "src" / "data" / "trans_by_outlet.json"
csv.field_size_limit(10 ** 9)

FILES = [("fox_wnba", "Fox News"), ("espn", "ESPN"), ("cbs_sports", "CBS Sports"),
         ("usa_today", "USA Today"), ("the_athletic", "The Athletic"),
         ("just_womens_sports", "Just Women's Sports")]
terms = [r["term"] for r in csv.DictReader((DATA / "topic_terms.csv").open())
         if r["topic"] == "transgender / trans"]
TRANS = re.compile("|".join(terms), re.I)

out, years = {}, set()
for name, outlet in FILES:
    articles, trans = Counter(), Counter()
    for row in csv.DictReader((DATA / f"{name}.csv").open()):
        year = (row.get("date") or "")[:4]
        if not year.isdigit():
            continue
        articles[year] += 1
        if TRANS.search((row.get("headline") or "") + " " + (row.get("body") or "")):
            trans[year] += 1
    out[outlet] = {"articles": dict(articles), "trans": dict(trans)}
    years |= set(articles)
OUT.write_text(json.dumps({"years": sorted(years), "outlets": out}))
for outlet, v in out.items():
    print(f"{outlet:20} 2026: {v['trans'].get('2026', 0)} of {v['articles'].get('2026', 0)}")
