"""Daily counts of WNBA articles containing a word, per outlet, for the
word-timeline chart ({.WordTimeline}) and the /words explore page. Each word
is a pattern; an article counts once when it matches, counted two ways: in
the headline alone, and anywhere (headline or body); `mentions` is every
occurrence, for the explore page's intensity view. Every outlet has full
text for most articles (CBS Sports and USA Today for about 80–90% of theirs).
Writes src/data/word_timeline.json:

    {"outlets": {"Fox News": {"articles": {"2024-06-01": 5, ...},
                              "words": {"hip-check": {"any": {day: n}, "headline": {day: n},
                                                      "examples": {day: "a headline"}}}}}}

Each outlet also carries `masks`: per day, one bit-set per article that
matched any word (bit i = word i of `order`), and `headMasks` the same for
headlines, so a chart adding several words up can count an article once.

Add a word to WORDS and rerun:  python3 notebooks/word_timeline.py
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
csv.field_size_limit(10 ** 9)
FILES = [("fox_wnba", "Fox News"), ("espn", "ESPN"), ("cbs_sports", "CBS Sports"),
         ("usa_today", "USA Today"), ("the_athletic", "The Athletic"),
         ("just_womens_sports", "Just Women's Sports")]
WORDS = {
    "hip-check": r"hip[- ]?check",
    "poke": r"\bpok(?:e|ed|es|ing)\b",
    "punch": r"\bpunch(?:ed|es|ing)?\b",
    "check": r"\bcheck(?:ed|ing|s)?\b",
    "shove": r"\bshov(?:e|ed|es|ing)\b",
    "flagrant": r"\bflagrant\b",
    "throat": r"\bthroat\b",
    "foul": r"\bfouls?\b",
    "technical": r"\btechnical\b",
    "fight": r"\bfight(?:s|ing)?\b",
    "target": r"\btarget(?:ed|ing|s)?\b",
    "bully": r"\bbull(?:y|ies|ied|ying)\b",
    "violent": r"\bviolen(?:t|ce)\b",
    "protect": r"\bprotect(?:s|ed|ing|ion|ive)?\b",
}
rx = {w: re.compile(p, re.I) for w, p in WORDS.items()}
out = {"outlets": {}}
for name, outlet in FILES:
    articles = Counter()
    hits = {w: {"any": Counter(), "headline": Counter(), "mentions": Counter(), "examples": {}} for w in WORDS}
    masks, head_masks = defaultdict(list), defaultdict(list)
    order = list(WORDS)
    for row in csv.DictReader((HERE / "data" / f"{name}.csv").open()):
        day = (row.get("date") or "")[:10]
        if len(day) < 10:
            continue
        articles[day] += 1
        head = row.get("headline") or ""
        text = head + " " + (row.get("body") or "")
        m_any, m_head = 0, 0
        for w in WORDS:
            in_head = bool(rx[w].search(head))
            n = len(rx[w].findall(text))
            if in_head or n:
                m_any |= 1 << order.index(w)
                if in_head:
                    m_head |= 1 << order.index(w)
                hits[w]["any"][day] += 1
                hits[w]["mentions"][day] += max(1, n)
                if in_head:
                    hits[w]["headline"][day] += 1
                if in_head or day not in hits[w]["examples"]:
                    hits[w]["examples"][day] = head
        if m_any:
            masks[day].append(m_any)
        if m_head:
            head_masks[day].append(m_head)
    out["outlets"][outlet] = {
        "articles": dict(sorted(articles.items())),
        "order": order,
        "masks": dict(sorted(masks.items())),
        "headMasks": dict(sorted(head_masks.items())),
        "words": {w: {"any": dict(sorted(h["any"].items())), "headline": dict(sorted(h["headline"].items())),
                      "mentions": dict(sorted(h["mentions"].items())), "examples": h["examples"]} for w, h in hits.items()}}
    print(f"{outlet:20} " + "  ".join(f"{w} {sum(hits[w]['any'].values())}" for w in list(WORDS)[:4]))
(HERE / "src" / "data" / "word_timeline.json").write_text(json.dumps(out))
