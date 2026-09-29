"""Bundle related outlets into one corpus each for the brand-level comparison
(2026-09-28). Each bundle file carries the bundle's label in `outlet` and the
member's own name in `source`, so nothing downstream changes and the members
can still be told apart.

  Fox News       = data/fox_wnba.csv (Fox News) + outkick.csv  -> rewritten in place (Fox Sports left out: too patchy)
  New York Times = new_york_times.csv + the_athletic.csv                        -> data/nyt_bundle.csv
  CBS            = cbs_sports.csv + cbs_news.csv                                 -> data/cbs_bundle.csv
  ESPN           = espn.csv + andscape.csv (ESPN's culture arm)                  -> data/espn_bundle.csv

Run after the filters (fox_corpus_filter.py, outlet_corpus_filter.py) and
before any notebook. Idempotent: a bundled fox_wnba.csv is unbundled first.
    python3 notebooks/bundle_outlets.py
"""
import csv, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "data"
csv.field_size_limit(10 ** 9)
FIELDS = ["outlet", "date", "headline", "author", "url", "body", "source"]

BUNDLES = {
    # label, output file, members (file, member label)
    "Fox News": ("fox_wnba.csv", [("fox_wnba.csv", "Fox News"), ("outkick.csv", "OutKick")]),
    "New York Times": ("nyt_bundle.csv", [("new_york_times.csv", "New York Times"), ("the_athletic.csv", "The Athletic")]),
    "CBS": ("cbs_bundle.csv", [("cbs_sports.csv", "CBS Sports"), ("cbs_news.csv", "CBS News")]),
    "ESPN": ("espn_bundle.csv", [("espn.csv", "ESPN"), ("andscape.csv", "Andscape")]),
}

def key(url):
    return (url or "").strip().rstrip("/").replace("http://", "https://").lower()

def rows_of(path, member):
    if not path.exists():
        print(f"  (no {path.name})"); return []
    out = []
    for r in csv.DictReader(path.open()):
        # a file already bundled in place keeps only its own rows (Fox News) —
        # including the foxnews.com/outkick-sports pages, which the Fox harvest
        # found and which are relabelled OutKick below
        if r.get("source") and r["source"] != member and not (member == "Fox News" and "foxnews.com" in (r.get("url") or "")):
            continue
        r = {f: r.get(f, "") for f in FIELDS}
        r["source"] = r["source"] or member
        # OutKick's pages end every headline with its tagline ("… | OutKick"):
        # site furniture, not the story, and it matched the "outkick"
        # culture-war term, flagging all 1,568 of them as political (2026-09-29)
        r["headline"] = re.sub(r"\s*\|\s*OutKick\s*$", "", r["headline"] or "")
        # OutKick moved under foxnews.com/outkick-sports in 2025-26: those pages
        # come in with the Fox News harvest but are OutKick's
        if r["source"] == "Fox News" and "/outkick" in (r.get("url") or ""):
            r["source"] = "OutKick"
        out.append(r)
    return out

for label, (out_name, members) in BUNDLES.items():
    seen, rows = set(), []
    for fname, member in members:
        got = rows_of(DATA / fname, member)
        kept = 0
        for r in got:
            k = key(r["url"])
            if k in seen:
                continue
            seen.add(k); r["outlet"] = label; rows.append(r); kept += 1
        print(f"  {label} <- {member}: {kept:,} rows" + (f" ({len(got) - kept} duplicate URLs skipped)" if len(got) != kept else ""))
    rows.sort(key=lambda r: r["date"])
    with (DATA / out_name).open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
    print(f"{label}: {len(rows):,} rows -> data/{out_name}")
