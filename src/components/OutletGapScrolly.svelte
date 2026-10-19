<script>
	import { base } from "$app/paths";
	// Head-to-head dot plot walked through. Doc options on the block:
	//   heading: How often Fox News names each player in WNBA headlines
	//   comparedWith: compared with    allOutlets: six other outlets combined
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import OutletGapDotPlot from "$components/OutletGapDotPlot.svelte";
	import { stageSteps } from "$utils/gapSteps.js";
	import { faces, clipPops } from "$utils/clips.js";

	let {
		steps = null,
		speed = 1000,
		heading = "",
		comparedWith = "",
		allOutlets = ""
	} = $props();

	const STEPS = $derived(stageSteps(steps));

	let index = $state(0);

	let last = $state(0);
	$effect(() => {
		if (index !== undefined && index !== null) last = index;
	});
	let current = $derived(STEPS[last] ?? STEPS[0]);
</script>

<section class="gap-scrolly">
	<div class="sticky">
		<OutletGapDotPlot
			highlight={current.explore ? null : current.names}
			bare={!current.explore}
			placed={current.placed}
			centered={current.center}
			{speed}
			centerLine
			wide
			{heading}
			{comparedWith}
			{allOutlets}
		/>
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					{#if step.html.trim()}
						<div class="stack">
							<p class="card">{@html clipPops(faces(step.html, base), base)}</p>
						</div>
					{/if}
				</div>
			{/each}
		</Scrolly>
		<!-- a beat after the last card, so the chart stays put while the reader explores -->
		<div class="linger"></div>
	</div>
</section>

<style>
	.gap-scrolly {
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
	/* cards overlapping the name column is accepted — clearing them cost ~120px of width */
	/* the frame is a column: title, pills and clipping on top, and the drawing
	   takes exactly the height that is left, so nothing is ever cut off */
	.sticky :global(.outlet-gap) {
		width: min(1040px, 97vw);
		height: 96vh;
		display: flex;
		flex-direction: column;
		justify-content: center;
	}
	/* the drawing keeps its own proportions: as wide as the box on a tall
	   screen, and shrunk to the height left on a short one — never a box
	   taller than the drawing with the slack above it */
	.sticky :global(.outlet-gap > .plot) {
		flex: 0 1 auto;
		min-height: 0;
	}
	.sticky :global(.outlet-gap > .plot > svg) {
		/* pixel-true: the drawing is already the frame's size */
		width: 100%;
		height: auto;
		display: block;
	}

	.steps {
		position: relative;
		z-index: 1;
		margin-top: -100vh;
		pointer-events: none;
	}
	.linger {
		height: 70vh;
	}
	.step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.stack {
		/* the cards sit over the middle of the plot, which already shows
		   through them: wider costs little here */
		max-width: 420px;
		opacity: 0.3;
		pointer-events: auto;
		margin: 0 auto;
		transition: opacity 250ms ease;
	}
	.step.active .stack {
		opacity: 1;
	}
	.card {
		margin: 0;
		background: #fff;
		padding: 14px 18px;
		border-radius: 4px;
		font-size: var(--step-text);
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
	}

	@media (max-width: 860px) {
		.stack {
			max-width: 84vw;
		}
	}
	/* the step cards let the pointer through to the chart behind them, but a
	   link in a step's text must still be clickable */
	.steps :global(a) {
		pointer-events: auto;
	}
</style>
