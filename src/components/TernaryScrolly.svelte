<script>
	// Chyron ternary walked through: the plot holds still and the called-out
	// words arrive one beat at a time.
	// Doc embed:  chart: ternary-scrolly | steps: swapSteps
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";

	let { steps = null } = $props();

	const FALLBACK = [
		{
			groups: [],
			html: "This is every word in the three networks&rsquo; cable coverage of the WNBA, via "
				+ "their chyrons. A word sits nearest the network that says it most."
		},
		{
			groups: [["viktor", "bout"]],
			html: "While MSNBC named the man Griner was exchanged for, Viktor Bout&hellip;"
		},
		{
			groups: [["merchant", "death"]],
			html: "&hellip;Fox mostly used his moniker: The Merchant of Death."
		},
		{
			groups: [["viktor", "bout"], ["merchant", "death", "trade"]],
			html: "By dramatizing his danger, they reinforced the idea that Griner&rsquo;s swap was "
				+ "a bad deal."
		}
	];

	// ArchieML gives "viktor, bout / merchant, death" — one group per slash
	const parseGroups = (step) => {
		const raw = (step.groups ?? step.words ?? "").trim();
		if (!raw) return [];
		return raw.split("/")
			.map((band) => band.split(",").map((w) => w.trim()).filter(Boolean))
			.filter((band) => band.length);
	};
	const STEPS = $derived(
		steps?.length
			? steps.filter((step) => (step.text ?? "").trim()).map((step) => ({
				groups: parseGroups(step),
				img: (step.img ?? "").trim(),
				html: step.text ?? "" }))
			: FALLBACK
	);

	let index = $state(0);
	let current = $derived(STEPS[index ?? 0] ?? STEPS[0]);
</script>

<section class="ternary-scrolly">
	<div class="sticky">
		<TernaryStatic groups={current.groups} bare big highlightColor="#c0392b" />
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					<div class="card">
						{#if step.img}
							<img class="step-img" src="{base}/images/{step.img}"
								alt="" loading="lazy" />
						{/if}
						<p class="card-text">{@html step.html}</p>
					</div>
				</div>
			{/each}
		</Scrolly>
	</div>
</section>

<style>
	.ternary-scrolly { position: relative; margin: 24px 0; }

	.sticky {
		position: sticky; top: 0; height: 100vh;
		display: flex; align-items: center; justify-content: center;
	}
	.sticky :global(.ternary-static) { width: min(660px, 92vw); }
	.sticky :global(svg) { max-height: 82vh; }

		.steps { position: relative; z-index: 1; margin-top: -100vh; pointer-events: none; }
	.step {
		height: 100vh; display: flex; align-items: center; justify-content: flex-start;
		pointer-events: none;
	}
	.card-text { margin: 0; }
	.step-img {
		display: block; width: 100%; border-radius: 3px;
		border: 1px solid rgba(42, 21, 3, 0.2); margin-bottom: 10px;
	}
	.card {
		max-width: 290px; margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid #c0392b;
		padding: 14px 16px; border-radius: 3px;
		font-size: 15.5px; line-height: 1.5; color: #2a1503;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3; transition: opacity 250ms ease;
	}
	.step.active .card { opacity: 1; }

	@media (max-width: 860px) {
		.sticky { height: 100vh; }
		.steps { margin-top: -100vh; }
		.card-text { margin: 0; }
	.step-img {
		display: block; width: 100%; border-radius: 3px;
		border: 1px solid rgba(42, 21, 3, 0.2); margin-bottom: 10px;
	}
	.card { max-width: 84vw; }
	}
</style>
