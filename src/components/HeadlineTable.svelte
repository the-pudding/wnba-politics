<script>
	// Every Fox News WNBA headline: searchable, sortable, RoBERTa-scored, every
	// row linking back to its article.
	// Doc embed:  chart: headline-table
	//             chart: headline-table | words: Sophie Cunningham, Brittney Griner
	import data from "$data/fox_player_headlines.json";
	import sentiment from "$data/headline_sentiment.json";

	let { words = [], title = "", caption = "" } = $props();

	const PLAYER_COLORS = {
		"Caitlin Clark": "#2a78d6",
		"Angel Reese": "#eb6834",
		"Brittney Griner": "#7a6bcc",
		"Sophie Cunningham": "#b04ac2",
		"DiJonai Carrington": "#d55181",
		"Natasha Cloud": "#1f9d6e"
	};
	const OTHER_COLOR = "#8a6d3b";
	const PAGE = 60;
	const MAX_TAGS = 3;

	const players = words.length ? words : data.players;

	let search = $state("");
	let activePlayers = $state([]);
	let sortBy = $state("date");
	let ascending = $state(true);
	let mood = $state("all");
	let shown = $state(PAGE);

	const scoreOf = (headline) => sentiment.scores[headline];
	const labelOf = (headline) => sentiment.labels[headline] ?? "unscored";

	function togglePlayer(name) {
		activePlayers = activePlayers.includes(name)
			? activePlayers.filter((p) => p !== name)
			: [...activePlayers, name];
	}

	function sortByColumn(column) {
		if (sortBy === column) ascending = !ascending;
		else {
			sortBy = column;
			ascending = true;
		}
	}

	const filtering = $derived(Boolean(search.trim() || activePlayers.length || mood !== "all"));

	let rows = $derived.by(() => {
		const term = search.trim().toLowerCase();
		const filtered = data.rows.filter((row) => {
			if (activePlayers.length && !row.p.some((p) => activePlayers.includes(p))) return false;
			if (mood !== "all" && labelOf(row.t) !== mood) return false;
			if (term && !row.t.toLowerCase().includes(term)
				&& !row.p.some((p) => p.toLowerCase().includes(term))) return false;
			return true;
		});
		// unscored rows stay at the bottom in either sort direction
		const sortable = sortBy === "sentiment"
			? filtered.filter((row) => scoreOf(row.t) !== undefined)
			: filtered;
		const leftovers = sortBy === "sentiment"
			? filtered.filter((row) => scoreOf(row.t) === undefined)
			: [];

		const sorted = [...sortable].sort((a, b) =>
			sortBy === "sentiment"
				? scoreOf(a.t) - scoreOf(b.t)
				: (a.d < b.d ? -1 : a.d > b.d ? 1 : 0));
		if (!ascending) sorted.reverse();
		return [...sorted, ...leftovers];
	});

	$effect(() => {
		search; activePlayers; sortBy; ascending; mood;
		shown = PAGE;
	});
	let visibleRows = $derived(rows.slice(0, shown));

	function visibleTags(row) {
		const rank = (name) => (activePlayers.includes(name) ? 0 : players.includes(name) ? 1 : 2);
		return [...row.p].sort((a, b) => rank(a) - rank(b)).slice(0, MAX_TAGS);
	}

	const escapeHtml = (text) => text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	function withHighlight(headline) {
		const safe = escapeHtml(headline);
		const term = search.trim();
		if (term.length < 2) return safe;
		const pattern = new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "ig");
		return safe.replace(pattern, (match) => `<mark>${match}</mark>`);
	}

	const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
	                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	const prettyDate = (iso) => {
		const [year, month, day] = iso.split("-");
		return `${MONTHS[+month - 1]} ${+day}, ${year}`;
	};

	const BAR_HALF = 26;
	const barWidth = (score) => Math.abs(score) * BAR_HALF;
	const barColor = (score) => (score < -0.05 ? "var(--color-fox)" : score > 0.05 ? "#1f9d6e" : "rgba(42,21,3,0.3)");

	let summary = $derived.by(() => {
		const total = data.rows.length.toLocaleString();
		if (!filtering) return `All ${total} Fox News WNBA headlines, 2019 to 2026.`;
		if (!rows.length) return "Nothing matches those filters.";
		const bits = [];
		if (search.trim()) bits.push(`matching “${search.trim()}”`);
		if (activePlayers.length) bits.push(`naming ${activePlayers.join(" or ")}`);
		if (mood !== "all") bits.push(`scored ${mood}`);
		return `${rows.length.toLocaleString()} of ${total} headlines ${bits.join(", ")}.`;
	});

	const clearAll = () => { activePlayers = []; search = ""; mood = "all"; };
