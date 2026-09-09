<script>
	// Two topic triangles side by side (stacked on phones), each with its
	// heat. With timeline: true one play button and one row of years drive
	// both. In the Doc:
	//   {.TernaryPair}
	//   topics: polrace, lgbtq
	//   timeline: true
	//   source: captions      (the closed captions instead of the chyrons)
	//   note: optional line under each triangle; {period} is filled in
	//   {}
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import chyYears from "$data/chyron_ternary_years.json";
	import capYears from "$data/captions_years.json";
	// source: chyrons (default) or captions, as on TernaryStatic
	let { topics = "polrace, lgbtq", note = null, timeline = false, source = "chyrons" } = $props();
	const yearly = source === "captions" ? capYears : chyYears;
	const withTimeline = timeline === true || timeline === "true";
	const HEAD = {
		polrace: "Race, politics and protest",
		lgbtq: "LGBTQ+ and trans athletes"
	};
	const COLOR = { polrace: "var(--color-politics)", lgbtq: "var(--color-lgbtq)" };
	const list = String(topics)
		.split(",")
		.map((t) => t.trim())
		.filter(Boolean);

	// one clock for both triangles
	const YEARS = (yearly.years ?? []).filter((y) => y >= "2018");
	let year = $state(null);
	let playing = $state(false);
	let playTimer = null;
	const YEAR_MS = 1400;
	function stopPlay() {
		clearInterval(playTimer);
		playTimer = null;
		playing = false;
	}
	function togglePlay() {
		if (playing) return stopPlay();
		playing = true;
		year = YEARS[0];
		playTimer = setInterval(() => {
			const i = YEARS.indexOf(year);
			if (i < 0 || i >= YEARS.length - 1) {
				stopPlay();
				year = null;
				return;
			}
			year = YEARS[i + 1];
		}, YEAR_MS);
	}
	$effect(() => () => clearInterval(playTimer));
</script>

<div class="ternary-pair-wrap">
	{#if withTimeline}
		<div class="years">
			<button
				class="play"
				onclick={togglePlay}
				aria-label={playing ? "Pause" : "Play"}>{playing ? "❚❚" : "▶"}</button
			>
			<div class="year-buttons" role="group" aria-label="Through which year">
				{#each YEARS as y (y)}
					<button
						class:on={year === y}
						onclick={() => {
							stopPlay();
							year = y;
						}}>{y}</button
					>
				{/each}
				<button
					class:on={year === null}
					onclick={() => {
						stopPlay();
						year = null;
					}}>all</button
				>
			</div>
		</div>
	{/if}
	<div class="ternary-pair">
		{#each list as topic (topic)}
			<div class="one">
				<h4 style="color:{COLOR[topic] ?? 'inherit'}">{HEAD[topic] ?? topic}</h4>
				<TernaryStatic {topic} {note} {source} timeline={withTimeline} controls={false} {year} />
			</div>
		{/each}
	</div>
</div>

<style>
	.ternary-pair-wrap {
		max-width: 1040px;
		margin: 12px auto 24px;
	}
	.ternary-pair {
		display: flex;
		gap: 18px;
	}
	.one {
		flex: 1 1 0;
		min-width: 0;
	}
	h4 {
		margin: 0 0 -6px;
		text-align: center;
		font-size: 15px;
	}
	.years {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		margin: 0 0 6px;
		flex-wrap: wrap;
	}
	.years .play {
		width: 30px;
		height: 26px;
		border: 0;
		border-radius: 5px;
		background: var(--color-ink);
		color: #fff;
		font-size: 11px;
		cursor: pointer;
	}
	.year-buttons {
		display: inline-flex;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 5px;
		overflow: hidden;
	}
	.year-buttons button {
		border: 0;
		background: transparent;
		color: var(--color-ink);
		font: inherit;
		font-size: 12px;
		font-weight: 700;
		padding: 4px 7px;
		cursor: pointer;
	}
	.year-buttons button.on {
		background: var(--color-ink);
		color: #fff;
	}
	@media (max-width: 860px) {
		.ternary-pair {
			flex-direction: column;
			gap: 6px;
		}
	}
</style>
