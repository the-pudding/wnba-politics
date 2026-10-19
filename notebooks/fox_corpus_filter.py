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

# A franchise counts when it is city-qualified. A bare nickname ("Sparks",
# "Liberty", "Mercury", "Fever") is an ordinary English word far more often
# than a team, so it counts only capitalised and only once the article has an
# unambiguous mention somewhere (WNBA, women's basketball, a city-qualified
# team, a roster name), so "Statue of Liberty" and "sparks outrage" stories
# stay out.
CITY_TEAMS = (r"Indiana Fever|Las Vegas Aces|New York Liberty|Minnesota Lynx|Phoenix Mercury|"
              r"Los Angeles Sparks|L\.?A\.? Sparks|Washington Mystics|Golden State Valkyries|"
              r"Toronto Tempo|Chicago Sky|Connecticut Sun|Atlanta Dream|Dallas Wings|"
              r"Seattle Storm|Portland Fire")
NICKNAMES = r"Fever|Aces|Liberty|Lynx|Mercury|Sparks|Mystics|Valkyries|Tempo|Wings|Storm"
people = json.loads((HERE / "src" / "data" / "people.json").read_text())
# a person counts by full name only. The per-person patterns in people.json
# fall through to a bare surname for 26 of the 38, which is right for counting
# mentions inside an article already about the league and wrong as a test of
# relevance: it admitted Martha Stewart and Senate candidate Cal Cunningham
#. Apostrophes and curly quotes are interchangeable.
def _full_name(name):
    return r"\s+".join(re.escape(part).replace("'", "['\u2019]") for part in name.split())
# people in the roster who are not WNBA figures do not make an article about
# the WNBA: the NBA commissioner's China week and his TV deals are not league
# coverage
NOT_WNBA = {"Adam Silver"}
ROSTER = "|".join(rf"\b{_full_name(name)}\b" for name, p in people.items()
                  if p.get("group") in ("players", "league") and name not in NOT_WNBA)
ANCHOR = re.compile(
    rf"\bWNBA\b|\bW\.N\.B\.A\.|women'?s (?:national )?basketball|\b(?:{CITY_TEAMS})\b|{ROSTER}", re.I)
# the league, not the adjective: capitalised only, so "an unrivaled record" is not a mention
UNRIVALED = re.compile(r"\bUnrivaled\b")
NICK = re.compile(rf"\b(?:{NICKNAMES})\b")   # case-sensitive on purpose
# a nickname that is plainly not the team: the Post's Knicks-parade history
# reached the corpus on "Statue of Liberty" plus "the WNBA's New York Liberty"
# counted three times over
NOT_NICK = re.compile(r"Statue of Liberty|Liberty (?:Bell|Island|University|Mutual|Media|Ballers)|"
                      r"Fever (?:pitch|dream)|Sparks (?:fly|flew|flying)|Storm (?:surge|warning|clouds?|system|damage)|"
                      r"Mercury (?:Prize|rising|poisoning)|Sun Belt|Sky Sports|Sky News")
MENTION = ANCHOR   # kept for callers that import it
# an article whose headline shows nothing needs the body to say it three times,
# or twice with the first mention inside the opening EARLY words: the genuine
# cases (a feature on the Storm's coach, a print sports brief) name the league
# up top; an inflation column that reaches Griner at word 4,280 does not
EARLY = 100


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


def _blank(text, blank):
    for surname in blank:
        text = surname.sub("", text)
    return text


def _nick_text(text):
    # a nickname counts only where it is not already inside a full team name
    # or league mention ("the WNBA's New York Liberty" is one mention, not
    # three) and not part of an unrelated phrase ("Statue of Liberty")
    return NICK.sub(lambda m: m.group(0), NOT_NICK.sub(" ", ANCHOR.sub(" ", text)))

def mentions(text, blank=(), anchored=True):
    text = _blank(text or "", blank)
    n = len(ANCHOR.findall(text)) + len(UNRIVALED.findall(text))
    if anchored:
        n += len(NICK.findall(_nick_text(text)))
    return n


def first_mention_word(text, blank=(), anchored=True):
    """How many words in the first qualifying mention sits; None if none."""
    text = _blank(text or "", blank)
    hits = [m.start() for m in ANCHOR.finditer(text)] + [m.start() for m in UNRIVALED.finditer(text)]
    if anchored:
        hits += [m.start() for m in NICK.finditer(text)]
    return len(text[:min(hits)].split()) if hits else None


def reason(row):
    if (row.get("headline") or "").strip() in DROP_HEADLINES:
        return "about another sport, with a passing WNBA mention"
    whole = (row.get("headline") or "") + " " + (row.get("body") or "")
    blank = [surname for lookalike, first, surname in LOOKALIKES
             if lookalike.search(whole) and not first.search(whole)]
    cleaned = _blank(whole, blank)
    anchored = bool(ANCHOR.search(cleaned) or UNRIVALED.search(cleaned))
    head, body = mentions(row.get("headline"), blank, anchored), mentions(row.get("body"), blank, anchored)
    if head + body == 0:
        return "no WNBA, team or roster mention anywhere"
    if head == 0 and body <= 1:
        return "headline about something else, one passing mention in the body"
    if head == 0 and body == 2 and (first_mention_word(row.get("body"), blank, anchored) or 0) > EARLY:
        return "headline about something else, two passing mentions deep in the body"
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
