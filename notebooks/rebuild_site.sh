#!/bin/bash
# rebuild every chart's data from the corpora in data/; run from anywhere
cd "$(dirname "$0")/.."
run() { echo; echo "=== $(date '+%H:%M:%S') $*"; "$@" 2>&1 | grep -v "Warning\|warn(\|Kernel is running\|IPKernelApp\|Inference\|Map:" || echo "!!! FAILED: $*"; }
nb() { (cd notebooks && python3 run_nb.py "$1"); }
run python3 notebooks/fox_corpus_filter.py
run python3 notebooks/outlet_corpus_filter.py
run python3 notebooks/bundle_outlets.py
run nb 03-full-corpus-csv.ipynb
run nb 07-headline-networks.ipynb
run nb 01-player-framing.ipynb
run python3 tasks/review_sheet.py push
run nb 02-headline-sentiment.ipynb
run nb 04-fox-timeline.ipynb
run nb 05-outlet-topics.ipynb
run python3 notebooks/outlet_topics_monthly.py
run nb 06-fightin-words-grid.ipynb
run python3 notebooks/player_sentences.py
rm -f notebooks/.cache/fox_parsed.json notebooks/.cache/others_parsed.json
run nb 09-player-words.ipynb
run python3 notebooks/sentence_framing.py
run python3 notebooks/cast_gap.py
run python3 notebooks/pair_gap.py
run python3 notebooks/word_timeline.py
run python3 notebooks/word_neighbors.py
run python3 notebooks/word_players.py
run python3 notebooks/player_phrases.py
run python3 notebooks/foul_feed.py
run python3 notebooks/trans_by_outlet.py
echo; echo "=== $(date '+%H:%M:%S') ROSTER PIPELINE DONE"
