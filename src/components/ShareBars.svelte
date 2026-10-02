<script>
	// Each outlet's share of its WNBA articles that mention trans issues, in
	// the topic graphics' style (FoxVsField, 2026-10-02): a headline that
	// states the finding, Fox's bar in the LGBTQ+ purple and its count beside
	// it, the other outlets in grey with their counts on hover.
	//
	//   {.ShareBars}
	//   year: 2026
	//   title: In 2026, Fox News published as many WNBA articles about trans issues as six other outlets combined.
	//   kicker: Trans issues · {year}
	//   subtitle: Share of each outlet’s {year} WNBA articles that mention trans athletes or issues. Fox News published {fox}; the six others, {others} between them.
	//   count: {hit} of {n} articles            (beside Fox's bar)
	//   hover: {hit} of {n} WNBA articles in {year}
	//   source: <b>Trans terms:</b> transgender, …
	//   {}
	// every line optional; {slots} are filled in from the data
	import trans from "$data/trans_by_outlet.json";
	import { SHORT } from "$utils/outlets.js";
	import { fill, or } from "$utils/fill.js";

	let { year = "2026", title = "", kicker = "", subtitle = "", count = "", hover = "", source = "", ...rest } = $props();

	const FOX = "Fox News";
	const Y = String(year).trim().slice(0, 4);
	// an outlet with almost nothing from the year (a corpus that ends early)
	// would show a misleading zero: left out
	const MIN_N = 20;
	const all = Object.entries(trans.outlets).map(([name, v]) => ({ name, hit: v.trans?.[Y] ?? 0, n: v.articles?.[Y] ?? 0 }));
	// the outlets dropped for it, named in the source line (none in 2026)
	const dropped = all.filter((r) => r.n < MIN_N).map((r) => r.name);
	const rows = all
		.filter((r) => r.n >= MIN_N)
		.map((r) => ({ ...r, share: r.hit / r.n }));
	const fox = rows.find((r) => r.name === FOX);
	const others = rows.filter((r) => r.name !== FOX).sort((a, b) => b.share - a.share);
	const pooled = others.reduce((s, r) => s + r.hit, 0);
	const pct = (v) => `${v < 0.1 ? (v * 100).toFixed(1) : Math.round(v * 100)}%`;
	const NUMBER = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];

	// the scale leaves room beside Fox's bar for its count (about 170px)
	let width = $state(640);
	const narrow = $derived(width < 520);
	const nameW = $derived(narrow ? 82 : 128);
	const max = $derived.by(() => {
		const track = Math.max(120, width - nameW - 12);
		return Math.max(0.3, (fox?.share ?? 0) / Math.max(0.4, 1 - 170 / track));
	});
	const w = (s) => `${(s / max) * 100}%`;

	// hover: an outlet's count
	let tip = $state(null);
	function show(e, r) {
		const box = e.currentTarget.closest(".chart").getBoundingClientRect();
		tip = { r, x: Math.min(box.width - 200, e.clientX - box.left + 14), y: e.clientY - box.top - 54 };
	}
</script>

