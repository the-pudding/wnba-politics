<script>
	// ---------------------------------------------------------------------------
	// Three views of how Fox frames each player, behind one set of tabs:
	//
	//   tone        — average sentiment of the headlines naming her
	//   political   — how often Fox makes her a political subject
	//   appearance  — how often the headline is about what she's wearing
	//   celebrity   — how often it is about her private life
	//
	// Same cast in all three, so switching tabs re-sorts the same people rather
	// than changing the subject.
	//
	// Doc embed:  chart: framing-tabs
	// ---------------------------------------------------------------------------
	import FacesBeeswarm from "$components/FacesBeeswarm.svelte";

	let { words = [] } = $props();

	// Four questions, all of them asked of Fox's own headlines. The cross-outlet
	// differential and the receiving-end measure are still computed — they are
	// one line away from coming back — but four tabs is the number a reader will
	// actually click through.
	const VIEWS = [
		{ key: "tone", label: "Tone",
		  blurb: "Average sentiment of every Fox headline naming her, from −1 to +1." },
		{ key: "political", label: "Politicized",
		  blurb: "Share of her Fox headlines carrying political or culture-war language." },
		{ key: "appearance", label: "Appearance",
		  blurb: "Share of her Fox headlines where a clothing word is grammatically hers." },
		{ key: "celebrity", label: "Celebrity",
		  blurb: "Share of her Fox headlines about her private life or her appearance — a partner, "
		       + "a divorce, a family member, an outfit — where the tabloid word is grammatically "
		       + "hers, not somebody else's in the same headline." },
	];

	let view = $state(words[0] && VIEWS.some((v) => v.key === words[0]) ? words[0] : "tone");
	let current = $derived(VIEWS.find((v) => v.key === view));
</script>

<div class="framing-tabs">
	<div class="tabs" role="group" aria-label="How to measure the framing">
		{#each VIEWS as option}
			<button class:active={view === option.key} onclick={() => (view = option.key)}>
				{option.label}
			</button>
		{/each}
	</div>
	<p class="blurb">{current.blurb}</p>

	<FacesBeeswarm metric={view} />
</div>

<style>
	.framing-tabs { max-width: 920px; margin: 0 auto; }
	.tabs { display: flex; justify-content: center; gap: 0; margin-bottom: 6px; }
	.tabs button {
		border: 1px solid rgba(42, 21, 3, 0.3); border-right-width: 0;
		background: transparent; color: #2a1503;
		padding: 6px 16px; font: inherit; font-size: 13px; font-weight: 600; cursor: pointer;
	}
	.tabs button:first-child { border-radius: 4px 0 0 4px; }
	.tabs button:last-child { border-right-width: 1px; border-radius: 0 4px 4px 0; }
	.tabs button.active { background: #2a1503; color: #fff; }
	.blurb { text-align: center; font-size: 12.5px; color: rgba(42, 21, 3, 0.65); margin: 0 0 14px; }
</style>
