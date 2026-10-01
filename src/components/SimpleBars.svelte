<script>
	// A plain horizontal bar chart, one bar per outlet or network, for a
	// single year
	import { base } from "$app/paths";
	import segments from "$data/chyron_segments.json";
	import trans from "$data/trans_by_outlet.json";

	// layout: "columns" (bars standing up) or "horizontal" (bars running right, one row each)
	let { source = "cable", year = "2026", mode = "count", note = "", layout = "columns" } = $props();
	const HORIZONTAL = String(layout).trim().toLowerCase().startsWith("h");
	const SHARE = String(mode).trim().toLowerCase() === "share";

	const COLOR = {
		"Fox News": "var(--color-fox-navy)",
		CNN: "var(--color-cnn)",
		MSNBC: "var(--color-msnbc)"
	};
	import { LOGO, SHORT as SHORT_NAMES, outletName } from "$utils/outlets.js";
	const LOGOS = Object.fromEntries(Object.entries(LOGO).map(([o, f]) => [o, { file: f, h: f.endsWith(".png") ? 22 : o === "Fox News" ? 22 : 14 }]));
	// the outlets with a bare icon get their name beside it
	const SHORT = SHORT_NAMES;

	let rows = $derived.by(() => {
		const y = String(year);
		if (source === "cable") {
			const i = segments.years.indexOf(+y);
			return segments.networks.map((n) => ({
				name: n.name,
				value: n.segments[i] ?? 0,
				color: COLOR[n.name] ?? "var(--color-ink)"
			}));
		}
		return Object.entries(trans.outlets)
			.map(([name, v]) => ({
				name,
				value: v.trans?.[y] ?? 0,
				of: v.articles?.[y] ?? 0,
				color: name === "Fox News" ? "var(--color-fox-navy)" : "var(--color-lgbtq)"
			}))
			// an outlet with almost nothing from that year (the papers' corpora end
			// early) would show a misleading zero: leave it out
			.filter((r) => r.of >= 20)
			.sort((a, b) =>
				SHARE ? b.value / (b.of || 1) - a.value / (a.of || 1) : b.value - a.value
			);
	});
	// a share bar's filled part, as a percentage of the whole
	const shareOf = (row) => (row.of ? (100 * row.value) / row.of : 0);
	const pct = (row) => {
		const v = shareOf(row);
		return `${v < 10 ? v.toFixed(1) : Math.round(v)}%`;
	};
	let most = $derived(Math.max(1, ...rows.map((r) => r.value)));
	// the hover card, styled like the charts' tooltips
	let tip = $state(null);
	let rootEl = $state(null);
	function showTip(event, row) {
		const box = rootEl.getBoundingClientRect();
		tip = { row, x: event.clientX - box.left, y: Math.min(Math.max(40, event.clientY - box.top), box.height - 40), flip: event.clientX - box.left > box.width - 260 };
	}
	let unit = $derived(source === "cable" ? "segments" : "articles");
	let showCounts = $state(true); // counts first, shares a click away
</script>

<!-- dense: a dozen or more bars, so each count wears its "of N" on a second line
     and the chart takes the full column width -->
