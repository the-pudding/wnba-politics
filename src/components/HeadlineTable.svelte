<script>
	// Every Fox News WNBA headline
	import headlineRows from "$data/fox_player_headlines.csv";
	import sentimentRows from "$data/headline_sentiment.csv";
	import labelRows from "$data/labeled_headlines.csv";

	const data = {
		rows: headlineRows.map((r) => ({
			d: r.date,
			t: r.title,
			u: r.url,
			p: r.players ? r.players.split("; ") : []
		}))
	};
	// which measures each headline triggered (from the player-framing notebook)
	const FRAMES = [
		"political",
		"appearance",
		"celebrity",
		"victim",
		"performance"
	];
	const FRAME_COLORS = {
		political: "var(--color-politics)",
		appearance: "var(--color-race)",
		celebrity: "var(--color-lgbtq)",
		victim: "var(--color-fox)",
		performance: "#1f9d6e"
	};
	const frames = Object.fromEntries(
		labelRows.map((r) => [r.headline, FRAMES.filter((f) => r[f])])
	);
	const framesOf = (headline) => frames[headline] ?? [];

	const sentiment = {
		scores: Object.fromEntries(
			sentimentRows.map((r) => [r.headline, +r.score])
		),
		labels: Object.fromEntries(sentimentRows.map((r) => [r.headline, r.label]))
	};

	let {
		words = [],
		title = "",
		caption = "",
		// set by the framing tabs: which measure's headlines to show
		frame: frameProp = null,
		// under the beeswarm: no lede, the tabs' width, no player chips
		embedded = false,
		// set from outside (a face clicked on the beeswarm): the players to show
		players: playersProp = null
	} = $props();

	const PLAYER_COLORS = {
		"Caitlin Clark": "#2a78d6",
		"Angel Reese": "#eb6834",
		"Brittney Griner": "#7a6bcc",
		"Sophie Cunningham": "#b04ac2",
		"DiJonai Carrington": "#d55181",
		"Natasha Cloud": "#1f9d6e"
	};
	const OTHER_COLOR = "#8a6d3b";
	const MAX_TAGS = 3;

	const players = words.length ? words : Object.keys(PLAYER_COLORS);

	// on a phone the embedded table hides behind a bar: a tall scroll region
	// in the middle of the page catches the finger and stops the page scrolling
	let narrow = $state(false);
	let open = $state(false);
	$effect(() => {
		const query = window.matchMedia("(max-width: 640px)");
		const sync = () => (narrow = query.matches);
		sync();
		query.addEventListener("change", sync);
		return () => query.removeEventListener("change", sync);
	});
	// on a phone the table always starts collapsed, embedded or not
	let collapsed = $derived(narrow && !open);

	let search = $state("");
	let activePlayers = $state([]);
	let sortBy = $state("date");
	let ascending = $state(true);
	let mood = $state("all");
	let frame = $state("all");
	$effect(() => {
		if (frameProp !== null) frame = frameProp;
	});
	$effect(() => {
		if (playersProp !== null) activePlayers = playersProp;
	});

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

	const filtering = $derived(
		Boolean(
			search.trim() || activePlayers.length || mood !== "all" || frame !== "all"
		)
	);

	let rows = $derived.by(() => {
		const term = search.trim().toLowerCase();
		const filtered = data.rows.filter((row) => {
			if (activePlayers.length && !row.p.some((p) => activePlayers.includes(p)))
				return false;
			if (mood !== "all" && labelOf(row.t) !== mood) return false;
			if (frame !== "all" && !framesOf(row.t).includes(frame)) return false;
			if (
				term &&
				!row.t.toLowerCase().includes(term) &&
				!row.p.some((p) => p.toLowerCase().includes(term))
			)
				return false;
			return true;
		});
		// unscored rows stay at the bottom in either sort direction
		const sortable =
			sortBy === "sentiment"
				? filtered.filter((row) => scoreOf(row.t) !== undefined)
				: filtered;
		const leftovers =
			sortBy === "sentiment"
				? filtered.filter((row) => scoreOf(row.t) === undefined)
				: [];

		const sorted = [...sortable].sort((a, b) =>
			sortBy === "sentiment"
				? scoreOf(a.t) - scoreOf(b.t)
				: a.d < b.d
					? -1
					: a.d > b.d
						? 1
						: 0
		);
		if (!ascending) sorted.reverse();
		return [...sorted, ...leftovers];
	});

	function visibleTags(row) {
		const rank = (name) =>
			activePlayers.includes(name) ? 0 : players.includes(name) ? 1 : 2;
		return [...row.p].sort((a, b) => rank(a) - rank(b)).slice(0, MAX_TAGS);
	}

	const escapeHtml = (text) =>
		text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	function withHighlight(headline) {
		const safe = escapeHtml(headline);
		const term = search.trim();
		if (term.length < 2) return safe;
		const pattern = new RegExp(
			term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
			"ig"
		);
		return safe.replace(pattern, (match) => `<mark>${match}</mark>`);
	}

	const MONTHS = [
		"Jan",
		"Feb",
		"Mar",
		"Apr",
		"May",
		"Jun",
		"Jul",
		"Aug",
		"Sep",
		"Oct",
		"Nov",
		"Dec"
	];
	const prettyDate = (iso) => {
		const [year, month, day] = iso.split("-");
		return `${MONTHS[+month - 1]} ${+day}, ${year}`;
	};

	const BAR_HALF = 26;
	const barWidth = (score) => Math.abs(score) * BAR_HALF;
	const barColor = (score) =>
		score < -0.05
			? "var(--color-fox)"
			: score > 0.05
				? "#1f9d6e"
				: "rgba(42,21,3,0.3)";

	let summary = $derived.by(() => {
		const total = data.rows.length.toLocaleString();
		if (!filtering)
			return `All ${total} Fox News WNBA headlines, 2019 to 2026.`;
		if (!rows.length) return "Nothing matches those filters.";
		const bits = [];
		if (search.trim()) bits.push(`matching “${search.trim()}”`);
		if (activePlayers.length) bits.push(`naming ${activePlayers.join(" or ")}`);
		if (mood !== "all") bits.push(`scored ${mood}`);
		if (frame !== "all")
			bits.push(
				`about ${frame === "victim" ? "victim framing" : frame === "political" ? "politics" : frame === "performance" ? "her play" : frame}`
			);
		return `${rows.length.toLocaleString()} of ${total} headlines ${bits.join(", ")}.`;
	});

	const clearAll = () => {
		activePlayers = [];
		search = "";
		mood = "all";
		frame = "all";
	};
