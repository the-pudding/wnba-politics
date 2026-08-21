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

``` bash
pip install pandas jupyter
jupyter lab notebooks/
```