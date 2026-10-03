<script>
	// Each outlet's share of its WNBA articles that mention trans issues, as a
	// figure on the page (not a card), wider than the text on desktop: a plain
	// title, gridlines labelled at the top, the values at the bar ends, Fox in
	// the LGBTQ+ purple and the other outlets in a warm grey, an italic note
	// at the foot. Hover a bar for its counts.
	//
	//   {.ShareBars}
	//   year: 2026
	//   title: WNBA articles mentioning trans issues, {year}
	//   note: Note: The share of each outlet’s {year} WNBA articles … Fox News published {fox} of its {foxN} …
	//   hover: {hit} of {n} WNBA articles in {year}
	//   {}
	// every line optional; {slots} are filled in from the data:
	//   {year}, {fox} {foxN} (Fox's articles on the topic, of all its WNBA
	//   articles), {others} (the other outlets' total), {count} (how many others)
	import trans from "$data/trans_by_outlet.json";
	import { SHORT } from "$utils/outlets.js";
	import { fill, or } from "$utils/fill.js";

	let {
		year = "2026",
		title = "",
		note = "",
		hover = "",
		...unused
	} = $props();

	// ---------------------------------------------------------------------
	// Settings
	// ---------------------------------------------------------------------

	const FOX = "Fox News";
	// an outlet with almost nothing from the year (a corpus that ends early)
	// would show a misleading zero: left out, and named in the note
	const MIN_N = 20;
	const WIDE = 880; // the figure's width on desktop (the text is 668)
	const TITLE = "WNBA articles mentioning trans issues, {year}";
	const NOTE =
		"Note: The share of each outlet’s {year} WNBA articles that mention trans athletes or issues: transgender, gender eligibility, or “biological” male, female or woman. " +
		"An article counts once, however often it uses them. Fox News published {fox} of its {foxN} WNBA articles on the topic; the {count} other outlets published {others} between them.";
	const HOVER = "{hit} of {n} WNBA articles in {year}";
	const NUMBER = [
		"no",
		"one",
		"two",
		"three",
		"four",
		"five",
		"six",
		"seven",
		"eight",
		"nine"
	];

	// ---------------------------------------------------------------------

	const Y = String(year).trim().slice(0, 4);
	const all = Object.entries(trans.outlets).map(([name, v]) => ({
		name,
		hit: v.trans?.[Y] ?? 0,
		n: v.articles?.[Y] ?? 0
	}));
	const dropped = all.filter((r) => r.n < MIN_N).map((r) => r.name);
	const rows = all
		.filter((r) => r.n >= MIN_N)
		.map((r) => ({ ...r, share: r.hit / r.n }));
	const fox = rows.find((r) => r.name === FOX);
	const others = rows
		.filter((r) => r.name !== FOX)
		.sort((a, b) => b.share - a.share);
	const ordered = fox ? [fox, ...others] : others;
	const pooled = others.reduce((s, r) => s + r.hit, 0);
	const pct = (v) => `${v < 0.1 ? (v * 100).toFixed(1) : Math.round(v * 100)}%`;

	// the scale runs to the next 10% above the biggest share, a gridline every 10
	const top = Math.max(
		0.1,
		Math.ceil(Math.max(...rows.map((r) => r.share)) * 10) / 10
	);
	const ticks = Array.from(
		{ length: Math.round(top * 10) + 1 },
		(_, i) => i / 10
	);
	const at = (s) => `${(s / top) * 100}%`;

	let width = $state(WIDE);
	const narrow = $derived(width < 520);
	const nameW = $derived(narrow ? 80 : 128);

	// hover: an outlet's counts
	let tip = $state(null);
	function show(e, r) {
		const box = e.currentTarget.closest(".plot").getBoundingClientRect();
		tip = {
			r,
			x: Math.min(box.width - 200, e.clientX - box.left + 14),
			y: e.clientY - box.top - 54
		};
	}
</script>

