"""
Who a bare surname means, when someone else in the coverage shares it.

Whoever the article names in full more often is its subject. When that is
the player, a bare surname is hers unless its own sentence names the
look-alike in full (a Griner detention story that mentions "Cherelle Griner"
once still means Brittney by "Griner"). When the look-alike is named as often
or more, the nearest full name before the surname decides: "Ryan Clark is so
dumb ... Clark's stupidity is so profound" is the ESPN analyst, even in a
column that names Caitlin Clark elsewhere. With no full name before it (a
headline, a lede), the article's first full name decides.

The other people were found by listing every "Firstname Surname" in the
corpora for each roster surname; misspellings of the player's
own first name ("Cailtin", "Britney") count as her.
"""

import re

# player -> (her own first names, other people's first names, surname)
RULES = {
    "Caitlin Clark": (r"cait?l[iy]n|cailtin|catilin|caitlyn", r"alysha|ryan", "clark"),
    "Angel Reese": (r"angel", r"arvell|julian|cate", "reese"),
    "Brittney Griner": (r"brittn?e?y|britney|brittany", r"", "griner"),
    "Sophie Cunningham": (r"sophie|sophia", r"cade|lindsey|ian|randall|brock", "cunningham"),
    "DiJonai Carrington": (r"dijonn?ai", r"bub|darren", "carrington"),
    "Paige Bueckers": (r"paige", r"", "bueckers"),
    "Napheesa Collier": (r"naphee?s+a|naphessa", r"charli", "collier"),
    "Breanna Stewart": (r"breanna", r"isaiah", "stewart"),
    "Marina Mabrey": (r"marina", r"dara|michaela", "mabrey"),
    "Jewell Loyd": (r"jewell?", r"jarryd", "loyd"),
    "DeWanna Bonner": (r"dewanna|dawanna", r"wales", "bonner"),
    "Arike Ogunbowale": (r"arike|arika", r"dare", "ogunbowale"),
}
# relatives the coverage never calls by the bare surname (her wife, her
# father): they take a bare surname only in a sentence that names them in full
RELATIVES = {
    "Brittney Griner": r"cherelle",
    "Paige Bueckers": r"bob",
}
_RELATIVE = {
    player: re.compile(rf"\b(?:{first})\W{{1,3}}{RULES[player][2]}\b", re.I)
    for player, first in RELATIVES.items()
}
_FULL = {
    player: (
        re.compile(rf"\b(?:{own})\W{{1,3}}{surname}\b", re.I),
        re.compile(rf"\b(?:{others})\W{{1,3}}{surname}\b", re.I),
    )
    for player, (own, others, surname) in RULES.items()
    if others
}


_OWN = {
    player: re.compile(rf"\b(?:{own})\W{{1,3}}{surname}\b", re.I)
    for player, (own, others, surname) in RULES.items()
}


def bare_is_her(player, article, pos, sentence_start=None):
    """True unless a bare surname at `pos` in `article` means a look-alike.
    `sentence_start` is where its sentence begins (defaults to `pos`)."""
    start = pos if sentence_start is None else sentence_start
    relative = _RELATIVE.get(player)
    if relative and any(start <= m.start() <= pos for m in relative.finditer(article)):
        own_here = _OWN[player].search(article, start, pos + 1)
        if not own_here:
            return False
    rule = _FULL.get(player)
    if not rule:
        return True
    own_rx, other_rx = rule
    others = [m.start() for m in other_rx.finditer(article)]
    if not others:
        return True
    own = [m.start() for m in own_rx.finditer(article)]
    if not own:
        return False
    before_other = max((p for p in others if p <= pos), default=-1)
    before_own = max((p for p in own if p <= pos), default=-1)
    if len(own) > len(others):
        return not (before_other >= start and before_other > before_own)
    if before_other >= 0 or before_own >= 0:
        return before_own > before_other
    return min(own) < min(others)


# every look-alike's and relative's full name, for masking
_ANY_OTHER = re.compile(
    r"\b(?:" + "|".join(
        rf"(?:{others})\W{{1,3}}{surname}" for player, (own, others, surname) in RULES.items() if others
    ) + "|" + "|".join(
        rf"(?:{first})\W{{1,3}}{RULES[player][2]}" for player, first in RELATIVES.items()
    ) + r")\b",
    re.I,
)


def mask(text):
    """The text with each look-alike's surname blanked to same-length filler
    ("Ryan Clark" -> "Ryan Cxxxx"), so a surname test on the parse cannot
    mistake him for her; offsets stay where they were."""
    def blank(m):
        first, _, surname = m.group(0).rpartition(" ")
        if not first:
            return m.group(0)
        return first + " " + surname[0] + "x" * (len(surname) - 1)
    return _ANY_OTHER.sub(blank, text)