<div class="simple-bars" class:dense={rows.length >= 10} class:horizontal={HORIZONTAL} style="--n: {rows.length}" bind:this={rootEl}>
	{#if HORIZONTAL}
	<!-- a table of bars (2026-09-30): the outlet's name, its share on a track
	     that runs to 100%, and its WNBA articles that year. Fox first, the
	     others by share. Counts alone (no "of") fill to the most -->
	{@const hasOf = rows.some((r) => r.of)}
	{@const share = hasOf && !showCounts}
	{@const ordered = hasOf
		? [...rows].sort((a, b) => (b.name === "Fox News") - (a.name === "Fox News") || (share ? shareOf(b) - shareOf(a) : b.value - a.value))
		: rows}
	<div class="table" role="table">
		<div class="thead" role="row">
			{#if hasOf}
				<!-- % or #: the share of each outlet's articles, or the articles
				     themselves, in the header row over the names (2026-10-01) -->
				<div class="measure-pick" role="group" aria-label="Show shares or counts">
					<button type="button" class:active={showCounts} aria-pressed={showCounts} title="Number of articles" onclick={() => (showCounts = true)}>#</button>
					<button type="button" class:active={!showCounts} aria-pressed={!showCounts} title="Share of each outlet's WNBA articles" onclick={() => (showCounts = false)}>%</button>
				</div>
			{:else}<span></span>{/if}
			<span class="th">{share ? "Share of WNBA articles mentioning trans issues" : hasOf ? "WNBA articles mentioning trans issues" : unit}</span>
			{#if hasOf}<span class="th total"><span class="full">Total articles</span><span class="brief">Total</span></span>{/if}
		</div>
		{#each ordered as row, i (row.name)}
			{@const w = share ? shareOf(row) : (100 * row.value) / most}
			{@const label = share ? `${Math.round(shareOf(row))}%` : row.value.toLocaleString()}
			<div class="trow" role="row">
				<span class="tname"><span class="full">{outletName(row.name)}</span><span class="brief">{SHORT[row.name] ?? row.name}</span></span>
				<div class="ttrack" class:filled={share} onpointermove={(e) => showTip(e, row)} onpointerleave={() => (tip = null)}>
					<div class="tbar" style="width:{w}%; background:{row.color}"></div>
					<!-- the value inside the bar's end, or just past it on a short bar -->
					<span class="tvalue" class:outside={w < 12} style={w < 12 ? `left:calc(${w}% + 7px)` : `right:calc(${100 - w}% + 8px)`}
						>{label}</span
					>
				</div>
				{#if hasOf}<span class="ttotal">{row.of.toLocaleString()}</span>{/if}
			</div>
		{/each}
	</div>
	{:else}
	<div class="columns">
		{#each rows as row (row.name)}
			<div class="col">
				{#if SHARE}
					<!-- the whole bar is every WNBA article the outlet ran that year;
					     the filled part is those that mention trans issues -->
					<div class="stem whole">
						<span class="value" style="bottom:calc(100% + 5px)"
							>{pct(row)}<span class="of">&nbsp;{row.value.toLocaleString()} of {row.of.toLocaleString()}</span></span
						>
						<div class="all"></div>
						<div class="bar" style="height:{shareOf(row)}%; background:{row.color}"></div>
					</div>
				{:else}
					<div class="stem">
						<!-- the count sits just above its bar -->
						<span class="value" style="bottom:calc({(100 * row.value) / most}% + 5px)"
							>{row.value.toLocaleString()}</span
						>
						<div class="bar" style="height:{(100 * row.value) / most}%; background:{row.color}"
							onpointermove={(e) => showTip(e, row)} onpointerleave={() => (tip = null)}></div>
					</div>
				{/if}
				<div class="who">
					{#if LOGOS[row.name]}
						<img
							src="{base}/logos/{LOGOS[row.name].file}"
							alt={row.name}
							style:height="{LOGOS[row.name].h}px"
						/>
					{/if}
					{#if !LOGOS[row.name]}<span>{SHORT[row.name] ?? row.name}</span>{/if}
					<!-- on a phone a dozen wordmarks are illegible: a short name, set vertically -->
					<span class="short">{SHORT[row.name] ?? row.name}</span>
				</div>
			</div>
		{/each}
	</div>
	{/if}
	{#if tip}
		<div class="tooltip" class:flip={tip.flip} style="left:{tip.x}px; top:{tip.y}px">
			<strong>{SHORT[tip.row.name] ?? tip.row.name} · {year}</strong>
			<p class="line">
				{#if tip.row.of}
					{tip.row.value.toLocaleString()} of its {tip.row.of.toLocaleString()} WNBA {unit} that year — {pct(tip.row)} — mention trans issues.
				{:else}
					{tip.row.value.toLocaleString()} WNBA {unit}.
				{/if}
			</p>
		</div>
	{/if}
	{#if String(note).trim().toLowerCase() !== "none"}
	<p class="note">
		{#if String(note).trim()}{@html note}{:else}{source === "cable"
			? `WNBA segments on each network's chyrons in ${year}, through ${segments.through}.`
			: SHARE
				? `Each bar is all of an outlet's WNBA articles in ${year}; the filled part are those that mention trans issues.`
				: `Articles about the WNBA that mention trans issues in ${year}, of each outlet's WNBA articles that year.`}{/if}
	</p>
	{/if}
</div>

<style>
	.simple-bars {
		position: relative;
		max-width: 680px;
		margin: 8px auto 20px;
	}
	.tooltip {
		position: absolute;
		transform: translate(14px, -50%);
		width: 240px;
		background: var(--tip-bg);
		border: 1px solid var(--tip-border);
		border-radius: var(--tip-radius);
		padding: var(--tip-pad);
		box-shadow: var(--tip-shadow);
		pointer-events: none;
		z-index: 5;
	}
	.tooltip.flip {
		transform: translate(calc(-100% - 14px), -50%);
	}
	/* the shared tooltip (variables.css): serif title, figures in the chart font */
	.tooltip strong {
		display: block;
		font: var(--tip-title);
		color: var(--tip-ink);
	}
	.tooltip .line {
		margin: 5px 0 0;
		font: var(--tip-body);
		color: var(--tip-ink);
	}
	/* % / #: set like the column titles beside it, the active one dark and underlined */
	.measure-pick {
		display: flex;
		gap: 10px;
		align-self: end;
	}
	.measure-pick button {
		appearance: none;
		margin: 0;
		padding: 0;
		border: 0;
		background: none;
		font-family: var(--font-chart);
		font-size: 13px;
		line-height: inherit;
		letter-spacing: 0.04em;
		color: rgba(42, 21, 3, 0.45);
		cursor: pointer;
	}
	.measure-pick button.active {
		color: var(--color-ink-dark);
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	/* the horizontal layout: a table of bars, name | bar on a track | total */
	.table {
		--name-w: 150px;
		--total-w: 116px;
		font-family: var(--font-chart);
		color: var(--color-ink);
	}
	.thead,
	.trow {
		display: grid;
		/* the bars' column gives way before the totals do */
		grid-template-columns: var(--name-w) minmax(0, 1fr) var(--total-w);
		align-items: center;
		column-gap: 14px;
	}
	.thead {
		margin-bottom: 8px;
		align-items: end;
	}
	.th {
		white-space: nowrap;
		font-size: 12px;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.75);
	}
	.th.total,
	.ttotal {
		text-align: right;
		font-variant-numeric: tabular-nums;
	}
	.trow {
		padding: 5px 0;
	}
	.tname {
		font-size: 16px;
		line-height: 1.2;
	}
	.tname .brief,
	.th .brief {
		display: none;
	}
	.ttotal {
		font-size: 16px;
	}
	.ttrack {
		position: relative;
		height: 36px;
	}
	.ttrack.filled {
		background: rgba(42, 21, 3, 0.09);
	}
	.tbar {
		position: absolute;
		left: 0;
		top: 0;
		height: 100%;
	}
	.tvalue {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		font-size: 16px;
		font-variant-numeric: tabular-nums;
		color: #fff;
		white-space: nowrap;
	}
	.tvalue.outside {
		color: var(--color-ink);
	}
	.horizontal .note {
		margin-top: 12px;
	}
	@media (max-width: 640px) {
		.table {
			--name-w: 92px;
			--total-w: 56px;
		}
		.thead,
		.trow {
			column-gap: 8px;
		}
		/* on a phone the header may take two lines rather than push the
		   totals off the page */
		.th {
			font-size: 10.5px;
			white-space: normal;
			line-height: 1.25;
		}
		.tname,
		.ttotal,
		.tvalue {
			font-size: 13.5px;
		}
		.ttrack {
			height: 28px;
		}
		/* short names on a phone, one line each */
		.tname .full,
		.th .full {
			display: none;
		}
		.tname .brief,
		.th .brief {
			display: inline;
		}
	}
	/* one column per bar, the bars standing on a shared baseline */
	.columns {
		display: grid;
		grid-template-columns: repeat(var(--n, 3), minmax(0, 1fr));
		gap: 14px;
		align-items: end;
		border-bottom: 1.5px solid var(--color-ink);
		padding: 0 6px;
	}
	.col {
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 0;
	}
	.stem {
		position: relative;
		width: 100%;
		max-width: 72px;
		height: 220px;
		margin-top: 22px; /* room for the count above the tallest bar */
		display: flex;
		align-items: flex-end;
	}
	/* the share bars: a faint full-height bar, the filled part on top of it */
	.stem.whole .all {
		position: absolute;
		inset: 0;
		background: rgba(42, 21, 3, 0.1);
		border: 1px solid rgba(42, 21, 3, 0.18);
		border-bottom: 0;
		border-radius: 3px 3px 0 0;
		box-sizing: border-box;
	}
	.stem.whole .bar {
		position: relative;
		border-radius: 0;
	}
	.bar {
		width: 100%;
		min-height: 2px;
		border-radius: 3px 3px 0 0;
		transition: height 600ms ease;
	}
	.value {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		font-family: var(--font-chart);
		font-size: 13px;
		font-weight: 700;
		color: var(--color-ink);
		white-space: nowrap;
	}
	.of {
		font-weight: 400;
		color: rgba(42, 21, 3, 0.55);
	}
	.simple-bars.dense {
		max-width: 960px;
	}
	.simple-bars.dense .columns {
		gap: 6px;
	}
	.simple-bars.dense .stem {
		margin-top: 36px;
	}
	.simple-bars.dense .value {
		font-size: 12px;
		line-height: 1.15;
		text-align: center;
	}
	.simple-bars.dense .of {
		display: block;
		font-size: 10.5px;
	}
	.simple-bars.dense .who img {
		max-width: 100%;
		height: auto !important;
		max-height: 18px;
		object-fit: contain;
	}
	.who {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		min-height: 36px;
		padding: 6px 0 4px;
		font-size: 13px;
		font-weight: 700;
		color: var(--color-ink);
		text-align: center;
		line-height: 1.2;
	}
	.who img {
		display: block;
	}
	.who .short {
		display: none;
	}
	.note {
		font-size: 12px;
		color: rgba(42, 21, 3, 0.6);
		margin: 10px 0 0;
		text-align: center;
	}
	@media (max-width: 640px) {
		.columns {
			gap: 4px;
		}
		.stem {
			height: 170px;
		}
		.value {
			font-size: 11.5px;
		}
		.of {
			display: none;
		}
		/* six columns share a phone's width: the logo above its name, the name
		   free to wrap, nothing spilling into the next column */
		.who {
			flex-direction: column;
			gap: 3px;
			min-height: 44px;
			padding: 6px 2px 2px;
			font-size: 10.5px;
			line-height: 1.15;
			overflow: hidden;
		}
		.who span {
			max-width: 100%;
			overflow-wrap: anywhere;
		}
		.who img {
			display: none;
		}
		.who .short {
			display: block;
			writing-mode: vertical-rl;
			transform: rotate(180deg);
			font-family: var(--font-chart);
			font-size: 10px;
			font-weight: 700;
			letter-spacing: 0.02em;
			line-height: 1;
			white-space: nowrap;
			min-height: 62px;
		}
	}
</style>