<figure class="sharebars" style:--wide="{WIDE}px" bind:clientWidth={width}>
	<p class="hed">{@html fill(or(title, TITLE), { year: Y })}</p>

	<div
		class="plot"
		role="img"
		aria-label="Share of each outlet’s {Y} WNBA articles mentioning trans issues: {ordered
			.map((r) => `${r.name} ${pct(r.share)}`)
			.join(', ')}"
		style:--name="{nameW + 12}px"
		onpointerleave={() => (tip = null)}
	>
		<!-- gridlines, labelled at the top; the last label sits inside its line -->
		{#each ticks as t, i (t)}
			<div
				class="grid"
				class:last={i === ticks.length - 1}
				style:left="calc(var(--name) + (100% - var(--name)) * {t / top})"
			>
				<span>{Math.round(t * 100)}%</span>
			</div>
		{/each}

		{#each ordered as r (r.name)}
			{@const isFox = r.name === FOX}
			<div
				class="row"
				class:fox={isFox}
				style:grid-template-columns="{nameW}px minmax(0, 1fr)"
				role="presentation"
				onpointermove={(e) => show(e, r)}
			>
				<div class="name">{narrow ? (SHORT[r.name] ?? r.name) : r.name}</div>
				<div class="track">
					<div class="bar" style:width={at(r.share)}></div>
					<span class="val" style:left={at(r.share)}>{pct(r.share)}</span>
				</div>
			</div>
		{/each}

		{#if tip}
			<div class="tip" style:left="{tip.x}px" style:top="{tip.y}px">
				<b>{tip.r.name}</b><br />{fill(or(hover, HOVER), {
					hit: tip.r.hit,
					n: tip.r.n.toLocaleString(),
					year: Y
				})}
			</div>
		{/if}
	</div>

	<p class="note">
		{@html fill(or(note, NOTE), {
			year: Y,
			fox: fox?.hit ?? 0,
			foxN: (fox?.n ?? 0).toLocaleString(),
			others: pooled,
			count: NUMBER[others.length] ?? others.length
		})}{#if dropped.length}
			Left out for having fewer than {MIN_N} WNBA articles in {Y}: {dropped.join(
				", "
			)}.{/if}
	</p>
</figure>

<style>
	/* on the page, wider than the text and centred under it (full width on phones) */
	.sharebars {
		--fig-w: min(var(--wide), calc(100vw - 32px));
		--ink: var(--color-ink-dark);
		--taupe: #8a6f5c;
		--grid: rgba(42, 21, 3, 0.2);
		width: var(--fig-w);
		max-width: none; /* the site caps figures at the text width */
		margin: 34px 0 38px calc((100% - var(--fig-w)) / 2);
		font-family: var(--font-graphic);
		color: var(--ink);
	}
	.hed {
		margin: 0 0 18px;
		font-size: 19px;
		font-weight: 700;
		line-height: 1.25;
		letter-spacing: -0.005em;
	}
	.plot {
		position: relative;
		padding-top: 22px;
	}
	.grid {
		position: absolute;
		top: 0;
		bottom: 0;
		border-left: 1px solid var(--grid);
	}
	.grid span {
		position: absolute;
		top: 0;
		left: 4px;
		font-size: 13px;
		color: rgba(42, 21, 3, 0.75);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	.grid.last span {
		left: auto;
		right: 4px;
	}
	.row {
		position: relative;
		display: grid;
		align-items: center;
		column-gap: 12px;
		height: 34px;
	}
	.name {
		font-size: 14px;
		font-weight: 700;
		text-align: right;
		white-space: nowrap;
		color: rgba(42, 21, 3, 0.85);
	}
	.row.fox .name {
		color: var(--ink);
	}
	.track {
		position: relative;
		height: 100%;
	}
	.bar {
		position: absolute;
		left: 0;
		top: 50%;
		height: 14px;
		transform: translateY(-50%);
		border-radius: 0 3px 3px 0;
		background: var(--taupe);
	}
	.row.fox .bar {
		height: 18px;
		background: var(--color-lgbtq);
	}
	.val {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		padding-left: 7px;
		font-size: 14px;
		font-weight: 700;
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	.row.fox .val {
		font-size: 16px;
		color: var(--color-lgbtq);
	}
	.tip {
		position: absolute;
		z-index: 4;
		width: 190px;
		padding: 8px 10px;
		background: #fff;
		border: 1px solid #e2e2e2;
		border-radius: 4px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
		font-size: 12.5px;
		line-height: 1.45;
		pointer-events: none;
	}
	.note {
		margin: 18px 0 0;
		font-family: var(--font-serif);
		font-style: italic;
		font-size: 14px;
		line-height: 1.55;
		color: rgba(42, 21, 3, 0.78);
	}
	.note :global(a) {
		color: inherit;
	}
	@media (max-width: 560px) {
		.hed {
			font-size: 17px;
		}
		.row {
			height: 30px;
		}
		.name {
			font-size: 13px;
		}
	}
</style>
