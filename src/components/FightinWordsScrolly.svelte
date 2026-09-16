<script>
	// The Fightin' Words scatter walked through
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import FightinWords from "$components/FightinWords.svelte";

	// chart: "scatter" (the quadrant) or "bars" (mirrored top words)
	let { steps = null, chart = "scatter", labels = "on", scale = "linear", caps = false, scores = false, ngrams = 1, note = undefined } = $props();

	const STEPS = $derived(
		(steps ?? [])
			.filter((step) => (step.text ?? "").trim())
			.map((step) => ({
				words: (step.words ?? "")
					.split(",")
					.map((w) => w.trim())
					.filter(Boolean),
				explore: step.explore === true || step.explore === "true",
				// a step can switch to two-word phrases (ngrams: 2) or back (ngrams: 1);
				// unset, the block's own setting carries on
				ngrams: String(step.ngrams ?? "").trim() || null,
				html: step.text ?? ""
			}))
	);

	let index = $state(0);
	// index can run one past the last card (the cardless sentinel step)
	let current = $derived(
		STEPS[Math.min(index ?? 0, STEPS.length - 1)] ?? STEPS[0]
	);
</script>

<section class="fw-scrolly" class:bars={chart === "bars"} class:open={index >= STEPS.length}>
	<div class="sticky">
		<!-- articles, not headlines: headline counts are too sparse for these words -->
		<FightinWords
			highlight={current.words}
			bare
			controls={current.explore}
			mode="articles"
			{chart}
			{labels}
			{scale}
			{caps}
			{scores}
			ngrams={current.ngrams ?? ngrams}
			fill={chart === "bars"}
			{note}
		/>
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					<p class="card">{@html step.html}</p>
				</div>
			{/each}
			<!-- cardless final beat: the chart stays put for another screen and a
			     half with every card gone, so the reader can search and click -->
			<div class="step step-open" aria-hidden="true"></div>
		</Scrolly>
	</div>
</section>

<style>
	.fw-scrolly {
		position: relative;
		margin: 24px 0;
	}

	.sticky {
		position: sticky;
		top: 0;
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	/* the bars hang from a fixed top: a step that adds rows or a card only
	   lengthens the chart downward, instead of re-centring it */
	.fw-scrolly.bars .sticky {
		align-items: flex-start;
		padding-top: 5vh;
		box-sizing: border-box;
	}
	/* flex item shrinks to its content without this */
	.sticky :global(.fightin-words) {
		width: min(1000px, 94vw);
	}
	/* leaves room for the controls the explore beat brings back; the bars
	   size their own rows to the viewport instead */
	.fw-scrolly:not(.bars) .sticky :global(svg) {
		max-height: 74vh;
	}

	.steps {
		position: relative;
		z-index: 1;
		margin-top: -100vh;
		pointer-events: none;
	}
	.step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
		pointer-events: none;
	}
	.card {
		max-width: 300px;
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px;
		border-radius: 3px;
		font-size: 15px;
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.35;
		transition: opacity 250ms ease;
	}
	.step.active .card {
		opacity: 1;
	}
	.step-open {
		height: 150vh;
	}
	/* on the open beat the cards leave the chart alone */
	.fw-scrolly.open .card {
		opacity: 0;
	}

	@media (max-width: 860px) {
		.sticky {
			height: 100vh;
		}
		.steps {
			margin-top: -100vh;
		}
		.card {
			max-width: 84vw;
		}
	}
</style>