<figure class="sharebars" bind:clientWidth={width}>
	<p class="kicker">{fill(or(kicker, "Trans issues · {year}"), { year: Y })}</p>
	{#if title}<h4 class="hed">{@html title}</h4>{/if}
	<p class="dek">
		{@html fill(
			or(
				subtitle,
				`Share of each outlet’s {year} WNBA articles that mention trans athletes or issues. Fox News published {fox}; the ${NUMBER[others.length] ?? others.length} others, {others} between them.`
			),
			{ year: Y, fox: fox?.hit ?? 0, others: pooled }
		)}
	</p>

	<div class="chart" role="img" aria-label="Share of each outlet’s {Y} WNBA articles mentioning trans issues: {rows.map((r) => `${r.name} ${pct(r.share)}`).join(', ')}" onpointerleave={() => (tip = null)}>
		{#each fox ? [fox, ...others] : others as r (r.name)}
			{@const isFox = r.name === FOX}
			<div class="row" class:fox={isFox} style:grid-template-columns="{nameW}px minmax(0, 1fr)" onpointermove={(e) => show(e, r)}>
				<div class="name">{narrow ? (SHORT[r.name] ?? r.name) : r.name}</div>
				<div class="track">
					<div class="bar" style:width={w(r.share)}></div>
					{#if isFox}
						<!-- Fox's share inside its bar, its count beside it -->
						<span class="val inside" style:right="calc({100 - (r.share / max) * 100}% + 7px)">{pct(r.share)}</span>
						<span class="count" style:left="calc({w(r.share)} + 8px)">{fill(or(count, "{hit} of {n} articles"), { hit: r.hit, n: r.n.toLocaleString(), year: Y })}</span>
					{:else}
						<span class="val" style:left="calc({w(r.share)} + 6px)">{pct(r.share)}</span>
					{/if}
				</div>
			</div>
		{/each}
		{#if tip}
			<div class="tip" style:left="{tip.x}px" style:top="{tip.y}px">
				<b>{tip.r.name}</b><br />{fill(or(hover, "{hit} of {n} WNBA articles in {year}"), { hit: tip.r.hit, n: tip.r.n.toLocaleString(), year: Y })}
			</div>
		{/if}
	</div>

	<p class="source">
		{@html fill(or(source, "<b>Trans terms:</b> transgender, gender eligibility, “biological” male / female / woman. An article counts once, however often it uses them."), { year: Y })}{#if dropped.length}
			Left out for having fewer than {MIN_N} WNBA articles in {Y}: {dropped.join(", ")}.{/if}
	</p>
</figure>

<style>
	.sharebars {
		margin: 28px 0;
		padding: 22px 32px 18px;
		background: #fff;
		border-radius: 4px;
		font-family: var(--font-graphic);
		color: var(--color-ink-dark);
	}
	.kicker {
		margin: 0 0 6px;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--color-lgbtq);
	}
	.hed {
		margin: 0 0 8px;
		font-family: var(--font-graphic);
		font-size: 24px;
		font-weight: 700;
		line-height: 1.22;
		letter-spacing: -0.01em;
	}
	.dek {
		margin: 0 0 22px;
		font-size: 15px;
		line-height: 1.45;
		color: #4a4a4a;
	}
	.chart {
		position: relative;
	}
	.row {
		display: grid;
		align-items: center;
		column-gap: 12px;
		min-height: 34px;
	}
	.row + .row {
		margin-top: 6px;
	}
	.name {
		font-size: 15px;
		font-weight: 600;
		text-align: right;
		color: #4a4a4a;
	}
	.row.fox .name {
		font-weight: 700;
		color: var(--color-ink-dark);
	}
	.track {
		position: relative;
		height: 26px;
	}
	.bar {
		position: absolute;
		top: 0;
		bottom: 0;
		left: 0;
		border-radius: 0 3px 3px 0;
		background: #d5d0c7;
	}
	.row.fox .bar {
		background: var(--color-lgbtq);
	}
	.val,
	.count {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		white-space: nowrap;
		font-variant-numeric: tabular-nums;
	}
	.val {
		font-size: 14px;
		font-weight: 700;
	}
	.val.inside {
		color: #fff;
	}
	.count {
		font-size: 13.5px;
		color: #727272;
	}
	.tip {
		position: absolute;
		z-index: 4;
		width: 190px;
		padding: 7px 10px;
		background: #fff;
		border: 1px solid #e2e2e2;
		border-radius: 4px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
		font-size: 12.5px;
		line-height: 1.4;
		color: #4a4a4a;
		pointer-events: none;
	}
	.tip b {
		color: var(--color-ink-dark);
	}
	.source {
		margin: 22px 0 0;
		padding-top: 10px;
		border-top: 1px solid #e2e2e2;
		font-size: 12px;
		line-height: 1.5;
		color: #727272;
	}
	.source :global(b) {
		font-weight: 600;
		color: #4a4a4a;
	}
	@media (max-width: 560px) {
		.sharebars {
			padding: 18px 14px 14px;
		}
		.hed {
			font-size: 21px;
		}
		.name {
			font-size: 13.5px;
		}
	}
</style>
