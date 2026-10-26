<script>
	// The per-player word bars (FightinWordsBars), loaded as the reader nears them
	// rather than built into the page: their data (player_words.json) is 11 MB, and
	// built in it held up every button on the first screen. The Doc's options pass
	// straight through.
	const AHEAD = "200%"; // start loading this far below the screen
	let props = $props();
	let Chart = $state(null);
	let holder = $state(null);
	$effect(() => {
		if (!holder) return;
		const io = new IntersectionObserver(
			(entries) => {
				if (!entries[0].isIntersecting) return;
				io.disconnect();
				import("$components/FightinWordsBars.svelte").then(
					(m) => (Chart = m.default)
				);
			},
			{ rootMargin: `${AHEAD} 0px` }
		);
		io.observe(holder);
		return () => io.disconnect();
	});
</script>

{#if Chart}
	<Chart {...props} />
{:else}
	<div class="holder" bind:this={holder}></div>
{/if}

<style>
	/* keeps the chart's place until it loads */
	.holder {
		min-height: 100vh;
	}
</style>
