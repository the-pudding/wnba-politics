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
	import { LOGO, SHORT as SHORT_NAMES } from "$utils/outlets.js";
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
</script>

<!-- dense: a dozen or more bars, so each count wears its "of N" on a second line
     and the chart takes the full column width -->
<div class="simple-bars" class:dense={rows.length >= 10} class:horizontal={HORIZONTAL} style="--n: {rows.length}" bind:this={rootEl}>
	{#if HORIZONTAL}
	<div class="rows">
		{#each rows as row (row.name)}
			<div class="hrow">
				<div class="hwho">
					{#if LOGOS[row.name]}
						<img src="{base}/logos/{LOGOS[row.name].file}" alt={row.name} style:height="{Math.min(LOGOS[row.name].h, 18)}px" />
					{:else}<span>{SHORT[row.name] ?? row.name}</span>{/if}
				</div>
				<div class="htrack" class:whole={SHARE} onpointermove={(e) => showTip(e, row)} onpointerleave={() => (tip = null)}>
					{#if SHARE}<div class="hall"></div>{/if}
					<div class="hbar" style="width:{SHARE ? shareOf(row) : (100 * row.value) / most}%; background:{row.color}"></div>
					<!-- the number alone; the "of N" and the share wait in the tooltip -->
					<span class="hvalue" style="left:calc({SHARE ? shareOf(row) : (100 * row.value) / most}% + 6px)"
						>{SHARE ? pct(row) : row.value.toLocaleString()}</span
					>
				</div>
			</div>
		{/each}
	</div>
	{:else}
	<div class="columns">
		{#each rows as row (row.name)}
			<div class="col">
				{#if SHARE}
					<!-- the whole bar is every WNBA article the outlet ran that year;
					     the filled part is those that mention trans athletes -->
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
					{tip.row.value.toLocaleString()} of its {tip.row.of.toLocaleString()} WNBA {unit} that year — {pct(tip.row)} — mention trans athletes.
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
				? `Each bar is all of an outlet's WNBA articles in ${year}; the filled part are those that mention trans athletes.`
				: `Articles about the WNBA that mention trans athletes in ${year}, of each outlet's WNBA articles that year.`}{/if}
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
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid rgba(42, 21, 3, 0.35);
		border-radius: 3px;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none;
		z-index: 5;
	}
	.tooltip.flip {
		transform: translate(calc(-100% - 14px), -50%);
	}
	.tooltip strong {
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.6);
	}
	.tooltip .line {
		margin: 5px 0 0;
		font-size: 13px;
		line-height: 1.5;
		color: var(--color-ink);
		font-family: var(--font-chart);
	}
	/* the horizontal layout: a row per outlet, its wordmark on the left */
	.rows {
		display: flex;
		flex-direction: column;
		gap: 7px;
		padding: 4px 0;
	}
	.hrow {
		display: grid;
		grid-template-columns: 96px 1fr;
		align-items: center;
		gap: 10px;
	}
	.hwho {
		display: flex;
		justify-content: flex-end;
		align-items: center;
		font-size: 12px;
		font-weight: 700;
		color: var(--color-ink);
	}
	.hwho img {
		max-width: 92px;
		object-fit: contain;
	}
	.htrack {
		position: relative;
		height: 18px;
		border-left: 1.5px solid var(--color-ink);
	}
	.htrack .hall {
		position: absolute;
		inset: 0;
		background: rgba(42, 21, 3, 0.1);
	}
	.hbar {
		position: absolute;
		left: 0;
		top: 0;
		height: 100%;
		border-radius: 0 3px 3px 0;
	}
	.hvalue {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		white-space: nowrap;
		font-size: 12px;
		font-weight: 800;
		color: var(--color-ink);
	}
	.hvalue .of {
		font-weight: 400;
		opacity: 0.7;
	}
	.horizontal .note {
		margin-top: 10px;
	}
	@media (max-width: 640px) {
		.hrow {
			grid-template-columns: 70px 1fr;
		}
		.hwho img {
			max-width: 66px;
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