</script>

<section class="headline-browser" class:embedded>
	{#if !embedded}<header class="lede">
			<p class="kicker">The data</p>
			<h3>{title ? title : "Read every headline yourself"}</h3>
			<p class="standfirst">
				All <strong>{data.rows.length.toLocaleString()}</strong> WNBA headlines Fox
				News published between July 2019 and August 2026, with the sentiment score
				the model gave each one. Search it, sort it, and follow any row back to the
				article.
			</p>
		</header>{/if}

	<div class="controls">
		<input
			type="search"
			placeholder="Search"
			bind:value={search}
			aria-label="Search headlines"
		/>
		<div class="toggle-group" role="group" aria-label="Filter by sentiment">
			{#each ["all", "negative", "neutral", "positive"] as option}
				<button class:active={mood === option} onclick={() => (mood = option)}
					>{option}</button
				>
			{/each}
		</div>
		<div
			class="toggle-group"
			role="group"
			aria-label="Filter by what the headline is about"
		>
			{#each ["all", ...FRAMES] as option}
				<button class:active={frame === option} onclick={() => (frame = option)}
					>{option}</button
				>
			{/each}
		</div>
	</div>

	<div class="chips" class:hidden={embedded}>
		{#each players as name}
			<button
				class="chip"
				class:on={activePlayers.includes(name)}
				style="--chip:{PLAYER_COLORS[name] ?? OTHER_COLOR}"
				onclick={() => togglePlayer(name)}>{name}</button
			>
		{/each}
		{#if filtering}
			<button class="chip clear" onclick={clearAll}>clear all</button>
		{/if}
	</div>

	<p class="count" aria-live="polite">{summary}</p>

	{#if narrow}
		<button class="reveal" onclick={() => (open = !open)} aria-expanded={open}>
			{open ? "Hide the headlines" : "See the headlines"}
			<span class="caret">{open ? "▴" : "▾"}</span>
		</button>
	{/if}
	<div class="scroller" class:short={narrow} hidden={collapsed}>
		<table>
			<thead>
				<tr>
					<th class="col-date">
						<button
							onclick={() => sortByColumn("date")}
							class:sorted={sortBy === "date"}
						>
							Date <span class="arrow"
								>{sortBy === "date" ? (ascending ? "↑" : "↓") : "↕"}</span
							>
						</button>
					</th>
					<th class="col-head">Headline</th>
					<th class="col-who">Names</th>
					<th class="col-frame">Framing</th>
					<th class="col-mood">
						<button
							onclick={() => sortByColumn("sentiment")}
							class:sorted={sortBy === "sentiment"}
						>
							Sentiment <span class="arrow"
								>{sortBy === "sentiment" ? (ascending ? "↑" : "↓") : "↕"}</span
							>
						</button>
					</th>
				</tr>
			</thead>
			<tbody>
				{#each rows as row (row.d + row.t)}
					{@const score = scoreOf(row.t)}
					<tr>
						<td class="col-date">{prettyDate(row.d)}</td>
						<td class="col-head">
							{#if row.u}
								<a href={row.u} target="_blank" rel="noreferrer"
									>{@html withHighlight(row.t)}</a
								>
							{:else}
								{@html withHighlight(row.t)}
							{/if}
						</td>
						<td class="col-who">
							{#each visibleTags(row) as name}
								<span
									class="tag"
									style="background:{PLAYER_COLORS[name] ?? OTHER_COLOR}"
								>
									{name.split(" ").slice(-1)[0]}
								</span>
							{/each}
						</td>
						<td class="col-frame">
							{#each framesOf(row.t) as f}
								<span
									class="frame-tag"
									style="color:{FRAME_COLORS[f]}; border-color:{FRAME_COLORS[
										f
									]}">{f}</span
								>
							{/each}
						</td>
						<td class="col-mood">
							{#if score === undefined}
								<span class="unscored">—</span>
							{:else}
								<span
									class="meter"
									title="{labelOf(row.t)} ({score.toFixed(2)})"
								>
									<span class="midline"></span>
									<span
										class="fill"
										style="width:{barWidth(score)}px; background:{barColor(
											score
										)};
											{score < 0 ? `right:${BAR_HALF}px` : `left:${BAR_HALF}px`}"
									></span>
								</span>
								<span class="score" style="color:{barColor(score)}"
									>{score.toFixed(2)}</span
								>
							{/if}
						</td>
					</tr>
				{:else}
					<tr
						><td colspan="5" class="empty">
							Nothing matches those filters. <button
								class="link"
								onclick={clearAll}>Clear them</button
							>
						</td></tr
					>
				{/each}
			</tbody>
		</table>
	</div>

	{#if caption}
		<p class="chart-caption">{@html caption}</p>
	{/if}
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
	/* under the framing beeswarm: its width, no title */
	.headline-browser.embedded {
		width: 100%;
		margin: 14px 0 0;
		transform: none;
	}
	.reveal {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 10px 14px;
		border: 1px solid var(--rule);
		border-radius: 6px;
		background: #fff;
		font: inherit;
		font-size: 13.5px;
		font-weight: 700;
		color: var(--ink);
		cursor: pointer;
	}
	.reveal .caret {
		margin-left: auto;
	}
	.scroller.short {
		max-height: 45vh;
		margin-top: 8px;
	}
	.chips.hidden {
		display: none;
	}

	.lede {
		max-width: 640px;
		margin: 0 auto 22px;
		text-align: center;
	}
	.kicker {
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: var(--accent);
		margin: 0 0 10px;
	}
	.lede h3 {
		font-family: Georgia, "Times New Roman", serif;
		font-size: 34px;
		font-weight: 400;
		line-height: 1.1;
		letter-spacing: -0.01em;
		margin: 0 0 10px;
		color: var(--ink);
	}
	.standfirst {
		font-size: 14px;
		line-height: 1.55;
		color: var(--muted);
		margin: 0;
	}
	.standfirst strong {
		color: var(--ink);
		font-weight: 700;
	}

	.controls {
		display: flex;
		gap: 8px;
		margin-bottom: 8px;
		flex-wrap: wrap;
		align-items: stretch;
	}
	input[type="search"] {
		flex: 1;
		min-width: 240px;
		padding: 0 14px;
		height: 40px;
		font-family: var(--sans);
		font-size: 14.5px;
		border: 1px solid var(--field-edge);
		border-radius: 3px;
		background: #fff;
		color: var(--ink);
		box-shadow: var(--field-shadow);
	}
	input[type="search"]::placeholder {
		color: var(--muted);
	}
	input[type="search"]:focus {
		outline: 0;
		border-color: var(--accent);
	}

	.toggle-group {
		display: inline-flex;
		height: 40px;
		background: #fff;
		border: 1px solid var(--field-edge);
		border-radius: 3px;
		box-shadow: var(--field-shadow);
		overflow: hidden;
	}
	.toggle-group button {
		border: 0;
		border-left: 1px solid var(--rule);
		/* the global button reset rounds every corner to 8px */
		border-radius: 0;
		background: transparent;
		color: var(--muted);
		padding: 0 14px;
		font-family: var(--sans);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.09em;
		text-transform: uppercase;
		cursor: pointer;
	}
	/* the rounded group clips its children — round the end buttons to match */
	.toggle-group button:first-child {
		border-left: 0;
		border-radius: 2px 0 0 2px;
	}
	.toggle-group button:last-child {
		border-radius: 0 2px 2px 0;
	}
	.toggle-group button:hover {
		color: var(--ink);
		background: rgba(28, 25, 23, 0.04);
	}
	.toggle-group button.active {
		color: #fff;
		background: var(--ink);
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-bottom: 12px;
	}
	.chip {
		border: 1px solid var(--field-edge);
		background: #fff;
		color: var(--ink);
		font-family: var(--sans);
		font-size: 12px;
		font-weight: 600;
		padding: 6px 13px;
		border-radius: 3px;
		cursor: pointer;
		box-shadow: var(--field-shadow);
	}
	.chip:hover {
		border-color: var(--chip, var(--ink));
	}
	.chip.on {
		background: var(--chip, #7a6bcc);
		border-color: var(--chip, #7a6bcc);
		color: #fff;
	}
	.chip.clear {
		color: var(--accent);
	}

	.count {
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.02em;
		color: rgba(28, 25, 23, 0.7);
		margin: 0 0 7px;
	}

	.scroller {
		max-height: 68vh;
		overflow-y: auto;
		background: #fff;
		border-top: 2px solid var(--ink);
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}
	thead th {
		position: sticky;
		top: 0;
		z-index: 1;
		background: #fff;
		text-align: left;
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: var(--muted);
		font-weight: 700;
		padding: 9px 12px 8px 0;
		border-bottom: 1px solid var(--rule);
		white-space: nowrap;
	}
	thead th:first-child {
		padding-left: 14px;
	}
	thead th:last-child {
		padding-right: 14px;
	}
	thead button {
		border: 0;
		background: transparent;
		padding: 0;
		cursor: pointer;
		font: inherit;
		color: inherit;
		letter-spacing: inherit;
		text-transform: inherit;
	}
	thead button:hover {
		color: var(--ink);
	}
	thead button.sorted {
		color: var(--ink);
	}
	.arrow {
		opacity: 0.4;
	}
	thead button.sorted .arrow {
		opacity: 1;
		color: var(--accent);
	}

	tbody td {
		padding: 10px 12px 10px 0;
		vertical-align: baseline;
		border-bottom: 1px solid var(--rule);
	}
	tbody td:first-child {
		padding-left: 14px;
	}
	tbody td:last-child {
		padding-right: 14px;
	}
	tbody tr:hover td {
		background: rgba(28, 25, 23, 0.045);
	}

	.col-date {
		width: 96px;
		white-space: nowrap;
	}
	tbody .col-date {
		font-size: 11px;
		font-variant-numeric: tabular-nums;
		letter-spacing: 0.03em;
		color: var(--muted);
	}
	tbody .col-head {
		font-family: Georgia, "Times New Roman", serif;
		font-size: 15px;
		line-height: 1.35;
		color: var(--ink);
	}
	.col-head a {
		color: inherit;
		text-decoration: none;
		background-image: linear-gradient(var(--rule), var(--rule));
		background-size: 100% 1px;
		background-position: 0 100%;
		background-repeat: no-repeat;
	}
	.col-head a:hover {
		background-image: linear-gradient(var(--accent), var(--accent));
		background-size: 100% 2px;
	}
	.col-who {
		width: 128px;
	}
	.col-mood {
		width: 108px;
		white-space: nowrap;
	}

	.frame-tag {
		display: inline-block;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		border: 1px solid;
		border-radius: 3px;
		padding: 1px 5px;
		margin: 1px 3px 1px 0;
		background: var(--color-paper);
	}
	.tag {
		display: inline-block;
		margin: 0 4px 3px 0;
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #fff;
		padding: 2px 6px;
		border-radius: 2px;
	}

	.meter {
		position: relative;
		display: inline-block;
		width: 52px;
		height: 10px;
		vertical-align: middle;
	}
	.meter .midline {
		position: absolute;
		left: 26px;
		top: 0;
		width: 1px;
		height: 100%;
		background: rgba(28, 25, 23, 0.25);
	}
	.meter .fill {
		position: absolute;
		top: 2px;
		height: 6px;
	}
	.score {
		font-size: 11px;
		margin-left: 7px;
		font-variant-numeric: tabular-nums;
		font-weight: 700;
	}
	.unscored {
		color: rgba(28, 25, 23, 0.3);
	}

	.empty {
		text-align: center;
		padding: 34px 12px;
		color: var(--muted);
		font-size: 14px;
	}
	.link {
		border: 0;
		background: none;
		padding: 0;
		font: inherit;
		cursor: pointer;
		color: var(--accent);
		text-decoration: underline;
	}

	.more {
		display: block;
		width: 100%;
		margin: 0;
		padding: 14px;
		border-radius: 0;
		border: 0;
		border-bottom: 1px solid var(--rule);
		background: transparent;
		color: var(--ink);
		font-family: var(--sans);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		cursor: pointer;
	}
	.more:hover {
		color: var(--accent);
	}
	.more span {
		font-weight: 500;
		letter-spacing: 0.04em;
		text-transform: none;
		color: var(--muted);
	}

	.chart-caption {
		font-size: 11.5px;
		line-height: 1.6;
		color: var(--muted);
		text-align: center;
		max-width: 620px;
		margin: 16px auto 0;
	}

	.col-head :global(mark) {
		background: transparent;
		color: inherit;
		font-weight: 700;
		box-shadow: inset 0 -0.55em 0 rgba(255, 224, 138, 0.85);
	}

	@media (max-width: 700px) {
		.col-who {
			display: none;
		}
		.lede h3 {
			font-size: 25px;
		}
	}
</style>
