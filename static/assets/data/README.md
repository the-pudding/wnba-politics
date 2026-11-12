# How Fox News and other outlets cover WNBA players

Data from The Pudding's story on Fox News and the WNBA, by Melanie Walsh and Jan Diehm.

The coverage goes from January 2019 to November 1, 2026 and compares Fox News (with OutKick, its sports site) against six other outlets: ESPN (with Andscape), CBS, USA Today, The New York Times (with The Athletic), AP and The Washington Post. The data focuses on the 34 players named most by Fox News (plus Gabby Williams). Chyrons drawn from Third Eye Internet Archive project.

## player_coverage.csv

How often each outlet named each player, by year. One row per player, outlet and year, plus an `all` row for the whole period.

| Column | Description |
|---|---|
| player | The player |
| outlet | The outlet |
| year | Calendar year, or `all` |
| headlines | That outlet's WNBA headlines naming her that year |
| articles | That outlet's WNBA articles naming her (in the headline or the text) |
| outlet_headlines | All of that outlet's WNBA headlines that year |
| outlet_articles | All of that outlet's WNBA articles that year |
| headline_share | headlines ÷ outlet_headlines |
| article_share | articles ÷ outlet_articles |

## player_summary_dot_plot.csv

Fox News against the six other outlets pooled, showing ratios that are used in the first dot plot with the players' faces.

| Column | Description |
|---|---|
| player | The player |
| year | Calendar year, or `all` |
| fox_headlines | Fox headlines naming her |
| fox_headline_share | fox_headlines as a share of all of Fox's WNBA headlines |
| other_headlines | The six other outlets' headlines naming her, together |
| other_headline_share | other_headlines as a share of all six outlets' WNBA headlines |
| fox_to_others_headline_ratio | fox_headline_share ÷ other_headline_share: how many times more of its headline coverage Fox gives her (above 1: Fox more; below 1: the other outlets more; 0: Fox never named her; blank: the other outlets never did) |
| fox_articles | Fox articles naming her, in the headline or the text |
| fox_article_share | fox_articles as a share of all of Fox's WNBA articles |
| other_articles | The six other outlets' articles naming her, together |
| other_article_share | other_articles as a share of all six outlets' WNBA articles |
| fox_to_others_article_ratio | fox_article_share ÷ other_article_share: the same ratio as above, for articles |

## player_chyrons.csv

TV: on-screen captions (chyrons) that mention the WNBA on cable news, sampled about once a minute (Internet Archive TV News, via the Third Eye project), 2017 on. One row per player, channel and year.

| Column | Description |
|---|---|
| player | The player |
| channel | Fox News, CNN, MSNBC (including MS NOW, its new name) |
| year | Calendar year |
| chyrons_naming_player | WNBA captions naming her |
| total_wnba_chyrons | All of that channel's WNBA captions that year (per channel and year, not across channels) |

## player_framing_fox.csv

How Fox News frames each player in its headlines.

Topics were tagged with keywords, an LLM classifier and manual labelling. Appearance, celebrity and performance tags count only headlines that describe the player.

| Column | Description |
|---|---|
| player | The player |
| fox_headlines | Fox headlines naming her |
| political_headlines | Fox headlines naming her that are political (race, LGBTQ+ issues, the culture war, transgender athletes and women's sports, activism, patriotism, politicians and government) |
| political_share | political_headlines ÷ fox_headlines |
| appearance_headlines | Fox headlines about her looks |
| appearance_share | appearance_headlines ÷ fox_headlines |
| celebrity_headlines | Fox headlines about her fame or celebrity (includes appearance) |
| celebrity_share | celebrity_headlines ÷ fox_headlines |
| performance_headlines | Fox headlines about her basketball play |
| performance_share | performance_headlines ÷ fox_headlines |
| mean_tone | Average tone of her headlines, from a sentiment model, −1 (negative) to 1 (positive) |

## fox_headlines.csv

Every Fox News and OutKick WNBA article in the story, one row each. Tone calculated with a RoBERTa sentiment model.

| Column | Description |
|---|---|
| date | The article's publication date |
| outlet | Fox News or OutKick |
| headline | The article's headline |
| url | The article's web address |
| author | The byline, if it has one |
| people | People named in the headline, separated by semicolons |
| political | `political` if the headline is political, otherwise blank |
| appearance | The players whose looks the headline is about, if any (separated by semicolons) |
| celebrity | The players the headline treats as celebrities, if any (separated by semicolons) |
| performance | The players whose basketball play the headline is about, if any (separated by semicolons) |
| tone | The headline's tone from a sentiment model: negative, neutral or positive |
| tone_score | −1 (negative) to 1 (positive) |

