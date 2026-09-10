<script>
	// A small figure: a few words, week by week, for one outlet at a time —
	// Fox News by default, the five sports outlets a click away, every one on
	// Fox's scale so they compare. In the Doc:
	//   {.WordCompare}
	//   words: hip-check, poke, punch, throat
	//   from: 2024-01-01
	//   mark: 2026-07-07        (optional)
	//   title: ...
	//   {}
	import { base } from "$app/paths";
	import WordTimeline from "$components/WordTimeline.svelte";

	let { words = "hip-check, poke, punch, throat", from = "2024-01-01", to = "", mark = "" } = $props();

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

<div class="word-compare">
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
		<!-- drawn at the text column's width, so the type stays true size -->
		<WordTimeline {outlet} {words} {from} {to} {mark} by="week" scope="any" scaleTo="Fox News" width={700} height={280} />
	{/key}
	<p class="note">
		{outlet}: articles per week that use each word anywhere in the text.
		{#if outlet !== "Fox News"}On Fox News's scale.{/if}
	</p>
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
	.note {
		font-size: 12px;
		color: rgba(42, 21, 3, 0.6);
		margin: 6px 0 0;
		text-align: center;
	}
</style>
