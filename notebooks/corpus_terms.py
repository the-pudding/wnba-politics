"""The one list of terms that decides what counts as WNBA coverage.

Every harvester searches with these terms and the corpus filters
(fox_corpus_filter.py, outlet_corpus_filter.py) keep an article by them, so
what gets searched for and what gets kept stay the same everywhere. Edit the
lists here, then run this file to write data/corpus_terms.json, which the
harvesters in ~/clark-reese-framing read (including the JavaScript ones):

    python3 notebooks/corpus_terms.py

An article counts when it is dated inside the study window (START–END) and
prominently mentions the league, a team by its full
name, one of the players or one of the league's own figures by full name (the
prominence test is in fox_corpus_filter.py). A team's nickname alone ("Fever",
"Storm") counts only once one of those is there. "Women's basketball",
Unrivaled and college coaches don't count: mostly college coverage and another
league.
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

# ---- settings ----
# the study window, the same for every outlet: articles dated outside it are
# left out (inclusive; move END to the day of the final scrape)
START = "2019-01-01"
END = "2026-10-20"

LEAGUE = ["WNBA", "W.N.B.A."]

# full name, nickname
TEAMS = [
    ("Atlanta Dream", "Dream"),
    ("Chicago Sky", "Sky"),
    ("Connecticut Sun", "Sun"),
    ("Dallas Wings", "Wings"),
    ("Golden State Valkyries", "Valkyries"),
    ("Indiana Fever", "Fever"),
    ("Las Vegas Aces", "Aces"),
    ("Los Angeles Sparks", "Sparks"),
    ("Minnesota Lynx", "Lynx"),
    ("New York Liberty", "Liberty"),
    ("Phoenix Mercury", "Mercury"),
    ("Portland Fire", "Fire"),
    ("Seattle Storm", "Storm"),
    ("Toronto Tempo", "Tempo"),
    ("Washington Mystics", "Mystics"),
]
# other ways a full team name is written
TEAM_ALIASES = {"Los Angeles Sparks": ["LA Sparks", "L.A. Sparks"]}
# nicknames too common as words to count even beside a league mention
COMMON_NICKNAMES = {"Sky", "Sun", "Dream", "Fire"}

# the players are the "players" group in src/data/people.json; the league's own
# figures (not college coaches, not the NBA commissioner) are these
LEAGUE_FIGURES = ["Cathy Engelbert", "Stephanie White", "Becky Hammon", "Cheryl Reeve"]

# extra words a URL slug may carry instead of a full name, for finding articles
# in sitemaps (the filter still decides from the text): surnames and nicknames
# rare enough not to flood a news site's sitemap with other stories
SLUG_EXTRAS = ["griner", "bueckers", "ionescu", "taurasi", "ogwumike", "vandersloot",
               "ogunbowale", "carrington", "engelbert", "mystics", "lynx", "valkyries"]

# a mention counts as prominent within this many opening words (see the filter)
EARLY = 100
# ------------------


def in_window(date):
    """Whether an article's date (YYYY-MM-DD…) falls inside START–END."""
    return START <= (date or "")[:10] <= END


def players():
    people = json.loads((HERE / "src/data/people.json").read_text())
    return [name for name, p in people.items() if p.get("group") == "players"]


def team_names():
    return [name for name, _ in TEAMS] + [a for names in TEAM_ALIASES.values() for a in names]


def nicknames():
    return [nick for _, nick in TEAMS if nick not in COMMON_NICKNAMES]


def people_names():
    return players() + LEAGUE_FIGURES


def search_terms():
    """What every site search runs: the league, each team, each person."""
    return ["WNBA"] + [name for name, _ in TEAMS] + people_names()


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("'", "").replace("’", "")).strip("-")


def slug_pattern():
    """A regex for URL slugs: the league, team and people names as slugs
    ("indiana-fever", "aja-wilson") plus SLUG_EXTRAS, each a whole slug part."""
    parts = ["wnba"] + [_slug(t) for t, _ in TEAMS] + [_slug(n) for n in people_names()] + SLUG_EXTRAS
    return r"(?<![a-z0-9])(?:" + "|".join(sorted(set(parts), key=len, reverse=True)) + r")(?![a-z0-9])"


def write_json():
    out = {
        "league": LEAGUE,
        "teams": [name for name, _ in TEAMS],
        "team_aliases": TEAM_ALIASES,
        "nicknames": nicknames(),
        "players": players(),
        "league_figures": LEAGUE_FIGURES,
        "search_terms": search_terms(),
        "slug_pattern": slug_pattern(),
        "early_words": EARLY,
        "start": START,
        "end": END,
    }
    path = HERE / "data/corpus_terms.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"wrote {path.relative_to(HERE)}: {len(out['search_terms'])} search terms")


if __name__ == "__main__":
    write_json()
