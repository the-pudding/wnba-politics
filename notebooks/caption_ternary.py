"""The caption clips as a ternary: where each word the three networks said
about the WNBA sits between Fox News, CNN and MSNBC.

Same recipe as the chyron ternary in 08-chyrons.ipynb, on data/tv_captions.tsv
(closed-caption windows from the TV News Archive via GDELT, Sept 2017 to
Oct 2024). A word counts once per clip, since neighbouring clips overlap;
each network's count is divided by its clip total and the three rates are
normalised to shares, which place the word. Writes src/data/captions.json
(months, channels, ternary) and src/data/captions_years.json (the same by
year, for the timeline), the shapes the triangle already reads, plus
src/data/captions_examples.json (a few whole clips per word and network) for
the explore page.

    python3 notebooks/caption_ternary.py
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "tv_captions.tsv"
OUT = ROOT / "src" / "data"
CHANNELS = ["Fox News", "CNN", "MSNBC"]
TOKEN = re.compile(r"[a-z][a-z'-]{2,}")
# caption furniture and the league's own name; players' names stay, as in the chyrons
DROP = set(ENGLISH_STOP_WORDS) | set("""wnba 're 've 'll 's don didn doesn isn wasn aren
    couldn wouldn shouldn won gonna gotta yeah okay hey right like just know think going
    said says say get got let lot thing things way well really actually mean want
    look people time year years today tonight day night week back come came make made
    take took see saw one two three first last new big good great little much more most
    many very also still even ever never always maybe something anything nothing
    talk talking talked said saying tell told hear heard sure kind sort bit""".split())
# the networks' own furniture and on-air staff, who otherwise own every corner
# (players and guests stay: rapinoe, montgomery, chennedy)
DROP |= set("""fox cnn cnn's msnbc nbc nbc's laughter applause cheers cheering alert outfront
    reidout wire bleacher doublet ncw morning's updates weather britteny britney
    carley arthel bret ainsley sandra coleman greg shannon martha sean christina steve
    lawrence dana dan charlie rich jesse pete rachel howard brian mike
    kylie scholes atwood pleitgen anderson rosa flores coy phillip polantz christine fred
    kaitlan andy bob carolyn wolf abby phil
    andrea brittani mcfaul reverend jose sharpton renee matt terry""".split())

clips = list(csv.DictReader(open(SRC), delimiter="\t"))
words = {c: Counter() for c in CHANNELS}
words_year = defaultdict(lambda: {c: Counter() for c in CHANNELS})
totals = Counter()
totals_year = defaultdict(Counter)
example = defaultdict(dict)
examples = defaultdict(dict)
months = set()
seen = set()
for row in clips:
    ch = row["station"]
    text = row["snippet"].lower()
    key = (ch, text)
    if key in seen:              # the same window served twice
        continue
    seen.add(key)
    year = row["date"][:4]
    months.add(row["date"][:7])
    totals[ch] += 1
    totals_year[year][ch] += 1
    toks = {t.strip("'-") for t in TOKEN.findall(text)} - DROP
    for t in toks:
        if len(t) < 3:
            continue
        words[ch][t] += 1
        words_year[year][ch][t] += 1
        example[t].setdefault(ch, row["snippet"][:150])
        # a few whole clips per network, for the explore page
        exs = examples[t].setdefault(ch, [])
        if len(exs) < 3:
            exs.append({"d": row["date"][:10], "show": row["show"], "t": row["snippet"], "u": row["preview_url"]})

all_w = Counter()
for ch in CHANNELS:
    all_w.update(words[ch])
ternary = []
for term, total in all_w.most_common():
    if total < 3:
        break
    counts = [words[ch][term] for ch in CHANNELS]
    rates = [n / max(totals[ch], 1) for n, ch in zip(counts, CHANNELS)]
    ssum = sum(rates)
    shares = [round(r / ssum, 4) for r in rates]
    dom = CHANNELS[shares.index(max(shares))]
    ex_ch = dom if example[term].get(dom) else next(iter(example[term]), "")
    ternary.append({"term": term, "total": total, "counts": counts, "shares": shares,
                    "ex_ch": ex_ch, "ex": example[term].get(ex_ch, "")})

(OUT / "captions.json").write_text(json.dumps({
    "months": sorted(months), "channels": CHANNELS,
    "clips": {ch: totals[ch] for ch in CHANNELS}, "ternary": ternary}))
# the whole clips, in a file of their own: only the explore page reads it
(OUT / "captions_examples.json").write_text(json.dumps(
    {t["term"]: examples[t["term"]] for t in ternary}))
years = sorted(totals_year)
(OUT / "captions_years.json").write_text(json.dumps({
    "years": years, "channels": CHANNELS,
    "totals": {y: [totals_year[y][ch] for ch in CHANNELS] for y in years},
    "terms": {t["term"]: {y: [words_year[y][ch][t["term"]] for ch in CHANNELS]
                          for y in years if any(words_year[y][ch][t["term"]] for ch in CHANNELS)}
              for t in ternary}}))
print(f"{len(seen):,} distinct clips, {len(ternary):,} words; clips per network {dict(totals)}")
for ch_i, ch in enumerate(CHANNELS):
    lean = sorted((t for t in ternary if t["total"] >= 15), key=lambda t: -t["shares"][ch_i])[:12]
    print(f"  leans {ch}: " + ", ".join(f"{t['term']} ({t['shares'][ch_i]:.2f})" for t in lean))
