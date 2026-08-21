# How Does Fox News Frame the WNBA?

A data-driven essay about how Fox News covers the WNBA, and how differently everyone else does.

## The site

A [SvelteKit](https://kit.svelte.dev/) app built on [The Pudding's svelte-starter](https://github.com/the-pudding/svelte-starter), using [ArchieML](http://archieml.org/) for a micro-CMS powered by Google Docs.

### Development

``` bash
npm install
npm run dev
```

### Deploy

``` bash
npm run build
```

This generates a directory called `build` with the statically rendered app. Pushing to `main` builds and deploys it to GitHub Pages automatically.

## The data (`data/`)

Every WNBA/NBA article we collected.

| file | articles | text | source |
|------------------|------------------|------------------|------------------|
| `fox_wnba.csv` | \~2,200 | full text | Fox's own tag feeds |
| `fox_nba.csv` | \~10,700 | full text | Fox's NBA tag feeds |
| `yahoo_sports.csv` | \~28,500 | full text | their syndication pool |
| `espn.csv` | \~5,700 | full text | ESPN's API |
| `just_womens_sports.csv` | \~3,200 | full text | their WordPress API |
| `the_athletic.csv` | \~2,500 | headlines | sitemaps (bodies paywalled) |
| `cbs_sports.csv` | \~3,200 | headlines | Wayback crawl index |
| `usa_today.csv` | \~2,700 | headlines | Wayback crawl index |
| `all_outlets_index.csv` | \~59,000 | index only | everything in one sheet |
| `chyron_words.csv` | — | — | TV chyrons via the Internet Archive's Third Eye |

Notebook 06 concatenates all of these into `all_outlets_full.csv` (\~170MB, gitignored) — every outlet and full body text in one file, for Google Drive.

## The notebooks (`notebooks/`)

1.  **01-fightin-words** — fightin words plots
2.  **02-topic-rates** — calculating the share of each outlet's articles touching race/BLM and LGBTQ topics
3.  **03-chyron-ternary** — each network's most distinctive chyron words
4.  **04-player-framing** — politicization, appearance & celebrity treatment, etc.
5.  **05-headline-sentiment** — every headline scored by RoBERTa sentiment analysis
6.  **06-full-corpus-csv** — builds `data/all_outlets_full.csv`, the one-file corpus for Google Drive
7.  **07-fox-timeline** — the monthly Fox WNBA timeline with topic and player layers, the NBA backdrop, and the trans-article list
8.  **08-outlet-topics** — race/politics and LGBTQ rates per outlet per year, and the who-gets-covered dot plot
9.  **09-fightin-words-grid** — the full fightin-words grids (headlines and article text, per outlet and per player) with example lookups
10. **10-headline-networks** — who Fox names together, in headlines and in articles; the cast of tracked people is an editable table at the top
11. **11-chyrons** — the cable-chyron analysis: monthly mentions per network, the ternary word-shares, and per-player word associations
12. **12-player-words** — what each player does vs. what is done to her, in Fox's sentences vs. everyone else's

Notebooks 7–12 regenerate the chart data in `src/data/` from the corpora in
`data/` — the site's numbers can be reproduced (and edited) entirely from this
repo. The topic vocabularies are plain term lists in `data/topic_terms.csv`
and `data/politicization_terms.csv`: one term per row, rows are OR-ed together.

``` bash
pip install pandas jupyter
jupyter lab notebooks/
```