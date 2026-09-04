<script>
	import { base } from "$app/paths";
	// Head-to-head dot plot walked through
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import OutletGapDotPlot from "$components/OutletGapDotPlot.svelte";
	import { stageSteps } from "$utils/gapSteps.js";
	import HeadlineClip from "$components/HeadlineClip.svelte";
	import { faces, clipPops } from "$utils/clips.js";

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

	// Where a step's headline clipping goes:
	//   wide desktop  — beside the chart, in the empty margin to its right
	//   narrower      — the slot above the plot
	//   phone         — under the step's text card
	let viewportWidth = $state(
		typeof window === "undefined" ? 1200 : window.innerWidth
	);
	let clipWhere = $derived(
		viewportWidth >= 1280 ? "side" : viewportWidth >= 640 ? "top" : "card"
	);
	let hasClips = $derived(STEPS.some((step) => step.clip));
	// the side card slides in with the first step that quotes a headline and
	// stays from then on: this step's clipping, else the last one shown (blurred)
	let lastClip = $state(null);
	$effect(() => {
		if (current.clip) lastClip = current.clip;
	});
	let sideClip = $derived(current.clip ?? lastClip);
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<section class="gap-scrolly">
	<div class="sticky">
		<OutletGapDotPlot
			highlight={current.explore ? null : current.names}
			bare={!current.explore}
			placed={current.placed}
			centered={current.center}
			clip={clipWhere === "top" ? current.clip : null}
			clipSlot={clipWhere === "top" && hasClips}
			centerLine
			clipHidden={current.explore}
			clipPlaceholder={STEPS.find((step) => step.clip)?.clip ?? null}
		/>
		{#if clipWhere === "side" && sideClip && !current.explore}
			<!-- wide screens: the clipping sits just right of the chart, blurred
			     between the steps that quote one -->
			<div class="side-clip">
				<HeadlineClip clip={sideClip} rot={1.2} blurred={!current.clip} />
			</div>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					<div class="stack">
						<p class="card">{@html clipPops(faces(step.html, base), base)}</p>
						{#if clipWhere === "card" && step.clip}
							<div class="clip-wrap">
								<HeadlineClip clip={step.clip} small />
							</div>
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
	/* cards overlapping the name column is accepted — clearing them cost ~120px of width */
	/* the frame is a column: title, pills and clipping on top, and the drawing
	   takes exactly the height that is left, so nothing is ever cut off */
	.sticky :global(.outlet-gap) {
		width: min(860px, 97vw);
		height: 96vh;
		display: flex;
		flex-direction: column;
	}
	.sticky :global(.outlet-gap > .plot) {
		flex: 1 1 auto;
		min-height: 0;
	}
	.sticky :global(.outlet-gap > .plot > svg) {
		width: 100%;
		height: 100%;
	}

	/* just right of the chart box: its right edge sits about 350px past the
	   page centre once the chart is slid to centre its equal line */
	.side-clip {
		position: absolute;
		left: min(calc(50% + 300px), calc(100% - 300px));
		top: 50%;
		transform: translateY(-50%);
		width: 280px;
		animation: slide-in 700ms cubic-bezier(0.22, 0.8, 0.3, 1);
	}
	@keyframes slide-in {
		from {
			opacity: 0;
			transform: translate(60vw, -50%);
		}
	}
	.clip-wrap {
		margin-top: 12px;
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
		max-width: 300px;
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.step.active .stack {
		opacity: 1;
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
