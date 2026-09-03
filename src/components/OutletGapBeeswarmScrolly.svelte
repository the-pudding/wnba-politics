<script>
	// Head-to-head beeswarm walked through — OutletGapScrolly with the swarm in the frame
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import OutletGapBeeswarm from "$components/OutletGapBeeswarm.svelte";

	let { steps = null } = $props();

	const STEPS = $derived(
		(steps ?? [])
			.filter((step) => (step.text ?? "").trim())
			.map((step) => ({
				names: (step.names ?? step.words ?? "")
					.split(",")
					.map((n) => n.trim())
					.filter(Boolean),
				explore: step.explore === true || step.explore === "true",
				html: step.text ?? ""
			}))
	);

	let index = $state(0);
	let current = $derived(STEPS[index ?? 0] ?? STEPS[0]);
</script>

<section class="gap-scrolly">
	<div class="sticky">
		<OutletGapBeeswarm
			highlight={current.explore ? null : current.names}
			bare={!current.explore}
		/>
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					<p class="card">{@html step.html}</p>
				</div>
			{/each}
		</Scrolly>
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
	.sticky :global(.outlet-gap-beeswarm) {
		width: min(920px, 97vw);
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
	}
	.card {
		max-width: 300px;
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px;
		border-radius: 3px;
		font-size: 15.5px;
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.step.active .card {
		opacity: 1;
	}

	@media (max-width: 860px) {
		.card {
			max-width: 84vw;
		}
	}
</style>
