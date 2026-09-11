<script>
	// A small figure: a few words, week by week, for one outlet at a time —
	// Fox News by default, the five sports outlets a click away, every one on
	// Fox's scale so they compare. In the Doc:
	//   {.WordCompare}
	//   words: hip-check, poke, punch, throat
	//   from: 2024-01-01
	//   mark: 2026-07-07        (optional)
	//   layout: pills | multiples | breakdown | total
	//       total: the words added up as one shaded line, each word named on
	//       the line at the week it peaks
	//       pills: one chart with outlet pills; multiples: every outlet at once,
	//       Fox on top, the five in rows beneath; breakdown: the words added up
	//       on top, then one shaded row per word, in the ternary's brown
	//   title: How {outlet} describes the contact   ({outlet} follows the pills)
	//   {}
	import { base } from "$app/paths";
	import WordTimeline from "$components/WordTimeline.svelte";

	let {
		words = "hip-check, poke, punch, throat",
		from = "2024-01-01",
		to = "",
		mark = "",
		chart = "lines",
		layout = "pills",
		title = ""
	} = $props();
	// the title is drawn here, not by the CMS, so it can name the outlet picked
	let heading = $derived(String(title).replaceAll("{outlet}", outlet));
	const multiples = String(layout).trim().toLowerCase().startsWith("multi");
	const breakdown = String(layout).trim().toLowerCase().startsWith("break");
	const totalOnly = String(layout).trim().toLowerCase() === "total";
	const BROWN = "#7a4a00";
	let wordList = $derived(String(words).split(",").map((w) => w.trim()).filter(Boolean));
	// the panes, on the outlet-topic panels' 30-column grid: Fox alone on top
	// (a third wide, centred), then rows of three
	const OTHERS = OUTLETS_LIST();
	function OUTLETS_LIST() {
		return ["ESPN", "CBS Sports", "USA Today", "The Athletic", "Just Women's Sports"];
	}
	const cells = [{ outlet: "Fox News", start: 10, span: 10, solo: true }];
	OTHERS.forEach((o, i) => {
		const row = Math.floor(i / 3), k = i % 3;
		const n = Math.min(3, OTHERS.length - row * 3);
		const start = (30 - n * 10) / 2;
		cells.push({ outlet: o, start: start + 10 * k, span: 10, solo: false });
	});

	const OUTLETS = ["Fox News", "ESPN", "CBS Sports", "USA Today", "The Athletic", "Just Women's Sports"];
	const LOGOS = {
		"Fox News": "fox-news.svg",
		ESPN: "espn.svg",
		"CBS Sports": "cbs-sports.svg",
		"USA Today": "usa-today.svg",
		"The Athletic": "the-athletic.png",
		"Just Women's Sports": "jws.png"
	};
	let outlet = $state("Fox News");
</script>

