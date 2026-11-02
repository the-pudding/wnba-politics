"""When a cable news chyron counts as a WNBA chyron. One rule for the harvester
(~/clark-reese-framing/scripts/harvest/harvest_chyrons.py), export_chyrons.py,
08-chyrons.ipynb and chyron_topics.py.

    wnba_hit(text) -> a label saying what matched ("wnba", "name: gabby williams",
                      "team: atlanta dream", "pair: dream down valkyries",
                      "surname: clark") or None

A banner counts when one of its lines has
  - the league's name, or a player's or official's full name,
  - a full team name ("ATLANTA DREAM", "LAS VEGAS ACES"),
  - a nickname no other team or common word has (Valkyries, Mystics),
  - two different team nicknames with a game word or a score
    ("DREAM DOWN VALKYRIES 97-71"),
  - a player's surname next to a basketball word ("CLARK EARNS 7TH TECHNICAL
    FOUL", "BOSTON, CLARK DELIVER HISTORIC OVERTIME WIN").
Weather and wildfire lines don't count for Storm, Fire, Sun, Sky or Mercury, and
surname lines that name an NBA team don't count (Cade Cunningham).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_terms import people_names

# ---- settings ----
# full names on top of corpus_terms.people_names()
EXTRA_NAMES = [
    "Gabby Williams", "Allisha Gray", "Rhyne Howard", "Brittney Sykes", "Jordin Canada",
    "Natalie Nakase", "Veronica Burton", "Kate Martin", "Tina Charles", "Maya Moore",
    "Skylar Diggins", "Elena Delle Donne", "Layshia Clarendon", "Sheryl Swoopes",
    "Lisa Leslie", "Kamilla Cardoso", "Women's National Basketball",
]
# surnames rare enough to count on their own
RARE_SURNAMES = ["Griner", "Bueckers", "Taurasi", "Ionescu", "Ogwumike", "Ogunbowale", "Vandersloot"]
# surnames that count next to a basketball word (common ones like Wilson or
# Jones are left out: too many other people share them)
SURNAMES = [
    "Clark", "Reese", "Bueckers", "Ionescu", "Cardoso", "Carrington", "Cunningham",
    "Engelbert", "Taurasi", "Collier", "Plum", "Ogwumike", "Ogunbowale", "Mabrey",
    "Vandersloot", "Nakase", "Hull",
]
# (Boston and Brink count only as full names: "BOSTON FIRE", "ON THE BRINK")
NOT_THEM = (
    r"jeffrey|katherine|kathy|wyndham|wesley|stephon|hope|sean|cade|randall|ramsey|"
    r"dick|blake|kevin|jonathan|mark|toni|shaelie|clark\s+county|clark\s+kent|"
    r"clark\s+lea|clark\s+atlanta|witherspoon|lewis\s*(?:and|&)"
)
# (the nicknames that are everyday words, Sky to Fire, aren't basketball words here)
BASKETBALL = (
    r"wnba|women'?s|fever|aces|lynx|mystics|valkyries|tempo|"
    r"technical|flagrant|ejected|tossed|hard foul|foul|"
    r"rookie|all-star|triple-double|double-double|career-high|basketball|hoops|mvp|"
    r"overtime|unrivaled|hawkeyes|ncaa|final four|uconn"
)
NBA_TEAMS = (
    r"\bnba\b|pistons|lakers|celtics|knicks|warriors|bulls|heat|bucks|nets|suns|"
    r"nuggets|thunder|cavaliers|cavs|76ers|sixers|raptors|hawks|hornets|magic|"
    r"pacers|wizards|spurs|rockets|mavericks|mavs|grizzlies|pelicans|jazz|kings|"
    r"clippers|blazers|timberwolves|wolves"
)
TEAMS = [
    ("Atlanta", "Dream"), ("Chicago", "Sky"), ("Connecticut", "Sun"), ("Dallas", "Wings"),
    ("Golden State", "Valkyries"), ("Indiana", "Fever"), ("(?:Las )?Vegas", "Aces"),
    ("(?:Los Angeles|L\\.?A\\.?)", "Sparks"), ("Minnesota", "Lynx"),
    ("(?:New York|N\\.?Y\\.?)", "Liberty"), ("Phoenix", "Mercury"), ("Portland", "Fire"),
    ("Seattle", "Storm"), ("Toronto", "Tempo"), ("Washington", "Mystics"),
]
UNIQUE = ["Valkyries", "Mystics"]
# other teams and things that share a nickname
NOT_WNBA = r"red wings|sun devils|chicago fire|sun belt|liberty (?:university|flames)|storm surge"
GAME_WORDS = (
    r"beat|beats|down|downs|tops?|defeats?|edges?|routs?|over|vs\.?|stuns?|sinks?|"
    r"blows? out|holds? off|rall(?:y|ies) past|crush(?:es)?|outlasts?|survives?|"
    r"cruises? past|rolls? past|shuts? down|knocks? off|game\s*\d|finals?|series|"
    r"playoffs?|semifinals?|anthem|win|wins|loss"
)
WEATHER = (
    r"degrees|°|heat wave|temps?\b|forecast|warning|watch\b|evacuat|acres|contain|"
    r"blaze|wildfire|rain|snow|wind"
)
WEATHER_NICKS = {"storm", "fire", "sun", "sky", "mercury"}
# nicknames that are everyday words: a pair made only of these needs a
# basketball word or a score in the line too ("FIRE OVER NIGHT SKY"); "Sparks",
# a verb, needs one even after a city ("LOS ANGELES SPARKS LEGAL QUESTIONS")
EVERYDAY_NICKS = {"storm", "fire", "sun", "sky", "mercury", "liberty", "sparks", "wings", "dream"}

# ---- patterns ----
S = r"[\s.]*"   # the OCR sometimes runs words together or adds dots


def _name(full):
    return S.join(re.escape(part) for part in full.split())


# "wnba" anywhere, as the OCR runs it into the next word ("WNBAPAY GAP",
# "WWNBA STAR"), but not inside "downballot" or "Brownback"
NAMES = re.compile(
    r"wnba(?!ll|ck)|\b(?:" + "|".join(_name(n) for n in people_names() + EXTRA_NAMES) + r")\b",
    re.I)
NICKS = sorted({nick for _, nick in TEAMS}, key=len, reverse=True)
NICK = r"\b(?:" + "|".join(NICKS) + r")\b"
FULL = re.compile(
    r"\b(?:" + "|".join(rf"{city.replace(' ', S)}{S}{nick}" for city, nick in TEAMS) + r")\b",
    re.I)
BARE = re.compile(r"\b(?:" + "|".join(UNIQUE) + r")\b", re.I)
RARE = re.compile(r"\b(?:" + "|".join(RARE_SURNAMES) + r")\b", re.I)
PAIR = re.compile(rf"({NICK})[^|/]{{0,40}}?({NICK})", re.I)
SURNAME = re.compile(r"(?:(\w+)\W+)?\b(" + "|".join(SURNAMES) + r")\b(?:\s+(\w+))?", re.I)
SCORE = re.compile(r"\b[\dO/]{2,3}\s*-\s*[\dO/]{2,3}\b")
GAME = re.compile(rf"\b(?:{GAME_WORDS})\b", re.I)
HOOPS = re.compile(rf"\b(?:{BASKETBALL})\b", re.I)
NBA = re.compile(NBA_TEAMS, re.I)
SKIP = re.compile(NOT_WNBA, re.I)
WEATHERY = re.compile(WEATHER, re.I)
NOT_PLAYER = re.compile(rf"^(?:{NOT_THEM})$", re.I)
NOT_PLAYER_PHRASE = re.compile(NOT_THEM, re.I)


def lines(text):
    """A Third Eye row holds several banners: split on its \\n and | marks."""
    return [line for line in re.split(r"\\n|\n|\|", text) if line.strip()]


def line_hit(line):
    m = NAMES.search(line)
    if m:
        return "wnba" if m.group(0).lower().startswith("wnba") else "name: " + " ".join(m.group(0).lower().split())
    line = SKIP.sub(" ", line)
    weather = bool(WEATHERY.search(line))
    hoops = bool(HOOPS.search(line) or GAME.search(line) or SCORE.search(line))
    m = FULL.search(line)
    if m:
        nick = m.group(0).split()[-1].lower()
        if not (weather and nick in WEATHER_NICKS) and (nick != "sparks" or hoops or "'s" in line[m.end():m.end() + 2].lower()):
            return "team: " + " ".join(m.group(0).lower().split())
    m = BARE.search(line)
    if m:
        return "nickname: " + m.group(0).lower()
    m = RARE.search(line)
    if m:
        return "surname: " + m.group(0).lower()
    for m in PAIR.finditer(line):
        a, b = m.group(1).lower(), m.group(2).lower()
        if a == b or (weather and {a, b} & WEATHER_NICKS):
            continue
        if {a, b} <= EVERYDAY_NICKS and not (HOOPS.search(line) or SCORE.search(line)):
            continue
        if GAME.search(line) or SCORE.search(line):
            return "pair: " + " ".join(m.group(0).lower().split())
    if HOOPS.search(line) and not NBA.search(line) and not weather:
        for m in SURNAME.finditer(line):
            before, surname, after = m.group(1) or "", m.group(2), m.group(3) or ""
            if NOT_PLAYER.match(before) or NOT_PLAYER_PHRASE.search(f"{surname} {after}"):
                continue
            # a guest caption: "Kevin Clark | New Hampshire Voter"
            if before[:1].isupper() and before[1:].islower():
                continue
            return "surname: " + surname.lower()
    return None


def wnba_hit(text):
    for line in lines(text):
        hit = line_hit(line)
        if hit:
            return hit
    return None
