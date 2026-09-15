"""Drop the articles in the sports outlets' corpora that are not about the WNBA.

The same rule as fox_corpus_filter.py, with two allowances for how these
corpora were gathered:

  * an article whose URL sits in the outlet's WNBA section is kept whatever
    its text says (CBS Sports and USA Today were harvested from those
    sections; the section is the outlet's own tag);
  * an article with no body text is kept — a headline alone cannot show
    the mentions the rule counts, and these rows came from WNBA sitemaps
    and feeds.

What goes is the rest: ESPN's search API returned MLB trade-deadline and
Formula 1 pieces for "wnba playoffs"; Just Women's Sports' feed carries
college basketball, softball and the USWNT; The Athletic's league feed
slips in sports trivia. The originals are kept as data/<outlet>.unfiltered.csv,
and what went, and why, in data/<outlet>_dropped.csv.

    python3 notebooks/outlet_corpus_filter.py            # filter
    python3 notebooks/outlet_corpus_filter.py --report   # list, change nothing
"""
import csv, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fox_corpus_filter import reason

HERE = Path(__file__).resolve().parent.parent
csv.field_size_limit(10 ** 9)
OUTLETS = ["espn", "cbs_sports", "usa_today", "the_athletic", "just_womens_sports"]


def why_drop(row):
    if "wnba" in (row.get("url") or "").lower():
        return None
    if not (row.get("body") or "").strip():
        return None
    return reason(row)


def run(stem, report_only):
    corpus = HERE / "data" / f"{stem}.csv"
    backup = HERE / "data" / f"{stem}.unfiltered.csv"
    dropped = HERE / "data" / f"{stem}_dropped.csv"
    source = backup if backup.exists() else corpus
    rows = list(csv.DictReader(source.open()))
    keep, drop = [], []
    for row in rows:
        why = why_drop(row)
        (drop if why else keep).append((row, why))
    print(f"{stem}: {len(rows):,} articles → keep {len(keep):,}, drop {len(drop)}")
    for row, why in drop[:8]:
        print(f"    - {row['date']} | {row['headline'][:70]} | {why}")
    if len(drop) > 8:
        print(f"    … and {len(drop) - 8} more")
    if report_only or not drop:
        return
    if not backup.exists():
        shutil.copy(corpus, backup)
    fields = list(rows[0].keys())
    with corpus.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(row for row, _ in keep)
    with dropped.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "headline", "url", "reason"])
        w.writerows((row["date"], row["headline"], row["url"], why) for row, why in drop)


if __name__ == "__main__":
    report = "--report" in sys.argv
    for stem in OUTLETS:
        run(stem, report)