</script>

<section class="headline-browser">
	<header class="lede">
		<p class="kicker">The data</p>
		<h3>{title ? title : "Read every headline yourself"}</h3>
		<p class="standfirst">
			All <strong>{data.rows.length.toLocaleString()}</strong> WNBA headlines Fox News published
			between July 2019 and August 2026, with the sentiment score the model gave each one.
			Search it, sort it, and follow any row back to the article.
		</p>
	</header>

	<div class="controls">
		<input
			type="search"
			placeholder="Search"
			bind:value={search}
			aria-label="Search headlines"
		/>
		<div class="toggle-group" role="group" aria-label="Filter by sentiment">
			{#each ["all", "negative", "neutral", "positive"] as option}
				<button class:active={mood === option} onclick={() => (mood = option)}>{option}</button>
			{/each}
		</div>
	</div>

	<div class="chips">
		{#each players as name}
			<button
				class="chip"
				class:on={activePlayers.includes(name)}
				style="--chip:{PLAYER_COLORS[name] ?? OTHER_COLOR}"
				onclick={() => togglePlayer(name)}
			>{name}</button>
		{/each}
		{#if filtering}
			<button class="chip clear" onclick={clearAll}>clear all</button>
		{/if}
	</div>

	<p class="count" aria-live="polite">{summary}</p>

	<div class="scroller">
		<table>
			<thead>
				<tr>
					<th class="col-date">
						<button onclick={() => sortByColumn("date")} class:sorted={sortBy === "date"}>
							Date <span class="arrow">{sortBy === "date" ? (ascending ? "↑" : "↓") : "↕"}</span>
						</button>
					</th>
					<th class="col-head">Headline</th>
					<th class="col-who">Names</th>
					<th class="col-mood">
						<button onclick={() => sortByColumn("sentiment")} class:sorted={sortBy === "sentiment"}>
							Sentiment <span class="arrow">{sortBy === "sentiment" ? (ascending ? "↑" : "↓") : "↕"}</span>
						</button>
					</th>
				</tr>
			</thead>
			<tbody>
				{#each visibleRows as row (row.d + row.t)}
					{@const score = scoreOf(row.t)}
					<tr>
						<td class="col-date">{prettyDate(row.d)}</td>
						<td class="col-head">
							{#if row.u}
								<a href={row.u} target="_blank" rel="noreferrer">{@html withHighlight(row.t)}</a>
							{:else}
								{@html withHighlight(row.t)}
							{/if}
						</td>
						<td class="col-who">
							{#each visibleTags(row) as name}
								<span class="tag" style="background:{PLAYER_COLORS[name] ?? OTHER_COLOR}">
									{name.split(" ").slice(-1)[0]}
								</span>
							{/each}
						</td>
						<td class="col-mood">
							{#if score === undefined}
								<span class="unscored">—</span>
							{:else}
								<span class="meter" title="{labelOf(row.t)} ({score.toFixed(2)})">
									<span class="midline"></span>
									<span
										class="fill"
										style="width:{barWidth(score)}px; background:{barColor(score)};
											{score < 0 ? `right:${BAR_HALF}px` : `left:${BAR_HALF}px`}"
									></span>
								</span>
								<span class="score" style="color:{barColor(score)}">{score.toFixed(2)}</span>
							{/if}
						</td>
					</tr>
				{:else}
					<tr><td colspan="4" class="empty">
						Nothing matches those filters. <button class="link" onclick={clearAll}>Clear them</button>
					</td></tr>
				{/each}
			</tbody>
		</table>

		{#if rows.length > shown}
			<button class="more" onclick={() => (shown += PAGE)}>
				Show {Math.min(PAGE, rows.length - shown).toLocaleString()} more
				<span>({(rows.length - shown).toLocaleString()} left)</span>
			</button>
		{/if}
	</div>

	<p class="chart-caption">
		{#if caption}{@html caption}{:else}
			Headlines collected from Fox News and OutKick. Sentiment is a five-class RoBERTa classifier
			scored as an expected value from −1 to +1; it reads tone, not accuracy or bias.
		{/if}
	</p>
</section>

<style>
	.headline-browser {
		--ink: #1c1917;
		--muted: rgba(28, 25, 23, 0.55);
		--rule: rgba(28, 25, 23, 0.14);
		--accent: var(--color-fox);
		--field-edge: rgba(28, 25, 23, 0.22);
		--field-shadow: 0 1px 0 rgba(28, 25, 23, 0.05);
		--sans: "Helvetica Neue", Helvetica, Arial, sans-serif;

		width: min(1000px, 94vw);
		margin: 46px auto 0;
		margin-left: 50%;
		transform: translateX(-50%);
		font-family: var(--sans);
		color: var(--ink);
	}

	.lede { max-width: 640px; margin: 0 auto 22px; text-align: center; }
	.kicker {
		font-size: 11px; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase;
		color: var(--accent); margin: 0 0 10px;
	}
	.lede h3 {
		font-family: Georgia, "Times New Roman", serif;
		font-size: 34px; font-weight: 400; line-height: 1.1; letter-spacing: -0.01em;
		margin: 0 0 10px; color: var(--ink);
	}
	.standfirst { font-size: 14px; line-height: 1.55; color: var(--muted); margin: 0; }
	.standfirst strong { color: var(--ink); font-weight: 700; }

	.controls { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; align-items: stretch; }
	input[type="search"] {
		flex: 1; min-width: 240px;
		padding: 0 14px; height: 40px;
		font-family: var(--sans); font-size: 14.5px;
		border: 1px solid var(--field-edge); border-radius: 3px;
		background: #fff; color: var(--ink);
		box-shadow: var(--field-shadow);
	}
	input[type="search"]::placeholder { color: var(--muted); }
	input[type="search"]:focus { outline: 0; border-color: var(--accent); }

	.toggle-group {
		display: inline-flex; height: 40px;
		background: #fff; border: 1px solid var(--field-edge); border-radius: 3px;
		box-shadow: var(--field-shadow); overflow: hidden;
	}
	.toggle-group button {
		border: 0; border-left: 1px solid var(--rule);
		/* the global button reset rounds every corner to 8px */
		border-radius: 0;
		background: transparent; color: var(--muted);
		padding: 0 14px; font-family: var(--sans);
		font-size: 11px; font-weight: 700; letter-spacing: 0.09em; text-transform: uppercase;
		cursor: pointer;
	}
	/* the rounded group clips its children — round the end buttons to match */
	.toggle-group button:first-child { border-left: 0; border-radius: 2px 0 0 2px; }
	.toggle-group button:last-child { border-radius: 0 2px 2px 0; }
	.toggle-group button:hover { color: var(--ink); background: rgba(28, 25, 23, 0.04); }
	.toggle-group button.active { color: #fff; background: var(--ink); }

	.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
	.chip {
		border: 1px solid var(--field-edge);
		background: #fff; color: var(--ink);
		font-family: var(--sans); font-size: 12px; font-weight: 600;
		padding: 6px 13px; border-radius: 3px; cursor: pointer;
		box-shadow: var(--field-shadow);
	}
	.chip:hover { border-color: var(--chip, var(--ink)); }
	.chip.on { background: var(--chip, #7a6bcc); border-color: var(--chip, #7a6bcc); color: #fff; }
	.chip.clear { color: var(--accent); }

	.count {
		font-size: 12px; font-weight: 600; letter-spacing: 0.02em;
		color: rgba(28, 25, 23, 0.7); margin: 0 0 7px;
	}

	.scroller {
		max-height: 68vh; overflow-y: auto;
		background: #fff; border-top: 2px solid var(--ink);
	}

	table { width: 100%; border-collapse: collapse; }
	thead th {
		position: sticky; top: 0; z-index: 1;
		background: #fff;
		text-align: left;
		font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em;
		color: var(--muted); font-weight: 700;
		padding: 9px 12px 8px 0; border-bottom: 1px solid var(--rule);
		white-space: nowrap;
	}
	thead th:first-child { padding-left: 14px; }
	thead th:last-child { padding-right: 14px; }
	thead button {
		border: 0; background: transparent; padding: 0; cursor: pointer;
		font: inherit; color: inherit; letter-spacing: inherit; text-transform: inherit;
	}
	thead button:hover { color: var(--ink); }
	thead button.sorted { color: var(--ink); }
	.arrow { opacity: 0.4; }
	thead button.sorted .arrow { opacity: 1; color: var(--accent); }

	tbody td { padding: 10px 12px 10px 0; vertical-align: baseline; border-bottom: 1px solid var(--rule); }
	tbody td:first-child { padding-left: 14px; }
	tbody td:last-child { padding-right: 14px; }
	tbody tr:hover td { background: rgba(28, 25, 23, 0.045); }

	.col-date { width: 96px; white-space: nowrap; }
	tbody .col-date {
		font-size: 11px; font-variant-numeric: tabular-nums;
		letter-spacing: 0.03em; color: var(--muted);
	}
	tbody .col-head {
		font-family: Georgia, "Times New Roman", serif;
		font-size: 15px; line-height: 1.35; color: var(--ink);
	}
	.col-head a { color: inherit; text-decoration: none; background-image: linear-gradient(var(--rule), var(--rule)); background-size: 100% 1px; background-position: 0 100%; background-repeat: no-repeat; }
	.col-head a:hover { background-image: linear-gradient(var(--accent), var(--accent)); background-size: 100% 2px; }
	.col-who { width: 128px; }
	.col-mood { width: 108px; white-space: nowrap; }

	.tag {
		display: inline-block; margin: 0 4px 3px 0;
		font-size: 9px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
		color: #fff; padding: 2px 6px; border-radius: 2px;
	}

	.meter { position: relative; display: inline-block; width: 52px; height: 10px; vertical-align: middle; }
	.meter .midline { position: absolute; left: 26px; top: 0; width: 1px; height: 100%; background: rgba(28, 25, 23, 0.25); }
	.meter .fill { position: absolute; top: 2px; height: 6px; }
	.score { font-size: 11px; margin-left: 7px; font-variant-numeric: tabular-nums; font-weight: 700; }
	.unscored { color: rgba(28, 25, 23, 0.3); }

	.empty { text-align: center; padding: 34px 12px; color: var(--muted); font-size: 14px; }
	.link {
		border: 0; background: none; padding: 0; font: inherit; cursor: pointer;
		color: var(--accent); text-decoration: underline;
	}

	.more {
		display: block; width: 100%; margin: 0; padding: 14px; border-radius: 0;
		border: 0; border-bottom: 1px solid var(--rule);
		background: transparent; color: var(--ink);
		font-family: var(--sans);
		font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
		cursor: pointer;
	}
	.more:hover { color: var(--accent); }
	.more span { font-weight: 500; letter-spacing: 0.04em; text-transform: none; color: var(--muted); }

	.chart-caption {
		font-size: 11.5px; line-height: 1.6; color: var(--muted);
		text-align: center; max-width: 620px; margin: 16px auto 0;
	}

	.col-head :global(mark) {
		background: transparent; color: inherit; font-weight: 700;
		box-shadow: inset 0 -0.55em 0 rgba(255, 224, 138, 0.85);
	}

	@media (max-width: 700px) {
		.col-who { display: none; }
		.lede h3 { font-size: 25px; }
	}
</style>
