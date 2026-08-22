"""Move the review sheet between Google Sheets and the repo.

The framing-review Google Sheet and data/framing_review.csv hold the same
table: every Fox headline with editable political / appearance / celebrity /
victim columns. Edits flow both ways:

    python3 tasks/review_sheet.py pull    # sheet -> data/framing_review.csv
                                          # (runs as part of npm run gdoc)
    python3 tasks/review_sheet.py push    # data/framing_review.csv -> sheet
                                          # (npm run sheetpush; run after
                                          # notebook 04 refreshes the CSV)

The sheet is private, so both directions use the service account in
~/.config/gspread/service_account.json, which has Editor access. The term
sheets are separate: those are public, pulled by npm run gdoc directly, and
never pushed back.
"""
import csv
import sys
from pathlib import Path

import gspread

SHEET_ID = "13RE_msKDrt6Ma_RJNIVgHyn3zXgexhdxqi5aJKncOhk"
CSV = Path(__file__).resolve().parent.parent / "data" / "framing_review.csv"


def main():
    direction = sys.argv[1] if len(sys.argv) > 1 else ""
    ws = gspread.service_account().open_by_key(SHEET_ID).sheet1
    if direction == "push":
        rows = list(csv.reader(CSV.open()))
        ws.clear()
        # RAW keeps every cell exactly as written — a headline starting with
        # an apostrophe stays that way instead of Sheets eating the apostrophe
        ws.update(rows, value_input_option="RAW")
        print(f"pushed {len(rows) - 1:,} headlines to the framing-review sheet")
    elif direction == "pull":
        rows = ws.get_all_values()
        with CSV.open("w", newline="") as f:
            csv.writer(f).writerows(rows)
        print(f"pulled {len(rows) - 1:,} headlines from the framing-review sheet")
    else:
        sys.exit("usage: python3 tasks/review_sheet.py pull|push")


if __name__ == "__main__":
    main()
