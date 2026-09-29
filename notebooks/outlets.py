"""The one list of outlets the piece compares, for every notebook and script.

    
"""
import json
from pathlib import Path

# 2026-09-28: the brand-level comparison. Sister outlets are bundled by
# notebooks/bundle_outlets.py into one corpus each (the member's own name
# survives in the `source` column): Fox News = Fox News + OutKick; New York
# Times = NYT + The Athletic; CBS Sports = CBS Sports + CBS News (incl. its
# local stations). Fox Sports (too patchy), Just Women's Sports, CNN, NBC News,
# NPR, the right-wing sites and BroBible stay on disk but are off the site. The previous registry is in git history.
OUTLETS = [
    # key                 label                  group     logo                   short
    ("fox_wnba",          "Fox News",            "fox",    "fox-news.svg",        "Fox"),
    ("espn_bundle",       "ESPN",                "outlet", "espn.svg",            "ESPN"),
    ("cbs_bundle",        "CBS",                 "outlet", "cbs.svg",             "CBS"),
    ("usa_today",         "USA Today",           "outlet", "usa-today.svg",       "USA Today"),
    ("nyt_bundle",        "New York Times",      "outlet", "nyt.svg",             "NYT"),
    ("ap",                "AP",                  "outlet", "ap.svg",              "AP"),
    ("washington_post",   "Washington Post",     "outlet", "washington-post.svg", "Post"),
]
# what each bundle contains, for captions and the sources table
MEMBERS = {"Fox News": ["Fox News", "OutKick"], "ESPN": ["ESPN", "Andscape"], "New York Times": ["New York Times", "The Athletic"],
           "CBS": ["CBS Sports", "CBS News"]}
FILES = {label: f"{key}.csv" for key, label, *_ in OUTLETS}          # label -> file
KEYS = {label: key for key, label, *_ in OUTLETS}
LABELS = {key: label for key, label, *_ in OUTLETS}
GROUP = {label: group for key, label, group, *_ in OUTLETS}
LOGO = {label: logo for key, label, group, logo, _ in OUTLETS}
SHORT = {label: short for key, label, group, logo, short in OUTLETS}
SPORTS = [label for key, label, group, *_ in OUTLETS if group == "sports"]
NEWS = [label for key, label, group, *_ in OUTLETS if group == "news"]
COMPARISON = [label for key, label, group, *_ in OUTLETS if group in ("sports", "news", "outlet")]   # everyone but Fox
# the pools the pickers offer beside each outlet on its own: only those with members
GROUPS = {name: members for name, members in (("sports outlets", SPORTS), ("news outlets", NEWS),
                                              ("all outlets", COMPARISON)) if members}

def write_json(path=None):
    path = Path(path or Path(__file__).resolve().parents[1] / "src/data/outlets.json")
    path.write_text(json.dumps({
        "outlets": [{"key": k, "label": l, "group": g, "logo": lo, "short": s} for k, l, g, lo, s in OUTLETS],
        "groups": GROUPS,
        "members": MEMBERS}, indent=1))
    return path

if __name__ == "__main__":
    print(write_json())
