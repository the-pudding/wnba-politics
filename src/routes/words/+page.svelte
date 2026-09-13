<script>
	import { base } from "$app/paths";
	import WordTimeline from "$components/WordTimeline.svelte";
	import data from "$data/word_timeline.json";
	const OUTLETS = ["Fox News", "ESPN", "CBS Sports", "USA Today", "The Athletic", "Just Women's Sports"];
	const LOGOS = { "Fox News": "fox-news.svg", ESPN: "espn.svg", "CBS Sports": "cbs-sports.svg", "USA Today": "usa-today.svg", "The Athletic": "the-athletic.png", "Just Women's Sports": "jws.png" };
	const ALL_WORDS = Object.keys(data.outlets["Fox News"].words);
	let outlet = $state("Fox News");
	let scope = $state("any");
	let chosen = $state(["hip-check", "poke", "punch", "throat"]);
	let by = $state("week");
	let from = $state("2024-01-01");
	let mark = $state("2026-07-07");
	// every outlet on Fox's y-axis, so the pictures compare
	let sameScale = $state(true);
	const toggle = (w) => (chosen = chosen.includes(w) ? chosen.filter((x) => x !== w) : [...chosen, w]);
	let total = $derived(Object.values(data.outlets[outlet].articles).reduce((s, n) => s + n, 0));
</script>

<div class="page">
	<h2>Words, week by week, by outlet</h2>
	<div class="controls">
		<span class="label">Outlet</span>
		<div class="picker" role="group" aria-label="Outlet">
			{#each OUTLETS as o}
				<button class:active={outlet === o} class:square={LOGOS[o].endsWith(".png")} title={o} aria-label={o} onclick={() => (outlet = o)}>
					<img src="{base}/logos/{LOGOS[o]}" alt="" />
				</button>
			{/each}
		</div>
		<span class="label">the word</span>
		<div class="toggle-group" role="group" aria-label="Where the word appears">
			<button class:active={scope === "any"} onclick={() => (scope = "any")}>anywhere in the article</button>
			<button class:active={scope === "headline"} onclick={() => (scope = "headline")}>in the headline</button>
			<button class:active={scope === "mentions"} onclick={() => (scope = "mentions")}>every mention</button>
		</div>
		<div class="toggle-group" role="group" aria-label="By">
			<button class:active={by === "week"} onclick={() => (by = "week")}>week</button>
			<button class:active={by === "day"} onclick={() => (by = "day")}>day</button>
		</div>
		<div class="toggle-group" role="group" aria-label="Scale">
			<button class:active={sameScale} onclick={() => (sameScale = true)}>Fox's scale</button>
			<button class:active={!sameScale} onclick={() => (sameScale = false)}>own scale</button>
		</div>
	</div>
	<div class="controls words">
		{#each ALL_WORDS as w}
			<button class="chip" class:on={chosen.includes(w)} onclick={() => toggle(w)}>{w}</button>
		{/each}
	</div>
	<div class="controls">
		<label>from <input type="date" bind:value={from} /></label>
		<label>mark <input type="date" bind:value={mark} /></label>
	</div>
	<p class="note">
		{outlet}: {total.toLocaleString()} WNBA articles in the corpus.
	</p>
	{#key `${outlet}|${scope}|${by}|${from}|${mark}|${sameScale}|${chosen.join(",")}`}
		<WordTimeline {outlet} {scope} {by} {from} {mark} scaleTo={sameScale ? "Fox News" : ""} words={chosen.length > 1 ? chosen.join(", ") : ""} word={chosen[0] ?? "hip-check"} />
	{/key}
</div>

<style>
	.page { max-width: 960px; margin: 0 auto; padding: 24px 20px 60px; }
	h2 { font-size: 20px; margin: 0 0 14px; color: var(--color-ink); }
	.controls { display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
	.label { font-size: 13px; color: var(--color-ink); }
	.picker { display: inline-flex; gap: 6px; flex-wrap: wrap; }
	.picker button { display: inline-flex; align-items: center; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 999px; background: rgba(255, 253, 248, 0.35); padding: 3px 8px; cursor: pointer; opacity: 0.85; }
	.picker button.active { opacity: 1; background: rgba(255, 253, 248, 0.95); border-color: var(--color-ink); box-shadow: 0 1px 4px rgba(42, 21, 3, 0.18); }
	.picker img { display: block; height: 12px; width: auto; }
	.picker button.square img { height: 15px; }
	.toggle-group { display: inline-flex; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 4px; overflow: hidden; }
	.toggle-group button { border: 0; background: transparent; color: var(--color-ink); padding: 5px 11px; font-size: 12.5px; font-weight: 600; cursor: pointer; }
	.toggle-group button.active { background: var(--color-ink); color: #fff; }
	.chip { border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 999px; background: transparent; color: rgba(42, 21, 3, 0.7); padding: 3px 10px; font-size: 12.5px; font-weight: 600; cursor: pointer; }
	.chip.on { background: var(--color-ink); color: #fff; border-color: var(--color-ink); }
	label { font-size: 12.5px; color: var(--color-ink); display: inline-flex; gap: 6px; align-items: center; }
	input[type="date"] { font: inherit; font-size: 12.5px; padding: 3px 6px; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 4px; background: #fffdf8; }
	.note { text-align: center; font-size: 12.5px; color: rgba(42, 21, 3, 0.6); margin: 2px 0 8px; }
</style>
