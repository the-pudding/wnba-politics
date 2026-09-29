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
    # the outlet chart's LGBTQ+ topic: sexuality and trans terms together
    "LGBTQ or trans": ["LGBTQ / sexuality", "transgender / trans"],
}


# a topic pinned here overrides (or adds to) the sheet's rows: "fouls" is only
# the four words the Republicans' letter to the WNBA cited; "protect" (the
# "protect Caitlin Clark" turn of summer 2026) is its own topic, drawn in a
# second colour beside it (2026-09-28)
OVERRIDES = {
    "fouls": [r"hip-?check", r"\bpoke[ds]?\b", r"\bpunch(?:ed|es|ing)?\b", r"\bthroat\b"],
    "protect": [r"\bprotects?\b"],
}


def patterns():
    """{topic name: regex string}, unions included."""
    groups = {}
    for row in csv.DictReader(open(TERMS_CSV)):
        groups.setdefault(row["topic"], []).append(row["term"])
    for topic, terms in OVERRIDES.items():
        groups[topic] = list(terms)
    pats = {topic: "|".join(terms) for topic, terms in groups.items()}
    for union, parts in UNIONS.items():
        pats[union] = "|".join(pats[p] for p in parts)
    return pats
