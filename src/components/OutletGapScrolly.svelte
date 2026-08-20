<script>
	// Head-to-head dot plot walked through: the plot holds still and each beat
	// calls out the players it's about, the rest receding.
	// Doc embed:  chart: outlet-gap-scrolly | steps: dotSteps
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import OutletGap from "$components/OutletGap.svelte";

	let { steps = null } = $props();

	const FALLBACK = [
		{ names: ["Caitlin Clark"],
		  html: "Overall, Fox News only discusses Caitlin Clark slightly more than other outlets." },
		{ names: ["DiJonai Carrington"],
		  html: "But they discuss players like DiJonai Carrington, who have committed fouls against "
		      + "Caitlin Clark, and who also have outspoken views against the Trump administration, "
		      + "much more." },
		{ names: ["Paige Bueckers", "Napheesa Collier", "A'ja Wilson"],
		  html: "And they discuss comparable stars like Paige Bueckers, Napheesa Collier, and "
		      + "A&rsquo;ja Wilson much less." },
		{ names: [], explore: true,
		  html: "Every player, and the outlet picker: set Fox against Yahoo, ESPN, CBS or USA Today "
		      + "on its own." }
	];

	const STEPS = $derived(
		steps?.length
			? steps.filter((step) => (step.text ?? "").trim()).map((step) => ({
				names: (step.names ?? step.words ?? "").split(",").map((n) => n.trim()).filter(Boolean),
				explore: step.explore === true || step.explore === "true",
				html: step.text ?? ""
			}))
			: FALLBACK
	);

	let index = $state(0);
	let current = $derived(STEPS[index ?? 0] ?? STEPS[0]);
</script>

<section class="gap-scrolly">
	<div class="sticky">
		<OutletGap highlight={current.explore ? null : current.names} bare={!current.explore} />
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
	.gap-scrolly { position: relative; margin: 24px 0; }

	.sticky {
		position: sticky; top: 0; height: 100vh;
		display: flex; align-items: center; justify-content: center;
	}
	/* cards overlapping the name column is accepted — clearing them cost ~120px of width */
	.sticky :global(.outlet-gap) { width: min(860px, 97vw); }
	/* height, not width, sizes this chart */
	.sticky :global(svg) { max-height: 93vh; }

	.steps { position: relative; z-index: 1; margin-top: -100vh; pointer-events: none; }
	.step {
		height: 100vh; display: flex; align-items: center; justify-content: flex-start;
	}
	.card {
		max-width: 300px; margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px; border-radius: 3px;
		font-size: 15.5px; line-height: 1.5; color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3; transition: opacity 250ms ease;
	}
	.step.active .card { opacity: 1; }

	@media (max-width: 860px) {
		.card { max-width: 84vw; }
	}
</style>