<div class="word-compare" class:multiples>
	{#if heading.trim()}<h4 class="chart-title">{@html heading}</h4>{/if}
	{#if multiples}
		<div class="grid">
			{#each cells as cell (cell.outlet)}
				<div class="pane" class:solo={cell.solo} style:grid-column="{cell.start + 1} / span {cell.span}">
					<div class="pane-hed">
						<img src="{base}/logos/{LOGOS[cell.outlet]}" alt={cell.outlet} style:height="{LOGOS[cell.outlet].endsWith('.png') ? 18 : 14}px" />
					</div>
					<WordTimeline outlet={cell.outlet} {words} {from} {to} {mark} by="week" scope="any" scaleTo="Fox News" width={440} height={230} {chart} />
				</div>
			{/each}
		</div>
		<p class="note">Articles per week that use each word anywhere in the text. Every panel shares Fox News's scale.</p>
	{:else}
	<div class="controls">
		<div class="picker" role="group" aria-label="Outlet">
			{#each OUTLETS as o (o)}
				<button
					class:active={outlet === o}
					class:square={LOGOS[o].endsWith(".png")}
					title={o}
					aria-label={o}
					onclick={() => (outlet = o)}
				>
					<img src="{base}/logos/{LOGOS[o]}" alt="" />
				</button>
			{/each}
		</div>
	</div>
	{#key outlet}
		{#if totalOnly}
			<WordTimeline {outlet} {words} combine annotate label="all {wordList.length} words" {from} {to} {mark} by="week" scope="any" scaleTo="Fox News" chart="area" color={BROWN} width={700} height={300} />
		{:else if breakdown}
			<!-- the words added up, then each on its own row, all in one colour -->
			<div class="rows">
				<div class="row">
					<WordTimeline {outlet} {words} combine label="all {wordList.length} words" {from} {to} {mark} by="week" scope="any" scaleTo="Fox News" chart="area" color={BROWN} width={700} height={220} xaxis={false} />
				</div>
				{#each wordList as w, i (w)}
					<div class="row">
						<span class="row-word">{w}</span>
						<WordTimeline {outlet} word={w} {from} {to} {mark} by="week" scope="any" scaleTo="Fox News" scaleWords={words} chart="area" color={BROWN} width={700} height={i === wordList.length - 1 ? 110 : 84} xaxis={i === wordList.length - 1} quiet />
					</div>
				{/each}
			</div>
		{:else}
			<!-- drawn at the text column's width, so the type stays true size -->
			<WordTimeline {outlet} {words} {from} {to} {mark} by="week" scope="any" scaleTo="Fox News" width={700} height={280} {chart} />
		{/if}
	{/key}
	<p class="note">
		{outlet}: articles per week that use each word anywhere in the text.
		{#if outlet !== "Fox News"}On Fox News's scale.{/if}
	</p>
	{/if}
</div>

<style>
	.word-compare {
		max-width: 100%;
		margin: 8px auto 20px;
	}
	.controls {
		display: flex;
		justify-content: center;
		margin-bottom: 6px;
	}
	/* the CMS's chart title, drawn here so it can change with the pills */
	.chart-title {
		font-size: 19px;
		text-align: center;
		margin: 0 0 10px;
		color: var(--color-ink);
	}
	/* the outlet pills, as on the dot plot */
	.picker {
		display: inline-flex;
		gap: 6px;
		flex-wrap: wrap;
		justify-content: center;
	}
	.picker button {
		display: inline-flex;
		align-items: center;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 999px;
		background: rgba(255, 253, 248, 0.35);
		padding: 3px 8px;
		cursor: pointer;
		opacity: 0.85;
	}
	.picker button:hover {
		opacity: 1;
	}
	.picker button.active {
		opacity: 1;
		background: rgba(255, 253, 248, 0.95);
		border-color: var(--color-ink);
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.18);
	}
	.picker img {
		display: block;
		height: 12px;
		width: auto;
	}
	.picker button.square img {
		height: 15px;
	}
	/* the panels, as on the outlet-topic small multiples */
	.multiples {
		max-width: 1000px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(30, minmax(0, 1fr));
		gap: 14px 22px;
	}
	.pane {
		min-width: 0;
	}
	.pane-hed {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		height: 24px;
		margin-bottom: 2px;
	}
	.pane-hed img {
		display: block;
	}
	@media (max-width: 640px) {
		.grid {
			grid-template-columns: 1fr;
		}
		.pane {
			grid-column: 1 / -1 !important;
		}
	}
	.rows {
		display: flex;
		flex-direction: column;
		gap: 0;
	}
	.row {
		position: relative;
	}
	.row-word {
		position: absolute;
		left: 42px;
		top: 4px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px;
		font-weight: 700;
		color: #7a4a00;
		z-index: 1;
	}
	.note {
		font-size: 12px;
		color: rgba(42, 21, 3, 0.6);
		margin: 6px 0 0;
		text-align: center;
	}
</style>
