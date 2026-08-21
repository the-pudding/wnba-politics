"""The topic vocabularies behind the timeline and outlet charts.

Edit data/topic_terms.csv — one term per row. A term is matched as-is
anywhere in the text (so "racis" catches racism and racist); a few terms
use regex for word boundaries (\\b) or spelling variants ([ae]).
The union topics ("politics or race" ...) are built from the base topics.
"""
import csv
from pathlib import Path

TERMS_CSV = Path(__file__).resolve().parent.parent / "data" / "topic_terms.csv"

UNIONS = {
    "politics or race": ["race / racism", "politics / protest"],
    "politics or LGBTQ": ["politics / protest", "LGBTQ / sexuality"],
    "politics or race or LGBTQ": ["race / racism", "politics / protest", "LGBTQ / sexuality"],
}

# the timeline's column order
ORDER = ["transgender / trans", "race / racism", "politics / protest", "politics or race",
         "LGBTQ / sexuality", "politics or LGBTQ", "politics or race or LGBTQ",
         "\u201cwoke\u201d", "Trump"]


def patterns():
    """{topic name: regex string}, unions included."""
    groups = {}
    for row in csv.DictReader(open(TERMS_CSV)):
        groups.setdefault(row["topic"], []).append(row["term"])
    pats = {topic: "|".join(terms) for topic, terms in groups.items()}
    for union, parts in UNIONS.items():
        pats[union] = "|".join(pats[p] for p in parts)
    return pats


def topics():
    """[(topic name, regex string)] in the timeline's column order."""
    pats = patterns()
    return [(t, pats[t]) for t in ORDER]
