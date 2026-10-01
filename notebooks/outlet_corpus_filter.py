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
import csv, shutil, sys, re
from dedupe import dedupe
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fox_corpus_filter import reason

HERE = Path(__file__).resolve().parent.parent
csv.field_size_limit(10 ** 9)
OUTLETS = ["espn", "cbs_sports", "usa_today", "the_athletic", "just_womens_sports",
           "cnn", "nbc_news", "cbs_news", "npr", "ap", "washington_post", "new_york_times",
           "breitbart", "redstate", "hotair", "gatewaypundit", "brobible", "outkick", "andscape"]


# articles the rule keeps but a reading rejects: other sports' stories that
# mention the WNBA in passing (found by their sport vocabulary)
DROP_URLS = set()   # by URL, when a headline is not unique enough
DROP_HEADLINES = {
    "Josh Lowe to Angels, Lux to Rays, Burke to Reds in 3-team trade",
    "Big stories of the NFL 2026 offseason, from Garrett to Kelce",
    "What have 2026 NFL rookies spent their first paychecks on?",
    "MLB Power Rankings Week 20: Brewers pass Dodgers for No. 1",
    "Updated 2026 MLB top 100 prospect rankings: Made, Arias, more",
    "Arena for 76ers, Flyers to open in 2030, marks 'new era'",
}


# the opinion sites' daily roundups: a WNBA item among a dozen others
ROUNDUP = re.compile(r"^(?:Morning Minute|Sunday Smiles|RedState Sports Report|The Morning Briefing|Weekend Parting Shot)\b|Newsletter", re.I)


# pages that are not articles: crossword answer pages whose clue says "WNBA team",
# podcast episode pages, video pages, lesson plans (the Times' Learning Network)
WNBA_SECTION = re.compile(r"(?<![a-z0-9])wnba(?![a-z0-9])", re.I)
NOT_ARTICLE = re.compile(r"/(crosswords|puzzles|podcasts|videos?|slideshow|gallery|interactive|learning|audio|newsletters)/", re.I)


# the print edition's multi-sport briefs pages (ProQuest): a WNBA brief among
# hockey, golf and soccer items, under a section label ("PRO BASKETBALL") or the
# first item's headline. Their WNBA items are mostly wire recaps the web corpus
# already has (2026-10-01)
SECTION = re.compile(r"(?<![A-Za-z])(PRO BASKETBALL|PRO FOOTBALL|HOCKEY|GOLF|SOCCER|TENNIS|BASEBALL|COLLEGES|"
                     r"COLLEGE BASKETBALL|COLLEGE FOOTBALL|COLLEGE BASEBALL|AUTO RACING|TRACK AND FIELD|BOXING|"
                     r"OLYMPICS|HORSE RACING|CYCLING|SWIMMING|THE DAY IN SPORTS)(?![A-Za-z])")


def print_digest(row):
    if "proquest.com" not in (row.get("url") or ""):
        return False
    return bool(re.fullmatch(r"[A-Z &,.'-]{4,}", (row.get("headline") or "").strip())) \
        or len(set(SECTION.findall(row.get("body") or ""))) >= 2


def why_drop(row):
    if print_digest(row):
        return "a print sports digest with a WNBA brief in it"
    if (row.get("url") or "").strip() in DROP_URLS or (row.get("headline") or "").strip() in DROP_HEADLINES:
        return "about another sport, with a passing WNBA mention"
    if NOT_ARTICLE.search(row.get("url") or ""):
        return "not an article: a crossword, podcast, video or lesson page"
    if row.get("outlet") in ("RedState", "Hot Air", "Breitbart", "Gateway Pundit") and ROUNDUP.search(row.get("headline") or ""):
        return "a daily roundup with a WNBA item in it"
    # the outlet's own WNBA section: a path segment, not any "wnba" inside a
    # word (Breitbart's Sam Brownback interviews slipped in on "brownback")
    if WNBA_SECTION.search(row.get("url") or ""):
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
    # one copy of each article (dedupe.py, 2026-09-30)
    kept, copies = dedupe([row for row, _ in keep])
    keep = [(row, None) for row in kept]
    drop += copies
    print(f"{stem}: {len(rows):,} articles → keep {len(keep):,}, drop {len(drop)} ({len(copies)} duplicate copies)")
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
