"""Drop the Fox articles in data/fox_wnba.csv that are not about the WNBA.

Fox tags some NBA and general sports stories as WNBA, and the harvest took
its tag feeds, search results and sitemap at their word: the corpus carried a
Lakers play-in recap, the Palace of Auburn Hills demolition, a Susan Rice and
Snoop Dogg story. Those feed every number in the piece, so they go.

An article counts a mention when its headline or body says WNBA, women's
basketball, Unrivaled, an unambiguous WNBA franchise, or someone on the
roster (by each person's own pattern in src/data/people.json). It is dropped
when

  * nothing in it is a mention at all, or
  * the headline has none and the body has at most one — a story about
    something else with a WNBA aside.

The original is kept as data/fox_wnba.unfiltered.csv; what went, and why, is
listed in data/fox_wnba_dropped.csv for checking by eye. Rerun after any
re-harvest:

    python3 notebooks/fox_corpus_filter.py            # filter
    python3 notebooks/fox_corpus_filter.py --report   # list, change nothing
"""
import csv, json, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CORPUS = HERE / "data" / "fox_wnba.csv"
BACKUP = HERE / "data" / "fox_wnba.unfiltered.csv"
DROPPED = HERE / "data" / "fox_wnba_dropped.csv"
csv.field_size_limit(10 ** 9)

TEAMS = (r"Fever|Aces|Liberty|Lynx|Mercury|Sparks|Mystics|Valkyries|Tempo|"
         r"Chicago Sky|Connecticut Sun|Atlanta Dream|Dallas Wings|Seattle Storm|Toronto Tempo")
people = json.loads((HERE / "src" / "data" / "people.json").read_text())
ROSTER = "|".join(p["rx"] for p in people.values()
                  if p.get("group") in ("players", "league") and p.get("rx"))
MENTION = re.compile(
    rf"\bWNBA\b|women'?s (?:national )?basketball|\bUnrivaled\b|\b(?:{TEAMS})\b|{ROSTER}", re.I)


# a roster surname that someone else in the news shares: when the article
# names the look-alike and never the player's first name, the bare surname
# is not her ("Cade Cunningham" in an NBA all-star piece is not Sophie)
LOOKALIKES = [
    (re.compile(r"cade\W{0,3}cunningham", re.I), re.compile(r"sophie", re.I), re.compile(r"\bcunningham\b", re.I)),
    (re.compile(r"alysha\W{0,3}clark", re.I), re.compile(r"caitlin", re.I), re.compile(r"\bclark\b", re.I)),
    (re.compile(r"cherelle\W{0,3}griner", re.I), re.compile(r"brittney", re.I), re.compile(r"\bgriner\b", re.I)),
    (re.compile(r"charli\W{0,3}collier", re.I), re.compile(r"napheesa", re.I), re.compile(r"\bcollier\b", re.I)),
    (re.compile(r"isaiah\W{0,3}stewart", re.I), re.compile(r"breanna", re.I), re.compile(r"\bstewart\b", re.I)),
    (re.compile(r"arvell\W{0,3}reese", re.I), re.compile(r"angel", re.I), re.compile(r"\breese\b", re.I)),
]

# other sports' stories the rule keeps on a passing roster mention, found by
# reading: an NBA column with one Clark sentence, a 2020 NBA H-O-R-S-E report
DROP_HEADLINES = {
    "Embrace of Wemby as face of the NBA proves resistance toward Jokic was always racial | Bobby Burack",
    "NBA, ESPN finishing up plan to televise H-O-R-S-E competition: report",
    "Knicks star Jalen Brunson's sister dunks on critics as New York wins NBA championship",
}


def mentions(text, blank=()):
    text = text or ""
    for surname in blank:
        text = surname.sub("", text)
    return len(MENTION.findall(text))


def reason(row):
    if (row.get("headline") or "").strip() in DROP_HEADLINES:
        return "about another sport, with a passing WNBA mention"
    whole = (row.get("headline") or "") + " " + (row.get("body") or "")
    blank = [surname for lookalike, first, surname in LOOKALIKES
             if lookalike.search(whole) and not first.search(whole)]
    head, body = mentions(row.get("headline"), blank), mentions(row.get("body"), blank)
    if head + body == 0:
        return "no WNBA, team or roster mention anywhere"
    if head == 0 and body <= 1:
        return "headline about something else, one passing mention in the body"
    return None


def main(report_only):
    source = BACKUP if BACKUP.exists() else CORPUS
    rows = list(csv.DictReader(source.open()))
    keep, drop = [], []
    for row in rows:
        why = reason(row)
        (drop if why else keep).append((row, why))
    print(f"{len(rows)} articles: keep {len(keep)}, drop {len(drop)}")
    for row, why in drop:
        print(f"  - {row['date']} | {row['headline'][:80]} | {why}")
    if report_only:
        return
    if not BACKUP.exists():
        shutil.copy(CORPUS, BACKUP)
    fields = list(rows[0].keys())
    with CORPUS.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(row for row, _ in keep)
    with DROPPED.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "headline", "url", "reason"])
        w.writerows((row["date"], row["headline"], row["url"], why) for row, why in drop)
    print(f"wrote {CORPUS.name} ({len(keep)} rows), {DROPPED.name} ({len(drop)} rows); original in {BACKUP.name}")


if __name__ == "__main__":
    main("--report" in sys.argv)
