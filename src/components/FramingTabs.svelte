<script>
	// How Fox frames each player — tone / political / appearance / celebrity —
	import FacesBeeswarm from "$components/FacesBeeswarm.svelte";
	import HeadlineTable from "$components/HeadlineTable.svelte";

	let { words = [] } = $props();

	// the cross-outlet differential and receiving-end measures are still computed upstream
	const VIEWS = [
		{
			key: "tone",
			label: "Tone",
			blurb:
				"Average sentiment of every Fox headline naming her, from −1 to +1."
		},
		{
			key: "political",
			label: "Politicized",
			blurb:
				"Share of Fox headlines carrying political or culture-war language."
		},
		{
			key: "appearance",
			label: "Appearance",
			blurb: "Share of Fox headlines discussing appearances."
		},
		{
			key: "celebrity",
			label: "Celebrity",
			blurb:
				"Share of her Fox headlines about private life, appearance, and celebrity."
		},
		{
			key: "performance",
			label: "Performance",
			blurb:
				"Share of her Fox headlines about her actual play: points, rebounds, assists, records."
		}
	];
	// the table under the chart filters to the tab's measure (tone has no filter)
	const FRAME_OF = {
		tone: "all",
		political: "political",
		appearance: "appearance",
		celebrity: "celebrity",
		performance: "performance"
	};

	let view = $state(
		words[0] && VIEWS.some((v) => v.key === words[0]) ? words[0] : "tone"
	);
	let current = $derived(VIEWS.find((v) => v.key === view));
</script>

<div class="framing-tabs">
	<div class="tabs" role="group" aria-label="How to measure the framing">
		{#each VIEWS as option}
			<button
				class:active={view === option.key}
				onclick={() => (view = option.key)}
			>
				{option.label}
			</button>
		{/each}
	</div>
	<p class="blurb">{current.blurb}</p>

	<FacesBeeswarm metric={view} />
	<HeadlineTable embedded frame={FRAME_OF[view]} />
</div>

<style>
	.framing-tabs {
		max-width: 920px;
		margin: 0 auto;
	}
	.tabs {
		display: flex;
		justify-content: center;
		gap: 0;
		margin-bottom: 6px;
	}
	.tabs button {
		/* border: 1px solid rgba(42, 21, 3, 0.3); */
		border-right-width: 0;
		background: transparent;
		color: var(--color-ink);
		padding: 6px 16px;
		font: inherit;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
	}
	/* .tabs button:first-child { border-radius: 4px 0 0 4px; }
	.tabs button:last-child { border-right-width: 1px; border-radius: 0 4px 4px 0; } */
	.tabs button.active {
		background: var(--color-ink);
		color: #fff;
	}
	.blurb {
		text-align: center;
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.65);
		margin: 0 0 14px;
	}
</style>
