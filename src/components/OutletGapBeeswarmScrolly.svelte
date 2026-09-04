<script>
	import { base } from "$app/paths";
	// Head-to-head beeswarm walked through — OutletGapScrolly with the swarm in the frame
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import OutletGapBeeswarm from "$components/OutletGapBeeswarm.svelte";
	import { stageSteps } from "$utils/gapSteps.js";
	import { faces, clipPops } from "$utils/clips.js";
	import HeadlineClip from "$components/HeadlineClip.svelte";

	let { steps = null } = $props();

	const STEPS = $derived(stageSteps(steps));

	let index = $state(0);
	// once no card is in view (scrolled past the end, or back above the start)
	// the chart keeps its last state instead of snapping back to step one
	let last = $state(0);
	$effect(() => {
		if (index !== undefined && index !== null) last = index;
	});
	let current = $derived(STEPS[last] ?? STEPS[0]);
</script>

<section class="gap-scrolly">
	<div class="sticky">
		<OutletGapBeeswarm
			highlight={current.explore ? null : current.names}
			bare={!current.explore}
			placed={current.placed}
		/>
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					<div class="stack">
						<p class="card">{@html clipPops(faces(step.html, base), base)}</p>
						{#if step.clip}
							<div class="clip-wrap"><HeadlineClip clip={step.clip} /></div>
						{/if}
					</div>
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
	/* the frame is a column: the picker on top, the swarm taking the height left */
	.sticky :global(.outlet-gap-beeswarm) {
		width: min(920px, 97vw);
		height: 96vh;
		display: flex;
		flex-direction: column;
	}
	.sticky :global(.outlet-gap-beeswarm > svg) {
		flex: 1 1 auto;
		min-height: 0;
		width: 100%;
		height: 100%;
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
		justify-content: flex-start;
	}
	.stack {
		max-width: 300px;
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.step.active .stack {
		opacity: 1;
	}
	.clip-wrap {
		margin-top: 14px;
	}
	.card {
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px;
		border-radius: 3px;
		font-size: 15.5px;
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
	}

	@media (max-width: 860px) {
		.stack {
			max-width: 84vw;
		}
	}
</style>
