"""Every sentence that describes a foul, per player: the feed behind
{.FoulReel}. One row per sentence, with where the foul word sits so the
component can highlight it and cut a short line out of the middle.

    python notebooks/foul_feed.py

Writes static/data/foul_feed.json.
"""
import html, json, re
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "static" / "data" / "foul_feed.json"

# the fouls vocabulary: the topic sheet's terms plus the physical verbs the
# piece keeps coming back to
TERMS = [
    r"hip[- ]?check(?:ed|s|ing)?", r"\bpunch(?:ed|es|ing)?\b", r"\bthroat\b", r"\bpoke[ds]?\b", r"\bpoking\b",
    r"\bflagrant(?:ly)?\b", r"\bfoul(?:s|ed|ing)?\b", r"\bshove[sd]?\b", r"\bshoving\b",
    r"\belbow(?:s|ed|ing)?\b", r"\bclothesline[sd]?\b", r"\bcheap shot\b", r"\bhard hit\b",
    # "knocked down seven 3-pointers" is shooting; only a body going down counts
    r"\bknock(?:ed|s|ing)? (?:her |them )?(?:over|to the (?:ground|floor|court))",
    r"\btackle[sd]?\b", r"\bslap(?:ped|s)?\b", r"\bscratch(?:ed|es)?\b", r"\bhit (?:her |them )?in the (?:face|head|eye|mouth)",
    r"\bbloodied\b", r"\bblack eye\b", r"\bejected\b", r"\bejection\b", r"\btechnical\b",
]
TERM_RX = re.compile("|".join(TERMS), re.I)
# Fox's spliced ALL-CAPS link headlines, and its app plug
SHOUT = re.compile(r"\b(?:[A-Z][A-Z'’.&-]{1,}[,:;?!]?\s+){3,}[A-Z][A-Z'’.&-]{1,}[,:;?!]?")
PLUG = re.compile(r"CLICK HERE (?:TO GET|FOR MORE)[^.]*?(?:APP|COM)\b\.?", re.I)
MAX_LEN = 360
MIN_PER_PLAYER = 12

PEOPLE = json.loads((HERE / "src" / "data" / "people.json").read_text())
NAME_RX = {name: re.compile(info["rx"], re.I) for name, info in PEOPLE.items()}


def clean(text):
    text = html.unescape(str(text)).replace("\xa0", " ")
    text = PLUG.sub(" ", text)
    text = SHOUT.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip(" \"“”")


def main():
    df = pd.read_csv(HERE / "data" / "player_sentences.csv")
    df["sentence"] = df.sentence.map(clean)
    df = df[df.sentence.str.contains(TERM_RX)]
    # one copy of a sentence per player and outlet: Fox reprints its own lines
    df = df.drop_duplicates(subset=["player", "outlet", "sentence"])
    counts = df.groupby("player").size()
    keep = counts[counts >= MIN_PER_PLAYER].index
    df = df[df.player.isin(keep)].sort_values(["date", "outlet"])

    rows = []
    for r in df.itertuples():
        s = r.sentence
        m = TERM_RX.search(s)
        if not m:
            continue
        # a very long sentence is cut to a window around the foul word
        if len(s) > MAX_LEN:
            start = max(0, m.start() - MAX_LEN // 2)
            end = min(len(s), start + MAX_LEN)
            piece = s[start:end]
            if start:
                piece = "…" + piece.split(" ", 1)[-1]
            if end < len(s):
                piece = piece.rsplit(" ", 1)[0] + "…"
            s = piece
            m = TERM_RX.search(s)
            if not m:
                continue
        # where the player's own name sits, for its highlight
        name = NAME_RX[r.player].search(s) if r.player in NAME_RX else None
        rows.append({
            "p": r.player,
            "o": r.outlet,
            "d": str(r.date)[:10],
            "u": r.url,
            "h": bool(r.in_headline),
            "s": s,
            "t": [m.start(), m.end()],
            "n": [name.start(), name.end()] if name else None,
        })
    players = {p: int(n) for p, n in counts[keep].sort_values(ascending=False).items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"players": players, "rows": rows}, ensure_ascii=False))
    print(f"{len(rows):,} sentences · {len(players)} players · {OUT.stat().st_size / 1e6:.1f} MB")
    for p, n in list(players.items())[:10]:
        fox = sum(1 for x in rows if x["p"] == p and x["o"] == "Fox News")
        print(f"  {p:22} {n:5}  Fox {fox}")


if __name__ == "__main__":
    main()
